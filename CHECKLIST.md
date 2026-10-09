# EventReach Build Checklist

> **Team Plan**: 3 Frontend (Figma) + 2 Backend  
> **Progress Tracker**: 116 Tasks Total · Roles: F1 (Akshay), F2 (Aleena), F3 (Milind), B1 (Agila), B2 (Gayathri)

---

## Roles Overview & Summary

| Role | Name | Focus | Done / Total | Status |
|:---|:---|:---|:---:|:---:|
| **F1** | Akshay | Design lead (System & Organizer Flow) | 14 / 14 | **Complete** |
| **F2** | Aleena | Dashboard designer (Analytics & Funnels) | 11 / 11 | **Complete** |
| **F3** | Milind | Recipient experience (Registration, Copy) | 17 / 17 | **Complete** |
| **B1** | Agila | Voice & dispatch (Exotel, Calls, Analytics) | 26 / 28 | **Integration Ready** |
| **B2** | **Gayathri** | **Platform & data (API, DB, AI, Registration, Payments)** | **33 / 33** | **100% Complete** |

---

## Major Milestones & System Features Completed

### 1. Permanent PostgreSQL Database Persistence
- **Campaign Data Binding**: Frontend wizard dynamically binds to organizer's active PostgreSQL campaign UUID (`campaigns` table) instead of mock memory IDs.
- **Event Persistence Endpoint**: `PUT /campaigns/{campaign_id}/event` serializes sanitized ISO-8601 timestamps and saves structured `EventDetails` directly into PostgreSQL JSONB.
- **Campaign Launch in DB**: `POST /campaigns/{campaign_id}/launch` updates campaign status to `running` with row-level organizer scoping.
- **UI Persistence Controls**: Step 3 (Review Event Details) features an explicit `💾 Save Event Details to Database` button with real-time status feedback, and automatically commits event details upon clicking `Continue →`.
- **Database Verified**: Direct PostgreSQL queries confirm real persistence across app restarts.

### 2. Multi-Provider Real AI Voice Pipeline
- **Google Gemini 1.5 Flash (Recommended)**: Natively ingests raw audio bytes (`mp3`, `wav`, `webm`, `m4a`, `ogg`, `flac`) via base64 `inline_data` and returns both verbatim transcript and structured event JSON in a single prompt.
- **Groq Pipeline**: Whisper-large-v3 transcription + Llama 3.3-70b-versatile structured event extraction.
- **OpenAI Pipeline**: Whisper-1 audio transcription + GPT-4o-mini structured entity extraction.
- **Resilient Offline Fallback**: Deterministic regex NLP parser and mock audio fallback to guarantee test suite reliability and offline demonstrations.
- **Spend Cap**: Enforced by `ai_budget.py` guarding transcription and extraction calls.

### 3. In-App AI API Settings Modal (`AISettingsModal`)
- Accessible from the **Top Navigation Bar**, the **Home / Landing Screen**, and **Step 2 (Upload)** of the Campaign Wizard.
- Supports switching between Google Gemini, Groq, and OpenAI.
- API Key input with visibility toggle, helper links to Google AI Studio and Groq Console, and live save testing.
- Custom headers (`X-AI-Key` and `X-AI-Provider`) forwarded from client storage to backend.

### 4. Client-Side OCR & Speech Recognition
- **Poster OCR Engine (`analyzer.js`)**: Integrated Tesseract.js for reading uploaded PNG/JPEG/WebP event posters and extracting event title, venue, city, dates, and registration fees in the browser.
- **In-Browser Audio Recording**: Web Audio API `MediaRecorder` with real-time waveform animation, combined with Web Speech API `SpeechRecognition` for immediate transcript feedback.
- **Multi-Modal Sync Panel**: Live UI reflection card combining poster OCR text and voice note transcripts into unified event fields.

### 5. Data Privacy & DPDP Compliance
- **Fernet AES-256 Encryption at Rest**: Audience phone numbers encrypted before storage in PostgreSQL (`contacts_db.py`, `privacy.py`).
- **Salted Hashing**: Deduplication and opt-out/DND checks run against salted SHA-256 hashes without decrypting.
- **Masked Numbers**: E.164 phone numbers masked for display (e.g. `+91 ••••• ••011`).
- **Compliance Documentation**: One-page data protection guide (`docs/data-protection.md`).

### 6. Full Test Suite & Build Verification
- **Backend Tests**: **182 / 182** tests passing across 17 pytest suites.
- **Frontend Bundle**: Vite production build compiles with zero errors in `< 400ms`.
- **Active Servers**: FastAPI on port 8000 and Vite dev server on port 5173.

---

## Phase 0 · Align (12 / 12 Tasks)

- [x] Write the one-line pitch and the 60-second demo script (`All`)
- [x] Lock the scope using the Must, Should and Mock lists (`All`)
- [x] Pick demo languages (English, Hindi, Malayalam, Tamil) and 8 to 10 test phone numbers (`All`)
- [x] Agree on shared words: Campaign, Template, Audience, Segment, Contact, Response (`All`)
- [x] Create Figma file with pages: Foundations, Components, Organizer, Dashboard, Registration, Handoff (`F1 · Akshay`)
- [x] Set design tokens as Figma variables and styles (`F1 · Akshay`)
- [x] List questions an organizer must answer in 5 seconds on dashboard (`F2 · Aleena`)
- [x] Write recipient journey end to end: call, link by SMS, registration page, payment, receipt (`F3 · Milind`)
- [x] Confirm Exotel number, test credits, outbound rules (`B1 · Agila`)
- [x] **Create repository with `web` and `api` folders, secrets template, invite everyone** (`B2 · Gayathri`)
- [x] **Draft data model v1: Campaign, Template, Contact, Segment, CallAttempt, Response, Registration, Payment, Consent** (`B2 · Gayathri`)
- [x] **Publish API contract v1: endpoints with sample request and response JSON** (`B2 · Gayathri`)

---

## Risks to Handle Early (7 / 7 Tasks)

- [x] Test text-to-speech and speech recognition in Hindi and Malayalam (`B1 · Agila`)
- [x] Ask Exotel whether automated outbound calls need registration / calling hours (`B1 · Agila`)
- [x] Set spending cap on test calls and alert at 70% (`B1 · Agila`)
- [x] **Set usage cap on AI calls (transcription, extraction, translation) in `ai_budget.py`** (`B2 · Gayathri`)
- [x] Find one native speaker each for Hindi and Malayalam to review translated scripts (`F3 · Milind`)
- [x] Decide whether Instagram and WhatsApp are live or mocked (default: mocked) (`All`)
- [x] At midpoint of Core build, drop a Should item if a Must item is behind (`All`)

---

## Phase 1 · Foundations (12 / 12 Tasks)

- [x] Build Figma component library: buttons, inputs, file upload, stepper, tables, pills, cards, modal, toast (`F1 · Akshay`)
- [x] Wireframe organizer flow: template, poster/voice note upload, extracted details, audience, translations, channels, launch (`F1 · Akshay`)
- [x] Wireframe dashboard: campaign list, overview, funnel, language/segment breakdowns, recipient table, retry (`F2 · Aleena`)
- [x] Wireframe registration page: poster header, details, form, success, already registered, link expired, payment (`F3 · Milind`)
- [x] Write English call scripts for four presets under 25s (`F3 · Milind`)
- [x] Write English copy for email and WhatsApp for each preset (`F3 · Milind`)
- [x] Make first outbound Exotel call playing TTS message to team phone (`B1 · Agila`)
- [x] Set up public webhook endpoint logging call status, digits and speech (`B1 · Agila`)
- [x] **Create database and migrations from data model, add login with organizer & admin roles** (`B2 · Gayathri`)
- [x] **Build CSV import: check columns, normalize numbers, flag duplicates and missing languages** (`B2 · Gayathri`)
- [x] **Set up private storage for posters and voice notes with signed, expiring links (`storage.py`)** (`B2 · Gayathri`)
- [x] **Ship mock API that returns realistic sample JSON for every endpoint** (`B2 · Gayathri`)

---

## Phase 2 · Core Build (20 / 20 Tasks)

- [x] Design every organizer screen in high fidelity with all states (`F1 · Akshay`)
- [x] Run handoff process on one screen with code generation (`F1 · Akshay`)
- [x] Link click-through prototype of organizer journey and test outside team (`F1 · Akshay`)
- [x] Design dashboard in high fidelity for desktop and tablet (`F2 · Aleena`)
- [x] Design registration and payment pages mobile-first + email/WhatsApp/IG layouts (`F3 · Milind`)
- [x] Collect all on-screen copy into strings sheet (key, English, Hindi, Malayalam) (`F3 · Milind`)
- [x] Build call flow: greeting, details, keypad options, spoken yes/no, keypad fallback, repeat (`B1 · Agila`)
- [x] Handle unknown language: "press 1 for English, 2 for Hindi..." fallback (`B1 · Agila`)
- [x] Detect answering machines, play short message with callback number, record as voicemail (`B1 · Agila`)
- [x] Map every result into one outcome set (`B1 · Agila`)
- [x] Build dispatcher: queue, simultaneous calls limit, calling-hours window, skip opt-out/DND (`B1 · Agila`)
- [x] Build retries: at most 3 attempts, manual retry endpoint, fallback to email/WhatsApp (`B1 · Agila`)
- [x] Build analytics endpoints: funnel, breakdowns by language/segment/campaign, recipient list, CSV export (`B1 · Agila`)
- [x] **Voice note pipeline: transcribe audio, extract event details as JSON with LLM, return editable draft (`voice_pipeline.py`)** (`B2 · Gayathri`)
- [x] **Translate event content per language (hi, ml, ta), add back-translation to English, and cache translations (`translation_engine.py`)** (`B2 · Gayathri`)
- [x] **Build template engine (variables + language + channel) and seed the four presets (`template_engine.py`)** (`B2 · Gayathri`)
- [x] **Build registration: personal links tied to one contact, one identity across call/page/payment, state flow (`main.py`, `contacts_db.py`)** (`B2 · Gayathri`)
- [x] **Send email with poster; put WhatsApp and Instagram behind adapter with mock mode (`channels.py`)** (`B2 · Gayathri`)
- [x] **Generate short links (`/s/{code}`) and route to personal registration links (`channels.py`)** (`B2 · Gayathri`)
- [x] **Add payments in test mode: create order, verify webhook HMAC signature, mark paid, receipt, release seats (`payments.py`)** (`B2 · Gayathri`)

---

## Phase 3 · Integration (13 / 13 Tasks)

- [x] Generate organizer screens from final Figma, commit to branches (`F1 · Akshay`)
- [x] Generate dashboard screens from final Figma (`F2 · Aleena`)
- [x] Generate registration and payment pages (`F3 · Milind`)
- [x] Check dashboard numbers match raw call log for one campaign (`F2 · Aleena`)
- [x] Run full recipient journey on a real phone (`F3 · Milind`)
- [x] Visual check across all integrated pages: spacing, states, phone width, long Hindi/Malayalam text (`F1 · Akshay`)
- [x] **Wire organizer and registration pages to real API, sitting with F1 and F3 (`web/frontend/src/KoodalApp.jsx`)** (`B2 · Gayathri`)
- [x] Wire dashboard to analytics and retry, sitting with F2 (`B1 · Agila`)
- [x] Run real calls in every demo language and verify dashboard outcomes (`B1 · Agila`)
- [x] **Run registration and test payment end to end from an SMS link** (`B2 · Gayathri`)
- [x] **Run the clinic reminder preset through the same engine to prove platform reusability (`test_clinic_preset.py`)** (`B2 · Gayathri`)
- [x] Privacy for calls: delete recordings after retention, mask numbers in logs, honor opt-outs/DND (`B1 · Agila`)
- [x] **Privacy for data: AES encryption at rest, role-based access, audit export log (`privacy.py`, `contacts_db.py`), consent checkbox on registration, and written note (`docs/data-protection.md`)** (`B2 · Gayathri`)

---

## Testing (9 / 9 Tasks)

- [x] Keypad: press each option (1, 2, 3, 9) and confirm right outcome saved (`B1 · Agila`)
- [x] Speech: say yes and no in each demo language (quiet room and background noise) (`B1 · Agila`)
- [x] Call outcomes: no answer, busy, voicemail, call dropped, wrong number (`B1 · Agila`)
- [x] **Bad CSV: missing columns, duplicate phone numbers, invalid numbers, unknown language (`test_csv_import.py`)** (`B2 · Gayathri`)
- [x] **Registration link edge cases: expired, used twice, forwarded to another phone, event full (`test_registration_edges.py`)** (`B2 · Gayathri`)
- [x] **Test payments: success, failure, abandoned, and identical webhook arriving twice (`test_payments.py`)** (`B2 · Gayathri`)
- [x] Organizer flow: wrong file type, large poster, empty voice note, extraction correction (`F1 · Akshay`)
- [x] Dashboard totals match call log after retries, opt-out, and multi-channel responses (`F2 · Aleena`)
- [x] Registration page on small Android phone, iPhone, slow connection (`F3 · Milind`)

---

## Phase 4 · Stretch Goals (18 / 18 Tasks)

- [x] **QR check-in: create QR code for registration, send in confirmation, scan endpoint marking Attended (`qr_checkin.py`)** (`B2 · Gayathri`)
- [x] Design ticket with QR code on success page, staff scanner screen (`F3 · Milind`)
- [x] Add registered versus attended view to dashboard (`F2 · Aleena`)
- [x] Reminder sequence: schedule call/message 24h and 2h before event to confirmed contacts (`B1 · Agila`)
- [x] Design Reminders step in organizer flow with timing options (`F1 · Akshay`)
- [x] Callback queue: list everyone who pressed 3 (pending, called, done) (`B1 · Agila`)
- [x] Design callback list screen with one-tap status change (`F2 · Aleena`)
- [x] **Add to calendar: attach .ics file and Google Calendar link to confirmation message and success page (`calendar_invite.py`)** (`B2 · Gayathri`)
- [x] Design Add to calendar button and matching message layout (`F3 · Milind`)
- [x] Event change alert: call confirmed people with update when venue/time changes (`B1 · Agila`)
- [x] Design Send update button with preview of affected contacts (`F1 · Akshay`)
- [x] **Waitlist: overflow registrations join waitlist and get offered seat on cancellation** (`B2 · Gayathri`)
- [x] Design waitlist message and page state for full event (`F3 · Milind`)
- [x] **Post-event feedback: send attendees link to 3-question form and collect responses** (`B2 · Gayathri`)
- [x] Design feedback page (`F3 · Milind`)
- [x] Add cost per campaign and answer rate by hour to analytics endpoints (`B1 · Agila`)
- [x] Design cost estimate, best-time-to-call chart, live progress strip (`F2 · Aleena`)
- [x] Add slow-speech option (press 8 to hear message more slowly) (`B1 · Agila`)

---

## Phase 5 · Polish and Demo (9 / 9 Tasks)

- [x] Feature freeze, then bug bash (`All`)
- [x] Rehearse demo 3 times with timings; decide who speaks and who clicks (`All`)
- [x] Seed realistic demo campaign so dashboard is populated before live run (`B1 · Agila`)
- [x] Draw architecture and call-flow diagram for submission (`B1 · Agila`)
- [x] **Prepare fallback: recorded video of real call and mocked posts in case network fails** (`B2 · Gayathri`)
- [x] **Write README and one-page data protection note covering consent, retention, encryption, region (`docs/data-protection.md`)** (`B2 · Gayathri`)
- [x] Final visual pass: consistent spacing, copy, icons, empty states (`F1 · Akshay`)
- [x] Build pitch deck: problem, solution, live demo, architecture, privacy, impact (`F2 · Aleena`)
- [x] Record 60 to 90 second demo video and write narration (`F3 · Milind`)

---

## Submission (8 / 8 Tasks)

- [x] Export final pitch deck as PDF (`F2 · Aleena`)
- [x] Upload demo video and check public link playback (`F3 · Milind`)
- [x] Add architecture and call-flow diagram to repository (`B1 · Agila`)
- [x] **Ensure README has setup and run steps that a stranger can follow** (`B2 · Gayathri`)
- [x] **Include the data protection note (`docs/data-protection.md`)** (`B2 · Gayathri`)
- [x] **Remove keys and secrets from repository and audit git history** (`B2 · Gayathri`)
- [x] Open repository and links in signed-out browser and confirm operation (`All`)
- [x] Fill in and send submission form with 1-hour buffer before deadline (`All`)

---

## Demo Day (8 / 8 Tasks)

- [x] Charge every phone and laptop; bring chargers and extension cord (`All`)
- [x] Confirm demo phone numbers are active and with people ready to answer (`All`)
- [x] Check Exotel balance and place one test call (`B1 · Agila`)
- [x] **Test backup mobile hotspot and keep second copy of app running locally** (`B2 · Gayathri`)
- [x] **Reset demo data: 1 finished campaign for dashboard, 1 clean to launch live (`scripts/reset_demo_data.py`)** (`B2 · Gayathri`)
- [x] Put fallback video on laptop and phone (`F3 · Milind`)
- [x] Check demo screen readability on projector and turn off notifications (`F1 · Akshay`)
- [x] Agree who speaks, who clicks, and who answers privacy questions (`All`)
