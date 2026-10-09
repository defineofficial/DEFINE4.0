from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
C = "/campaigns/cmp_001"


def test_health_and_templates():
    assert client.get("/health").json()["status"] == "ok"
    keys = [t["key"] for t in client.get("/templates").json()]
    assert keys == ["seminar_invite", "clinic_reminder", "school_notice", "payment_reminder"]


def test_every_template_offers_opt_out_on_9():
    for t in client.get("/templates").json():
        assert any(o["digit"] == "9" and o["outcome"] == "opted_out" for o in t["keypad_options"])


def test_contacts_never_expose_full_phone_numbers():
    page = client.get(f"{C}/contacts").json()
    assert page["total"] == 14
    for c in page["items"]:
        assert "phone" not in c
        assert "•" in c["phone_masked"]


def test_contact_filters():
    ml = client.get(f"{C}/contacts", params={"language": "ml"}).json()
    assert ml["total"] == 4 and all(c["language"] == "ml" for c in ml["items"])


def test_breakdowns_add_up_to_total():
    funnel = client.get(f"{C}/analytics/funnel").json()
    assert funnel["contacts"] == 14
    for path in ("by-language", "by-segment"):
        rows = client.get(f"{C}/analytics/{path}").json()
        assert sum(r["contacts"] for r in rows) == funnel["contacts"]
        for r in rows:
            parts = r["confirmed"] + r["declined"] + r["callback"] + r["opted_out"] + r["no_response"]
            assert parts == r["contacts"]


def test_retry_skips_people_over_the_attempt_cap():
    res = client.post(f"{C}/retry", json={"target": "non_responders"}).json()
    assert res == {"queued": 3, "skipped_opted_out": 0, "skipped_max_attempts": 1}


def test_registration_requires_consent_then_payment_flow():
    token = "tok_ct_004"
    page = client.get(f"/r/{token}").json()
    assert page["first_name"] == "Arjun" and page["language"] == "hi"
    assert client.post(f"/r/{token}/register", json={"name": "Arjun", "consent": False}).status_code == 400
    reg = client.post(f"/r/{token}/register", json={"name": "Arjun", "consent": True}).json()
    assert reg["stage"] == "registered" and reg["requires_payment"] is True
    order = client.post(f"/r/{token}/pay").json()
    assert order["amount_inr"] == 500
    assert client.post("/webhooks/payment", json={"order_id": order["order_id"], "status": "paid"}).status_code == 200
    assert client.get(f"/r/{token}").json()["stage"] == "paid"


def test_unknown_link_is_404():
    assert client.get("/r/not-a-real-token").status_code == 404


def test_opt_out_is_remembered():
    c = client.post("/contacts/ct_013/opt-out").json()
    assert c["opted_out"] is True and c["last_outcome"] == "opted_out"
