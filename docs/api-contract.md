# EventReach API contract v1

**Source of truth for field names and types:** `docs/openapi.json` (generated from `api/app/schemas.py`).
**Try it live:** run the mock API and open `http://localhost:8000/docs`.
This page covers what the OpenAPI file cannot say: who owns what, conventions, and the order screens call things.

## Conventions

- JSON in and out, `snake_case` field names, base URL `http://localhost:8000` in development.
- Dates and times are ISO 8601 with offset, for example `2026-11-14T10:00:00+05:30`.
- IDs are strings (`cmp_001`, `ct_004`).
- The API never returns a full phone number, only `phone_masked`.
- Errors look like `{"detail": "Consent is required to register"}` with a normal HTTP status (400, 404, 409, 422).
- Auth has two modes. With no `DATABASE_URL` (mock mode) any login works and nothing is checked, so the frontend can be built without a database. With a database, send `Authorization: Bearer <token>`. `/me` already requires it, and every organizer endpoint will as it moves to the database. The public `/r/...` links never need it.
- When the database is down the API answers 503 with a plain sentence.
- Shared words: Outcome, Stage, Channel and Language codes are listed in `docs/data-model.md`. Use them exactly.

## Endpoints

Owner is who builds the real logic. The mock already answers all of them.

### Auth and templates (B2)
| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/register` | **Real with a database.** Create an organizer account and return a token. 409 if the email exists, 403 if sign-up is closed, 422 for a weak password (under 8 characters) |
| POST | `/auth/login` | **Real with a database.** Email and password, returns a token that lasts 8 hours. 401 with the same message for a wrong password and an unknown email |
| GET | `/me` | **Real with a database.** The signed-in organizer. Needs `Authorization: Bearer <token>`, otherwise 401 |
| GET | `/templates` | The four presets with variables and keypad options |

### Campaign setup (B2)
| Method | Path | Purpose | Screen |
|---|---|---|---|
| GET | `/campaigns` | List campaigns | Campaign list |
| POST | `/campaigns` | Create from a template | Step 1: choose template |
| GET | `/campaigns/{id}` | One campaign | Any |
| POST | `/campaigns/{id}/poster` | Upload poster (multipart `file`) | Step 2 |
| POST | `/campaigns/{id}/voice-note` | Upload voice note (multipart `file`), returns an `EventDraft` | Step 2 |
| PUT | `/campaigns/{id}/event` | Save reviewed event details | Step 3: review details |
| POST | `/campaigns/{id}/audience` | **Real.** Upload CSV (multipart `file`, optional `default_language` query), returns an `ImportReport` with `errors` (skipped rows) and `warnings` (kept rows to check). Returns 422 with a plain sentence if the file cannot be read, 413 over 2 MB. Format: `docs/csv-format.md` | Step 4: audience |
| GET | `/audience/template.csv` | Download a starter CSV | Step 4: audience |
| GET | `/campaigns/{id}/contacts` | Contacts, filter by `language`, `segment`, `outcome`, `stage`, with `limit` and `offset` | Step 4 and dashboard table |
| GET | `/campaigns/{id}/translations` | One translation per language, with back-translation | Step 5: review translations |
| PUT | `/campaigns/{id}/translations/{language}` | Save an edited or approved translation | Step 5 |

### Launch and dispatch (B1)
| Method | Path | Purpose | Screen |
|---|---|---|---|
| POST | `/campaigns/{id}/test-call` | Call one number so the organizer hears the script | Step 7: preview |
| POST | `/campaigns/{id}/launch` | Start the campaign | Step 8: launch |
| POST | `/campaigns/{id}/retry` | Retry non-responders. Skips opted-out people and anyone with 3 attempts | Dashboard retry panel |

### Analytics (B1)
| Method | Path | Purpose |
|---|---|---|
| GET | `/campaigns/{id}/analytics/funnel` | Contacts, dialed, answered, responded, confirmed, registered, paid |
| GET | `/campaigns/{id}/analytics/by-language` | One row per language |
| GET | `/campaigns/{id}/analytics/by-segment` | One row per segment |

Planned, not in the mock yet: `GET /campaigns/{id}/analytics/export.csv` and the Exotel webhooks (`/webhooks/exotel/status`, `/webhooks/exotel/input`), which B1 adds.

### Contacts (B2)
| Method | Path | Purpose |
|---|---|---|
| POST | `/contacts/{id}/opt-out` | Mark a person as opted out |

### Registration page, public (B2)
Reached from a personal link like `https://app.example/r/tok_ct_004`. No login.

| Method | Path | Purpose |
|---|---|---|
| GET | `/r/{token}` | Event, poster, the person's name and language, current stage |
| POST | `/r/{token}/register` | Submit the form. `consent` must be `true` |
| POST | `/r/{token}/pay` | Create a payment order |
| POST | `/webhooks/payment` | Gateway callback. The mock marks the person paid. The real one verifies the signature |

## Rules that guide every screen

1. A confirmed answer on a call is a valid RSVP. The registration page is only needed when the event asks for details or a fee.
2. The dashboard reads outcomes and stages only. It does not need to know which channel an answer came from.
3. Opt-out and consent always win over a retry or a reminder.
4. Anything the organizer must check before launch (event details, translations) has an explicit save or approve step.

## Sample payloads

**Create a campaign**
```json
POST /campaigns
{ "name": "AI in Healthcare Seminar", "template_key": "seminar_invite" }
```

**Event draft from a voice note** (response of `POST /campaigns/{id}/voice-note`)
```json
{
  "transcript": "We are holding an AI in Healthcare seminar on the fourteenth of November...",
  "detected_language": "en",
  "event": {
    "title": "AI in Healthcare Seminar",
    "starts_at": "2026-11-14T10:00:00+05:30",
    "venue": "Seminar Hall, Block A",
    "city": "Kochi",
    "fee_inr": 500
  },
  "needs_review": ["ends_at", "capacity"]
}
```

**Funnel**
```json
{ "contacts": 14, "dialed": 13, "answered": 8, "responded": 7,
  "confirmed": 5, "registered": 4, "paid": 2 }
```

**Retry**
```json
POST /campaigns/cmp_001/retry
{ "target": "non_responders", "fallback_channel": "whatsapp" }
-> { "queued": 3, "skipped_opted_out": 0, "skipped_max_attempts": 1 }
```

**Register**
```json
POST /r/tok_ct_004/register
{ "name": "Arjun Verma", "email": "arjun@example.com", "party_size": 1, "consent": true }
-> { "stage": "registered", "requires_payment": true, "amount_inr": 500 }
```

## Changing the contract

1. Edit `api/app/schemas.py`.
2. Run `python scripts/export_openapi.py` from the `api` folder.
3. Post in the team chat what changed. Frontend updates the Figma annotation and the generated code.
