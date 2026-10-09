"""Poster and voice note storage against a real PostgreSQL. Skipped unless TEST_DATABASE_URL is set.

The main point: organizer B can never upload to, or learn anything about, organizer A's campaign.
"""
import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app import db, dbsetup, storage
from app.main import app

TEST_URL = os.getenv("TEST_DATABASE_URL", "").strip()
pytestmark = [
    pytest.mark.database,
    pytest.mark.skipif(not TEST_URL, reason="Set TEST_DATABASE_URL to run the database tests"),
]

ASHA = {"name": "Asha Thomas", "email": "asha@example.com", "password": "correct-horse-1"}
BEN = {"name": "Ben Joseph", "email": "ben@example.com", "password": "battery-staple-2"}
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
WAV = b"RIFF\x24\x00\x00\x00WAVEfmt " + b"\x00" * 64


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", TEST_URL)
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "store"))
    monkeypatch.setenv("SECRET_KEY", "k" * 40)
    db.close_pool()
    dbsetup.setup(TEST_URL, reset=True)
    with TestClient(app) as c:
        yield c
    db.close_pool()


def sign_in(client, creds) -> dict:
    token = client.post("/auth/register", json=creds).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def new_campaign(client, headers) -> str:
    return client.post("/campaigns", json={"name": "AI Seminar", "template_key": "seminar_invite"},
                       headers=headers).json()["id"]


def up(client, headers, cid, what="poster"):
    path, name, data = (("poster", "p.png", PNG) if what == "poster" else ("voice-note", "v.wav", WAV))
    return client.post(f"/campaigns/{cid}/{path}", files={"file": (name, data)}, headers=headers)


def test_uploads_need_login(client):
    fake = str(uuid4())
    assert client.post(f"/campaigns/{fake}/poster", files={"file": ("p.png", PNG)}).status_code == 401
    assert client.post(f"/campaigns/{fake}/voice-note", files={"file": ("v.wav", WAV)}).status_code == 401


def test_poster_is_saved_on_the_campaign_and_shown_with_a_fresh_link(client):
    h = sign_in(client, ASHA)
    cid = new_campaign(client, h)
    link = up(client, h, cid).json()["poster_url"]
    assert client.get(link).content == PNG                       # the link needs no login, only the signature
    shown = client.get(f"/campaigns/{cid}", headers=h).json()["poster_url"]
    assert shown and client.get(shown).content == PNG
    assert client.get("/campaigns", headers=h).json()[0]["poster_url"]


def test_another_organizer_cannot_upload_to_my_campaign(client, tmp_path):
    asha, ben = sign_in(client, ASHA), sign_in(client, BEN)
    cid = new_campaign(client, asha)
    assert up(client, ben, cid).status_code == 404
    assert up(client, ben, cid, "voice").status_code == 404
    assert client.get(f"/campaigns/{cid}", headers=asha).json()["poster_url"] is None
    assert not (tmp_path / "store").exists()


def test_replacing_a_poster_removes_the_old_file(client):
    h = sign_in(client, ASHA)
    cid = new_campaign(client, h)
    first = up(client, h, cid).json()["poster_url"]
    up(client, h, cid)
    assert client.get(first).status_code == 404


def test_voice_note_path_is_recorded(client):
    h = sign_in(client, ASHA)
    cid = new_campaign(client, h)
    assert up(client, h, cid, "voice").status_code == 200
    with db.get_pool().connection() as conn:
        row = conn.execute("SELECT voice_note_path FROM campaigns WHERE id = %s", (cid,)).fetchone()
    assert row["voice_note_path"].startswith("voice-notes/") and storage.read_bytes(row["voice_note_path"]) == WAV
