# EventReach Data Protection & Privacy Architecture

> **One-Page Compliance & Privacy Note for EventReach**  
> **Classification:** Confidential / Team & Evaluator Reference  
> **Author:** Gayathri (B2 · Platform & Data Lead)  
> **Applicable Regulations:** Digital Personal Data Protection (DPDP) Act (India), IT Act 2000, GDPR Privacy Principles

---

## 1. Principles of Privacy by Design

EventReach is built to handle personal outreach across phone, email, and instant messaging without compromising personal identifiable information (PII). Full phone numbers are **never returned by the API** under any circumstances.

```
       [Raw E.164 Number] (+919876543210)
               │
       ┌───────┴────────────────────────┐
       ▼                                ▼
[Encryption at Rest]           [Salted HMAC Hash]
AES-128/256-CBC / HMAC          HMAC-SHA256 (Peppered)
Stored in DB: phone_enc        Stored in DB: phone_hash
Used strictly for calling/SMS   Used for dedupe & opt-outs
                                        │
                                        ▼
                                [Masked Display]
                                +91 98••• ••210
                                Returned by API
```

---

## 2. Technical Safeguards & Data Lifecycle

### A. Encryption at Rest & Key Management
* **Personal Phone Numbers**: Stored encrypted in PostgreSQL as `bytea` (`phone_enc`) using authenticated cryptography (Fernet / AES-CBC with HMAC-SHA256).
* **Key Segregation**: The encryption key (`ENCRYPTION_KEY`) is kept in environment variables and is completely distinct from the session secret (`SECRET_KEY`) and HMAC pepper.
* **Storage Assets**: Uploaded event posters and audio voice notes sit in isolated private disk/object storage (`api/uploads/`). They are accessible solely via HMAC-signed, time-limited URLs that expire after 15 minutes (`STORAGE_LINK_TTL_SECONDS=900`). Direct static directory listing is blocked.

### B. Salted Hashing & Global Opt-Outs
* Phone numbers are hashed using a private salt (`PHONE_HASH_PEPPER`).
* This enables fast duplicate detection and cross-campaign opt-out matching without retaining or searching raw plaintext numbers.
* Pressing **9** during any automated call or submitting an opt-out request permanently writes the hash to `opt_outs`. The dispatcher and audience importer automatically reject opted-out recipients across all past and future campaigns.

### C. Consent Framework
* **Registration Landing Page**: Every registration requires explicit, affirmative consent (`consent: true`). Submission without consent is blocked at the schema and validation layers (HTTP 400).
* **Identity Continuity**: Each recipient receives an unguessable 128-bit entropy personal token (`registration_token`). This token correlates the call response, registration form, and payment without exchanging raw contact details in public parameters.

### D. Data Retention & Automatic Erasure
* **Voice Call Recordings**: Retained for a maximum of 30 days (`RECORDING_RETENTION_DAYS=30`) for quality assurance, after which automated scheduled cleanup jobs purge recording paths and files.
* **Seat Holds & Inactive Orders**: Unpaid checkout holds automatically release after 15 minutes (`HOLD_DURATION_MINUTES=15`).

---

## 3. Processing Region & Sovereignty

* **Primary Processing Jurisdiction**: India (`ap-south-1` / Mumbai AWS/GCP region), configured via `PROCESSING_REGION`.
* **AI Transcription & Language Processing**: Audio transcription and multilingual LLM translation are routed through region-pinned gateways, strictly respecting the organizational monthly spending cap (`LLM_MONTHLY_BUDGET_USD`).

---

## 4. Role-Based Access Control & Audit Trails

1. **Role Separation**:
   * `organizer`: Limited strictly to campaigns and contacts they own. Cannot query other organizers' records.
   * `admin`: System-level operational inspection and budget monitoring.
2. **Immutable Audit Logging**:
   * All sensitive data actions (`upload_contacts`, `export_contacts`, `view_recording`) are recorded in the `audit_log` table with `actor_id`, timestamp, action name, and affected object identifier.
