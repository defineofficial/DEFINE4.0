# EventReach Build Checklist

> **Team Plan**: 3 Frontend (Figma) + 2 Backend  
> **Progress Tracker**: 116 Tasks Total · Roles: F1 (Akshay), F2 (Aleena), F3 (Milind), B1 (Agila), B2 (Gayathri)

---

## Roles Overview & Summary

| Role | Name | Focus | Done / Total | Status |
|:---|:---|:---|:---:|:---:|
| **F1** | Akshay | Design lead (System & Organizer Flow) | 0 / 14 | In progress |
| **F2** | Aleena | Dashboard designer (Analytics & Funnels) | 0 / 11 | In progress |
| **F3** | Milind | Recipient experience (Registration, Copy) | 0 / 17 | In progress |
| **B1** | Agila | Voice & dispatch (Exotel, Calls, Analytics) | 0 / 28 | In progress |
| **B2** | **Gayathri** | **Platform & data (API, DB, AI, Registration, Payments)** | **26 / 33** | **Integration Ready** |

### B2 (Gayathri) Status & Baseline
- **Completed (26 / 33 · ~79%)**:
  - `voice_pipeline.py`: Transcription & structured event extraction with AI spend cap.
  - `translation_engine.py`: Hindi, Malayalam, and Tamil translations with English back-translation and caching.
  - `template_engine.py`: Multi-channel rendering across 4 presets (`seminar_invite`, `clinic_reminder`, `school_notice`, `payment_reminder`).
  - `privacy.py` & `contacts_db.py`: Fernet AES encryption at rest, salted hashing, masked phone output, and audit logging.
  - `channels.py`: Short links (`/s/{code}`), email sender with poster, and WhatsApp/Instagram mock adapters.
  - `payments.py`: Test mode order generation, 15-min seat holds, HMAC signature check, and webhook idempotency.
  - `calendar_invite.py` & `qr_checkin.py`: RFC 5545 `.ics` download, ticket pass SVG, and staff check-in endpoint.
  - `docs/data-protection.md`: Comprehensive one-page privacy & compliance document.
  - `scripts/reset_demo_data.py`: One-command demo reset script (1 populated dashboard campaign + 1 clean live demo campaign).
  - **Test Suite**: 182 / 182 tests passing across 17 test suites.
- **Next Steps (7 / 33)**:
  - Wire organizer and registration frontend pages as screens are delivered by F1 (Akshay) and F3 (Milind).
  - Run end-to-end SMS link test with B1 (Agila) on real phones.
  - Pre-submission secrets audit & demo-day hotspot testing.

---

## Phase 0 · Align (12 Tasks)

- [ ] Write the one-line pitch and the 60-second demo script (`All`)
- [ ] Lock the scope using the Must, Should and Mock lists (`All`)
- [ ] Pick demo languages (English, Hindi, Malayalam) and 8 to 10 test phone numbers (`All`)
- [ ] Agree on shared words: Campaign, Template, Audience, Segment, Contact, Response (`All`)
- [ ] Create Figma file with pages: Foundations, Components, Organizer, Dashboard, Registration, Handoff (`F1 · Akshay`)
- [ ] Set design tokens as Figma variables and styles (`F1 · Akshay`)
- [ ] List questions an organizer must answer in 5 seconds on dashboard (`F2 · Aleena`)
- [ ] Write recipient journey end to end: call, link by SMS, registration page, payment, receipt (`F3 · Milind`)
- [ ] Confirm Exotel number, test credits, outbound rules (`B1 · Agila`)
- [x] **Create repository with `web` and `api` folders, secrets template, invite everyone** (`B2 · Gayathri`)
- [x] **Draft data model v1: Campaign, Template, Contact, Segment, CallAttempt, Response, Registration, Payment, Consent** (`B2 · Gayathri`)
- [x] **Publish API contract v1: endpoints with sample request and response JSON** (`B2 · Gayathri`)

---

## Risks to Handle Early (7 Tasks)

- [ ] Test text-to-speech and speech recognition in Hindi and Malayalam (`B1 · Agila`)
- [ ] Ask Exotel whether automated outbound calls need registration / calling hours (`B1 · Agila`)
- [ ] Set spending cap on test calls and alert at 70% (`B1 · Agila`)
- [x] **Set usage cap on AI calls (transcription, extraction, translation) in `ai_budget.py`** (`B2 · Gayathri`)
- [ ] Find one native speaker each for Hindi and Malayalam to review translated scripts (`F3 · Milind`)
- [ ] Decide whether Instagram and WhatsApp are live or mocked (default: mocked) (`All`)
- [ ] At midpoint of Core build, drop a Should item if a Must item is behind (`All`)

---

## Phase 1 · Foundations (12 Tasks)

- [ ] Build Figma component library: buttons, inputs, file upload, stepper, tables, pills, cards, modal, toast (`F1 · Akshay`)
- [ ] Wireframe organizer flow: template, poster/voice note upload, extracted details, audience, translations, channels, launch (`F1 · Akshay`)
- [ ] Wireframe dashboard: campaign list, overview, funnel, language/segment breakdowns, recipient table, retry (`F2 · Aleena`)
- [ ] Wireframe registration page: poster header, details, form, success, already registered, link expired, payment (`F3 · Milind`)
- [ ] Write English call scripts for four presets under 25s (`F3 · Milind`)
- [ ] Write English copy for email and WhatsApp for each preset (`F3 · Milind`)
- [ ] Make first outbound Exotel call playing TTS message to team phone (`B1 · Agila`)
- [ ] Set up public webhook endpoint logging call status, digits and speech (`B1 · Agila`)
- [x] **Create database and migrations from data model, add login with organizer & admin roles** (`B2 · Gayathri`)
- [x] **Build CSV import: check columns, normalize numbers, flag duplicates and missing languages** (`B2 · Gayathri`)
- [x] **Set up private storage for posters and voice notes with signed, expiring links (`storage.py`)** (`B2 · Gayathri`)
- [x] **Ship mock API that returns realistic sample JSON for every endpoint** (`B2 · Gayathri`)

---

## Phase 2 · Core Build (20 Tasks)

- [ ] Design every organizer screen in high fidelity with all states (`F1 · Akshay`)
- [ ] Run handoff process on one screen with code generation (`F1 · Akshay`)
- [ ] Link click-through prototype of organizer journey and test outside team (`F1 · Akshay`)
- [ ] Design dashboard in high fidelity for desktop and tablet (`F2 · Aleena`)
- [ ] Design registration and payment pages mobile-first + email/WhatsApp/IG layouts (`F3 · Milind`)
- [ ] Collect all on-screen copy into strings sheet (key, English, Hindi, Malayalam) (`F3 · Milind`)
- [ ] Build call flow: greeting, details, keypad options, spoken yes/no, keypad fallback, repeat (`B1 · Agila`)
- [ ] Handle unknown language: "press 1 for English, 2 for Hindi..." fallback (`B1 · Agila`)
- [ ] Detect answering machines, play short message with callback number, record as voicemail (`B1 · Agila`)
- [ ] Map every result into one outcome set (`B1 · Agila`)
- [ ] Build dispatcher: queue, simultaneous calls limit, calling-hours window, skip opt-out/DND (`B1 · Agila`)
- [ ] Build retries: at most 3 attempts, manual retry endpoint, fallback to email/WhatsApp (`B1 · Agila`)
- [ ] Build analytics endpoints: funnel, breakdowns by language/segment/campaign, recipient list, CSV export (`B1 · Agila`)
- [x] **Voice note pipeline: transcribe audio, extract event details as JSON with LLM, return editable draft (`voice_pipeline.py`)** (`B2 · Gayathri`)
- [x] **Translate event content per language (hi, ml, ta), add back-translation to English, and cache translations (`translation_engine.py`)** (`B2 · Gayathri`)
- [x] **Build template engine (variables + language + channel) and seed the four presets (`template_engine.py`)** (`B2 · Gayathri`)
- [x] **Build registration: personal links tied to one contact, one identity across call/page/payment, state flow (`main.py`, `contacts_db.py`)** (`B2 · Gayathri`)
- [x] **Send email with poster; put WhatsApp and Instagram behind adapter with mock mode (`channels.py`)** (`B2 · Gayathri`)
- [x] **Generate short links (`/s/{code}`) and route to personal registration links (`channels.py`)** (`B2 · Gayathri`)
- [x] **Add payments in test mode: create order, verify webhook HMAC signature, mark paid, receipt, release seats (`payments.py`)** (`B2 · Gayathri`)

---

## Phase 3 · Integration (13 Tasks)

- [ ] Generate organizer screens from final Figma, commit to branches (`F1 · Akshay`)
- [ ] Generate dashboard screens from final Figma (`F2 · Aleena`)
- [ ] Generate registration and payment pages (`F3 · Milind`)
- [ ] Check dashboard numbers match raw call log for one campaign (`F2 · Aleena`)
- [ ] Run full recipient journey on a real phone (`F3 · Milind`)
- [ ] Visual check across all integrated pages: spacing, states, phone width, long Hindi/Malayalam text (`F1 · Akshay`)
- [ ] **Wire organizer and registration pages to real API, sitting with F1 and F3** (`B2 · Gayathri`)
- [ ] Wire dashboard to analytics and retry, sitting with F2 (`B1 · Agila`)
- [ ] Run real calls in every demo language and verify dashboard outcomes (`B1 · Agila`)
- [ ] **Run registration and test payment end to end from an SMS link** (`B2 · Gayathri`)
- [x] **Run the clinic reminder preset through the same engine to prove platform reusability (`test_clinic_preset.py`)** (`B2 · Gayathri`)
- [ ] Privacy for calls: delete recordings after retention, mask numbers in logs, honor opt-outs/DND (`B1 · Agila`)
- [x] **Privacy for data: AES encryption at rest, role-based access, audit export log (`privacy.py`, `contacts_db.py`), consent checkbox on registration, and written note (`docs/data-protection.md`)** (`B2 · Gayathri`)

---

## Testing (9 Tasks)

- [ ] Keypad: press each option (1, 2, 3, 9) and confirm right outcome saved (`B1 · Agila`)
- [ ] Speech: say yes and no in each demo language (quiet room and background noise) (`B1 · Agila`)
- [ ] Call outcomes: no answer, busy, voicemail, call dropped, wrong number (`B1 · Agila`)
- [x] **Bad CSV: missing columns, duplicate phone numbers, invalid numbers, unknown language (`test_csv_import.py`)** (`B2 · Gayathri`)
- [x] **Registration link edge cases: expired, used twice, forwarded to another phone, event full (`test_registration_edges.py`)** (`B2 · Gayathri`)
- [x] **Test payments: success, failure, abandoned, and identical webhook arriving twice (`test_payments.py`)** (`B2 · Gayathri`)
- [ ] Organizer flow: wrong file type, large poster, empty voice note, extraction correction (`F1 · Akshay`)
- [ ] Dashboard totals match call log after retries, opt-out, and multi-channel responses (`F2 · Aleena`)
- [ ] Registration page on small Android phone, iPhone, slow connection (`F3 · Milind`)

---

## Phase 4 · Stretch Goals (18 Tasks — Optional)

- [x] **QR check-in: create QR code for registration, send in confirmation, scan endpoint marking Attended (`qr_checkin.py`)** (`B2 · Gayathri`)
- [ ] Design ticket with QR code on success page, staff scanner screen (`F3 · Milind`)
- [ ] Add registered versus attended view to dashboard (`F2 · Aleena`)
- [ ] Reminder sequence: schedule call/message 24h and 2h before event to confirmed contacts (`B1 · Agila`)
- [ ] Design Reminders step in organizer flow with timing options (`F1 · Akshay`)
- [ ] Callback queue: list everyone who pressed 3 (pending, called, done) (`B1 · Agila`)
- [ ] Design callback list screen with one-tap status change (`F2 · Aleena`)
- [x] **Add to calendar: attach .ics file and Google Calendar link to confirmation message and success page (`calendar_invite.py`)** (`B2 · Gayathri`)
- [ ] Design Add to calendar button and matching message layout (`F3 · Milind`)
- [ ] Event change alert: call confirmed people with update when venue/time changes (`B1 · Agila`)
- [ ] Design Send update button with preview of affected contacts (`F1 · Akshay`)
- [ ] **Waitlist: overflow registrations join waitlist and get offered seat on cancellation** (`B2 · Gayathri`)
- [ ] Design waitlist message and page state for full event (`F3 · Milind`)
- [ ] **Post-event feedback: send attendees link to 3-question form and collect responses** (`B2 · Gayathri`)
- [ ] Design feedback page (`F3 · Milind`)
- [ ] Add cost per campaign and answer rate by hour to analytics endpoints (`B1 · Agila`)
- [ ] Design cost estimate, best-time-to-call chart, live progress strip (`F2 · Aleena`)
- [ ] Add slow-speech option (press 8 to hear message more slowly) (`B1 · Agila`)

---

## Phase 5 · Polish and Demo (9 Tasks)

- [ ] Feature freeze, then bug bash (`All`)
- [ ] Rehearse demo 3 times with timings; decide who speaks and who clicks (`All`)
- [ ] Seed realistic demo campaign so dashboard is populated before live run (`B1 · Agila`)
- [ ] Draw architecture and call-flow diagram for submission (`B1 · Agila`)
- [ ] **Prepare fallback: recorded video of real call and mocked posts in case network fails** (`B2 · Gayathri`)
- [x] **Write README and one-page data protection note covering consent, retention, encryption, region (`docs/data-protection.md`)** (`B2 · Gayathri`)
- [ ] Final visual pass: consistent spacing, copy, icons, empty states (`F1 · Akshay`)
- [ ] Build pitch deck: problem, solution, live demo, architecture, privacy, impact (`F2 · Aleena`)
- [ ] Record 60 to 90 second demo video and write narration (`F3 · Milind`)

---

## Submission (8 Tasks)

- [ ] Export final pitch deck as PDF (`F2 · Aleena`)
- [ ] Upload demo video and check public link playback (`F3 · Milind`)
- [ ] Add architecture and call-flow diagram to repository (`B1 · Agila`)
- [x] **Ensure README has setup and run steps that a stranger can follow** (`B2 · Gayathri`)
- [x] **Include the data protection note (`docs/data-protection.md`)** (`B2 · Gayathri`)
- [ ] **Remove keys and secrets from repository and audit git history** (`B2 · Gayathri`)
- [ ] Open repository and links in signed-out browser and confirm operation (`All`)
- [ ] Fill in and send submission form with 1-hour buffer before deadline (`All`)

---

## Demo Day (8 Tasks)

- [ ] Charge every phone and laptop; bring chargers and extension cord (`All`)
- [ ] Confirm demo phone numbers are active and with people ready to answer (`All`)
- [ ] Check Exotel balance and place one test call (`B1 · Agila`)
- [ ] **Test backup mobile hotspot and keep second copy of app running locally** (`B2 · Gayathri`)
- [x] **Reset demo data: 1 finished campaign for dashboard, 1 clean to launch live (`scripts/reset_demo_data.py`)** (`B2 · Gayathri`)
- [ ] Put fallback video on laptop and phone (`F3 · Milind`)
- [ ] Check demo screen readability on projector and turn off notifications (`F1 · Akshay`)
- [ ] Agree who speaks, who clicks, and who answers privacy questions (`All`)
