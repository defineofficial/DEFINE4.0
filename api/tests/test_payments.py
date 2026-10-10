"""Tests for payment order creation, webhook verification, idempotency, and seat hold."""
import hashlib
import hmac
import pytest
from app.payments import (
    create_order,
    get_order,
    is_hold_expired,
    process_payment_webhook,
    release_expired_holds,
    verify_webhook_signature,
    _webhook_secret,
)


def test_create_order_sets_hold():
    order = create_order("ct_001", 500, "cmp_001", party_size=2)
    assert order.amount_inr == 500
    assert order.currency == "INR"
    assert order.status == "created"
    
    rec = get_order(order.order_id)
    assert rec is not None
    assert rec["party_size"] == 2
    assert is_hold_expired(order.order_id) is False


def test_webhook_signature_verification():
    body = b'{"order_id": "order_123", "status": "paid"}'
    secret = _webhook_secret().encode("utf-8")
    valid_sig = hmac.new(secret, body, hashlib.sha256).hexdigest()
    
    assert verify_webhook_signature(body, valid_sig) is True
    assert verify_webhook_signature(body, "invalid_signature") is False


def test_webhook_idempotency():
    order = create_order("ct_002", 500, "cmp_001")
    
    # First delivery
    res1 = process_payment_webhook(order.order_id, "paid", event_id="evt_1")
    assert res1["ok"] is True
    assert res1.get("duplicate") is None or res1.get("duplicate") is False
    assert get_order(order.order_id)["status"] == "paid"

    # Duplicate delivery of exact same webhook
    res2 = process_payment_webhook(order.order_id, "paid", event_id="evt_1")
    assert res2["ok"] is True
    assert res2.get("duplicate") is True
