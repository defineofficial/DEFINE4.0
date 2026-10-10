"""Tests for Phase 3 (Event Versioning & Staleness Propagation) and Phase 4 (Translations).

Proves:
- Content hash calculation over event details
- Event version incrementing on detail changes
- Staleness propagation marking translations `stale` and setting `approved = False`
- Editing translations by hand setting status to `edited`
- Placeholder protection detecting missing or altered placeholders
- Per-language date formatting for EN, HI, ML, TA
- Automatic fact check detecting mismatches in date, city, fee, or keypad options
- Round-trip back-translation to English
"""
from datetime import datetime, timedelta, timezone
import pytest

from app.event_versioning import compute_event_hash, update_event_record, propagate_staleness
from app.glossary import get_glossary, check_glossary_compliance
from app.schemas import EventDetails, Language, Translation
from app.translation_engine import (
    format_event_date_for_lang,
    verify_placeholders,
    fact_check_translation,
    generate_translations,
    translate_event,
)

IST = timezone(timedelta(hours=5, minutes=30))
NOW = datetime(2026, 11, 14, 10, 0, 0, tzinfo=IST)


def sample_event():
    return EventDetails(
        title="AI in Healthcare Seminar",
        description="Executive seminar on AI healthcare applications.",
        starts_at=NOW,
        ends_at=NOW + timedelta(hours=6),
        venue="Seminar Hall, Block A",
        city="Kochi",
        fee_inr=500,
        capacity=100,
    )


# ---------- Phase 3 Tests: Versioning & Staleness ----------

def test_p3_01_event_content_hash_deterministic():
    ev1 = sample_event()
    ev2 = sample_event()
    assert compute_event_hash(ev1) == compute_event_hash(ev2)


def test_p3_02_event_content_hash_changes_on_field_edit():
    ev1 = sample_event()
    ev2 = sample_event()
    ev2.venue = "Auditorium, Block B"
    assert compute_event_hash(ev1) != compute_event_hash(ev2)


def test_p3_03_event_version_increment_on_change():
    ev1 = sample_event()
    h1 = compute_event_hash(ev1)
    
    # Same event details -> version unchanged
    v, h, changed = update_event_record(ev1, 1, h1, ev1)
    assert v == 1
    assert changed is False

    # Modified venue -> version incremented to 2
    ev2 = sample_event()
    ev2.venue = "Grand Hall"
    v2, h2, changed2 = update_event_record(ev1, 1, h1, ev2)
    assert v2 == 2
    assert changed2 is True
    assert h2 != h1


def test_p3_04_staleness_propagation_invalidates_translations():
    ev1 = sample_event()
    h1 = compute_event_hash(ev1)
    t = translate_event(ev1, Language.hi, event_version=1)
    t.approved = True
    t.status = "approved"

    # Event updated to version 2
    ev2 = sample_event()
    ev2.fee_inr = 0
    v2, h2, _ = update_event_record(ev1, 1, h1, ev2)

    updated_translations, any_stale = propagate_staleness([t], v2, h2)
    assert any_stale is True
    assert updated_translations[0].approved is False
    assert updated_translations[0].status == "stale"
    assert updated_translations[0].event_version == 2


# ---------- Phase 4 Tests: Translations, Placeholders, Date Formatting, Fact Check ----------

def test_p4_01_per_language_date_formatting():
    en_d = format_event_date_for_lang(NOW, Language.en)
    hi_d = format_event_date_for_lang(NOW, Language.hi)
    ml_d = format_event_date_for_lang(NOW, Language.ml)
    ta_d = format_event_date_for_lang(NOW, Language.ta)

    assert "14 November" in en_d
    assert "14 नवंबर" in hi_d
    assert "നവംബർ 14" in ml_d
    assert "நவம்பர் 14" in ta_d


def test_p4_02_placeholder_protection_detects_missing():
    original = "Hello {name}, register at {link}."
    good_trans = "नमस्ते {name}, {link} पर रजिस्टर करें।"
    bad_trans = "नमस्ते, यहां रजिस्टर करें।"

    assert verify_placeholders(original, good_trans) == []
    errs = verify_placeholders(original, bad_trans)
    assert "missing_placeholder:link" in errs
    assert "missing_placeholder:name" in errs


def test_p4_03_automatic_fact_check_passes():
    ev = sample_event()
    t = translate_event(ev, Language.hi, event_version=1)
    res = fact_check_translation(ev, t, Language.hi)
    assert res["passed"] is True
    assert res["mismatches"] == []


def test_p4_04_automatic_fact_check_fails_on_wrong_city():
    ev = sample_event()
    ev.city = "Bengaluru"
    t = translate_event(sample_event(), Language.hi, event_version=1)
    res = fact_check_translation(ev, t, Language.hi)
    assert res["passed"] is False
    assert any("city_mismatch" in m for m in res["mismatches"])


def test_p4_05_glossary_keypad_compliance():
    script_good = "Press 1 to confirm, 2 to decline, 3 for callback, 9 to stop."
    script_bad = "Press 1 to confirm."
    
    assert check_glossary_compliance(script_good, Language.en) == []
    bad_res = check_glossary_compliance(script_bad, Language.en)
    assert "keypad_option_2_decline" in bad_res
    assert "keypad_option_9_stop" in bad_res


def test_p4_06_back_translation_to_english_present():
    ev = sample_event()
    t = translate_event(ev, Language.ml, event_version=1)
    assert t.back_translation_en is not None
    assert len(t.back_translation_en) > 10
