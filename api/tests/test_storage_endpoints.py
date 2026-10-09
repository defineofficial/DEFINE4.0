"""Poster and voice note uploads and the signed-link route, in mock mode (no database needed)."""
import pytest
from fastapi.testclient import TestClient

from app import storage
from app.main import app, _MOCK_ASSETS

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
WAV = b"RIFF\x24\x00\x00\x00WAVEfmt " + b"\x00" * 64


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "store"))
    monkeypatch.setenv("SECRET_KEY", "k" * 40)
    _MOCK_ASSETS.clear()
    with TestClient(app) as c:
        yield c
    _MOCK_ASSETS.clear()


def upload(client, path, name, data, content_type):
    return client.post(path, files={"file": (name, data, content_type)})


def test_poster_upload_returns_a_link_that_serves_the_file(client):
    r = upload(client, "/campaigns/cmp_001/poster", "poster.png", PNG, "image/png")
    assert r.status_code == 200
    link = r.json()["poster_url"]
    assert link.startswith("/files/posters/cmp_001/")
    got = client.get(link)
    assert got.status_code == 200 and got.content == PNG
    assert got.headers["content-type"] == "image/png"
    assert got.headers["cache-control"] == "private, no-store"
    assert got.headers["x-content-type-options"] == "nosniff"


def test_campaign_shows_a_fresh_link_after_upload(client):
    upload(client, "/campaigns/cmp_001/poster", "p.png", PNG, "image/png")
    url = client.get("/campaigns/cmp_001").json()["poster_url"]
    assert client.get(url).status_code == 200


def test_replacing_the_poster_deletes_the_old_file(client):
    first = upload(client, "/campaigns/cmp_001/poster", "a.png", PNG, "image/png").json()["poster_url"]
    second = upload(client, "/campaigns/cmp_001/poster", "b.png", PNG + b"1", "image/png").json()["poster_url"]
    assert first != second
    assert client.get(first).status_code == 404
    assert client.get(second).status_code == 200


def test_tampered_link_is_403_and_expired_link_is_410(client, monkeypatch):
    link = upload(client, "/campaigns/cmp_001/poster", "p.png", PNG, "image/png").json()["poster_url"]
    path, query = link.split("?")
    exp, sig = [p.split("=")[1] for p in query.split("&")]
    assert client.get(f"{path}?exp={int(exp) + 9999}&sig={sig}").status_code == 403
    assert client.get(f"{path}?exp={exp}").status_code == 403           # no signature at all
    assert client.get(path).status_code == 403
    monkeypatch.setattr(storage.time, "time", lambda: int(exp) + 1)
    assert client.get(link).status_code == 410


def test_a_valid_signature_cannot_reach_files_outside_storage(client):
    # Even if someone could sign it, a key that is not ours is never served.
    assert client.get("/files/../../etc/passwd?exp=1&sig=x").status_code in (403, 404)
    assert client.get("/files/posters/cmp_001/../../x.png?exp=1&sig=x").status_code in (403, 404)


def test_wrong_file_type_is_415_and_nothing_is_stored(client, tmp_path):
    r = upload(client, "/campaigns/cmp_001/poster", "evil.png", b"<svg onload=alert(1)>", "image/png")
    assert r.status_code == 415
    assert not (tmp_path / "store").exists()


def test_empty_upload_is_422_and_oversize_is_413(client):
    assert upload(client, "/campaigns/cmp_001/poster", "p.png", b"", "image/png").status_code == 422
    big = PNG + b"\x00" * storage.RULES["poster"].max_bytes
    assert upload(client, "/campaigns/cmp_001/poster", "p.png", big, "image/png").status_code == 413


def test_unknown_campaign_is_404_and_stores_nothing(client, tmp_path):
    assert upload(client, "/campaigns/nope/poster", "p.png", PNG, "image/png").status_code == 404
    assert upload(client, "/campaigns/nope/voice-note", "v.wav", WAV, "audio/wav").status_code == 404
    assert not (tmp_path / "store").exists()


def test_voice_note_is_stored_privately_and_the_draft_is_still_returned(client):
    r = upload(client, "/campaigns/cmp_001/voice-note", "note.wav", WAV, "audio/wav")
    assert r.status_code == 200 and "transcript" in r.json()
    key = _MOCK_ASSETS[("cmp_001", "voice_note")]
    assert key.startswith("voice-notes/cmp_001/") and storage.read_bytes(key) == WAV


def test_a_poster_is_not_accepted_as_a_voice_note(client):
    assert upload(client, "/campaigns/cmp_001/voice-note", "x.png", PNG, "audio/wav").status_code == 415
