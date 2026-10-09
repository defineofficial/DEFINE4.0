"""PostgreSQL persistence for contacts, personal registration tokens, and encryption at rest.

Follows db/schema.sql:
- `phone_enc`: encrypted E.164 bytea via privacy.encrypt_phone
- `phone_hash`: salted HMAC-SHA256
- `phone_masked`: +91 90••• ••013
- `registration_token`: unguessable unique token per contact
- Audit logging for contacts import and export actions
"""
import os
import secrets
from typing import Any, List, Optional, Tuple
import psycopg
from psycopg.rows import dict_row

from app import privacy
from app.csv_import import ParsedContact
from app.schemas import Campaign, Channel, Contact, ContactPage, Language, Me, Outcome, Stage

WEB_BASE_URL = os.getenv("WEB_BASE_URL", "http://localhost:3000")


def add_contacts_for(
    conn: psycopg.Connection,
    me: Me,
    campaign_id: str,
    parsed: List[ParsedContact],
) -> List[Contact]:
    """Saves parsed CSV contacts to PostgreSQL with encryption and registration tokens."""
    created: List[Contact] = []

    with conn.cursor() as cur:
        # Check campaign ownership
        cur.execute("SELECT id FROM campaigns WHERE id = %s AND organizer_id = %s", (campaign_id, me.id))
        if not cur.fetchone():
            raise ValueError("Campaign not found or not owned by organizer")

        for row in parsed:
            phone_enc = privacy.encrypt_phone(row.phone_e164)
            # Insert or retrieve contact
            cur.execute(
                """
                INSERT INTO contacts (organizer_id, name, phone_enc, phone_hash, phone_masked, email)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (organizer_id, phone_hash) DO UPDATE
                SET name = EXCLUDED.name, email = COALESCE(EXCLUDED.email, contacts.email)
                RETURNING id
                """,
                (me.id, row.name, phone_enc, row.phone_hash, row.phone_masked, row.email),
            )
            contact_id = cur.fetchone()[0]

            token = f"tok_{secrets.token_urlsafe(16)}"
            cur.execute(
                """
                INSERT INTO campaign_contacts (campaign_id, contact_id, language, segment, stage, last_outcome, attempts, registration_token)
                VALUES (%s, %s, %s, %s, 'invited', 'pending', 0, %s)
                ON CONFLICT (campaign_id, contact_id) DO UPDATE
                SET language = EXCLUDED.language, segment = EXCLUDED.segment
                RETURNING id, registration_token
                """,
                (campaign_id, contact_id, row.language.value, row.segment, token),
            )
            row_res = cur.fetchone()
            cc_id, reg_token = row_res[0], row_res[1]

            contact = Contact(
                id=str(contact_id),
                name=row.name,
                phone_masked=row.phone_masked,
                email=row.email,
                language=row.language,
                segment=row.segment,
                stage=Stage.invited,
                last_outcome=Outcome.pending,
                attempts=0,
                opted_out=False,
                registration_link=f"{WEB_BASE_URL}/r/{reg_token}",
            )
            created.append(contact)

        # Audit log entry for contact import
        cur.execute(
            """
            INSERT INTO audit_log (actor_id, action, object)
            VALUES (%s, 'upload_contacts', %s)
            """,
            (me.id, f"campaign:{campaign_id}:count:{len(parsed)}"),
        )

    conn.commit()
    return created


def log_export_audit(conn: psycopg.Connection, me: Me, campaign_id: str) -> None:
    """Logs contact export in the audit_log table for data protection tracking."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO audit_log (actor_id, action, object)
            VALUES (%s, 'export_contacts', %s)
            """,
            (me.id, f"campaign:{campaign_id}"),
        )
    conn.commit()
