"""Payment gateway integration (test mode), webhook signature verification, seat hold timer, and receipts.

Supports Razorpay-style test mode order creation and HMAC-SHA256 webhook verification.
Guarantees webhook idempotency and manages 15-minute seat reservation holds.
"""
import hashlib
import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Set

from app.schemas import PaymentOrder, Stage

log = logging.getLogger("eventreach.payments")

HOLD_DURATION_MINUTES = 15

# In-memory payment store for orders: order_id -> order dict
_ORDERS: Dict[str, Dict[str, Any]] = {}
# Idempotency cache: set of processed webhook IDs / signatures
_PROCESSED_WEBHOOKS: Set[str] = set()


def _webhook_secret() -> str:
    return os.getenv("PAYMENT_WEBHOOK_SECRET", "dev-webhook-secret-change-me")


def _key_id() -> str:
    return os.getenv("PAYMENT_KEY_ID", "rzp_test_mock_12345")


# ---------- 1. Create Payment Order with Seat Hold ----------

def create_order(
    contact_id: str,
    amount_inr: int,
    campaign_id: str,
    party_size: int = 1,
) -> PaymentOrder:
    """Creates a new test payment order with a 15-minute seat hold."""
    order_id = f"order_{secrets.token_hex(8)}"
    now = datetime.now(timezone.utc)
    hold_expires = now + timedelta(minutes=HOLD_DURATION_MINUTES)

    order_record = {
        "order_id": order_id,
        "contact_id": contact_id,
        "campaign_id": campaign_id,
        "amount_inr": amount_inr,
        "currency": "INR",
        "status": "created",
        "party_size": party_size,
        "created_at": now,
        "hold_expires_at": hold_expires,
        "paid_at": None,
    }
    _ORDERS[order_id] = order_record

    return PaymentOrder(
        order_id=order_id,
        amount_inr=amount_inr,
        currency="INR",
        gateway_key_id=_key_id(),
        status="created",
    )


# ---------- 2. Verify Webhook Signature ----------

def verify_webhook_signature(body_bytes: bytes, signature_header: str) -> bool:
    """Verifies HMAC-SHA256 signature from payment gateway."""
    secret = _webhook_secret().encode("utf-8")
    expected = hmac.new(secret, body_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


# ---------- 3. Process Webhook with Idempotency ----------

def process_payment_webhook(order_id: str, status: str, event_id: Optional[str] = None) -> Dict[str, Any]:
    """Processes payment webhook. Idempotent: duplicate calls safely return success."""
    webhook_key = f"{order_id}:{status}:{event_id or ''}"
    if webhook_key in _PROCESSED_WEBHOOKS:
        log.info("Duplicate webhook received and ignored: %s", webhook_key)
        return {"ok": True, "duplicate": True}

    order = _ORDERS.get(order_id)
    if not order:
        raise ValueError("Order not found")

    if status.lower() in ("paid", "captured", "success"):
        order["status"] = "paid"
        order["paid_at"] = datetime.now(timezone.utc)
        try:
            from app import mock_data as db
            for group in db.CONTACTS.values():
                for c in group:
                    if c.id == order["contact_id"]:
                        c.stage = Stage.paid
                        c.last_outcome = Outcome.confirmed
        except Exception:
            pass
    elif status.lower() in ("failed", "cancelled"):
        order["status"] = "failed"

    _PROCESSED_WEBHOOKS.add(webhook_key)
    return {"ok": True, "status": order["status"], "contact_id": order["contact_id"]}


# ---------- 4. Seat Hold Expiration / Cleanup ----------

def is_hold_expired(order_id: str) -> bool:
    """Checks if an unpaid order has exceeded its 15-minute reservation window."""
    order = _ORDERS.get(order_id)
    if not order or order["status"] == "paid":
        return False
    now = datetime.now(timezone.utc)
    return now > order["hold_expires_at"]


def release_expired_holds() -> int:
    """Releases seats for all unpaid orders older than 15 minutes."""
    released_count = 0
    now = datetime.now(timezone.utc)
    for order in _ORDERS.values():
        if order["status"] == "created" and now > order["hold_expires_at"]:
            order["status"] = "expired"
            released_count += order.get("party_size", 1)
    return released_count


def get_order(order_id: str) -> Optional[Dict[str, Any]]:
    return _ORDERS.get(order_id)
