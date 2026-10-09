# EventReach

A multilingual voice-first outreach platform. An organizer uploads a poster, a voice note and a contact list. EventReach turns them into a live calling campaign (Exotel), with email, WhatsApp and social posts alongside, and shows RSVPs by campaign, language and segment.

## What is in this repository

```
eventreach/
  api/        FastAPI backend (mock API today, real logic replaces it step by step)
  web/        Frontend (generated from Figma designs, see web/README.md)
  db/         schema.sql, the PostgreSQL tables
  docs/       data-model.md, api-contract.md, openapi.json
  .env.example
```

## Run the mock API

You need Python 3.10 or newer.

```bash
cd api
python -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs to try every endpoint. It returns realistic sample data: one running campaign with 14 contacts in English, Hindi, Malayalam and Tamil, and one draft campaign.

Run the tests:

```bash
cd api
pytest
```

Regenerate the OpenAPI file after changing `api/app/schemas.py`:

```bash
cd api
python scripts/export_openapi.py
```

## How the pieces fit

- `api/app/schemas.py` defines the contract. Frontend and the Figma annotations use the same field names.
- `api/app/main.py` is the mock. Replace a handler with real logic when it is ready, keeping the same schema.
- `db/schema.sql` is the real database. `docs/data-model.md` explains it.
- Phone numbers are stored encrypted and hashed, and the API only returns masked numbers.

## Who owns what

| Area | Owner |
|---|---|
| Data model, auth, CSV import, voice note extraction, translation, templates, registration, payments, email and social channels | B2 |
| Exotel calls, keypad and speech capture, voicemail, dispatcher, retries, analytics | B1 |
| Organizer flow and design system | F1 |
| Dashboard | F2 |
| Registration page, message layouts, call-script copy | F3 |

See **[CHECKLIST.md](./CHECKLIST.md)** for the complete 116-task team tracker and live status.

## Next steps for B2

1. ~~PostgreSQL and login~~ Done: see `docs/database-setup-windows.md`. Next: move campaigns, then contacts, onto the database one endpoint at a time, and require sign-in on the organizer endpoints with the `current_organizer` dependency in `api/app/auth.py`.
2. ~~Real CSV import~~ Done: see `docs/csv-format.md`, `api/app/csv_import.py` and the sample files in `docs/samples/`. It currently stores people in memory. Moving it to PostgreSQL means replacing `add_imported_contacts` in `api/app/mock_data.py` and adding the encrypted phone column.
4. ~~Voice note pipeline: transcribe, extract event JSON, return an EventDraft~~ Done: see `api/app/voice_pipeline.py`.
5. ~~Translation with back-translation, then the template engine and the four preset seeds~~ Done: see `api/app/translation_engine.py` and `api/app/template_engine.py`.
6. ~~Registration with personal tokens, channels, and test mode payments~~ Done: see `api/app/payments.py`, `api/app/channels.py`, `api/app/contacts_db.py`, and `api/app/privacy.py`.
7. ~~Data protection note and privacy architecture~~ Done: see `docs/data-protection.md`.
8. Wire organizer & registration frontend pages with F1 and F3 as screens merge; conduct live telecom rehearsal with B1.
