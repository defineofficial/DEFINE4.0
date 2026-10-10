"""Tests for the template engine across all presets, languages, and channels."""
import pytest
from app.schemas import Channel, Language
from app.template_engine import list_templates, get_template, render_message, PRESETS


def test_presets_exist():
    assert len(PRESETS) == 4
    keys = {t.key for t in list_templates()}
    assert keys == {"seminar_invite", "clinic_reminder", "school_notice", "payment_reminder"}


def test_render_seminar_invite_multilingual():
    vars = {
        "name": "Asha Thomas",
        "event_title": "AI in Healthcare Seminar",
        "date": "14 November",
        "time": "10:00 AM",
        "venue": "Seminar Hall A",
        "city": "Kochi",
        "link": "https://reach.local/r/abc",
    }
    
    # English call
    en_call = render_message("seminar_invite", Language.en, Channel.call, vars)
    assert "Asha Thomas" in en_call["script"]
    assert "AI in Healthcare Seminar" in en_call["script"]
    assert "Press 1 to confirm" in en_call["script"]
    
    # Hindi WhatsApp
    hi_wa = render_message("seminar_invite", Language.hi, Channel.whatsapp, vars)
    assert "Asha Thomas" in hi_wa["body"]
    assert "https://reach.local/r/abc" in hi_wa["body"]
    
    # Malayalam Call
    ml_call = render_message("seminar_invite", Language.ml, Channel.call, vars)
    assert "നമസ്കാരം" in ml_call["script"]
    assert "Asha Thomas" in ml_call["script"]

    # Tamil SMS
    ta_sms = render_message("seminar_invite", Language.ta, Channel.sms, vars)
    assert "வணக்கம்" in ta_sms["body"]


def test_render_clinic_reminder():
    vars = {
        "name": "Rohan",
        "doctor": "Radhakrishnan",
        "date": "Tomorrow",
        "time": "4:30 PM",
        "clinic_name": "Apollo Clinic",
        "link": "https://reach.local/r/xyz",
    }
    res = render_message("clinic_reminder", Language.en, Channel.call, vars)
    assert "Dr. Radhakrishnan" in res["script"]
    assert "Apollo Clinic" in res["script"]


def test_render_payment_reminder():
    vars = {
        "name": "Kavitha",
        "amount_inr": "1500",
        "purpose": "Course Fee",
        "due_date": "15 October",
        "link": "https://reach.local/r/pay123",
    }
    res = render_message("payment_reminder", Language.en, Channel.sms, vars)
    assert "1500" in res["body"]
    assert "https://reach.local/r/pay123" in res["body"]
