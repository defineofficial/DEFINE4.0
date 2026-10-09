"""Tests that need a real PostgreSQL. They are skipped unless TEST_DATABASE_URL is set.

TEST_DATABASE_URL must point at a separate, empty database (eventreach_test).
These tests delete everything in it before each test.
"""
import os
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

from app import auth, db, dbsetup
from app.main import app

TEST_URL = os.getenv("TEST_DATABASE_URL", "").strip()
pytestmark = [
    pytest.mark.database,
    pytest.mark.skipif(not TEST_URL, reason="Set TEST_DATABASE_URL to run the database tests"),
]

GOOD = {"name": "Asha Thomas", "email": "asha@example.com", "password": "correct-horse-1"}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", TEST_URL)
    db.close_pool()
    dbsetup.setup(TEST_URL, reset=True)
    with TestClient(app) as c:
        yield c
    db.close_pool()


def sign_in(client, creds=GOOD) -> str:
    client.post("/auth/register", json=creds)
    return client.post("/auth/login", json={"email": creds["email"], "password": creds["password"]}).json()["access_token"]


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def query(sql: str, params=()):
    with db.get_pool().connection() as conn:
        return conn.execute(sql, params).fetchall()


def test_register_login_and_me_round_trip(client):
    token = sign_in(client)
    me = client.get("/me", headers=bearer(token)).json()
    assert me["email"] == "asha@example.com" and me["name"] == "Asha Thomas" and me["role"] == "organizer"


def test_indian_language_names_are_stored_correctly(client):
    token = sign_in(client, {**GOOD, "name": "അഞ്ജലി മേനോൻ"})
    assert client.get("/me", headers=bearer(token)).json()["name"] == "അഞ്ജലി മേനോൻ"
    assert query("SHOW server_encoding")[0]["server_encoding"] == "UTF8"


def test_register_returns_a_working_token_straight_away(client):
    token = client.post("/auth/register", json=GOOD).json()["access_token"]
    assert client.get("/me", headers=bearer(token)).status_code == 200


def test_password_is_stored_only_as_an_argon2_hash(client):
    client.post("/auth/register", json=GOOD)
    stored = query("SELECT password_hash FROM organizers")[0]["password_hash"]
    assert stored.startswith("$argon2") and GOOD["password"] not in stored


def test_email_is_unique_ignoring_capitals(client):
    assert client.post("/auth/register", json=GOOD).status_code == 201
    again = client.post("/auth/register", json={**GOOD, "email": "ASHA@Example.com"})
    assert again.status_code == 409
    assert query("SELECT count(*) AS n FROM organizers")[0]["n"] == 1


def test_wrong_password_and_unknown_email_get_the_same_answer(client):
    client.post("/auth/register", json=GOOD)
    wrong = client.post("/auth/login", json={"email": GOOD["email"], "password": "not-the-password"})
    unknown = client.post("/auth/login", json={"email": "nobody@example.com", "password": "whatever-1"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_me_needs_a_valid_token(client):
    assert client.get("/me").status_code == 401
    assert client.get("/me", headers=bearer("garbage")).status_code == 401


def test_expired_token_is_refused(client):
    token = sign_in(client)
    sub = jwt.decode(token, auth._secret(), algorithms=["HS256"])["sub"]
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    old = jwt.encode({"sub": sub, "role": "organizer", "exp": past}, auth._secret(), algorithm="HS256")
    assert client.get("/me", headers=bearer(old)).status_code == 401


def test_token_for_a_deleted_account_is_refused(client):
    token = sign_in(client)
    with db.get_pool().connection() as conn:
        conn.execute("DELETE FROM organizers")
        conn.commit()
    assert client.get("/me", headers=bearer(token)).status_code == 401


def test_token_signed_with_another_key_is_refused(client):
    token = sign_in(client)
    sub = jwt.decode(token, auth._secret(), algorithms=["HS256"])["sub"]
    forged = jwt.encode({"sub": sub, "role": "admin"}, "x" * 40, algorithm="HS256")
    assert client.get("/me", headers=bearer(forged)).status_code == 401


def test_weak_signup_is_rejected(client):
    assert client.post("/auth/register", json={**GOOD, "password": "short"}).status_code == 422
    assert client.post("/auth/register", json={**GOOD, "email": "nope"}).status_code == 422


def test_sign_up_can_be_closed(client, monkeypatch):
    monkeypatch.setenv("ALLOW_REGISTRATION", "false")
    assert client.post("/auth/register", json=GOOD).status_code == 403
    assert query("SELECT count(*) AS n FROM organizers")[0]["n"] == 0


def test_admin_role_comes_through(client):
    with db.get_pool().connection() as conn:
        auth.create_organizer(conn, "Root", "root@example.com", "correct-horse-1", role="admin")
    token = client.post("/auth/login", json={"email": "root@example.com", "password": "correct-horse-1"}).json()["access_token"]
    assert client.get("/me", headers=bearer(token)).json()["role"] == "admin"


def test_templates_are_loaded_and_loading_twice_changes_nothing(client):
    assert query("SELECT count(*) AS n FROM templates")[0]["n"] == 4
    assert dbsetup.setup(TEST_URL) == "already existed"
    assert query("SELECT count(*) AS n FROM templates")[0]["n"] == 4
    # psycopg returns arrays of custom enum types as text, so cast to text[] when reading them
    row = query("SELECT default_channels::text[] AS default_channels, keypad_options "
                "FROM templates WHERE key = 'seminar_invite'")[0]
    assert row["default_channels"] == ["call", "sms", "email", "whatsapp"]
    assert any(o["digit"] == "9" for o in row["keypad_options"])


def test_reset_refuses_a_database_on_another_machine():
    with pytest.raises(RuntimeError):
        dbsetup.setup("postgresql://u:p@db.example.com:5432/x", reset=True)


def test_health_reports_the_database(client):
    assert client.get("/health").json()["database"] == "connected"


def test_health_degrades_when_the_database_is_down(client, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://nobody:nothing@127.0.0.1:1/none")
    res = client.get("/health")
    assert res.status_code == 503 and res.json()["database"] == "unreachable"
