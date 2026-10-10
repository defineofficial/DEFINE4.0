"""Tests for stretch goals: .ics calendar invite generation and QR ticket check-in."""
from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.schemas import Stage


@pytest.fixture
def client():
    return TestClient(app)


def test_download_calendar_invite(client):
    r = client.get("/r/tok_ct_001/calendar.ics")
    assert r.status_code == 200
    assert "text/calendar" in r.headers["content-type"]
    assert "BEGIN:VCALENDAR" in r.text
    assert "BEGIN:VEVENT" in r.text
    assert "STATUS:CONFIRMED" in r.text
    assert "END:VCALENDAR" in r.text


def test_get_ticket_svg(client):
    r = client.get("/r/tok_ct_001/ticket.svg")
    assert r.status_code == 200
    assert "image/svg+xml" in r.headers["content-type"]
    assert "<svg" in r.text
    assert "EVENTPASS" in r.text
    assert "Anjali Menon" in r.text


def test_staff_qr_checkin_flow(client):
    token = "tok_ct_001"
    # First check-in
    r1 = client.post(f"/r/{token}/check-in")
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1["status"] == "checked_in"
    assert data1["stage"] == "attended"

    # Idempotent re-scan
    r2 = client.post(f"/r/{token}/check-in")
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["status"] == "already_checked_in"
    assert data2["stage"] == "attended"
