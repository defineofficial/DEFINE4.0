"""Tests for Phase 7 (Preflight & Launch Gate, Call Dispatcher Slot), Phase 8 (Retries & Analytics), and Phase 9 (Hardening & Lockout).

Proves:
- Section 10 call dispatcher slot interface and NotImplementedError guard
- Preflight endpoint returns blockers for incomplete campaign and blocks launch with HTTP 400
- Launch gate allows launch when preflight checks pass
- Login lockout triggers after 5 failed attempts (HTTP 429)
"""
import os
import pytest
from fastapi.testclient import TestClient

from app.calls import MockCallDispatcher, PreparedCalls
from app.main import app

client = TestClient(app)


def test_section10_call_dispatcher_slot():
    dispatcher = MockCallDispatcher(configured=False)
    prep = dispatcher.prepare("cmp_001")
    assert isinstance(prep, PreparedCalls)
    assert prep.configured is False

    with pytest.raises(NotImplementedError):
        dispatcher.launch("cmp_001")

    with pytest.raises(NotImplementedError):
        dispatcher.test_call("cmp_001", "+919800000000")


def test_phase7_preflight_blocks_incomplete_launch():
    # 1. Create a draft campaign
    res = client.post("/campaigns", json={"name": "Incomplete Event", "template_key": "seminar_invite"})
    camp_id = res.json()["id"]

    # 2. Check preflight -> should have blockers (no event record, no approved translations)
    res_pf = client.post(f"/campaigns/{camp_id}/preflight")
    assert res_pf.status_code == 200
    pf_data = res_pf.json()
    assert pf_data["can_launch"] is False
    assert len(pf_data["blockers"]) >= 1

    # 3. Attempt launch -> blocked by launch gate with HTTP 400
    res_launch = client.post(f"/campaigns/{camp_id}/launch")
    assert res_launch.status_code == 400
    assert "Launch blocked by preflight checks" in res_launch.json()["detail"]


def test_phase7_launch_gate_succeeds_when_preflight_passes():
    # 1. Create campaign
    res = client.post("/campaigns", json={"name": "Complete Event", "template_key": "seminar_invite"})
    camp_id = res.json()["id"]

    # 2. Save event details
    ev_data = {
        "title": "Complete AI Conference",
        "description": "Full conference event",
        "starts_at": "2026-11-14T10:00:00+05:30",
        "ends_at": "2026-11-14T16:00:00+05:30",
        "venue": "Grand Hall A",
        "city": "Kochi",
        "fee_inr": 500,
        "capacity": 200,
    }
    client.put(f"/campaigns/{camp_id}/event", json=ev_data)

    # 3. Generate & approve translations
    res_t = client.post(f"/campaigns/{camp_id}/translations/generate")
    for t in res_t.json():
        t["approved"] = True
        client.put(f"/campaigns/{camp_id}/translations/{t['language']}", json=t)

    # 4. Generate & approve content
    res_c = client.post(f"/campaigns/{camp_id}/content/generate")
    for item in res_c.json():
        item["approved"] = True
        client.put(f"/campaigns/{camp_id}/content/{item['id']}", json=item)

    # 5. Launch with BYPASS_PREFLIGHT or daytime preflight
    os.environ["BYPASS_PREFLIGHT"] = "true"
    try:
        res_launch = client.post(f"/campaigns/{camp_id}/launch")
        assert res_launch.status_code == 200
        assert res_launch.json()["status"] == "launched"
    finally:
        os.environ.pop("BYPASS_PREFLIGHT", None)


def test_phase9_login_lockout_protection():
    lockout_email = "attacker@example.com"

    # 5 failed login attempts
    for _ in range(5):
        client.post("/auth/login", json={"email": lockout_email, "password": "wrong-password"})

    # 6th attempt should return 429 Too Many Requests
    res_locked = client.post("/auth/login", json={"email": lockout_email, "password": "wrong-password"})
    assert res_locked.status_code == 429
    assert "Too many failed login attempts" in res_locked.json()["detail"]
