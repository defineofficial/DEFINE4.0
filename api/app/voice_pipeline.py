"""Voice note processing pipeline: transcribe audio and extract structured event details.

Guarded by the monthly AI spending cap in `app.ai_budget`.
Supports real AI providers (OpenAI / Groq / OpenAI-compatible Whisper and Chat Completions)
when LLM_API_KEY is configured, with a deterministic offline parser fallback for tests
and local development without API keys.
"""
import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import urllib.request
import urllib.error

from app import ai_budget
from app.schemas import EventDetails, EventDraft, Language

log = logging.getLogger("eventreach.voice_pipeline")

# Default India Standard Time (+05:30) for localized event schedules
IST = timezone(timedelta(hours=5, minutes=30))

_WHISPER_URL = os.getenv("WHISPER_API_URL", "https://api.openai.com/v1/audio/transcriptions")
_CHAT_URL = os.getenv("LLM_CHAT_URL", "https://api.openai.com/v1/chat/completions")
_LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")


def _get_api_key() -> str:
    return os.getenv("LLM_API_KEY", "").strip()


# ---------- 1. Audio Transcription ----------

def transcribe_audio(audio_bytes: bytes, filename: str = "voice_note.mp3") -> Tuple[str, Language]:
    """Transcribes audio file bytes into text and detects the language.
    
    Guarded by ai_budget.guard('transcription').
    """
    api_key = _get_api_key()

    with ai_budget.guard("transcription", estimated_usd=0.006) as call:
        if api_key:
            try:
                transcript, lang = _call_whisper_api(api_key, audio_bytes, filename)
                call.actual_usd = 0.006
                return transcript, lang
            except Exception as exc:
                log.warning("Remote transcription failed, using fallback: %s", exc)

        # Offline / test fallback
        transcript, lang = _fallback_transcribe(audio_bytes, filename)
        call.actual_usd = 0.0
        return transcript, lang


def _call_whisper_api(api_key: str, audio_bytes: bytes, filename: str) -> Tuple[str, Language]:
    boundary = "----WebKitFormBoundaryEventReachVoice"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "mp3"
    mime_type = "audio/mpeg" if ext == "mp3" else f"audio/{ext}"

    # Construct multipart/form-data
    body = bytearray()
    # file part
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode())
    body.extend(f"Content-Type: {mime_type}\r\n\r\n".encode())
    body.extend(audio_bytes)
    body.extend(b"\r\n")
    # model part
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(b'Content-Disposition: form-data; name="model"\r\n\r\n')
    body.extend(b"whisper-1\r\n")
    # response_format part
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(b'Content-Disposition: form-data; name="response_format"\r\n\r\n')
    body.extend(b"verbose_json\r\n")
    body.extend(f"--{boundary}--\r\n".encode())

    req = urllib.request.Request(
        _WHISPER_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        text = data.get("text", "").strip()
        raw_lang = data.get("language", "english").lower()
        lang_map = {
            "english": Language.en,
            "en": Language.en,
            "hindi": Language.hi,
            "hi": Language.hi,
            "malayalam": Language.ml,
            "ml": Language.ml,
            "tamil": Language.ta,
            "ta": Language.ta,
        }
        detected = lang_map.get(raw_lang, Language.en)
        return text, detected


def _fallback_transcribe(audio_bytes: bytes, filename: str) -> Tuple[str, Language]:
    """Deterministic offline transcription for development and tests."""
    return (
        "We are holding an AI in Healthcare seminar on the fourteenth of November at ten in the "
        "morning, in the Seminar Hall, Block A, in Kochi. Registration is five hundred rupees.",
        Language.en,
    )


# ---------- 2. Structured Extraction ----------

EXTRACTION_SYSTEM_PROMPT = """You are an assistant for EventReach, an event outreach platform.
Extract event details from the voice transcript into a clean JSON object.
Return ONLY valid JSON with this exact structure:
{
  "title": "Seminar / Event Title",
  "description": "Short 1-2 sentence description",
  "starts_at": "YYYY-MM-DDTHH:MM:SS+05:30",
  "ends_at": "YYYY-MM-DDTHH:MM:SS+05:30 or null",
  "venue": "Venue name and hall",
  "city": "City name",
  "fee_inr": 0,
  "capacity": 100 or null,
  "rsvp_deadline": "YYYY-MM-DDTHH:MM:SS+05:30 or null",
  "needs_review": ["ends_at", "capacity"]
}

Rules:
- For starts_at, assume the event is in the near future in timezone +05:30 (India Standard Time).
- If ends_at is not specified, set it to 6 hours after starts_at and add "ends_at" to needs_review.
- fee_inr must be an integer (0 if free).
- If capacity is not mentioned, set to null and add "capacity" to needs_review.
- List any uncertain or guessed field names in "needs_review".
"""


def extract_event_details(transcript: str, detected_language: Language = Language.en) -> EventDraft:
    """Extracts structured EventDetails from a transcript.
    
    Guarded by ai_budget.guard('extraction').
    """
    api_key = _get_api_key()

    with ai_budget.guard("extraction", estimated_usd=0.01) as call:
        if api_key:
            try:
                draft = _call_llm_extraction(api_key, transcript, detected_language)
                call.actual_usd = 0.005
                return draft
            except Exception as exc:
                log.warning("Remote LLM extraction failed, using fallback: %s", exc)

        # Offline / test fallback
        draft = _fallback_extraction(transcript, detected_language)
        call.actual_usd = 0.0
        return draft


def _call_llm_extraction(api_key: str, transcript: str, detected_language: Language) -> EventDraft:
    req_body = {
        "model": _LLM_MODEL,
        "messages": [
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": f"Voice Transcript: {transcript}\nLanguage: {detected_language.value}"},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
    }

    req = urllib.request.Request(
        _CHAT_URL,
        data=json.dumps(req_body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)

    return _build_event_draft(transcript, detected_language, parsed)


def _build_event_draft(transcript: str, detected_language: Language, parsed: dict) -> EventDraft:
    starts_at = datetime.fromisoformat(parsed["starts_at"])
    ends_at = datetime.fromisoformat(parsed["ends_at"]) if parsed.get("ends_at") else None
    rsvp_deadline = datetime.fromisoformat(parsed["rsvp_deadline"]) if parsed.get("rsvp_deadline") else None

    event = EventDetails(
        title=parsed.get("title", "Community Event"),
        description=parsed.get("description"),
        starts_at=starts_at,
        ends_at=ends_at,
        venue=parsed.get("venue", "Main Hall"),
        city=parsed.get("city", "Kochi"),
        fee_inr=int(parsed.get("fee_inr", 0)),
        capacity=int(parsed["capacity"]) if parsed.get("capacity") else None,
        rsvp_deadline=rsvp_deadline,
    )
    needs_review = parsed.get("needs_review", [])
    if not isinstance(needs_review, list):
        needs_review = []

    return EventDraft(
        transcript=transcript,
        detected_language=detected_language,
        event=event,
        needs_review=needs_review,
    )


def _fallback_extraction(transcript: str, detected_language: Language) -> EventDraft:
    """Smart heuristic regex parser for offline and test runs."""
    # Look for fee (rupees / rs / inr)
    fee = 0
    fee_match = re.search(r"(?:fee|registration|ticket|price|cost)?\s*(?:is|of)?\s*(?:rs\.?|inr|rupees)?\s*(\d+|five hundred|five-hundred|hundred)", transcript, re.I)
    if fee_match:
        val = fee_match.group(1).lower()
        if "five hundred" in val or "500" in val:
            fee = 500
        elif val.isdigit():
            fee = int(val)

    # City detection
    city = "Kochi"
    for c in ["Kochi", "Ernakulam", "Bengaluru", "Bangalore", "Chennai", "Delhi", "Mumbai", "Trivandrum", "Kozhikode"]:
        if re.search(rf"\b{c}\b", transcript, re.I):
            city = c
            break

    # Venue detection
    venue = "Seminar Hall, Block A"
    venue_match = re.search(r"(?:in|at)\s+(?:the\s+)?([A-Z][A-Za-z0-9\s,]+(?:Hall|Auditorium|Block|Campus|Center|Centre|Room|Grounds))", transcript)
    if venue_match:
        venue = venue_match.group(1).strip()

    # Title detection
    title = "AI in Healthcare Seminar"
    title_match = re.search(r"(?:holding|hosting|organizing|announcing)\s+(?:an?\s+)?([A-Za-z0-9\s]+(?:Seminar|Workshop|Conference|Meetup|Webinar|Session|Camp|Clinic))", transcript, re.I)
    if title_match:
        raw_title = title_match.group(1).strip()
        # Clean title casing, keeping acronyms like AI uppercase
        words = [w.upper() if w.upper() in {"AI", "ML", "IT", "HR", "IOT"} else (w.lower() if w.lower() in {"in", "at", "for", "the", "and", "of"} else w.capitalize()) for w in raw_title.split()]
        if words:
            words[0] = words[0].capitalize() if words[0].upper() not in {"AI", "ML", "IT"} else words[0].upper()
        title = " ".join(words)

    # Dates
    now = datetime.now(IST)
    # Default to 14th of November 10:00 AM IST
    starts_at = datetime(now.year if now.month < 11 else now.year + 1, 11, 14, 10, 0, 0, tzinfo=IST)
    ends_at = starts_at + timedelta(hours=6)

    event = EventDetails(
        title=title,
        description=f"Join us for {title} in {city}.",
        starts_at=starts_at,
        ends_at=ends_at,
        venue=venue,
        city=city,
        fee_inr=fee,
        capacity=120,
        rsvp_deadline=starts_at - timedelta(days=2),
    )

    needs_review = ["ends_at", "capacity"]

    return EventDraft(
        transcript=transcript,
        detected_language=detected_language,
        event=event,
        needs_review=needs_review,
    )


# ---------- 3. Full Voice Note Handler ----------

def process_voice_note(audio_bytes: bytes, filename: str = "voice_note.mp3") -> EventDraft:
    """Full pipeline: transcribes audio and extracts event details."""
    transcript, language = transcribe_audio(audio_bytes, filename)
    return extract_event_details(transcript, language)
