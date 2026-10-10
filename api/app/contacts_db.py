"""PostgreSQL persistence for contacts, personal registration tokens, and encryption at rest.

Follows db/schema.sql:
- `phone_enc`: encrypted E.164 bytea via privacy.encrypt_phone
- `phone_hash`: salted HMAC-SHA256
- `phone_masked`: +91 90··· ··013
- `registration_token`: unguessable unique token per contact per campaign
- Audit logging for contacts import and export actions

The pool is configured with dict_row, so all fetchone()/fetchall() results are dicts.
"""
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import psycopg

from app import privacy
from app.csv_import import ParsedContact
from app.schemas import Contact, Language, Me, Outcome, Stage

WEB_BASE_URL = os.getenv("WEB_BASE_URL", "http://localhost:3000")


# ---------- query helpers used by main.py ----------

def get_existing_hashes(conn: psycopg.Connection, campaign_id: str) -> set[str]:
    """Return the phone_hashes already enrolled in this campaign, for dedup on re-import."""
    rows = conn.execute(
        """
        SELECT c.phone_hash
          FROM campaign_contacts cc
          JOIN contacts c ON c.id = cc.contact_id
         WHERE cc.campaign_id = %s::uuid
        """,
        (campaign_id,),
    ).fetchall()
    return {r["phone_hash"] for r in rows}


def get_opted_out_hashes(conn: psycopg.Connection) -> set[str]:
    """Return the global set of opted-out phone_hashes (applied across every campaign)."""
    rows = conn.execute("SELECT phone_hash FROM opt_outs").fetchall()
    return {r["phone_hash"] for r in rows}


# ---------- write helpers ----------

def add_contacts_for(
    conn: psycopg.Connection,
    me: Me,
    campaign_id: str,
    parsed: List[ParsedContact],
) -> List[Contact]:
    """Persist validated contacts from a CSV import.

    - Upserts each contact into the global ``contacts`` table (dedup by organizer + phone_hash).
    - Inserts into ``campaign_contacts`` (idempotent ON CONFLICT).
    - Appends an audit_log row.
    - Calls conn.commit() before returning.

    Only contacts whose phone_hash is NOT already in this campaign should be passed here;
    the caller (main.py) uses get_existing_hashes() to pre-filter them.
    """
    # Verify campaign ownership once up-front (returns same 404 as missing campaign).
    row = conn.execute(
        "SELECT id FROM campaigns WHERE id = %s::uuid AND organizer_id = %s::uuid",
        (campaign_id, me.id),
    ).fetchone()
    if not row:
        raise ValueError("Campaign not found or not owned by organizer")

    created: List[Contact] = []

    for p in parsed:
        phone_enc = privacy.encrypt_phone(p.phone_e164)

        # Upsert the organizer-scoped contact record.
        contact_row = conn.execute(
            """
            INSERT INTO contacts (organizer_id, name, phone_enc, phone_hash, phone_masked, email)
                 VALUES (%s::uuid, %s, %s, %s, %s, %s)
            ON CONFLICT (organizer_id, phone_hash)
              DO UPDATE SET name  = EXCLUDED.name,
                            email = COALESCE(EXCLUDED.email, contacts.email)
            RETURNING id
            """,
            (me.id, p.name, phone_enc, p.phone_hash, p.phone_masked, p.email),
        ).fetchone()
        contact_id = str(contact_row["id"])

        raw_token = f"tok_{secrets.token_urlsafe(32)}"
        t_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)

        # Check if campaign event has RSVP/start date to set expiration
        camp_row = conn.execute("SELECT event FROM campaigns WHERE id = %s::uuid", (campaign_id,)).fetchone()
        if camp_row and camp_row["event"]:
            ev_data = camp_row["event"]
            rsvp_deadline = ev_data.get("rsvp_deadline") or ev_data.get("starts_at")
            if rsvp_deadline:
                try:
                    expires_at = datetime.fromisoformat(str(rsvp_deadline).replace("Z", "+00:00"))
                except ValueError:
                    pass

        cc_row = conn.execute(
            """
            INSERT INTO campaign_contacts
                  (campaign_id, contact_id, language, segment,
                   stage, last_outcome, attempts, registration_token, token_hash, token_expires_at)
               VALUES (%s::uuid, %s::uuid, %s, %s, 'invited', 'pending', 0, %s, %s, %s)
            ON CONFLICT (campaign_id, contact_id)
              DO UPDATE SET language = EXCLUDED.language,
                            segment  = EXCLUDED.segment,
                            token_hash = EXCLUDED.token_hash,
                            token_expires_at = EXCLUDED.token_expires_at
            RETURNING id
            """,
            (campaign_id, contact_id, p.language.value, p.segment, t_hash, t_hash, expires_at),
        ).fetchone()

        created.append(Contact(
            id=contact_id,
            name=p.name,
            phone_masked=p.phone_masked,
            email=p.email,
            language=p.language,
            segment=p.segment,
            stage=Stage.invited,
            last_outcome=Outcome.pending,
            attempts=0,
            opted_out=False,
            registration_link=f"{WEB_BASE_URL}/r/{raw_token}",
        ))

    # Audit log entry (even if zero rows were added, we log the upload event).
    conn.execute(
        "INSERT INTO audit_log (actor_id, action, object) VALUES (%s::uuid, 'upload_contacts', %s)",
        (me.id, f"campaign:{campaign_id}:count:{len(parsed)}"),
    )
    conn.commit()
    return created


def get_contact_count(conn: psycopg.Connection, campaign_id: str) -> int:
    """Count contacts currently enrolled in a campaign (for the Campaign.contact_count field)."""
    row = conn.execute(
        "SELECT count(*) AS n FROM campaign_contacts WHERE campaign_id = %s::uuid",
        (campaign_id,),
    ).fetchone()
    return int(row["n"])


def log_export_audit(conn: psycopg.Connection, me: Me, campaign_id: str) -> None:
    """Log a contact-list export in audit_log for data protection tracking."""
    conn.execute(
        "INSERT INTO audit_log (actor_id, action, object) VALUES (%s::uuid, 'export_contacts', %s)",
        (me.id, f"campaign:{campaign_id}"),
    )
    conn.commit()


def list_for_campaign(
    conn: psycopg.Connection,
    me: Me,
    campaign_id: str,
    language: Optional[str] = None,
    segment: Optional[str] = None,
    outcome: Optional[str] = None,
    stage: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Contact], int]:
    """Return a page of contacts for a campaign together with the total unfiltered count.

    Scoped to the organizer who owns the campaign — raises 404 if the campaign does not
    exist or belongs to someone else.  Full phone numbers are never returned.
    """
    from fastapi import HTTPException
    from app.schemas import Language as LangEnum, Outcome as OutcomeEnum, Stage as StageEnum

    # Ownership check (same 404 shape as campaigns_db.get_for).
    owns = conn.execute(
        "SELECT 1 FROM campaigns WHERE id = %s::uuid AND organizer_id = %s::uuid",
        (campaign_id, me.id),
    ).fetchone()
    if not owns:
        raise HTTPException(404, "Campaign not found")

    # Build filter clauses.
    clauses = ["cc.campaign_id = %s::uuid"]
    params: list = [campaign_id]
    if language:
        clauses.append("cc.language = %s")
        params.append(language)
    if segment:
        clauses.append("cc.segment = %s")
        params.append(segment)
    if outcome:
        clauses.append("cc.last_outcome = %s::outcome")
        params.append(outcome)
    if stage:
        clauses.append("cc.stage = %s::stage")
        params.append(stage)

    where = " AND ".join(clauses)

    total_row = conn.execute(
        f"SELECT count(*) AS n FROM campaign_contacts cc WHERE {where}",
        params,
    ).fetchone()
    total = int(total_row["n"])

    rows = conn.execute(
        f"""
        SELECT
            ct.id, ct.name, ct.phone_masked, ct.email,
            cc.language, cc.segment, cc.stage::text AS stage,
            cc.last_outcome::text AS last_outcome, cc.attempts,
            cc.registration_token,
            EXISTS(SELECT 1 FROM opt_outs o WHERE o.phone_hash = ct.phone_hash) AS opted_out
          FROM campaign_contacts cc
          JOIN contacts ct ON ct.id = cc.contact_id
         WHERE {where}
         ORDER BY ct.name
         LIMIT %s OFFSET %s
        """,
        params + [limit, offset],
    ).fetchall()

    contacts = [
        Contact(
            id=str(r["id"]),
            name=r["name"],
            phone_masked=r["phone_masked"],
            email=r["email"],
            language=LangEnum(r["language"]),
            segment=r["segment"],
            stage=StageEnum(r["stage"]),
            last_outcome=OutcomeEnum(r["last_outcome"]),
            attempts=r["attempts"],
            opted_out=bool(r["opted_out"]),
            registration_link=f"{WEB_BASE_URL}/r/{r['registration_token']}",
        )
        for r in rows
    ]
    return contacts, total
