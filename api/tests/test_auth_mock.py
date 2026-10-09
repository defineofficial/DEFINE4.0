from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_mock_mode_login_and_me_work_without_a_database():
    assert client.post("/auth/login", json={"email": "a@b.co", "password": "whatever"}).json()["access_token"]
    assert client.get("/me").json()["role"] == "organizer"


def test_mock_mode_register_returns_a_token():
    res = client.post("/auth/register", json={"name": "Asha", "email": "asha@example.com", "password": "longenough1"})
    assert res.status_code == 201 and res.json()["access_token"]


def test_health_without_a_database():
    body = client.get("/health").json()
    assert body["status"] == "ok" and body["database"] == "not configured"


def test_signup_rules_are_checked_even_in_mock_mode():
    bad = {"name": "Asha", "email": "not-an-email", "password": "short"}
    assert client.post("/auth/register", json=bad).status_code == 422
