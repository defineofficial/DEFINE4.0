from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app import mailer
from app.main import app

client = TestClient(app)
H = {"Authorization": "Bearer x"}


def setup_function(_):
    mailer.OUTBOX.clear()


def test_invitation_has_the_facts_in_every_language():
    for lang in ("en", "hi", "ml", "ta"):
        m = mailer.build_invitation(name="Anjali", language=lang, title="AI in Healthcare Seminar",
                                    starts_at=datetime(2026, 11, 14, 4, 30, tzinfo=timezone.utc),
                                    venue="Seminar Hall, Block A", city="Kochi", fee_inr=500, link="http://x/r/t")
        for fact in ("AI in Healthcare Seminar", "14 November 2026", "10:00 AM", "Seminar Hall, Block A", "Rs 500", "http://x/r/t"):
            assert fact in m["text"], (lang, fact)


def test_html_escapes_input():
    m = mailer.build_invitation(name="<b>x</b>", language="en", title="<script>", starts_at=datetime.now(timezone.utc),
                                venue="v", city="c", link="http://x/?a=1&b=2")
    assert "<script>" not in m["html"] and "&lt;script&gt;" in m["html"]


def test_mock_mode_records_and_never_raises(monkeypatch):
    monkeypatch.delenv("SMTP_HOST", raising=False)
    r = mailer.send_email("a@example.com", "s", "t")
    assert r["status"] == "mocked" and mailer.OUTBOX[-1]["to"] == "a@example.com"


def test_bad_address_is_a_failure_not_a_crash():
    assert mailer.send_email("not-an-email", "s", "t")["status"] == "failed"


def test_real_send_uses_smtp(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.test"); monkeypatch.setenv("MOCK_CHANNELS", "false")
    monkeypatch.setenv("EMAIL_FROM", "me@test"); monkeypatch.setenv("SMTP_USER", "me@test"); monkeypatch.setenv("SMTP_PASSWORD", "pw")
    calls = []

    class FakeSMTP:
        def __init__(self, h, p, timeout=0): calls.append(("connect", h, p))
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def starttls(self): calls.append(("tls",))
        def login(self, u, p): calls.append(("login", u))
        def send_message(self, m): calls.append(("send", m["To"], m["Subject"]))
    monkeypatch.setattr(mailer.smtplib, "SMTP", FakeSMTP)
    r = mailer.send_email("a@example.com", "Hi", "body", "<p>body</p>")
    assert r["status"] == "sent" and ("send", "a@example.com", "Hi") in calls and ("tls",) in calls


def test_smtp_error_is_reported(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.test"); monkeypatch.setenv("MOCK_CHANNELS", "false"); monkeypatch.setenv("EMAIL_FROM", "me@test")
    def boom(*a, **k): raise OSError("connection refused")
    monkeypatch.setattr(mailer.smtplib, "SMTP", boom)
    r = mailer.send_email("a@example.com", "s", "t")
    assert r["status"] == "failed" and "refused" in r["error"]


def test_send_campaign_emails_skips_opted_out_and_missing():
    r = client.post("/campaigns/cmp_001/email/send", headers=H, json={"stages": ["invited", "responded", "registered", "paid", "attended"]})
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["mocked"] + b["skipped_no_email"] + b["skipped_opted_out"] == 14
    assert b["mocked"] == len(mailer.OUTBOX) and b["live"] is False


def test_test_email_and_outbox():
    r = client.post("/campaigns/cmp_001/email/test", headers=H, json={"to": "me@example.com"})
    assert r.status_code == 200 and r.json()["status"] == "mocked"
    o = client.get("/campaigns/cmp_001/email/outbox", headers=H).json()
    assert o["items"][0]["subject"].startswith("[TEST]")


def test_unknown_campaign_404():
    assert client.post("/campaigns/nope/email/send", headers=H).status_code == 404


def test_registration_sends_confirmation_and_survives_email_failure(monkeypatch):
    r = client.post("/r/tok_ct_004/register", json={"name": "Arjun", "email": "arjun@example.com", "consent": True})
    assert r.status_code == 200
    assert any(m["subject"].startswith("Registration confirmed") for m in mailer.OUTBOX)
    monkeypatch.setattr(mailer, "send_email", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("down")))
    assert client.post("/r/tok_ct_004/register", json={"name": "Arjun", "email": "arjun@example.com", "consent": True}).status_code == 200
