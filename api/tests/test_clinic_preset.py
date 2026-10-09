"""Test demonstrating that clinic_reminder preset runs through the exact same engine.

Proves platform reusability across domains (healthcare clinic reminders vs seminars).
"""
from datetime import datetime, timezone
from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.schemas import Channel, EventDetails, Language
from app.template_engine import get_template, render_message
from app.translation_engine import translate_event


@pytest.fixture
def client():
    return TestClient(app)


def test_clinic_reminder_template_configuration():
    tpl = get_template("clinic_reminder")
    assert tpl is not None
    assert tpl.name == "Clinic appointment reminder"
    assert "doctor" in tpl.variables
    assert "clinic_name" in tpl.variables
    # Keypad outcomes
    digits = {opt.digit: opt.outcome for opt in tpl.keypad_options}
    assert digits["1"] == "confirmed"
    assert digits["2"] == "callback"   # Reschedule
    assert digits["3"] == "declined"   # Cancel
    assert digits["9"] == "opted_out"  # Stop


def test_clinic_reminder_multilingual_dispatch():
    vars = {
        "name": "Rohan Menon",
        "doctor": "Nair",
        "date": "15 November",
        "time": "11:00 AM",
        "clinic_name": "Sunrise Healthcare Clinic",
        "link": "https://reach.local/r/tok_clinic_01",
    }

    # 1. Spoken Call Script (English)
    en_call = render_message("clinic_reminder", Language.en, Channel.call, vars)
    assert "Dr. Nair" in en_call["script"]
    assert "Sunrise Healthcare Clinic" in en_call["script"]
    assert "Press 1 to confirm, 2 to reschedule, 3 to cancel" in en_call["script"]

    # 2. Spoken Call Script (Hindi)
    hi_call = render_message("clinic_reminder", Language.hi, Channel.call, vars)
    assert "डॉ. Nair" in hi_call["script"]
    assert "पुष्टि के लिए 1" in hi_call["script"]

    # 3. Spoken Call Script (Malayalam)
    ml_call = render_message("clinic_reminder", Language.ml, Channel.call, vars)
    assert "ഡോക്ടർ Nair" in ml_call["script"]
    assert "സ്ഥിരീകരിക്കാൻ 1" in ml_call["script"]

    # 4. WhatsApp Layout (Tamil)
    ta_wa = render_message("clinic_reminder", Language.ta, Channel.whatsapp, vars)
    assert "மருத்துவர் Nair" in ta_wa["body"]
    assert "https://reach.local/r/tok_clinic_01" in ta_wa["body"]


def test_clinic_event_translation_and_back_translation():
    clinic_event = EventDetails(
        title="Dr. Nair Consultation Appointment",
        starts_at=datetime(2026, 11, 15, 11, 0, tzinfo=timezone.utc),
        venue="Room 204",
        city="Kochi",
        fee_inr=0,  # Consultation is free or post-pay
    )
    res = translate_event(clinic_event, Language.ml)
    assert res.language == Language.ml
    assert "Dr. Nair" in res.call_script or "Consultation" in res.call_script
    assert res.back_translation_en is not None
