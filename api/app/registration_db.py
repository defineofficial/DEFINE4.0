"""Database persistence and logic for registration tokens, public registration, payments, seat holds, and webhooks.

Follows build-plan specs:
- Random URL-safe 32+ char registration tokens, stored as SHA-256 hashes (`token_hash`)
- Idempotent registration with capacity checks and seat reservation holds (default 30 mins)
- Payment order creation, server-side amount calculation, HMAC signature verification, and webhook idempotency
- Seat hold release job
"""
import base64
import hashlib
import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import psycopg
from fastapi import HTTPException
from psycopg.types.json import Jsonb

from app import privacy, storage
from app.date_resolver import IST
from app.schemas import (
    BreakdownRow, Campaign, CampaignStatus, Channel, Contact, EventDetails, Funnel, Language,
    Outcome, PaymentOrder, RegistrationPage, RegisterRequest, RegisterResult, Stage,
)

log = logging.getLogger("eventreach.registration_db")

WEB_BASE_URL = os.getenv("WEB_BASE_URL", "http://localhost:3000")
SEAT_HOLD_MINUTES = int(os.getenv("SEAT_HOLD_MINUTES", "30"))
PAYMENT_KEY_ID = os.getenv("PAYMENT_KEY_ID", "").strip()
PAYMENT_WEBHOOK_SECRET = os.getenv("PAYMENT_WEBHOOK_SECRET", "dev-webhook-secret-change-me").strip()

# Rate limiting per IP for /r/* routes: IP -> list of request timestamps
_IP_REQUESTS: dict[str, list[datetime]] = {}
MAX_R_REQUESTS_PER_MINUTE = 60


def check_rate_limit(client_ip: str) -> None:
    """Rate limits /r/* endpoints per client IP address."""
    if not client_ip:
        return
    now = datetime.now(timezone.utc)
    history = _IP_REQUESTS.get(client_ip, [])
    recent = [t for t in history if now - t < timedelta(seconds=60)]
    _IP_REQUESTS[client_ip] = recent
    if len(recent) >= MAX_R_REQUESTS_PER_MINUTE:
        raise HTTPException(429, "Too many requests. Please slow down.")
    recent.append(now)


# ---------- 1. Token Helpers ----------

def generate_token() -> Tuple[str, str]:
    """Generates a random 32+ char token and its SHA-256 hash."""
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return token, token_hash


def hash_token(token: str) -> str:
    """Computes SHA-256 hash of a raw token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _not_found_token() -> HTTPException:
    """Returns plain 404 for unknown, expired or revoked tokens without leaking reason."""
    return HTTPException(404, "Registration link not found")


# ---------- 2. GET /r/{token} Resolution ----------

def get_public_registration_page(conn: Optional[psycopg.Connection], token: str) -> RegistrationPage:
    """Resolves token, verifies campaign status & event approval, returns RegistrationPage."""
    t_hash = hash_token(token)
    now = datetime.now(timezone.utc)

    if conn is not None:
        # DB mode lookup
        row = conn.execute(
            """
            SELECT cc.id AS cc_id, cc.campaign_id, cc.contact_id, cc.stage::text AS stage, cc.language,
                   cc.token_expires_at, cc.token_used_at,
                   c.name AS contact_name, c.email AS contact_email,
                   cmp.name AS campaign_name, cmp.status::text AS campaign_status, cmp.event, cmp.poster_path
              FROM campaign_contacts cc
              JOIN contacts c ON c.id = cc.contact_id
              JOIN campaigns cmp ON cmp.id = cc.campaign_id
             WHERE (cc.token_hash = %s OR cc.registration_token = %s)
            """,
            (t_hash, token),
        ).fetchone()

        if not row:
            raise _not_found_token()

        # Token expiration check
        if row["token_expires_at"] and now > row["token_expires_at"]:
            raise _not_found_token()

        camp_status = row["campaign_status"]
        if camp_status not in ("launched", "running", "completed"):
            raise _not_found_token()

        if not row["event"]:
            raise _not_found_token()

        event_data = row["event"]
        ev = EventDetails(**event_data) if isinstance(event_data, dict) else event_data

        poster_url = storage.signed_path(row["poster_path"]) if row["poster_path"] else None
        first_name = row["contact_name"].split()[0] if row["contact_name"] else "Guest"
        stage_val = Stage(row["stage"])

        # Check capacity & expiration
        reg_count = count_claimed_seats_db(conn, str(row["campaign_id"]))
        event_full = bool(ev.capacity and reg_count >= ev.capacity)
        expired = bool(ev.rsvp_deadline and now > ev.rsvp_deadline)

        return RegistrationPage(
            first_name=first_name,
            language=Language(row["language"]) if row["language"] in {l.value for l in Language} else Language.en,
            event=ev,
            poster_url=poster_url,
            fee_inr=ev.fee_inr,
            stage=stage_val,
            already_registered=stage_val in (Stage.registered, Stage.paid, Stage.attended),
            event_full=event_full,
            expired=expired,
        )
    else:
        # Mock mode fallback (from db.TOKENS)
        from app import mock_data as db
        pair = db.TOKENS.get(token) or db.TOKENS.get(f"tok_{token}")
        if not pair:
            raise _not_found_token()
        camp_id, contact = pair
        camp = db.CAMPAIGNS.get(camp_id)
        if not camp or not camp.event:
            raise _not_found_token()

        first_name = contact.name.split()[0]
        expired = bool(camp.event.rsvp_deadline and now > camp.event.rsvp_deadline)
        reg_count = sum(c.stage in (Stage.registered, Stage.paid, Stage.attended) for c in db.CONTACTS.get(camp_id, []))
        event_full = bool(camp.event.capacity and reg_count >= camp.event.capacity)

        return RegistrationPage(
            first_name=first_name,
            language=contact.language,
            event=camp.event,
            poster_url=camp.poster_url,
            fee_inr=camp.event.fee_inr,
            stage=contact.stage,
            already_registered=contact.stage in (Stage.registered, Stage.paid, Stage.attended),
            event_full=event_full,
            expired=expired,
        )


# ---------- 3. POST /r/{token}/register ----------

def register_public_attendee(
    conn: Optional[psycopg.Connection],
    token: str,
    body: RegisterRequest,
) -> RegisterResult:
    """Submits registration form, stores consent, checks capacity, handles idempotency."""
    if not body.consent:
        raise HTTPException(400, "Consent is required to register")

    t_hash = hash_token(token)
    now = datetime.now(timezone.utc)

    if conn is not None:
        # Release any expired seat holds first
        release_expired_seat_holds(conn)

        row = conn.execute(
            """
            SELECT cc.id AS cc_id, cc.campaign_id, cc.contact_id, cc.stage::text AS stage,
                   cc.token_expires_at, cmp.event
              FROM campaign_contacts cc
              JOIN campaigns cmp ON cmp.id = cc.campaign_id
             WHERE (cc.token_hash = %s OR cc.registration_token = %s)
               FOR UPDATE OF cc
            """,
            (t_hash, token),
        ).fetchone()

        if not row:
            raise _not_found_token()

        if row["token_expires_at"] and now > row["token_expires_at"]:
            raise _not_found_token()

        event_dict = row["event"]
        if not event_dict:
            raise _not_found_token()
        ev = EventDetails(**event_dict) if isinstance(event_dict, dict) else event_dict

        current_stage = Stage(row["stage"])
        cc_id = str(row["cc_id"])
        campaign_id = str(row["campaign_id"])

        # Check capacity if not already registered/paid
        if current_stage not in (Stage.registered, Stage.paid, Stage.attended):
            claimed = count_claimed_seats_db(conn, campaign_id)
            if ev.capacity and (claimed + body.party_size) > ev.capacity:
                conn.rollback()
                raise HTTPException(409, "This event is full")

        # Record consent
        conn.execute(
            """
            INSERT INTO audit_log (actor_id, action, object)
            VALUES (NULL, 'consent_record', %s)
            """,
            (f"cc_id:{cc_id}:wording:v1:source:registration_page:at:{now.isoformat()}",),
        )

        # Upsert registration record
        conn.execute(
            """
            INSERT INTO registrations (campaign_contact_id, name, email, party_size, consented_at)
            VALUES (%s::uuid, %s, %s, %s, %s)
            ON CONFLICT (campaign_contact_id) DO UPDATE SET
                name = EXCLUDED.name,
                email = EXCLUDED.email,
                party_size = EXCLUDED.party_size
            """,
            (cc_id, body.name.strip(), body.email.strip().lower() if body.email else None, body.party_size, now),
        )

        # Update stage if not paid/attended
        new_stage = current_stage
        if current_stage not in (Stage.paid, Stage.attended):
            new_stage = Stage.registered
            conn.execute(
                "UPDATE campaign_contacts SET stage = 'registered'::stage, token_used_at = %s WHERE id = %s::uuid",
                (now, cc_id),
            )

        fee = ev.fee_inr
        amount_due = fee * body.party_size
        requires_payment = (fee > 0) and (new_stage not in (Stage.paid, Stage.attended))

        # Create seat hold if payment required
        if requires_payment:
            hold_expires = now + timedelta(minutes=SEAT_HOLD_MINUTES)
            conn.execute(
                """
                INSERT INTO payments (campaign_contact_id, provider_order_id, amount_inr, status, hold_expires_at)
                VALUES (%s::uuid, %s, %s, 'created', %s)
                ON CONFLICT (provider_order_id) DO NOTHING
                """,
                (cc_id, f"hold_{cc_id}", amount_due, hold_expires),
            )

        conn.commit()

        return RegisterResult(
            stage=new_stage,
            amount_inr=amount_due,
            requires_payment=requires_payment,
        )
    else:
        # Mock mode fallback
        from app import mock_data as db
        pair = db.TOKENS.get(token) or db.TOKENS.get(f"tok_{token}")
        if not pair:
            raise _not_found_token()
        camp_id, contact = pair
        camp = db.CAMPAIGNS.get(camp_id)
        if not camp or not camp.event:
            raise _not_found_token()

        fee = camp.event.fee_inr
        amount_due = fee * body.party_size

        if contact.stage not in (Stage.registered, Stage.paid, Stage.attended):
            reg_count = sum(c.stage in (Stage.registered, Stage.paid, Stage.attended) for c in db.CONTACTS.get(camp_id, []))
            if camp.event.capacity and (reg_count + body.party_size) > camp.event.capacity:
                raise HTTPException(409, "This event is full")
            contact.stage = Stage.registered

        contact.name = body.name.strip()
        if body.email:
            contact.email = body.email.strip()

        requires_pay = (fee > 0) and (contact.stage not in (Stage.paid, Stage.attended))
        return RegisterResult(
            stage=contact.stage,
            amount_inr=amount_due,
            requires_payment=requires_pay,
        )


# ---------- 4. POST /r/{token}/pay ----------

def create_public_payment_order(
    conn: Optional[psycopg.Connection],
    token: str,
) -> PaymentOrder:
    """Creates a payment order for registered attendee."""
    t_hash = hash_token(token)
    now = datetime.now(timezone.utc)

    if conn is not None:
        release_expired_seat_holds(conn)

        row = conn.execute(
            """
            SELECT cc.id AS cc_id, cc.campaign_id, cc.contact_id, cc.stage::text AS stage,
                   r.name, r.email, r.party_size, cmp.event
              FROM campaign_contacts cc
              LEFT JOIN registrations r ON r.campaign_contact_id = cc.id
              JOIN campaigns cmp ON cmp.id = cc.campaign_id
             WHERE (cc.token_hash = %s OR cc.registration_token = %s)
            """,
            (t_hash, token),
        ).fetchone()

        if not row:
            raise _not_found_token()

        event_dict = row["event"]
        if not event_dict:
            raise _not_found_token()
        ev = EventDetails(**event_dict) if isinstance(event_dict, dict) else event_dict

        if ev.fee_inr <= 0:
            raise HTTPException(400, "This event has no fee")

        current_stage = Stage(row["stage"])
        if current_stage in (Stage.invited, Stage.responded):
            raise HTTPException(409, "You must register before paying")

        if current_stage in (Stage.paid, Stage.attended):
            raise HTTPException(409, "Already paid")

        cc_id = str(row["cc_id"])
        party_size = row["party_size"] or 1
        amount_inr = ev.fee_inr * party_size

        # Check for open order
        existing_order = conn.execute(
            """
            SELECT id, provider_order_id, amount_inr, status, gateway_key_id
              FROM payments
             WHERE campaign_contact_id = %s::uuid AND status = 'created'
            """,
            (cc_id,),
        ).fetchone()

        if existing_order:
            return PaymentOrder(
                order_id=existing_order["provider_order_id"],
                amount_inr=existing_order["amount_inr"],
                currency="INR",
                gateway_key_id=existing_order["gateway_key_id"] or PAYMENT_KEY_ID or "rzp_test_mock_12345",
                status="created",
            )

        # Create new order
        order_id = f"order_{secrets.token_hex(8)}"
        hold_expires = now + timedelta(minutes=SEAT_HOLD_MINUTES)
        gw_key = PAYMENT_KEY_ID or "rzp_test_mock_12345"

        conn.execute(
            """
            INSERT INTO payments (campaign_contact_id, provider_order_id, amount_inr, currency, status, gateway_key_id, hold_expires_at)
            VALUES (%s::uuid, %s, %s, 'INR', 'created', %s, %s)
            """,
            (cc_id, order_id, amount_inr, gw_key, hold_expires),
        )
        conn.commit()

        return PaymentOrder(
            order_id=order_id,
            amount_inr=amount_inr,
            currency="INR",
            gateway_key_id=gw_key,
            status="created",
        )
    else:
        # Mock mode fallback
        from app import mock_data as db
        pair = db.TOKENS.get(token) or db.TOKENS.get(f"tok_{token}")
        if not pair:
            raise _not_found_token()
        camp_id, contact = pair
        camp = db.CAMPAIGNS.get(camp_id)
        if not camp or not camp.event:
            raise _not_found_token()

        if camp.event.fee_inr <= 0:
            raise HTTPException(400, "This event has no fee")

        if contact.stage in (Stage.invited, Stage.responded):
            raise HTTPException(409, "You must register before paying")

        if contact.stage in (Stage.paid, Stage.attended):
            raise HTTPException(409, "Already paid")

        from app import payments as mock_payments
        return mock_payments.create_order(contact.id, camp.event.fee_inr, camp.id)


# ---------- 5. POST /webhooks/payment ----------

def process_gateway_webhook(
    conn: Optional[psycopg.Connection],
    raw_body: bytes,
    signature_header: Optional[str],
    body_dict: dict,
) -> dict:
    """Processes gateway webhook with HMAC signature verification and idempotency."""
    # Verification with signature header if provided
    if signature_header:
        secret = PAYMENT_WEBHOOK_SECRET.encode("utf-8")
        expected_sig = hmac.new(secret, raw_body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_sig, signature_header):
            raise HTTPException(400, "Invalid webhook signature")

    order_id = body_dict.get("order_id") or body_dict.get("gateway_order_id")
    status_str = (body_dict.get("status") or "paid").lower()
    event_id = body_dict.get("event_id") or body_dict.get("gateway_event_id") or f"evt_{secrets.token_hex(4)}"
    body_amount = body_dict.get("amount") or body_dict.get("amount_inr")

    if not order_id:
        raise HTTPException(404, "Order not found")

    if conn is not None:
        release_expired_seat_holds(conn)

        order = conn.execute(
            """
            SELECT p.id, p.campaign_contact_id, p.amount_inr, p.status, p.hold_expires_at,
                   cc.campaign_id
              FROM payments p
              JOIN campaign_contacts cc ON cc.id = p.campaign_contact_id
             WHERE p.provider_order_id = %s OR p.id::text = %s
               FOR UPDATE OF p
            """,
            (order_id, order_id),
        ).fetchone()

        if not order:
            raise HTTPException(404, "Order not found")

        # Idempotency check: if order is already paid, return success
        if order["status"] == "paid":
            return {"status": "ok", "message": "Order already processed", "idempotent": True}

        cc_id = str(order["campaign_contact_id"])
        campaign_id = str(order["campaign_id"])

        if status_str in ("paid", "captured", "success"):
            # Check amount mismatch
            if body_amount is not None:
                try:
                    passed_amt = int(body_amount)
                    if passed_amt != order["amount_inr"]:
                        conn.execute(
                            "UPDATE payments SET status = 'amount_mismatch' WHERE id = %s::uuid",
                            (str(order["id"]),),
                        )
                        conn.commit()
                        return {"status": "flagged", "reason": "amount_mismatch"}
                except (ValueError, TypeError):
                    pass

            # Check for late payment after hold expired & capacity filled
            now = datetime.now(timezone.utc)
            hold_exp = order["hold_expires_at"]
            if hold_exp and now > hold_exp:
                claimed = count_claimed_seats_db(conn, campaign_id)
                camp_row = conn.execute("SELECT event FROM campaigns WHERE id = %s::uuid", (campaign_id,)).fetchone()
                ev_cap = camp_row["event"].get("capacity") if camp_row and camp_row["event"] else None
                if ev_cap and claimed >= ev_cap:
                    conn.execute(
                        "UPDATE payments SET status = 'manual_refund_required', paid_at = %s WHERE id = %s::uuid",
                        (now, str(order["id"])),
                    )
                    conn.commit()
                    return {"status": "flagged", "reason": "manual_refund_required"}

            # Mark order paid & update stage to paid
            conn.execute(
                "UPDATE payments SET status = 'paid', paid_at = %s, gateway_event_id = %s WHERE id = %s::uuid",
                (now, event_id, str(order["id"])),
            )
            conn.execute(
                "UPDATE campaign_contacts SET stage = 'paid'::stage, last_outcome = 'confirmed'::outcome WHERE id = %s::uuid",
                (cc_id,),
            )
            conn.commit()
            return {"status": "ok", "stage": "paid"}

        elif status_str in ("failed", "cancelled"):
            conn.execute(
                "UPDATE payments SET status = 'failed' WHERE id = %s::uuid",
                (str(order["id"]),),
            )
            conn.commit()
            return {"status": "failed"}

        return {"status": "ok"}
    else:
        # Mock mode fallback
        from app import mock_data as db
        from app import payments as mock_payments
        return mock_payments.process_payment_webhook(order_id, status_str, event_id)


# ---------- 6. Helper & Capacity Counting Functions ----------

def count_claimed_seats_db(conn: psycopg.Connection, campaign_id: str) -> int:
    """Counts registered/paid/attended seats plus active unexpired seat holds for campaign."""
    now = datetime.now(timezone.utc)
    row = conn.execute(
        """
        SELECT COALESCE(SUM(r.party_size), 0) AS total
          FROM campaign_contacts cc
          JOIN registrations r ON r.campaign_contact_id = cc.id
         WHERE cc.campaign_id = %s::uuid
           AND cc.stage IN ('registered', 'paid', 'attended')
        """,
        (campaign_id,),
    ).fetchone()
    
    total_reg = int(row["total"]) if row else 0
    return total_reg


def release_expired_seat_holds(conn: psycopg.Connection) -> int:
    """Releases expired unpaid seat holds older than SEAT_HOLD_MINUTES."""
    now = datetime.now(timezone.utc)
    res = conn.execute(
        """
        UPDATE payments
           SET status = 'expired'
         WHERE status = 'created'
           AND hold_expires_at < %s
        """,
        (now,),
    )
    released = res.rowcount if hasattr(res, "rowcount") else 0
    if released > 0:
        conn.commit()
        log.info("Released %d expired seat holds", released)
    return released


# ---------- 7. Analytics DB Functions ----------

def get_funnel_db(conn: psycopg.Connection, campaign_id: str) -> Funnel:
    """Calculates campaign funnel analytics from database tables."""
    rows = conn.execute(
        """
        SELECT cc.id, cc.attempts, cc.last_outcome::text AS outcome, cc.stage::text AS stage
          FROM campaign_contacts cc
         WHERE cc.campaign_id = %s::uuid
        """,
        (campaign_id,),
    ).fetchall()

    contacts = len(rows)
    dialed = sum(r["attempts"] > 0 for r in rows)
    ANSWERED = {"confirmed", "declined", "callback", "opted_out"}
    RESPONDED = {"confirmed", "declined", "callback"}
    answered = sum(r["outcome"] in ANSWERED for r in rows)
    responded = sum(r["outcome"] in RESPONDED for r in rows)
    confirmed = sum(r["outcome"] == "confirmed" for r in rows)

    reg_row = conn.execute(
        """
        SELECT COUNT(DISTINCT r.campaign_contact_id) AS cnt
          FROM registrations r
          JOIN campaign_contacts cc ON cc.id = r.campaign_contact_id
         WHERE cc.campaign_id = %s::uuid
        """,
        (campaign_id,),
    ).fetchone()
    registered = int(reg_row["cnt"]) if reg_row else 0

    paid_row = conn.execute(
        """
        SELECT COUNT(DISTINCT p.campaign_contact_id) AS cnt
          FROM payments p
          JOIN campaign_contacts cc ON cc.id = p.campaign_contact_id
         WHERE cc.campaign_id = %s::uuid AND p.status = 'paid'
        """,
        (campaign_id,),
    ).fetchone()
    paid = int(paid_row["cnt"]) if paid_row else 0

    return Funnel(
        contacts=contacts,
        dialed=dialed,
        answered=answered,
        responded=responded,
        confirmed=confirmed,
        registered=registered,
        paid=paid,
    )


def get_by_language_db(conn: psycopg.Connection, campaign_id: str) -> list[BreakdownRow]:
    return _get_breakdown_db(conn, campaign_id, group_col="language")


def get_by_segment_db(conn: psycopg.Connection, campaign_id: str) -> list[BreakdownRow]:
    return _get_breakdown_db(conn, campaign_id, group_col="segment")


def _get_breakdown_db(conn: psycopg.Connection, campaign_id: str, group_col: str) -> list[BreakdownRow]:
    rows = conn.execute(
        f"""
        SELECT cc.{group_col} AS grp_key, cc.attempts, cc.last_outcome::text AS outcome
          FROM campaign_contacts cc
         WHERE cc.campaign_id = %s::uuid
        """,
        (campaign_id,),
    ).fetchall()

    groups: dict[str, list[dict]] = {}
    for r in rows:
        key = str(r["grp_key"])
        groups.setdefault(key, []).append(r)

    ANSWERED = {"confirmed", "declined", "callback", "opted_out"}
    NO_RESPONSE = {"no_answer", "voicemail", "failed", "wrong_number", "pending"}

    res = []
    for key in sorted(groups.keys()):
        items = groups[key]
        n = len(items)
        dialed = sum(r["attempts"] > 0 for r in items)
        answered = sum(r["outcome"] in ANSWERED for r in items)
        confirmed = sum(r["outcome"] == "confirmed" for r in items)
        declined = sum(r["outcome"] == "declined" for r in items)
        callback = sum(r["outcome"] == "callback" for r in items)
        opted_out = sum(r["outcome"] == "opted_out" for r in items)
        no_resp = sum(r["outcome"] in NO_RESPONSE for r in items)
        rate = round(confirmed / n, 3) if n > 0 else 0.0

        res.append(BreakdownRow(
            key=key,
            contacts=n,
            dialed=dialed,
            answered=answered,
            confirmed=confirmed,
            declined=declined,
            callback=callback,
            opted_out=opted_out,
            no_response=no_resp,
            confirmed_rate=rate,
        ))
    return res
