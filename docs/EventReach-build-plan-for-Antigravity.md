# EventReach: Build Plan for Antigravity

Audience: an AI coding agent (Antigravity) working inside the existing EventReach repo, plus the human reviewing its work (B2).
Scope of this plan: everything from login to the dashboard **except phone-call automation**, which is left as a clearly marked empty slot (section 10).

---

## 0. How to use this document

1. Read sections 1 to 4 first. They explain how the whole product fits together.
2. Build in the order of section 14. Finish and test each phase before the next.
3. Rules the agent must follow in every task:
   - **The API contract is `api/app/schemas.py` (exported to `docs/openapi.json`).** Do not rename or remove fields. Adding optional fields is fine. After any schema change run `python scripts/export_openapi.py` from `api/`.
   - **Keep the mock mode working.** If `DATABASE_URL` is empty the API still answers every endpoint with sample data, because the frontend team builds against it.
   - **Every organizer endpoint requires login** (`current_organizer` dependency in `api/app/auth.py`) and every query is scoped to the organizer who owns the campaign. A user must never reach another organizer's campaign by guessing an ID.
   - **Never log or return a full phone number.** Only `phone_masked` leaves the API. Phones are stored as `phone_enc` (encrypted) plus `phone_hash` (salted HMAC).
   - **Never invent facts.** Any AI step that cannot find a value returns `null` and lists it in `needs_review`. A confident wrong date is worse than a blank.
   - Every AI call goes through one module (`api/app/ai/`) with a spending cap (`LLM_MONTHLY_BUDGET_USD`) and a fake provider for tests. Tests never call a real model.
   - Always `conn.commit()` after writes. Add `::text[]` when selecting enum arrays.
   - Write tests with each feature. Existing tests (66) must keep passing.
4. Existing code to build on: `auth.py`, `db.py`, `dbsetup.py`, `csv_import.py`, `privacy.py`, `mock_data.py`, `main.py`, `schemas.py`, `db/schema.sql`, `docs/*.md`.

---

## 1. The product flow, screen by screen

| # | Screen | What the organizer does | What the system does behind it |
|---|---|---|---|
| 1 | Login | Signs in | Issues a token (done) |
| 2 | Choose type | Picks a preset: seminar invite, clinic reminder, school notice, payment reminder | Creates a draft campaign linked to that template. The template decides which fields the event needs and which keypad options the call offers |
| 3 | Upload poster and voice note | Drops a poster image and records or uploads a voice note | Stores both privately, transcribes the voice, reads the poster, extracts structured event details |
| 4 | Confirm details | Reviews and edits the extracted details | Shows each value next to the evidence it came from. Saving locks the **event record** that everything else is generated from |
| 5 | Upload contacts | Uploads a CSV | Validates and imports (done), stores encrypted phones, groups by language and segment |
| 6 | Translations | Reviews the message in each language found in the contact list | Generates translations, back-translates to English, runs a fact check, organizer approves each language |
| 7 | Channels and schedule | Chooses which channels to use (call, SMS, email, WhatsApp, Instagram) and when | Generates the content for each channel from the same event record. Shows previews |
| 8 | Call automation | (left blank for now, section 10) | |
| 9 | Test call and launch | Sends a test to themselves, then launches | Preflight checks must pass before the launch button works |
| 10 | Dashboard | Watches results | Shows outcomes by campaign, language and segment, with a retry action. Registration and payment status feed in |

---

## 2. The one idea that keeps everything accurate

**There is one source of truth: the approved event record.** Poster text, voice transcript, translations, call scripts, emails, WhatsApp messages, Instagram captions and the registration page are all *derived* from it. None of them is typed separately.

```
poster ---------\
                 +--> extraction --> EventDraft --(organizer approves)--> EVENT RECORD (versioned)
voice note -----/                                                              |
                                                                               v
                                         template engine (variables + language + channel)
                                                                               |
        +----------------+----------------+----------------+----------------+--+
        v                v                v                v                v
   call script     SMS / link        email + poster   WhatsApp text    Instagram caption
   (per language)  (per language)    (per language)   (per language)   + image
        |                |                |                |                |
        +----------------+--------+-------+----------------+----------------+
                                   v
                      personal link per contact  -->  registration page  -->  payment
                                   v
                        responses and stages  -->  DASHBOARD
```

### Versioning rule (this prevents stale, wrong messages)

- The event record has a `version` and a `content_hash` over its meaningful fields (title, start, end, venue, city, fee, capacity, contact, description).
- Every translation and every generated channel message stores the `event_version` it was made from.
- If the organizer edits the event after translations exist, every dependent item becomes `stale`. The UI shows "details changed, regenerate" and **launch is blocked** while anything is stale.
- Editing a translation by hand does not change the event version, but marks that translation `edited`, and it must be re-approved.

### Campaign status machine

```
draft -> details_approved -> audience_ready -> translations_approved -> content_ready -> tested -> launched -> completed
```

Each step is only reachable from the previous one. Going back to an earlier step (editing the event) moves later steps back to `needs_regeneration`, never silently keeps old content.

---

## 3. Data that links everything

Check `db/schema.sql` first and extend it with migrations in `dbsetup.py`. Do not drop existing tables. Proposed additions (adjust names to match the existing style):

| Table | Purpose | Key columns |
|---|---|---|
| `media_assets` | Poster images and voice notes | `id`, `campaign_id`, `kind` (poster, voice_note), `storage_key`, `mime`, `size_bytes`, `sha256`, `uploaded_by`, `created_at`, `delete_after` |
| `transcripts` | Result of speech to text | `id`, `asset_id`, `text`, `detected_language`, `language_confidence`, `segments` (json with timestamps), `provider`, `created_at` |
| `event_drafts` | Raw extraction output, kept for audit | `id`, `campaign_id`, `source_transcript_id`, `source_poster_asset_id`, `fields` (json), `evidence` (json), `confidence` (json), `needs_review` (text[]), `model`, `prompt_version`, `created_at` |
| `events` | The approved event record | `id`, `campaign_id`, `version`, `content_hash`, title, `starts_at`, `ends_at`, venue, city, `fee_inr`, capacity, `organizer_contact`, `description`, `approved_by`, `approved_at` |
| `translations` | One per campaign, language, channel | `id`, `campaign_id`, `language`, `channel`, `event_version`, `body`, `back_translation`, `fact_check` (json), `status` (generated, edited, approved, stale), `approved_by`, `approved_at`, `content_hash` |
| `outreach_items` | Everything that goes out on a non-call channel | `id`, `campaign_id`, `channel`, `language`, `segment`, `subject`, `body`, `media_asset_id`, `event_version`, `scheduled_at`, `status` (draft, approved, queued, sent, failed, mocked), `provider_ref`, `error` |
| `outreach_log` | One row per message to one person | `id`, `item_id`, `contact_id`, `status`, `sent_at`, `error` |
| `ai_usage` | Cost control | `id`, `purpose`, `model`, `input_units`, `output_units`, `cost_usd`, `campaign_id`, `created_at` |

Existing tables (campaigns, contacts, templates, consents, etc.) stay. `contacts` gets `phone_enc` and `phone_hash` filled when import moves to the database.

---

## 4. API surface to add or change

Keep existing paths. New or changed, all behind login and scoped to the owner:

| Method | Path | Purpose |
|---|---|---|
| GET, POST | `/campaigns` | Real database versions. A list returns only the organizer's own |
| GET | `/campaigns/{id}` | One campaign with its status and a `checklist` of what blocks launch |
| POST | `/campaigns/{id}/poster` | Upload poster. Validates type (png, jpg, webp), size, and reads the image |
| POST | `/campaigns/{id}/voice-note` | Upload voice note. Returns an `EventDraft` (section 5) |
| POST | `/campaigns/{id}/extract` | Re-run extraction after a new poster, a new voice note or a corrected transcript |
| PUT | `/campaigns/{id}/transcript` | Organizer corrects the transcript, then calls `/extract` again |
| PUT | `/campaigns/{id}/event` | Approve and save event details. Creates a new event version |
| POST | `/campaigns/{id}/audience` | Import (done). Persist contacts, encrypted |
| GET | `/campaigns/{id}/languages` | Languages present in the audience with counts. Drives what gets translated |
| POST | `/campaigns/{id}/translations/generate` | Generate translations for all needed languages and channels |
| GET | `/campaigns/{id}/translations` | List with back-translation and fact check result |
| PUT | `/campaigns/{id}/translations/{language}` | Edit or approve |
| POST | `/campaigns/{id}/content/generate` | Generate email, WhatsApp, SMS and Instagram content from the event record |
| GET, PUT | `/campaigns/{id}/content/{item_id}` | Preview, edit, approve |
| POST | `/campaigns/{id}/channels` | Choose channels and schedule |
| POST | `/campaigns/{id}/preflight` | Returns every blocker before launch (section 11) |
| POST | `/campaigns/{id}/test-send` | Send each non-call channel to the organizer's own address, number or test account |
| GET | `/campaigns/{id}/media/{asset_id}` | Short-lived signed link to a private file |

---

## 5. Voice note to event details: the accuracy-critical part

Goal: the organizer speaks naturally, in any supported language (including mixed Hindi and English or Malayalam and English), and the app reliably gets the event name, date, time, venue, city, fee and capacity right, or says clearly what it is unsure of.

### 5.1 Pipeline

```
upload -> validate -> normalize audio -> transcribe -> (organizer can fix transcript)
      -> read poster text -> extract fields from both -> cross-check -> resolve dates
      -> score confidence -> EventDraft with evidence and needs_review
```

**Step 1. Validate and store.** Accept common audio types (mp3, m4a, wav, ogg, webm) up to a sensible limit (for example 10 MB or 3 minutes). Reject others with a plain sentence. Store privately, record the SHA-256, set `delete_after` from retention settings.

**Step 2. Normalize audio.** Convert to mono 16 kHz with ffmpeg if available. Fail gracefully with a clear message if it is not.

**Step 3. Transcribe.** Put speech to text behind an interface:

```python
class Transcriber(Protocol):
    def transcribe(self, audio_path: str, language_hint: str | None) -> Transcript: ...
```

`Transcript` has `text`, `detected_language`, `language_confidence`, and `segments` with start and end times. Provide a `FakeTranscriber` for tests and one real provider chosen by the team. The provider must support Hindi, Malayalam and Tamil, and the choice and its processing region must be written into the data protection note. Do not hard-code a vendor in feature code.

**Step 4. Show and allow correction of the transcript.** The UI shows the transcript before or beside the extracted details. Wrong names in transcripts are the most common error source, so the organizer can edit it and re-run extraction cheaply (`PUT /transcript`, then `POST /extract`).

**Step 5. Read the poster.** Poster text comes from the image (vision-capable model or OCR). Treat the poster as a second source for the same fields. Posters usually have the official event title, date and venue spelled correctly, so the poster should win on spelling of names and the voice note should win on details the poster lacks (for example, "bring your ID").

**Step 6. Structured extraction.** Call the language model with a strict JSON schema, one call combining transcript and poster text. Requirements for the prompt (version it as `prompt_version`):

- Role: "You extract event details. You never guess."
- Output must validate against the schema below. Retry once on invalid JSON, then fall back to all-null with a `needs_review` list.
- For every field return `value`, `evidence` (the exact quote from the transcript or poster that supports it) and `source` (`voice`, `poster`, `both`).
- If a value is not stated, return `null`. Do not infer fee, capacity or venue.
- Dates: capture the words the speaker used ("next Saturday", "the fourteenth") as `raw_date_text`. A separate **code** step turns them into real dates (see 5.3). The model must not do date arithmetic.
- Event name: return the full official title as spoken or printed. Return `title_candidates` (up to 3) if the name is ambiguous. Do not translate the title.
- Keep proper nouns (people, venues, city names) exactly as heard or printed, in the original script.
- Return `detected_language` of the voice note.

Schema (fields marked required must be present, but may be null):

```json
{
  "title":        { "value": "string|null", "evidence": "string|null", "source": "voice|poster|both|null" },
  "title_candidates": ["string"],
  "raw_date_text": "string|null",
  "start_time_text": "string|null",
  "end_time_text": "string|null",
  "venue":        { "value": "string|null", "evidence": "...", "source": "..." },
  "city":         { "value": "string|null", "evidence": "...", "source": "..." },
  "fee":          { "amount": "number|null", "currency": "INR|null", "evidence": "...", "free": "boolean|null" },
  "capacity":     { "value": "integer|null", "evidence": "..." },
  "organizer_contact": { "name": "string|null", "phone": "string|null", "email": "string|null" },
  "description":  "string|null",
  "audience_note": "string|null",
  "detected_language": "en|hi|ml|ta|other"
}
```

**Step 7. Cross-check voice against poster.** In code, not in the model. Compare title, date, venue and fee between the two sources after normalizing case and spacing. If they disagree, keep both values, mark the field `conflict`, put it in `needs_review`, and show both to the organizer with their evidence. Never silently pick one for date or fee.

**Step 8. Resolve dates in code.** Take `raw_date_text` and `start_time_text` and convert them using the server date and the `Asia/Kolkata` time zone:
- Absolute dates ("14 November", "14/11") become a full date. If no year is stated, use the next occurrence in the future.
- Relative phrases ("this Saturday", "next Friday", "tomorrow") are resolved against today and the resolved date is displayed with its weekday so the organizer can see an error immediately.
- Times like "ten in the morning" or "4 PM" become 24 hour times. If AM or PM is missing, leave the time null and add `starts_at` to `needs_review`.
- If the resulting date is in the past, set it null and flag it.
- Use a small, well-tested date parser; do not trust the model for this. Include tests for English, Hindi, Malayalam and Tamil phrasings, spoken numbers, and the Indian date order day-month-year.

**Step 9. Confidence and needs_review.** A field goes to `needs_review` when: it is null, in conflict, has no evidence quote, the quote is not actually found in the source text (this catches model hallucination: verify with a substring or fuzzy match), or the transcript confidence is low. Required for a seminar: title, starts_at, venue, city. Fee and capacity are optional but flagged when null.

**Step 10. Return `EventDraft`.** Keep the existing shape (`transcript`, `detected_language`, `event`, `needs_review`) and add optional fields: `evidence`, `conflicts`, `title_candidates`, `poster_text`, `prompt_version`. Existing consumers keep working.

### 5.2 The confirmation screen (screen 4) must

- Show every field as an editable input, with a small "heard: …" line from the evidence.
- Highlight fields in `needs_review` and block saving until required ones are filled or acknowledged.
- Show the resolved date with weekday, in the organizer's language, so mistakes jump out.
- Offer the title candidates as one-tap choices.
- Show the transcript in a collapsible panel with an edit and "re-read" button.
- On save, create `events` row version N+1 and mark dependent translations and content `stale`.

### 5.3 Template aware extraction

Different presets need different fields. Read the preset's `variables` list from the template, and ask for exactly those:
- Seminar invite: title, date, time, venue, city, fee, speaker, registration needed.
- Clinic reminder: patient name comes from the contact list, not the voice note. The voice note provides clinic name, doctor, appointment instructions.
- School notice: title, date, class or group, action needed.
- Payment reminder: amount, due date, payment link, late fee note.
Per-contact values (name, appointment time, amount due) come from CSV columns and are merged at send time, never extracted from the voice note.

### 5.4 Tests and a quality bar (the agent must create these)

- A golden set in `api/tests/golden/` of at least 20 transcripts plus expected JSON: English, Hindi, Malayalam, Tamil, code-mixed, missing fields, conflicting date between poster and voice, relative dates, spoken numbers ("five hundred rupees"), names with initials, noisy transcripts.
- A test runner that uses the `FakeProvider` with recorded responses, so it runs offline in CI.
- A separate optional script `scripts/eval_extraction.py` that runs the real provider against the golden set and prints per-field accuracy. Target: title 95 percent, date 95 percent, venue 90 percent. Record results in `docs/extraction-eval.md`.
- Unit tests for the date resolver (30 or more cases) and for the evidence check (a quote that is not in the source is rejected).
- Test that an extraction with all fields null still returns a valid draft and does not crash.

---

## 6. Translation linked to the event record

Languages needed = languages found in the contact list (`GET /languages`), plus English as the reference. Start with `en`, `hi`, `ml`, `ta`.

### 6.1 What gets translated and what never does

Build the message **from the template with placeholders**, then translate the *template wording*, and insert event facts afterwards. This protects the facts.

- Protected values (inserted after translation, never passed through the model as free text): event title, venue, city, fee amount, date, time, links, phone numbers, person names.
- Dates and times are formatted per language by code (for example `14 नवंबर, सुबह 10:00`), not translated by the model.
- Numbers use the same digits as the source unless the organizer picks otherwise.
- Event title stays in the original script, optionally with a transliteration in brackets for Indic scripts. Make this an option on the translation screen.
- A glossary (`api/app/ai/glossary.py`) for fixed terms: RSVP, registration, seminar, workshop, press 1, and so on, per language. Used in the prompt and checked afterwards.

### 6.2 Generation

For each (language, channel) pair:
1. Take the approved template wording for the channel.
2. Ask the model to translate the wording only, keeping `{placeholders}` untouched, using a natural spoken register for calls and short, polite written language for SMS and WhatsApp.
3. Code checks that every placeholder is present exactly once and no extra ones were added. Retry once, then flag.
4. Fill placeholders from the event record.
5. Cache by `(template_hash, language, channel)` so identical requests cost nothing.

### 6.3 Review aids for the organizer, who may not read the language

1. **Back-translation to English**, done by a separate call with no access to the original English, so it is a real check.
2. **Fact check (automatic):** extract date, time, venue, fee and title from the translated text using code (regexes and the known inserted values) and compare with the event record. Any mismatch marks the translation `needs_review` with the reason.
3. **Length check:** call script under about 25 seconds when read aloud (estimate by words per second per language), SMS segments counted correctly (GSM versus Unicode), WhatsApp and Instagram limits.
4. Show original, translation and back-translation side by side with a green, amber or red status.
5. Statuses: `generated`, `edited`, `approved`, `stale`. **Launch needs every language that has contacts to be `approved`.**
6. A native speaker review is recommended before the live demo (the checklist already assigns this to F3).

### 6.4 Linking back to the audience

Each contact has a `language`. At send time the system picks the contact's language, falls back to the campaign default if that language is not approved, and records which language was used on the attempt. The dashboard's language breakdown reads this same field, so numbers are consistent between sending and reporting.

---

## 7. Template engine

One function turns data into a message:

```
render(template_key, channel, language, event_record, contact, links) -> RenderedMessage
```

- Variables come from three places: the event record (shared), the contact row (personal: name, appointment time, amount due), and system values (personal registration link, opt-out words).
- Missing required variables raise a clear error at **preflight**, not at send time. The error names the variable and the number of contacts missing it.
- The four presets are seeded already; extend each with channel specific wording and keypad options.
- Every message includes an opt-out route for non-call channels ("Reply STOP") and, for calls, a keypad option, without exceptions. Opt-outs are global by `phone_hash` and always override a schedule or retry.

---

## 8. Outreach content: email, WhatsApp, SMS and Instagram

All of these are generated from the same event record and the same approved translations.

### 8.1 Common design

```python
class Channel(Protocol):
    name: str
    def validate(self, item) -> list[str]: ...        # problems found before sending
    def preview(self, item) -> dict: ...              # what the organizer will see
    def send(self, item, recipient) -> SendResult: ...
```

- A **mock adapter** for each channel (default while `MOCK_CHANNELS=true`) that writes what would be sent to `outreach_log` with status `mocked` and shows it in the UI. This is what the demo uses for anything not yet approved by the real provider.
- Real adapters are added behind the same interface only when credentials exist.
- Sending is done by a background worker (Redis queue later). Each item is idempotent: a retry never sends the same message twice to the same person.
- Respect consent and opt-out before every send. Respect quiet hours (no messages between 21:00 and 08:00 local time, configurable).
- Rate limit per channel and keep a daily cap.

### 8.2 Email

- Content: subject line, HTML body and plain text fallback, poster as an inline or attached image, personal registration link, unsubscribe line, per language.
- Subject generated from the event title and date (never from free-form model output without the fact check).
- Send through SMTP using the existing `SMTP_*` variables. Test send goes to the organizer.
- Template layout comes from the frontend team (F3 provides message layouts); the backend only fills slots.

### 8.3 WhatsApp

- Outbound business messages to people who have not messaged first must use **pre-approved message templates** on the WhatsApp Business platform. That approval takes time and may not be ready, so default to mock mode and make the mock show the exact template name, variables and rendered text.
- Build a `whatsapp_templates` mapping from (preset, language) to approved template name, with variables in order. Content generation fills the variables.
- Include the personal link and the poster as a media header where the template allows.
- Delivery status webhooks (`sent`, `delivered`, `read`, `failed`) update `outreach_log`.

### 8.4 SMS

- Short text with the personal link. Count segments correctly (70 characters per segment for Unicode, 160 for plain). Warn when a Hindi, Malayalam or Tamil message goes over three segments.
- Indian SMS rules require registered sender IDs and templates. Mock until confirmed with the provider.

### 8.5 Instagram

- Instagram publishing is for **business or creator accounts** connected through the official platform API, which takes setup and review. Treat live posting as optional and default to mock.
- Generate: a caption (title, date, venue, call to action, link in bio note), hashtags (a short, relevant set), and the image (the poster, resized to the required aspect ratios: 1:1 and 4:5, with a check that important text is not cropped).
- Provide a **manual fallback**: "Download image and copy caption" so the organizer can post by hand in 10 seconds if the API is not available. This is a real feature, not an apology; it keeps the demo safe.
- Caption length limit 2,200 characters, hashtag count limit 30, aim for 5 to 8.
- One post per campaign per language is allowed, scheduled by the organizer.

### 8.6 Linking outreach to the funnel

Every link in an email, SMS, WhatsApp or post carries a personal or campaign token (`/r/{token}`), so clicks, registrations and payments are attributed to the channel that produced them. The dashboard's channel breakdown reads `outreach_log` and the registration source. Social posts use a campaign token with the source `instagram` since they are not personal.

### 8.7 Content generation prompts

Use the model only for *wording*: tone, caption style, hashtags. Facts are inserted by code. Every generated item passes the same fact check as translations before it can be approved.

---

## 9. Contacts and privacy (done in step 5 but linked everywhere)

- Move the CSV import to the database: store `phone_enc` (encrypted with `ENCRYPTION_KEY`) and `phone_hash` (HMAC with `PHONE_HASH_PEPPER`). Fail startup if these are empty in non-mock mode.
- Dedupe within a campaign by `phone_hash`. Opt-outs are global by `phone_hash`.
- The registration token for each contact is random and unguessable, and expires.
- Log every export of a contact list (who, when, which campaign).
- Voice notes, posters and recordings are private files with signed, expiring links and a deletion date.
- Write the processing location table (where transcription, language model, translation, speech and storage run) into `docs/data-protection.md` and set `PROCESSING_REGION`. Fill it from the providers actually chosen.
- Before any real person's data is used, apply login lockout and rate limiting.

---

## 10. Phone call automation: left blank on purpose

Do **not** build this now. Create only the empty slot so the rest of the product can plug into it later.

Create `api/app/calls/__init__.py` with a docstring and an interface that raises `NotImplementedError`, plus a mock that records a fake attempt:

```python
class CallDispatcher(Protocol):
    def prepare(self, campaign_id: str) -> PreparedCalls: ...   # inputs listed below
    def launch(self, campaign_id: str) -> None: ...
    def test_call(self, campaign_id: str, to_number: str) -> None: ...
```

**What the rest of the system provides to it (already produced by this plan):** the approved call script per language with keypad options, the contact list with language and segment, the audio or text to speak, the voicemail version, the personal link to send afterwards, and the opt-out rule.

**What it must write back (so the dashboard works the moment it exists):** a `call_attempts` row per call and a `responses` row with one outcome from: `pending, confirmed, declined, callback, no_answer, voicemail, opted_out, wrong_number, failed`, plus the stage (`invited, responded, registered, paid, attended`).

The call screens (screen 8 and the test call part of screen 9) show a "Coming next" placeholder and the preflight treats the call channel as `not_configured` rather than failing.

---

## 11. Preflight and launch gate

`POST /campaigns/{id}/preflight` returns a list of blockers and warnings. Launch is disabled until there are no blockers.

Blockers:
- No approved event record, or required fields missing.
- Audience empty, or more than X percent of rows rejected.
- A language with contacts has no approved translation.
- Any translation or content item is `stale` or failed the fact check.
- Selected channel has no approved content, or a required template variable is missing for some contacts (show count).
- No test send done in the last 24 hours for each selected channel.
- No consent basis or opt-out wording in a non-call message.
- Launch time inside quiet hours.

Warnings:
- Mock mode is on for a channel ("this will not really send").
- Contacts with unknown language were assigned the default.
- Many contacts missing an email or WhatsApp number for a chosen channel.

After launch: the campaign becomes read-only for event details. A later change creates an **event update** (a new version with its own outreach), instead of editing in place.

---

## 12. Dashboard inputs

The dashboard reads, and the plan above writes, these facts. If a number cannot be traced to a row, it should not be shown.

- Funnel: contacts, reached, responded, confirmed, registered, paid, attended.
- By language: the contact's language, with the translation version that was used.
- By segment: the segment column from the CSV.
- By channel: from `outreach_log` and the registration source.
- Retry actions: non-responders per channel, skipping opted-out people and people at the attempt limit.
- Content health: any stale or failed items.

---

## 13. Non-functional requirements

- **Errors:** plain sentences the organizer can act on, with the HTTP status codes already used (400, 401, 403, 404, 409, 413, 422, 503).
- **Slow steps** (transcription, translation, generation) run as background jobs with a status endpoint, so the screen shows progress and nothing times out. A first version may run them inline but must keep the endpoint shapes identical.
- **Cost control:** record each AI call in `ai_usage`, refuse new calls when the monthly cap is reached, return a clear message.
- **Observability:** structured logs with campaign id and step, no personal data, no full phone numbers.
- **Idempotency:** re-running extraction, translation or content generation replaces drafts but never touches approved items without an explicit organizer action.
- **Config:** every key lives in `.env` and is documented in `.env.example`.

---

## 14. Build order for Antigravity

Each phase ends with passing tests and an updated `docs/` page. Do not start the next phase before the previous one passes.

**Phase 1: Campaigns and contacts on the database**
- Real `GET/POST /campaigns`, `GET /campaigns/{id}`, scoped by organizer.
- Move audience import to the database with encrypted phones and hashes.
- Tests: organizer A cannot read, update or import into organizer B's campaign (expect 404). Import twice is idempotent. Full phone numbers never appear in any response.

**Phase 2: Media and the voice note pipeline**
- Private storage with signed links, poster upload, voice upload.
- Transcriber interface with fake provider and one real provider.
- Date resolver and evidence checker with their tests.
- Extraction with schema, conflict detection and `needs_review`.
- Golden set and evaluation script.
- Acceptance: the golden set passes offline. A voice note with only a title and a relative date produces a draft with the date resolved and venue marked for review.

**Phase 3: Event record and confirmation**
- `PUT /campaigns/{id}/event` with versioning, hash, and staleness propagation.
- Status machine enforcement.
- Acceptance: editing the venue after translations exist marks all translations and content stale and blocks launch.

**Phase 4: Translations**
- Glossary, placeholder protection, per-language date formatting, caching.
- Back-translation and the automatic fact check.
- Acceptance: a translation that changes the date or drops the venue is flagged. Placeholders are never altered.

**Phase 5: Template engine and content generation**
- `render()` with per-channel templates for the four presets.
- Email, WhatsApp, SMS and Instagram content generation, previews, edit and approve.
- Mock adapters and the log.
- Acceptance: the same event record produces consistent date, venue and fee in all channels and all languages.

**Phase 6: Sending infrastructure**
- Worker, idempotent sends, quiet hours, opt-out, rate limits, delivery status.
- Real email through SMTP. Others stay mock.
- Test sends.

**Phase 7: Preflight and launch**
- Preflight endpoint and launch gate. Call dispatcher slot (section 10) wired in as `not_configured`.

**Phase 8: Dashboard data and retries**
- Make analytics read the real tables. Retry endpoint for non-call channels.

**Phase 9: Hardening**
- Login lockout, rate limiting, export logs, retention deletion job, data protection note with the processing location table, README and docs.

---

## 15. Ready-to-paste prompts for Antigravity

Give it one prompt at a time.

**Prompt 1 (setup context)**
> You are working in the EventReach repo. Read `README.md`, `docs/*.md`, `api/app/schemas.py`, `auth.py`, `db.py`, `dbsetup.py`, `csv_import.py`, `privacy.py` and `db/schema.sql`. Read `docs/build-plan.md` sections 0 to 4 and summarise the rules back to me. Do not change any code yet.

**Prompt 2 (Phase 1)**
> Implement Phase 1 of `docs/build-plan.md`. Replace the mock campaign endpoints with database versions requiring login and scoped to the owner. Move audience import to the database with encrypted phone numbers and hashes. Keep mock mode working when `DATABASE_URL` is empty. Add tests proving organizer A cannot access organizer B's campaign. Run the full test suite and show me the result.

**Prompt 3 (Phase 2)**
> Implement Phase 2 of `docs/build-plan.md` (voice note pipeline). Build the Transcriber interface with a fake provider, the date resolver in code with at least 30 tests, the evidence verification, the structured extraction with the schema in section 5.1, and the voice-versus-poster conflict detection. Create the golden test set and the offline runner. Do not call any real model in tests.

**Prompt 4 (Phase 3 and 4)**
> Implement Phases 3 and 4: event versioning with staleness propagation, then translations with placeholder protection, per-language date formatting, back-translation and the automatic fact check. Follow section 6 exactly. Show me a table of test cases and results.

**Prompt 5 (Phase 5 and 6)**
> Implement Phases 5 and 6: the template engine and content for email, WhatsApp, SMS and Instagram with mock adapters, previews, approval, idempotent sending, quiet hours and opt-out. Real sending only for email through SMTP. Follow sections 7 and 8.

**Prompt 6 (Phases 7 to 9)**
> Implement the preflight and launch gate, the empty call dispatcher slot described in section 10 (do not build call automation), dashboard data from real tables, retries for non-call channels, and the hardening list in Phase 9.

---

## 16. Open decisions for the team

1. Which speech to text and language model provider (must handle Hindi, Malayalam and Tamil well, and decide the processing region).
2. Is WhatsApp live or mocked for the demo? Default: mocked.
3. Is Instagram live or manual download plus caption copy? Default: manual fallback.
4. Quiet hours and daily caps.
5. Whether the event title should show a transliteration beside Indic scripts.
6. Maximum voice note length and file sizes.

---

## 17. Definition of done for this plan

- A new organizer can go from login to a launched mock campaign, using a real voice note and poster, with no manual database edits.
- The same date, venue and fee appear in the event record, every translation, every message and the registration page.
- Editing the event after approval visibly invalidates dependent content and blocks launch until regenerated.
- Everything that sends is idempotent, respects opt-out and consent, and works in mock mode.
- The call automation slot exists, is empty, and the dashboard shows call channel as "not configured" without errors.
- Tests pass, docs updated, no secrets in the repo.
