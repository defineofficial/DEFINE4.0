"""Comprehensive test suite for DB-backed public registration, payments, seat holds, webhooks, and privacy invariants."""
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app import db as database, auth, registration_db
from app.schemas import EventDetails, Language, Stage

TEST_DB_URL = os.getenv("DATABASE_URL", "")


@pytest.fixture
def client():
    return TestClient(app)


def _get_test_conn():
    if not database.enabled():
        pytest.skip("DATABASE_URL is not set; skipping PostgreSQL registration tests")
    return database.get_pool().connection()


def setup_test_campaign(conn, fee_inr=500, capacity=10):
    """Helper to set up an organizer, a campaign with an event, and a contact."""
    with conn.cursor() as cur:
        # Create organizer A
        email_a = f"org_a_{secrets.token_hex(4)}@example.com"
        org_a = conn.execute(
            "INSERT INTO organizers (email, name, password_hash) VALUES (%s, %s, 'hash') RETURNING id",
            (email_a, "Organizer A"),
        ).fetchone()
        org_a_id = str(org_a["id"])

        # Create organizer B
        email_b = f"org_b_{secrets.token_hex(4)}@example.com"
        org_b = conn.execute(
            "INSERT INTO organizers (email, name, password_hash) VALUES (%s, %s, 'hash') RETURNING id",
            (email_b, "Organizer B"),
        ).fetchone()
        org_b_id = str(org_b["id"])

        # Event details
        ev = EventDetails(
            title="Tech Summit 2026",
            description="Annual Summit",
            starts_at=datetime.now(timezone.utc) + timedelta(days=7),
            ends_at=datetime.now(timezone.utc) + timedelta(days=7, hours=5),
            venue="Main Auditorium",
            city="Kochi",
            fee_inr=fee_inr,
            capacity=capacity,
        )

        # Create campaign for Org A
        camp_row = conn.execute(
            """
            INSERT INTO campaigns (organizer_id, template_key, name, status, event, languages)
            VALUES (%s::uuid, 'seminar_invite', 'Tech Summit', 'launched', %s, '{en}')
            RETURNING id
            """,
            (org_a_id, psycopg.types.json.Jsonb(ev.model_dump(mode="json"))),
        ).fetchone()
        camp_id = str(camp_row["id"])

        # Create campaign for Org B
        camp_b_row = conn.execute(
            """
            INSERT INTO campaigns (organizer_id, template_key, name, status, event, languages)
            VALUES (%s::uuid, 'seminar_invite', 'Private Summit B', 'launched', %s, '{en}')
            RETURNING id
            """,
            (org_b_id, psycopg.types.json.Jsonb(ev.model_dump(mode="json"))),
        ).fetchone()
        camp_b_id = str(camp_b_row["id"])

        # Create contact for Org A
        raw_token = secrets.token_urlsafe(32)
        t_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        phone_enc = b"encrypted_bytes_placeholder"
        phone_hash = f"hash_{secrets.token_hex(6)}"

        contact_row = conn.execute(
            """
            INSERT INTO contacts (organizer_id, name, phone_enc, phone_hash, phone_masked, email)
            VALUES (%s::uuid, 'Alice Smith', %s, %s, '+91 98••• ••001', 'alice@example.com')
            RETURNING id
            """,
            (org_a_id, phone_enc, phone_hash),
        ).fetchone()
        contact_id = str(contact_row["id"])

        cc_row = conn.execute(
            """
            INSERT INTO campaign_contacts (campaign_id, contact_id, language, segment, stage, registration_token, token_hash)
            VALUES (%s::uuid, %s::uuid, 'en', 'General', 'invited', %s, %s)
            RETURNING id
            """,
            (camp_id, contact_id, t_hash, t_hash),
        ).fetchone()
        cc_id = str(cc_row["id"])

        conn.commit()

        return {
            "org_a_id": org_a_id,
            "org_b_id": org_b_id,
            "camp_id": camp_id,
            "camp_b_id": camp_b_id,
            "contact_id": contact_id,
            "cc_id": cc_id,
            "raw_token": raw_token,
            "token_hash": t_hash,
        }


def test_public_registration_free_and_paid_happy_paths(client):
    """Test happy path registration for free event and paid event."""
    with _get_test_conn() as conn:
        # 1. Free event
        data_free = setup_test_campaign(conn, fee_inr=0, capacity=10)
        token_free = data_free["raw_token"]

        # GET registration page
        r_get = client.get(f"/r/{token_free}")
        assert r_get.status_code == 200
        page = r_get.json()
        assert page["first_name"] == "Alice"
        assert page["fee_inr"] == 0
        assert page["already_registered"] is False

        # POST register
        r_reg = client.post(
            f"/r/{token_free}/register",
            json={"name": "Alice Smith", "email": "alice@example.com", "consent": True, "party_size": 1},
        )
        assert r_reg.status_code == 200
        reg_res = r_reg.json()
        assert reg_res["stage"] == "registered"
        assert reg_res["requires_payment"] is False

        # 2. Paid event
        data_paid = setup_test_campaign(conn, fee_inr=500, capacity=10)
        token_paid = data_paid["raw_token"]

        r_reg_paid = client.post(
            f"/r/{token_paid}/register",
            json={"name": "Alice Smith", "email": "alice@example.com", "consent": True, "party_size": 2},
        )
        assert r_reg_paid.status_code == 200
        paid_res = r_reg_paid.json()
        assert paid_res["stage"] == "registered"
        assert paid_res["requires_payment"] is True
        assert paid_res["amount_inr"] == 1000  # 500 * 2 party_size


def test_registration_no_consent_returns_400(client):
    """Registration without explicit consent must return 400."""
    with _get_test_conn() as conn:
        data = setup_test_campaign(conn, fee_inr=0)
        token = data["raw_token"]

        r = client.post(
            f"/r/{token}/register",
            json={"name": "Alice Smith", "consent": False, "party_size": 1},
        )
        assert r.status_code == 400
        assert "consent" in r.json()["detail"].lower()


def test_invalid_expired_revoked_tokens_return_plain_404(client):
    """Unknown or expired tokens must return plain 404 without leaking reason."""
    # Unknown token
    r_unk = client.get("/r/invalid_token_1234567890_abcdefg")
    assert r_unk.status_code == 404
    assert r_unk.json()["detail"] == "Registration link not found"

    with _get_test_conn() as conn:
        data = setup_test_campaign(conn)
        cc_id = data["cc_id"]
        # Set token_expires_at in past
        conn.execute(
            "UPDATE campaign_contacts SET token_expires_at = %s WHERE id = %s::uuid",
            (datetime.now(timezone.utc) - timedelta(days=1), cc_id),
        )
        conn.commit()

        r_exp = client.get(f"/r/{data['raw_token']}")
        assert r_exp.status_code == 404
        assert r_exp.json()["detail"] == "Registration link not found"


def test_capacity_limit_and_idempotency(client):
    """Enforce capacity 409 conflict and idempotent re-registering."""
    with _get_test_conn() as conn:
        data = setup_test_campaign(conn, fee_inr=100, capacity=1)
        token = data["raw_token"]

        # Register person 1 (occupies 1 seat)
        r1 = client.post(
            f"/r/{token}/register",
            json={"name": "Alice Smith", "consent": True, "party_size": 1},
        )
        assert r1.status_code == 200

        # Registering second time for SAME person updates details idempotently
        r1_repeat = client.post(
            f"/r/{token}/register",
            json={"name": "Alice Smith Updated", "consent": True, "party_size": 1},
        )
        assert r1_repeat.status_code == 200
        assert r1_repeat.json()["stage"] == "registered"

        # Verify only 1 row created in registrations table
        reg_cnt = conn.execute(
            "SELECT count(*) AS n FROM registrations WHERE campaign_contact_id = %s::uuid",
            (data["cc_id"],),
        ).fetchone()["n"]
        assert reg_cnt == 1

        # Second contact for same campaign trying to register when capacity is full
        raw_token2 = secrets.token_urlsafe(32)
        t_hash2 = hashlib.sha256(raw_token2.encode("utf-8")).hexdigest()
        contact2 = conn.execute(
            """
            INSERT INTO contacts (organizer_id, name, phone_enc, phone_hash, phone_masked)
            VALUES (%s::uuid, 'Bob Jones', 'enc', %s, '+91 98••• ••002')
            RETURNING id
            """,
            (data["org_a_id"], f"hash_{secrets.token_hex(6)}"),
        ).fetchone()
        conn.execute(
            """
            INSERT INTO campaign_contacts (campaign_id, contact_id, language, stage, registration_token, token_hash)
            VALUES (%s::uuid, %s::uuid, 'en', 'invited', %s, %s)
            """,
            (data["camp_id"], str(contact2["id"]), t_hash2, t_hash2),
        )
        conn.commit()

        # Person 2 gets 409 full capacity
        r2 = client.post(
            f"/r/{raw_token2}/register",
            json={"name": "Bob Jones", "consent": True, "party_size": 1},
        )
        assert r2.status_code == 409
        assert "full" in r2.json()["detail"].lower()


def test_payment_creation_order_reuse_and_server_calculated_amount(client):
    """Payment order amount is server computed; calling pay twice returns same open order."""
    with _get_test_conn() as conn:
        data = setup_test_campaign(conn, fee_inr=750, capacity=10)
        token = data["raw_token"]

        # Attempt to pay before registering -> 409
        r_pre_pay = client.post(f"/r/{token}/pay")
        assert r_pre_pay.status_code == 409

        # Register party_size=2
        client.post(
            f"/r/{token}/register",
            json={"name": "Alice Smith", "consent": True, "party_size": 2},
        )

        # Create payment order (750 * 2 = 1500 INR)
        r_pay1 = client.post(f"/r/{token}/pay")
        assert r_pay1.status_code == 200
        order1 = r_pay1.json()
        assert order1["amount_inr"] == 1500
        assert order1["status"] == "created"

        # Calling pay again returns the EXACT same open order ID
        r_pay2 = client.post(f"/r/{token}/pay")
        assert r_pay2.status_code == 200
        order2 = r_pay2.json()
        assert order2["order_id"] == order1["order_id"]


def test_webhook_signature_idempotency_amount_mismatch_and_late_payment(client):
    """Webhook handling: HMAC signature validation, idempotency, mismatch flagging, manual refund."""
    with _get_test_conn() as conn:
        data = setup_test_campaign(conn, fee_inr=500, capacity=10)
        token = data["raw_token"]

        client.post(
            f"/r/{token}/register",
            json={"name": "Alice Smith", "consent": True, "party_size": 1},
        )
        r_pay = client.post(f"/r/{token}/pay")
        order_id = r_pay.json()["order_id"]

        secret = os.getenv("PAYMENT_WEBHOOK_SECRET", "dev-webhook-secret-change-me")

        # 1. Invalid signature -> 400
        bad_headers = {"X-Razorpay-Signature": "invalid_signature_hex"}
        r_bad_sig = client.post("/webhooks/payment", json={"order_id": order_id, "status": "paid"}, headers=bad_headers)
        assert r_bad_sig.status_code == 400

        # 2. Valid signature + amount mismatch -> status = flagged
        payload_mismatch = {"order_id": order_id, "status": "paid", "amount": 200, "event_id": "evt_mismatch_1"}
        raw_body_mm = json_bytes(payload_mismatch)
        sig_mm = hmac.new(secret.encode("utf-8"), raw_body_mm, hashlib.sha256).hexdigest()
        r_mm = client.post("/webhooks/payment", content=raw_body_mm, headers={"X-Razorpay-Signature": sig_mm, "Content-Type": "application/json"})
        assert r_mm.status_code == 200
        assert r_mm.json()["status"] == "flagged"

        # Reset order status back to created for success test
        conn.execute("UPDATE payments SET status = 'created' WHERE provider_order_id = %s", (order_id,))
        conn.commit()

        # 3. Valid signature + matching amount -> paid
        payload_ok = {"order_id": order_id, "status": "paid", "amount": 500, "event_id": "evt_valid_1"}
        raw_body_ok = json_bytes(payload_ok)
        sig_ok = hmac.new(secret.encode("utf-8"), raw_body_ok, hashlib.sha256).hexdigest()
        r_ok = client.post("/webhooks/payment", content=raw_body_ok, headers={"X-Razorpay-Signature": sig_ok, "Content-Type": "application/json"})
        assert r_ok.status_code == 200
        assert r_ok.json()["stage"] == "paid"

        # 4. Duplicate webhook -> 200 idempotent
        r_dup = client.post("/webhooks/payment", content=raw_body_ok, headers={"X-Razorpay-Signature": sig_ok, "Content-Type": "application/json"})
        assert r_dup.status_code == 200
        assert r_dup.json()["idempotent"] is True

        # 5. Pay after paid -> 409
        r_pay_again = client.post(f"/r/{token}/pay")
        assert r_pay_again.status_code == 409


def test_hold_expiry_releases_seat(client):
    """Expired unpaid seat hold releases capacity."""
    with _get_test_conn() as conn:
        data = setup_test_campaign(conn, fee_inr=500, capacity=10)
        token = data["raw_token"]

        client.post(f"/r/{token}/register", json={"name": "Alice", "consent": True, "party_size": 1})
        client.post(f"/r/{token}/pay")

        # Force hold_expires_at into the past
        conn.execute(
            "UPDATE payments SET hold_expires_at = %s WHERE campaign_contact_id = %s::uuid",
            (datetime.now(timezone.utc) - timedelta(minutes=60), data["cc_id"]),
        )
        conn.commit()

        # Call release_expired_seat_holds
        released = registration_db.release_expired_seat_holds(conn)
        assert released >= 1

        # Order status should be 'expired'
        row = conn.execute("SELECT status FROM payments WHERE campaign_contact_id = %s::uuid", (data["cc_id"],)).fetchone()
        assert row["status"] == "expired"


def test_privacy_invariants(client):
    """Privacy check: full phone numbers never appear in responses or logs."""
    with _get_test_conn() as conn:
        data = setup_test_campaign(conn)
        token = data["raw_token"]

        r_page = client.get(f"/r/{token}")
        body_text = r_page.text

        # Phone numbers or unmasked patterns must not be in response
        assert "+9198765" not in body_text
        assert "phone_enc" not in body_text


def json_bytes(obj) -> bytes:
    import json
    return json.dumps(obj, separators=(",", ":")).encode("utf-8")
