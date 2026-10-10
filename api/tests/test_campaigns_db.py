"""Campaign tests against a real PostgreSQL. Skipped unless TEST_DATABASE_URL is set.

The main point: organizer A can never see or change organizer B's campaigns.
"""
import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app import db, dbsetup
from app.main import app

TEST_URL = os.getenv("TEST_DATABASE_URL", "").strip()
pytestmark = [
    pytest.mark.database,
    pytest.mark.skipif(not TEST_URL, reason="Set TEST_DATABASE_URL to run the database tests"),
]

ASHA = {"name": "Asha Thomas", "email": "asha@example.com", "password": "correct-horse-1"}
BEN = {"name": "Ben Joseph", "email": "ben@example.com", "password": "battery-staple-2"}
EVENT = {
    "title": "AI in Healthcare Seminar", "starts_at": "2026-11-14T10:00:00+05:30",
    "ends_at": "2026-11-14T16:00:00+05:30", "venue": "Seminar Hall, Block A", "city": "Kochi",
    "fee_inr": 500, "capacity": 120,
}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", TEST_URL)
    db.close_pool()
    dbsetup.setup(TEST_URL, reset=True)
    with TestClient(app) as c:
        yield c
    db.close_pool()


def sign_in(client, creds) -> dict:
    token = client.post("/auth/register", json=creds).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def make(client, headers, name="AI Seminar", template="seminar_invite"):
    return client.post("/campaigns", json={"name": name, "template_key": template}, headers=headers)


def test_every_campaign_endpoint_needs_login(client):
    fake = str(uuid4())
    assert client.get("/campaigns").status_code == 401
    assert client.post("/campaigns", json={"name": "x", "template_key": "seminar_invite"}).status_code == 401
    assert client.get(f"/campaigns/{fake}").status_code == 401
    assert client.put(f"/campaigns/{fake}/event", json=EVENT).status_code == 401


def test_create_then_read_back(client):
    h = sign_in(client, ASHA)
    res = make(client, h)
    assert res.status_code == 201
    created = res.json()
    assert created["name"] == "AI Seminar" and created["status"] == "draft"
    assert created["template_key"] == "seminar_invite" and created["contact_count"] == 0
    assert created["event"] is None and created["poster_url"] is None
    assert client.get(f"/campaigns/{created['id']}", headers=h).json() == created
    assert client.get("/campaigns", headers=h).json() == [created]


def test_new_campaign_gets_the_template_default_channels(client):
    h = sign_in(client, ASHA)
    assert make(client, h).json()["channels"] == ["call", "sms", "email", "whatsapp"]
    assert make(client, h, template="clinic_reminder").json()["channels"] == ["call", "sms"]


def test_unknown_template_and_blank_name_are_rejected(client):
    h = sign_in(client, ASHA)
    assert make(client, h, template="nope").status_code == 422
    assert make(client, h, name="   ").status_code == 422
    assert make(client, h, name="").status_code == 422
    assert client.get("/campaigns", headers=h).json() == []


def test_names_in_indian_languages_are_saved(client):
    h = sign_in(client, ASHA)
    created = make(client, h, name="കൊച്ചി സെമിനാർ").json()
    assert client.get(f"/campaigns/{created['id']}", headers=h).json()["name"] == "കൊച്ചി സെമിനാർ"


def test_save_event_round_trip(client):
    h = sign_in(client, ASHA)
    cid = make(client, h).json()["id"]
    res = client.put(f"/campaigns/{cid}/event", json=EVENT, headers=h)
    assert res.status_code == 200
    event = res.json()["event"]
    assert event["title"] == "AI in Healthcare Seminar" and event["city"] == "Kochi"
    assert event["fee_inr"] == 500 and event["capacity"] == 120
    assert client.get(f"/campaigns/{cid}", headers=h).json()["event"]["venue"] == "Seminar Hall, Block A"
    changed = client.put(f"/campaigns/{cid}/event", json={**EVENT, "fee_inr": 0}, headers=h).json()
    assert changed["event"]["fee_inr"] == 0


def test_bad_event_details_are_rejected_and_nothing_is_saved(client):
    h = sign_in(client, ASHA)
    cid = make(client, h).json()["id"]
    backwards = {**EVENT, "ends_at": "2026-11-14T08:00:00+05:30"}
    assert client.put(f"/campaigns/{cid}/event", json=backwards, headers=h).status_code == 422
    assert client.put(f"/campaigns/{cid}/event", json={**EVENT, "fee_inr": -1}, headers=h).status_code == 422
    assert client.put(f"/campaigns/{cid}/event", json={**EVENT, "capacity": 0}, headers=h).status_code == 422
    assert client.get(f"/campaigns/{cid}", headers=h).json()["event"] is None


def test_organizers_only_see_their_own_campaigns(client):
    asha, ben = sign_in(client, ASHA), sign_in(client, BEN)
    a = make(client, asha, name="Asha's seminar").json()
    b = make(client, ben, name="Ben's workshop").json()
    assert [c["id"] for c in client.get("/campaigns", headers=asha).json()] == [a["id"]]
    assert [c["id"] for c in client.get("/campaigns", headers=ben).json()] == [b["id"]]


def test_organizer_a_cannot_open_organizer_bs_campaign(client):
    asha, ben = sign_in(client, ASHA), sign_in(client, BEN)
    b_id = make(client, ben, name="Ben's workshop").json()["id"]
    assert client.get(f"/campaigns/{b_id}", headers=asha).status_code == 404


def test_organizer_a_cannot_change_organizer_bs_campaign(client):
    asha, ben = sign_in(client, ASHA), sign_in(client, BEN)
    b_id = make(client, ben).json()["id"]
    assert client.put(f"/campaigns/{b_id}/event", json=EVENT, headers=asha).status_code == 404
    assert client.get(f"/campaigns/{b_id}", headers=ben).json()["event"] is None  # untouched


def test_someone_elses_campaign_looks_the_same_as_one_that_does_not_exist(client):
    asha, ben = sign_in(client, ASHA), sign_in(client, BEN)
    b_id = make(client, ben).json()["id"]
    theirs = client.get(f"/campaigns/{b_id}", headers=asha)
    missing = client.get(f"/campaigns/{uuid4()}", headers=asha)
    assert theirs.status_code == missing.status_code == 404
    assert theirs.json() == missing.json()


def test_an_id_that_is_not_a_uuid_is_a_404_not_a_crash(client):
    h = sign_in(client, ASHA)
    assert client.get("/campaigns/cmp_001", headers=h).status_code == 404
    assert client.get("/campaigns/not-an-id", headers=h).status_code == 404
    assert client.put("/campaigns/not-an-id/event", json=EVENT, headers=h).status_code == 404


def test_admin_role_does_not_open_other_organizers_campaigns_yet(client):
    from app import auth
    ben = sign_in(client, BEN)
    b_id = make(client, ben).json()["id"]
    with db.get_pool().connection() as conn:
        auth.create_organizer(conn, "Root", "root@example.com", "correct-horse-1", role="admin")
    token = client.post("/auth/login", json={"email": "root@example.com", "password": "correct-horse-1"}).json()["access_token"]
    assert client.get(f"/campaigns/{b_id}", headers={"Authorization": f"Bearer {token}"}).status_code == 404
