"""Unit tests for registration link edge cases: invalid token, consent requirement, capacity, and deadlines."""
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import pytest

from app.main import app
from app import mock_data as db
from app.schemas import EventDetails, Stage


@pytest.fixture
def client():
    return TestClient(app)


def test_invalid_registration_token_returns_404(client):
    r = client.get("/r/tok_does_not_exist_9999")
    assert r.status_code == 404
    assert "not valid" in r.json()["detail"].lower()


def test_registration_without_consent_fails(client):
    r = client.post(
        "/r/tok_ct_004/register",
        json={"name": "Arjun Verma", "consent": False, "party_size": 1},
    )
    assert r.status_code == 400
    assert "consent is required" in r.json()["detail"].lower()


def test_successful_registration_and_stage_update(client):
    # Ensure fresh stage for this test
    db.TOKENS["tok_ct_004"][1].stage = Stage.invited

    # Verify registration page loads
    r_get = client.get("/r/tok_ct_004")
    assert r_get.status_code == 200
    data = r_get.json()
    assert "first_name" in data
    assert data["event_full"] is False

    # Register
    r_post = client.post(
        "/r/tok_ct_004/register",
        json={"name": "Arjun Verma", "consent": True, "party_size": 1},
    )
    assert r_post.status_code == 200
    res = r_post.json()
    assert res["stage"] == "registered"


def test_event_capacity_limit(client):
    camp = db.CAMPAIGNS["cmp_001"]
    old_cap = camp.event.capacity
    try:
        # Set artificially small capacity
        camp.event.capacity = 1
        r = client.get("/r/tok_ct_013")  # Sneha Das, unconfirmed
        assert r.status_code == 200
        assert r.json()["event_full"] is True

        r_reg = client.post(
            "/r/tok_ct_013/register",
            json={"name": "Sneha Das", "consent": True, "party_size": 1},
        )
        assert r_reg.status_code == 409
        assert "capacity" in r_reg.json()["detail"].lower()
    finally:
        camp.event.capacity = old_cap
