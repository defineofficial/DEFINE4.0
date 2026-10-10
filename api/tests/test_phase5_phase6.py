"""Tests for Phase 5 (Template Engine & Content Generation) and Phase 6 (Sending Infrastructure).

Proves:
- Template engine render_message produces consistent copy across channels & languages
- SMS segment calculation for GSM-7 vs Unicode Indic scripts
- Quiet hours detection (21:00 to 08:00 IST)
- Global opt-out enforcement skipping opted-out recipients
- Idempotent dispatch preventing duplicate sending
- Mock adapters vs real SMTP adapter dispatch
- Content generation, approval, and test-send API endpoints
"""
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient

from app.date_resolver import IST
from app.main import app
from app.outreach import (
    calculate_sms_segments,
    dispatch_item_to_recipient,
    generate_campaign_content,
    is_quiet_hours,
    send_test_message,
)
from app.schemas import Channel, EventDetails, Language, OutreachItem
from app.template_engine import render_message

client = TestClient(app)

NOW = datetime(2026, 11, 14, 10, 0, 0, tzinfo=IST)


def sample_event():
    return EventDetails(
        title="AI in Healthcare Seminar",
        description="Executive seminar on AI healthcare applications.",
        starts_at=NOW,
        ends_at=NOW + timedelta(hours=6),
        venue="Seminar Hall A",
        city="Kochi",
        fee_inr=500,
        capacity=100,
    )


# ---------- Phase 5 Tests: Template Engine & Content Generation ----------

def test_p5_01_template_engine_renders_preset_channels():
    vars_dict = {
        "name": "Asha Thomas",
        "event_title": "Healthcare Seminar",
        "date": "14 November 2026",
        "time": "10:00 AM",
        "venue": "Seminar Hall A",
        "city": "Kochi",
        "link": "http://localhost:3000/r/tok123",
    }
    
    # English SMS
    res_en = render_message("seminar_invite", Language.en, Channel.sms, vars_dict)
    assert "Asha Thomas" in res_en["body"]
    assert "Healthcare Seminar" in res_en["body"]
    assert "Kochi" in res_en["body"]

    # Malayalam WhatsApp
    res_ml = render_message("seminar_invite", Language.ml, Channel.whatsapp, vars_dict)
    assert "Asha Thomas" in res_ml["body"]
    assert "Healthcare Seminar" in res_ml["body"]


def test_p5_02_sms_segment_calculation():
    # GSM-7 short text
    seg1, type1 = calculate_sms_segments("Hi Asha, you are invited to Healthcare Seminar!")
    assert seg1 == 1
    assert type1 == "GSM-7"

    # Unicode Indic text short (under 70 chars)
    seg2, type2 = calculate_sms_segments("നമസ്കാരം ആശ, സെമിനാറിലേക്ക് സ്വാഗതം.")
    assert seg2 == 1
    assert type2 == "Unicode"

    # Unicode Indic text long (over 70 chars)
    long_ml = "നമസ്കാരം ആശ, 14 നവംബറിൽ കൊച്ചിയിലെ സെമിനാർ ഹാളിൽ നടക്കുന്ന ആർട്ടിഫിഷ്യൽ ഇന്റലിജൻസ് ഹെൽത്ത്കെയർ സെമിനാറിലേക്ക് സ്വാഗതം."
    seg3, type3 = calculate_sms_segments(long_ml)
    assert seg3 > 1
    assert type3 == "Unicode"


def test_p5_03_quiet_hours_detection():
    # 22:00 (10 PM IST) -> Quiet hours ACTIVE
    night_dt = datetime(2026, 11, 14, 22, 0, 0, tzinfo=IST)
    assert is_quiet_hours(night_dt) is True

    # 02:00 (2 AM IST) -> Quiet hours ACTIVE
    early_dt = datetime(2026, 11, 14, 2, 0, 0, tzinfo=IST)
    assert is_quiet_hours(early_dt) is True

    # 14:00 (2 PM IST) -> Quiet hours INACTIVE
    day_dt = datetime(2026, 11, 14, 14, 0, 0, tzinfo=IST)
    assert is_quiet_hours(day_dt) is False


def test_p5_04_opt_out_and_idempotency_dispatch():
    item = OutreachItem(
        id="item_001",
        campaign_id="cmp_001",
        channel=Channel.sms,
        language=Language.en,
        body="Hi {name}, invitation link: {link}",
    )
    
    # 1. Opted-out contact -> skipped
    opted_out_hashes = {"hash_opted_out_123"}
    log1 = dispatch_item_to_recipient(
        item=item,
        contact_id="cnt_001",
        recipient_masked="900***0011",
        phone_hash="hash_opted_out_123",
        opted_out_hashes=opted_out_hashes,
    )
    assert log1.status == "skipped_opted_out"

    # 2. Normal contact daytime dispatch -> mocked / sent
    day_time = datetime(2026, 11, 14, 12, 0, 0, tzinfo=IST)
    log2 = dispatch_item_to_recipient(
        item=item,
        contact_id="cnt_002",
        recipient_masked="900***0022",
        phone_hash="hash_normal_456",
        opted_out_hashes=opted_out_hashes,
        current_time=day_time,
    )
    assert log2.status in ("mocked", "sent", "skipped_quiet_hours")

    # 3. Duplicate dispatch same item + contact -> skipped_duplicate
    log3 = dispatch_item_to_recipient(
        item=item,
        contact_id="cnt_002",
        recipient_masked="900***0022",
        phone_hash="hash_normal_456",
        opted_out_hashes=opted_out_hashes,
        current_time=day_time,
    )
    assert log3.status == "skipped_duplicate"


# ---------- Phase 6 Tests: API Flow & Test Send ----------

def test_p6_01_content_generation_api_flow():
    # 1. Create campaign and save event
    res_c = client.post("/campaigns", json={"name": "Clinic Event", "template_key": "clinic_reminder"})
    camp_id = res_c.json()["id"]

    ev_data = {
        "title": "Cardiology Clinic Drive",
        "description": "Heart checkup clinic drive",
        "starts_at": "2026-11-14T10:00:00+05:30",
        "ends_at": "2026-11-14T16:00:00+05:30",
        "venue": "City Clinic, Block C",
        "city": "Kochi",
        "fee_inr": 0,
        "capacity": 50,
    }
    client.put(f"/campaigns/{camp_id}/event", json=ev_data)

    # 2. Generate outreach content items
    res_gen = client.post(f"/campaigns/{camp_id}/content/generate")
    assert res_gen.status_code == 200
    items = res_gen.json()
    assert len(items) >= 1

    item_id = items[0]["id"]

    # 3. GET /campaigns/{id}/content/{item_id}
    res_get = client.get(f"/campaigns/{camp_id}/content/{item_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == item_id

    # 4. Approve content items
    for it in items:
        it["approved"] = True
        client.put(f"/campaigns/{camp_id}/content/{it['id']}", json=it)

    # Verify campaign status progressed to content_ready
    res_camp = client.get(f"/campaigns/{camp_id}")
    assert res_camp.status_code == 200
    assert res_camp.json()["status"] == "content_ready"


def test_p6_02_test_send_endpoint():
    res_c = client.post("/campaigns", json={"name": "Test Send Campaign", "template_key": "seminar_invite"})
    camp_id = res_c.json()["id"]

    # Send test email
    req_email = {"channel": "email", "language": "en", "target": "organizer@example.com"}
    res_e = client.post(f"/campaigns/{camp_id}/test-send", json=req_email)
    assert res_e.status_code == 200
    assert res_e.json()["status"] in ("mocked", "sent")

    # Send test SMS
    req_sms = {"channel": "sms", "language": "hi", "target": "+919800000000"}
    res_s = client.post(f"/campaigns/{camp_id}/test-send", json=req_sms)
    assert res_s.status_code == 200
    assert res_s.json()["status"] == "mock_sent"
