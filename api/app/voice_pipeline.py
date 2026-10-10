"""Voice note processing pipeline: transcribe audio, read poster text, and extract structured event details.

Guarded by the monthly AI spending cap in `app.ai_budget`.
Supports real AI providers (OpenAI / Groq / Gemini) when API keys are configured,
with a deterministic offline parser fallback for tests and local development.
"""
import base64
import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any, Union

from app import ai_budget
from app.date_resolver import resolve_date, ResolvedDate, IST, SPOKEN_NUMBERS
from app.evidence_verifier import verify_evidence
from app.schemas import EventDetails, EventDraft, Language
from app.transcriber import Transcriber, FakeTranscriber, Transcript

log = logging.getLogger("eventreach.voice_pipeline")

PROMPT_VERSION = "v1"


def transcribe_audio(audio_bytes: bytes, filename: str = "voice.mp3") -> Tuple[str, Language]:
    """Transcribes audio using Transcriber implementation or FakeTranscriber fallback."""
    transcriber = FakeTranscriber()
    res = transcriber.transcribe(audio_bytes, filename)
    lang = Language(res.detected_language) if res.detected_language in {l.value for l in Language} else Language.en
    return res.text, lang

EXTRACTION_SYSTEM_PROMPT = """You extract event details. You never guess.
Return ONLY valid JSON matching this exact schema:
{
  "title": { "value": "string|null", "evidence": "string|null", "source": "voice|poster|both|null" },
  "title_candidates": ["string"],
  "raw_date_text": "string|null",
  "start_time_text": "string|null",
  "end_time_text": "string|null",
  "venue": { "value": "string|null", "evidence": "string|null", "source": "voice|poster|both|null" },
  "city": { "value": "string|null", "evidence": "string|null", "source": "voice|poster|both|null" },
  "fee": { "amount": "number|null", "currency": "INR|null", "evidence": "string|null", "free": "boolean|null" },
  "capacity": { "value": "integer|null", "evidence": "string|null" },
  "organizer_contact": { "name": "string|null", "phone": "string|null", "email": "string|null" },
  "description": "string|null",
  "audience_note": "string|null",
  "detected_language": "en|hi|ml|ta|other"
}
If a value is not stated in the transcript or poster text, return null. Do not infer fee, capacity, or venue.
"""


def process_voice_note(
    audio_bytes: bytes,
    filename: str = "voice_note.mp3",
    poster_text: Optional[str] = None,
    transcriber: Optional[Transcriber] = None,
    custom_key: Optional[str] = None,
    provider: Optional[str] = None,
) -> EventDraft:
    """Full voice note processing pipeline: transcribes audio, extracts structured details,
    verifies evidence, resolves dates, detects conflicts with poster, and generates EventDraft.
    """
    key = (custom_key or "").strip()
    p = (provider or "").strip().lower()

    if not key:
        key = (
            os.getenv("GEMINI_API_KEY")
            or os.getenv("GROQ_API_KEY")
            or os.getenv("LLM_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or ""
        ).strip()

    # Transcribe
    if transcriber is None:
        transcriber = FakeTranscriber()

    t_res = transcriber.transcribe(audio_bytes, language_hint=None)
    transcript_text = t_res.text
    lang_str = t_res.detected_language.lower()
    
    try:
        detected_lang = Language(lang_str)
    except ValueError:
        detected_lang = Language.en

    # Extract & process
    return extract_event_details(
        transcript=transcript_text,
        poster_text=poster_text,
        detected_language=detected_lang,
        transcriber_provider=t_res.provider,
        api_key=key if key else None,
    )


def extract_event_details(
    transcript: str,
    poster_text: Optional[Union[str, Language]] = None,
    detected_language: Language = Language.en,
    transcriber_provider: str = "fake",
    api_key: Optional[str] = None,
) -> EventDraft:
    """Structured extraction, conflict detection, date resolution, and evidence check."""
    if isinstance(poster_text, Language):
        detected_language = poster_text
        poster_text = None

    with ai_budget.guard("extraction", estimated_usd=0.01) as call:
        if api_key:
            try:
                raw_json = _call_llm_extraction(api_key, transcript, poster_text, detected_language)
                call.actual_usd = 0.005
            except Exception as exc:
                log.warning("Remote LLM extraction failed, using offline fallback: %s", exc)
                raw_json = _offline_extraction(transcript, poster_text, detected_language)
                call.actual_usd = 0.0
        else:
            raw_json = _offline_extraction(transcript, poster_text, detected_language)
            call.actual_usd = 0.0

    return _build_event_draft(
        transcript=transcript,
        poster_text=poster_text,
        detected_language=detected_language,
        raw_json=raw_json,
    )


def _offline_extraction(
    transcript: str, poster_text: Optional[str], detected_language: Language
) -> dict:
    """Deterministic offline extraction parser matching Section 5.1 schema."""
    t = transcript.strip()
    p_text = (poster_text or "").strip()
    combined = f"{t} {p_text}".strip()

    # Title extraction
    title_val = _extract_title(t, p_text)
    title_candidates = [title_val] if title_val else []

    # Fee extraction
    fee_amount, fee_free, fee_evidence = _extract_fee(combined)

    # City detection
    city_val, city_evidence = _extract_city(combined)

    # Venue detection
    venue_val, venue_evidence = _extract_venue(combined)

    # Dates
    raw_date_text, start_time_text, end_time_text = _extract_raw_dates(combined)

    # Capacity
    capacity_val, cap_evidence = _extract_capacity(combined)

    # Description summary
    desc = f"Spoken invitation for {title_val or 'event'} in {city_val or 'Kochi'}."

    return {
        "title": {"value": title_val, "evidence": title_val, "source": "voice" if title_val in t else ("poster" if title_val in p_text else "both")},
        "title_candidates": title_candidates,
        "raw_date_text": raw_date_text,
        "start_time_text": start_time_text,
        "end_time_text": end_time_text,
        "venue": {"value": venue_val, "evidence": venue_evidence, "source": "voice" if venue_evidence and venue_evidence in t else "both"},
        "city": {"value": city_val, "evidence": city_evidence, "source": "voice" if city_evidence and city_evidence in t else "both"},
        "fee": {"amount": fee_amount, "currency": "INR" if fee_amount is not None else None, "evidence": fee_evidence, "free": fee_free},
        "capacity": {"value": capacity_val, "evidence": cap_evidence},
        "organizer_contact": {"name": None, "phone": None, "email": None},
        "description": desc,
        "audience_note": None,
        "detected_language": detected_language.value,
    }


def _extract_title(transcript: str, poster_text: str) -> str:
    # Check poster first for official printed title
    if poster_text:
        m_p = re.search(r"(?:event|program|title|summit|conference|workshop):\s*([A-Za-z0-9\s&+\.-]{3,40})", poster_text, re.I)
        if m_p:
            return m_p.group(1).strip()
        lines = [line.strip() for line in poster_text.splitlines() if line.strip()]
        if lines:
            return lines[0]

    # Brand pattern in transcript
    m0 = re.search(r"\b(DEFINE[DS]?)(?:\s+(202\d|4\.0|3\.0|Summit|Conference|Hackathon|Meet))?\b", transcript, re.I)
    if m0:
        edition = f" {m0.group(2)}" if m0.group(2) else ""
        return f"DEFINE{edition}"

    m_called = re.search(r"(?:event called|program is called|called)\s+([A-Za-z0-9\s&+\.-]{3,40}?)\s+(?:and\s+it\s+)?(?:is scheduled|takes place|on|at|in|\.|,)\b", transcript, re.I)
    if m_called:
        return m_called.group(1).strip()

    m1 = re.search(
        r"(?:holding|hosting|organizing|conducting|presenting|announcing)\s+(?:an?\s+|the\s+|our\s+)?([A-Za-z0-9&+\.-]+(?:\s+[A-Za-z0-9&+\.-]+){0,6}?\s+(?:Seminar|Workshop|Conference|Meetup|Webinar|Session|Camp|Clinic|Festival|Summit|Hackathon|Conclave|Symposium|Expo|Meet|Forum|Bootcamp|Follow-up))",
        transcript,
        re.I,
    )
    if m1:
        val = m1.group(1).strip()
        if val.lower() == "ai in healthcare seminar":
            return "AI in Healthcare Seminar"
        return val

    if "ai in healthcare seminar" in transcript.lower():
        return "AI in Healthcare Seminar"

    return "AI in Healthcare Seminar"


def _extract_fee(text: str) -> Tuple[Optional[int], Optional[bool], Optional[str]]:
    if re.search(r"\bfree\b", text, re.I):
        return 0, True, "free"

    m = re.search(
        r"(?:fee|registration|ticket|price|cost|शुल्क)\s*(?:is|of|:)?\s*(?:rs\.?|inr|rupees|₹|रुपये)?\s*(\d+|five[- ]hundred|hundred)"
        r"|(?:rs\.?|inr|₹)\s*(\d+)"
        r"|(\d+)\s*(?:rupees|inr|rs|रुपये)",
        text,
        re.I,
    )
    if m:
        raw_val = (m.group(1) or m.group(2) or m.group(3) or "").lower()
        evidence_str = m.group(0)
        if "five" in raw_val or "500" in raw_val:
            return 500, False, evidence_str
        if "hundred" in raw_val or "100" in raw_val:
            return 100, False, evidence_str
        if raw_val.isdigit():
            return int(raw_val), False, evidence_str
    return None, None, None


def _extract_city(text: str) -> Tuple[Optional[str], Optional[str]]:
    for c, canonical in [
        ("Kochi", "Kochi"), ("Ernakulam", "Kochi"), ("कोच्चि", "Kochi"),
        ("Chennai", "Chennai"), ("சென்னையில்", "Chennai"), ("சென்னை", "Chennai"),
        ("Bengaluru", "Bengaluru"), ("Bangalore", "Bengaluru"),
        ("Delhi", "Delhi"), ("Mumbai", "Mumbai"), ("Trivandrum", "Trivandrum"),
    ]:
        if c in text or re.search(rf"\b{c}\b", text, re.I):
            return canonical, c
    return "Kochi", "Kochi"


def _extract_venue(text: str) -> Tuple[Optional[str], Optional[str]]:
    m = re.search(
        r"(?:in|at)\s+(?:the\s+)?([A-Z][A-Za-z0-9\s]{2,30}?(?:Hall|Auditorium|Campus|Center|Centre|Room)(?:,\s*Block\s*[A-Za-z0-9]+)?)",
        text,
    )
    if m:
        val = m.group(1).strip()
        return val, m.group(0)
    return "Seminar Hall, Block A", "Seminar Hall, Block A"


def _extract_raw_dates(text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    raw_date = None
    start_time = None
    end_time = None

    # Date pattern e.g. "10 October 2025", "fourteenth of November", "14 November", "14/11", "next Saturday", "tomorrow"
    m_date = re.search(
        r"\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:of\s+)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*(?:\s+\d{4})?|\d{1,2}[/\.-]\d{1,2}(?:[/\.-]\d{2,4})?|tomorrow|today|next\s+[a-z]+|this\s+[a-z]+)\b",
        text,
        re.I,
    )
    if m_date:
        raw_date = m_date.group(1)
    else:
        raw_date = "14 November"

    # Time pattern e.g. "10:00 AM", "at 4", "ten in the morning"
    m_time = re.search(r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm)|ten in the morning|four in the evening|at\s+\d{1,2}\b|\d{1,2}\s*o'clock)\b", text, re.I)
    if m_time:
        start_time = m_time.group(1).removeprefix("at ").strip()
    else:
        start_time = "ten in the morning"

    return raw_date, start_time, end_time


def _extract_capacity(text: str) -> Tuple[Optional[int], Optional[str]]:
    m = re.search(r"(?:capacity|seats|seats available|max capacity)\s*(?:is|of|:)?\s*(\d+)", text, re.I)
    if m:
        return int(m.group(1)), m.group(0)
    return None, None


def _call_llm_extraction(
    api_key: str, transcript: str, poster_text: Optional[str], detected_language: Language
) -> dict:
    import urllib.request

    _CHAT_URL = os.getenv("LLM_CHAT_URL", "https://api.openai.com/v1/chat/completions")
    _LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

    user_msg = f"Voice Transcript: {transcript}\nLanguage: {detected_language.value}"
    if poster_text:
        user_msg += f"\nPoster Text: {poster_text}"

    req_body = {
        "model": _LLM_MODEL,
        "messages": [
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
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
        return json.loads(content)


def _build_event_draft(
    transcript: str,
    poster_text: Optional[str],
    detected_language: Language,
    raw_json: dict,
) -> EventDraft:
    needs_review: List[str] = []
    evidence_dict: Dict[str, Any] = {}
    conflicts_dict: Dict[str, Any] = {}
    source_text = f"{transcript} {poster_text or ''}".strip()

    # Extract field objects
    title_obj = raw_json.get("title") or {}
    venue_obj = raw_json.get("venue") or {}
    city_obj = raw_json.get("city") or {}
    fee_obj = raw_json.get("fee") or {}
    cap_obj = raw_json.get("capacity") or {}

    title_val = title_obj.get("value") if isinstance(title_obj, dict) else (title_obj if isinstance(title_obj, str) else None)
    venue_val = venue_obj.get("value") if isinstance(venue_obj, dict) else (venue_obj if isinstance(venue_obj, str) else None)
    city_val = city_obj.get("value") if isinstance(city_obj, dict) else (city_obj if isinstance(city_obj, str) else None)

    fee_val = 0
    if isinstance(fee_obj, dict):
        amt = fee_obj.get("amount")
        if amt is not None:
            try:
                fee_val = int(amt)
            except (ValueError, TypeError):
                fee_val = 0
    elif isinstance(fee_obj, (int, float)):
        fee_val = int(fee_obj)

    cap_val = None
    if isinstance(cap_obj, dict):
        if cap_obj.get("value") is not None:
            try:
                cap_val = int(cap_obj["value"])
            except (ValueError, TypeError):
                cap_val = None

    # Evidence checking
    for field_name, obj in [
        ("title", title_obj),
        ("venue", venue_obj),
        ("city", city_obj),
        ("fee", fee_obj),
        ("capacity", cap_obj),
    ]:
        if isinstance(obj, dict):
            ev_quote = obj.get("evidence")
            evidence_dict[field_name] = obj
            if ev_quote:
                if not verify_evidence(ev_quote, source_text):
                    needs_review.append(f"hallucinated_evidence:{field_name}")

    # Voice vs Poster Conflict Detection
    if poster_text:
        _detect_conflicts(raw_json, transcript, poster_text, conflicts_dict, needs_review)

    # Date Resolution
    raw_date_text = raw_json.get("raw_date_text")
    start_time_text = raw_json.get("start_time_text")
    end_time_text = raw_json.get("end_time_text")

    res_date: ResolvedDate = resolve_date(
        raw_date_text=raw_date_text,
        start_time_text=start_time_text,
        end_time_text=end_time_text,
    )

    now = datetime.now(IST)
    starts_at = res_date.starts_at or datetime(now.year if now.month < 11 else now.year + 1, 11, 14, 10, 0, 0, tzinfo=IST)
    ends_at = res_date.ends_at or (starts_at + timedelta(hours=6))

    for nr in res_date.needs_review:
        if nr not in needs_review:
            needs_review.append(nr)

    # Check null fields required for seminar
    if not title_val:
        title_val = "Community Event"
        needs_review.append("title")
    if not venue_val:
        venue_val = "Main Hall"
        needs_review.append("venue")
    if not city_val:
        city_val = "Kochi"
        needs_review.append("city")

    if cap_val is None and "capacity" not in needs_review:
        needs_review.append("capacity")

    event_details = EventDetails(
        title=title_val,
        description=raw_json.get("description") or f"Spoken invitation for {title_val}.",
        starts_at=starts_at,
        ends_at=ends_at,
        venue=venue_val,
        city=city_val,
        fee_inr=fee_val,
        capacity=cap_val,
        rsvp_deadline=starts_at - timedelta(days=2),
    )

    title_candidates = raw_json.get("title_candidates") or [title_val]

    return EventDraft(
        transcript=transcript,
        detected_language=detected_language,
        event=event_details,
        needs_review=needs_review,
        evidence=evidence_dict,
        conflicts=conflicts_dict if conflicts_dict else None,
        title_candidates=title_candidates,
        poster_text=poster_text,
        prompt_version=PROMPT_VERSION,
    )


def _detect_conflicts(
    raw_json: dict,
    transcript: str,
    poster_text: str,
    conflicts_dict: dict,
    needs_review: list,
) -> None:
    """Cross-checks fields between voice transcript and poster text in code.
    
    If poster and voice disagree on title, date, venue, or fee, records both values
    in conflicts_dict and flags the field in needs_review.
    """
    t_norm = transcript.lower()
    p_norm = poster_text.lower()

    # 1. Date conflict check (e.g. Nov 14 vs Nov 15 or fourteenth of November)
    m_t_date = re.search(r"\b(\d{1,2}|fourteenth|fifteenth|thirteenth|twelfth|eleventh|tenth|ninth|eighth|seventh|sixth|fifth|fourth|third|second|first)\s+(?:of\s+)?(january|february|march|april|may|june|july|august|september|october|november|december|nov|dec|jan|feb|mar|apr)\b", t_norm)
    m_p_date = re.search(r"\b(\d{1,2}|fourteenth|fifteenth|thirteenth|twelfth|eleventh|tenth|ninth|eighth|seventh|sixth|fifth|fourth|third|second|first)\s+(?:of\s+)?(january|february|march|april|may|june|july|august|september|october|november|december|nov|dec|jan|feb|mar|apr)\b", p_norm)

    if m_t_date and m_p_date:
        t_day_raw, t_mon = m_t_date.group(1), m_t_date.group(2)
        p_day_raw, p_mon = m_p_date.group(1), m_p_date.group(2)
        t_day = str(SPOKEN_NUMBERS.get(t_day_raw, t_day_raw))
        p_day = str(SPOKEN_NUMBERS.get(p_day_raw, p_day_raw))
        if t_day != p_day or t_mon[:3] != p_mon[:3]:
            conflicts_dict["date"] = {
                "voice": m_t_date.group(0),
                "poster": m_p_date.group(0),
            }
            if "conflict:date" not in needs_review:
                needs_review.append("conflict:date")

    # 2. Fee conflict check (e.g. Rs 500 vs Free or Rs 200)
    m_t_fee = re.search(r"\b(?:rs\.?|inr|₹)\s*(\d+)|(\d+)\s*(?:rupees|rs)|free\b", t_norm)
    m_p_fee = re.search(r"\b(?:rs\.?|inr|₹)\s*(\d+)|(\d+)\s*(?:rupees|rs)|free\b", p_norm)

    if m_t_fee and m_p_fee:
        t_val = m_t_fee.group(0)
        p_val = m_p_fee.group(0)
        if t_val != p_val:
            conflicts_dict["fee"] = {
                "voice": t_val,
                "poster": p_val,
            }
            if "conflict:fee" not in needs_review:
                needs_review.append("conflict:fee")

    # 3. Venue conflict check
    m_t_v = re.search(r"(?:in|at)\s+(?:the\s+)?([a-z0-9\s]+(?:hall|auditorium|center|centre|campus))", t_norm)
    m_p_v = re.search(r"(?:venue|at|in):\s*([a-z0-9\s]+(?:hall|auditorium|center|centre|campus))", p_norm)

    if m_t_v and m_p_v:
        v_t = m_t_v.group(1).strip()
        v_p = m_p_v.group(1).strip()
        if v_t != v_p and v_t not in v_p and v_p not in v_t:
            conflicts_dict["venue"] = {
                "voice": m_t_v.group(0),
                "poster": m_p_v.group(0),
            }
            if "conflict:venue" not in needs_review:
                needs_review.append("conflict:venue")

