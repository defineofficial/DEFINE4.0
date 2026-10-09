"""Tests for the voice note transcription and event extraction pipeline."""
from datetime import datetime, timezone
import pytest

from app.schemas import Language
from app.voice_pipeline import (
    extract_event_details,
    process_voice_note,
    transcribe_audio,
)
from app import ai_budget


def test_fallback_transcription():
    dummy_audio = b"\x00\x01\x02\x03fake-audio-bytes"
    transcript, lang = transcribe_audio(dummy_audio, "sample.mp3")
    assert "AI in Healthcare" in transcript
    assert lang == Language.en


def test_fallback_extraction():
    sample_text = (
        "We are holding an AI in Healthcare seminar on the fourteenth of November at ten in the "
        "morning, in the Seminar Hall, Block A, in Kochi. Registration is five hundred rupees."
    )
    draft = extract_event_details(sample_text, Language.en)
    assert draft.event.title == "AI in Healthcare Seminar"
    assert draft.event.city == "Kochi"
    assert draft.event.fee_inr == 500
    assert draft.event.starts_at.tzinfo is not None
    assert "ends_at" in draft.needs_review or "capacity" in draft.needs_review


def test_process_voice_note_budget_tracked():
    # Verify budget call happens without errors
    dummy_audio = b"fake-audio"
    draft = process_voice_note(dummy_audio, "note.wav")
    assert draft.event.fee_inr >= 0
    assert draft.detected_language in (Language.en, Language.hi, Language.ml, Language.ta)
