"""Unit tests for the multilingual translation and back-translation engine."""
from datetime import datetime, timezone
import pytest

from app.schemas import EventDetails, Language
from app.translation_engine import generate_translations, translate_event, _CACHE


@pytest.fixture
def sample_event():
    return EventDetails(
        title="AI in Healthcare Seminar",
        starts_at=datetime(2026, 11, 14, 10, 0, tzinfo=timezone.utc),
        venue="Seminar Hall, Block A",
        city="Kochi",
        fee_inr=500,
    )


def test_translate_english(sample_event):
    res = translate_event(sample_event, Language.en)
    assert res.language == Language.en
    assert "AI in Healthcare Seminar" in res.call_script
    assert res.approved is True
    assert res.back_translation_en == res.call_script


def test_translate_hindi_and_back_translation(sample_event):
    res = translate_event(sample_event, Language.hi)
    assert res.language == Language.hi
    assert "{name}" in res.call_script
    assert "AI in Healthcare Seminar" in res.call_script
    assert res.back_translation_en is not None
    assert "invited" in res.back_translation_en.lower()


def test_translate_malayalam_and_tamil(sample_event):
    ml_res = translate_event(sample_event, Language.ml)
    assert ml_res.language == Language.ml
    assert "നമസ്കാരം" in ml_res.call_script

    ta_res = translate_event(sample_event, Language.ta)
    assert ta_res.language == Language.ta
    assert "வணக்கம்" in ta_res.call_script


def test_translation_caching(sample_event):
    _CACHE.clear()
    t1 = translate_event(sample_event, Language.hi)
    # Second call should be served from cache
    t2 = translate_event(sample_event, Language.hi)
    assert t1 is t2


def test_generate_translations_batch(sample_event):
    langs = [Language.en, Language.hi, Language.ml, Language.ta]
    translations = generate_translations("cmp_001", sample_event, langs)
    assert len(translations) == 4
    assert {t.language for t in translations} == set(langs)
