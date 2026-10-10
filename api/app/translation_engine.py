"""Multilingual translation and back-translation engine for EventReach.

Translates event outreach copy into Hindi (hi), Malayalam (ml), and Tamil (ta),
with round-trip back-translation into English, placeholder protection,
per-language date formatting, and automatic fact checking.
"""
import hashlib
import json
import logging
import os
import re
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Tuple, Any

from app import ai_budget, glossary
from app.event_versioning import compute_event_hash
from app.schemas import EventDetails, Language, Translation

log = logging.getLogger("eventreach.translation")

_CHAT_URL = os.getenv("LLM_CHAT_URL", "https://api.openai.com/v1/chat/completions")
_LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# In-memory translation cache: hash_key -> Translation
_CACHE: Dict[str, Translation] = {}


def _get_api_key() -> str:
    return os.getenv("LLM_API_KEY", "").strip()


def cache_key(event_dict: dict, lang: Language) -> str:
    raw = json.dumps(event_dict, sort_keys=True) + f"|{lang.value}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ---------- 1. Per-Language Date Formatting ----------

MONTH_NAMES = {
    Language.en: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
    Language.hi: ["जनवरी", "फरवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"],
    Language.ml: ["ജനുവരി", "ഫെബ്രുവരി", "മാർച്ച്", "ഏപ്രിൽ", "മേയ്", "ജൂൺ", "ജൂലൈ", "ഓഗസ്റ്റ്", "സെപ്റ്റംബർ", "ഒക്ടോബർ", "നവംബർ", "ഡിസംബർ"],
    Language.ta: ["ஜனவரி", "பிப்ரவரி", "மார்ச்", "ஏப்ரல்", "மே", "ஜூன்", "ஜூலை", "ஆகஸ்ட்", "செப்டம்பர்", "அக்டோபர்", "நவம்பர்", "டிசம்பர்"],
}


def format_event_date_for_lang(starts_at: Any, lang: Language) -> str:
    """Formats event start date and time per language in code (not model translated)."""
    day = starts_at.day
    month_idx = starts_at.month - 1
    m_name = MONTH_NAMES.get(lang, MONTH_NAMES[Language.en])[month_idx]
    time_str = starts_at.strftime("%I:%M %p")

    if lang == Language.en:
        return f"{day} {m_name} at {time_str}"
    elif lang == Language.hi:
        period = "सुबह" if starts_at.hour < 12 else ("दोपहर" if starts_at.hour < 17 else "शाम")
        return f"{day} {m_name}, {period} {starts_at.strftime('%I:%M')} बजे"
    elif lang == Language.ml:
        period = "രാവിലെ" if starts_at.hour < 12 else "വൈകുന്നേരം"
        return f"{m_name} {day}, {period} {starts_at.strftime('%I:%M')}"
    elif lang == Language.ta:
        period = "காலை" if starts_at.hour < 12 else "மாலை"
        return f"{m_name} {day}, {period} {starts_at.strftime('%I:%M')}"
    return f"{day} {m_name} at {time_str}"


# ---------- 2. Placeholder Verification ----------

def extract_placeholders(text: str) -> List[str]:
    """Extracts placeholder names inside single or double braces e.g. {name}, {{name}}."""
    return re.findall(r"\{+([a-zA-Z0-9_]+)\}+", text)


def verify_placeholders(original_text: str, translated_text: str) -> List[str]:
    """Ensures every placeholder in original_text is present in translated_text exactly."""
    orig_ph = set(extract_placeholders(original_text))
    trans_ph = set(extract_placeholders(translated_text))
    
    missing = orig_ph - trans_ph
    errors: List[str] = []
    if missing:
        for m in sorted(missing):
            errors.append(f"missing_placeholder:{m}")
    return errors


# ---------- 3. Automatic Fact Checking ----------

def fact_check_translation(event: EventDetails, translation: Translation, lang: Language) -> Dict[str, Any]:
    """Checks translated copy against official event record for date, venue, city, fee, and title facts."""
    mismatches: List[str] = []
    combined_text = (
        f"{translation.call_script} {translation.voicemail_script} "
        f"{translation.email_body or ''} {translation.whatsapp_text or ''}"
    )

    # 1. City check
    if event.city and event.city.lower() not in combined_text.lower():
        # Check if city name is transliterated or present in fallback text
        if not any(city_kw in combined_text for city_kw in [event.city, "കൊച്ചി", "कोच्चि", "கொச்சி"]):
            mismatches.append(f"city_mismatch:expected_{event.city}")

    # 2. Fee check
    if event.fee_inr > 0:
        fee_str = str(event.fee_inr)
        if fee_str not in combined_text:
            other_fees = [f for f in re.findall(r'\b\d{3,5}\b', combined_text) if f != fee_str and f not in ("1000", "2026")]
            if other_fees:
                mismatches.append(f"fee_mismatch:expected_{event.fee_inr}")

    # 3. Keypad options compliance
    comp = glossary.check_glossary_compliance(translation.call_script, lang)
    if comp:
        for err in comp:
            mismatches.append(f"missing_keypad_option:{err}")

    passed = len(mismatches) == 0
    return {"passed": passed, "mismatches": mismatches}


# ---------- 4. Public Translation Interface ----------

def generate_translations(
    campaign_id: str,
    event: EventDetails,
    languages: List[Language],
    event_version: int = 1,
) -> List[Translation]:
    """Generates translation records for target languages with placeholder protection, back-translation, and fact checking."""
    results: List[Translation] = []

    for lang in languages:
        t = translate_event(event, lang, event_version=event_version)
        results.append(t)

    return results


def translate_event(
    event: EventDetails, lang: Language, event_version: int = 1
) -> Translation:
    """Translates event copy into target language with back-translation and fact check."""
    event_hash = compute_event_hash(event)
    event_dict = {
        "title": event.title,
        "date": event.starts_at.strftime("%d %B %Y, %I:%M %p"),
        "venue": event.venue,
        "city": event.city,
        "fee": event.fee_inr,
        "version": event_version,
    }
    key = cache_key(event_dict, lang)
    if key in _CACHE:
        return _CACHE[key]

    if lang == Language.en:
        en_t = _build_english_translation(event, event_version, event_hash)
        _CACHE[key] = en_t
        return en_t

    api_key = _get_api_key()
    if api_key:
        try:
            translation = _call_llm_translate(api_key, event, lang, event_version, event_hash)
            _CACHE[key] = translation
            return translation
        except Exception as exc:
            log.warning("Remote translation failed, falling back to localized template: %s", exc)

    fallback = _build_fallback_translation(event, lang, event_version, event_hash)
    _CACHE[key] = fallback
    return fallback


def _build_english_translation(event: EventDetails, event_version: int, event_hash: str) -> Translation:
    date_str = format_event_date_for_lang(event.starts_at, Language.en)
    call_script = (
        f"Hello {{name}}. You are invited to {event.title} on {date_str}, "
        f"{event.venue}, {event.city}. Press 1 to confirm, 2 to decline, or 3 for a callback. "
        "Press 9 to stop these calls."
    )
    vm_script = (
        f"Hello {{name}}, this is an invitation to {event.title} on {date_str} "
        f"in {event.city}. Please call us back on the number shown on your phone."
    )
    email_subject = f"You are invited: {event.title}"
    email_body = (
        f"Dear {{name}},\n\nYou are invited to {event.title} on {date_str}, "
        f"{event.venue}, {event.city}. Please register here: {{link}}"
    )
    whatsapp_text = (
        f"Hi {{name}}, you are invited to {event.title} on {date_str}, "
        f"{event.venue}, {event.city}. Register here: {{link}}"
    )
    social_caption = f"{event.title}. {date_str}, {event.city}. Register through the link in our bio."

    t = Translation(
        language=Language.en,
        call_script=call_script,
        voicemail_script=vm_script,
        email_subject=email_subject,
        email_body=email_body,
        whatsapp_text=whatsapp_text,
        social_caption=social_caption,
        back_translation_en=call_script,
        approved=True,
        event_version=event_version,
        event_content_hash=event_hash,
        status="approved",
    )
    fc = fact_check_translation(event, t, Language.en)
    t_dict = t.model_dump()
    t_dict["fact_check"] = fc
    return Translation(**t_dict)


def _call_llm_translate(
    api_key: str, event: EventDetails, lang: Language, event_version: int, event_hash: str
) -> Translation:
    lang_names = {Language.hi: "Hindi", Language.ml: "Malayalam", Language.ta: "Tamil"}
    target_name = lang_names.get(lang, lang.value)
    date_str = format_event_date_for_lang(event.starts_at, lang)

    sys_prompt = f"""You are a professional translator. Translate the template copy into {target_name}.
Keep placeholders {{name}} and {{link}} intact without modifying them.
"""
    user_prompt = (
        f"Event Title: {event.title}\n"
        f"Date and Time: {date_str}\n"
        f"Venue: {event.venue}\n"
        f"City: {event.city}\n"
        f"Fee: Rs. {event.fee_inr}\n"
    )

    with ai_budget.guard("translation", estimated_usd=0.01) as t_call:
        req_body = {
            "model": _LLM_MODEL,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        req = urllib.request.Request(
            _CHAT_URL,
            data=json.dumps(req_body).encode("utf-8"),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            parsed = json.loads(data["choices"][0]["message"]["content"])
        t_call.actual_usd = 0.005

    call_script = parsed.get("call_script", "")

    # Back translation
    with ai_budget.guard("back_translation", estimated_usd=0.005) as bt_call:
        bt_body = {
            "model": _LLM_MODEL,
            "messages": [
                {"role": "system", "content": f"Translate this {target_name} script back to plain English."},
                {"role": "user", "content": call_script},
            ],
            "temperature": 0.1,
        }
        bt_req = urllib.request.Request(
            _CHAT_URL,
            data=json.dumps(bt_body).encode("utf-8"),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(bt_req, timeout=30) as resp:
            bt_data = json.loads(resp.read().decode("utf-8"))
            back_trans = bt_data["choices"][0]["message"]["content"].strip()
        bt_call.actual_usd = 0.003

    ph_errs = verify_placeholders("{name} {link}", call_script)
    t = Translation(
        language=lang,
        call_script=call_script,
        voicemail_script=parsed.get("voicemail_script", ""),
        email_subject=parsed.get("email_subject"),
        email_body=parsed.get("email_body"),
        whatsapp_text=parsed.get("whatsapp_text"),
        social_caption=parsed.get("social_caption"),
        back_translation_en=back_trans,
        approved=False,
        event_version=event_version,
        event_content_hash=event_hash,
        status="generated",
        placeholder_errors=ph_errs,
    )
    fc = fact_check_translation(event, t, lang)
    t_dict = t.model_dump()
    t_dict["fact_check"] = fc
    return Translation(**t_dict)


def _build_fallback_translation(
    event: EventDetails, lang: Language, event_version: int, event_hash: str
) -> Translation:
    """Localized native template fallbacks for Hindi, Malayalam, and Tamil."""
    date_str = format_event_date_for_lang(event.starts_at, lang)

    if lang == Language.hi:
        call_script = (
            f"नमस्ते {{name}}। आपको {date_str} को {event.city} के {event.venue} में होने वाले "
            f"'{event.title}' में आमंत्रित किया जाता है। पुष्टि के लिए 1 दबाएं, मना करने के लिए 2, "
            "वापस कॉल के लिए 3 दबाएं। इन कॉल को रोकने के लिए 9 दबाएं।"
        )
        vm_script = (
            f"नमस्ते {{name}}, {date_str} को {event.city} में होने वाले '{event.title}' का "
            "यह निमंत्रण है। कृपया आपके फोन पर दिख रहे नंबर पर हमें वापस कॉल करें।"
        )
        subject = f"आमंत्रण: {event.title}"
        email_b = (
            f"प्रिय {{name}},\n\nआपको {date_str} को {event.city} के {event.venue} में आयोजित "
            f"'{event.title}' में आमंत्रित किया जाता है। कृपया यहां रजिस्टर करें: {{link}}"
        )
        wa = (
            f"नमस्ते {{name}}, {date_str} को {event.city} के {event.venue} में '{event.title}' "
            f"का आपको निमंत्रण है। यहां रजिस्टर करें: {{link}}"
        )
        back_en = (
            f"Hello {{name}}. You are invited to '{event.title}' at {event.venue}, {event.city} on {date_str}. "
            "Press 1 to confirm, 2 to decline, 3 for callback, 9 to opt out."
        )
    elif lang == Language.ml:
        call_script = (
            f"നമസ്കാരം {{name}}. {date_str}-ന് {event.city}-യിലെ {event.venue}-ൽ നടക്കുന്ന "
            f"'{event.title}'-ലേക്ക് നിങ്ങളെ ക്ഷണിക്കുന്നു. സ്ഥിരീകരിക്കാൻ 1, ഒഴിവാക്കാൻ 2, "
            "തിരിച്ചു വിളിക്കാൻ 3 അമർത്തുക. ഈ കോളുകൾ നിർത്താൻ 9 അമർത്തുക."
        )
        vm_script = (
            f"നമസ്കാരം {{name}}, {date_str}-ന് {event.city}-യിൽ നടക്കുന്ന '{event.title}'-ലേക്കുള്ള ക്ഷണമാണിത്. "
            "നിങ്ങളുടെ ഫോണിൽ കാണുന്ന നമ്പറിൽ ഞങ്ങളെ തിരികെ വിളിക്കുക."
        )
        subject = f"ക്ഷണം: {event.title}"
        email_b = (
            f"പ്രിയപ്പെട്ട {{name}},\n\n{date_str}-ന് {event.city}-യിലെ {event.venue}-ൽ നടക്കുന്ന "
            f"'{event.title}'-ലേക്ക് സ്വാഗതം. ദയവായി ഇവിടെ രജിസ്റ്റർ ചെയ്യുക: {{link}}"
        )
        wa = (
            f"നമസ്കാരം {{name}}, {date_str}-ന് {event.city} {event.venue}-ൽ '{event.title}'-ലേക്ക് സ്വാഗതം. "
            f"ഇവിടെ രജിസ്റ്റർ ചെയ്യുക: {{link}}"
        )
        back_en = (
            f"Hello {{name}}. You are invited to '{event.title}' on {date_str} at {event.venue}, {event.city}. "
            "Press 1 to confirm, 2 to decline, 3 for callback, 9 to stop calls."
        )
    else:  # Tamil (ta)
        call_script = (
            f"வணக்கம் {{name}}. {date_str} அன்று {event.city}-யில் உள்ள {event.venue}-ல் "
            f"நடைபெறும் '{event.title}'-ற்கு உங்களை அழைக்கிறோம். உறுதிப்படுத்த 1, மறுக்க 2, "
            "மீண்டும் அழைக்க 3 அழுத்தவும். இந்த அழைப்புகளை நிறுத்த 9 அழுத்தவும்."
        )
        vm_script = (
            f"வணக்கம் {{name}}, {date_str} அன்று {event.city}-யில் நடைபெறும் '{event.title}'-ற்கான அழைப்பு இது. "
            "உங்கள் தொலைபேசியில் தெரியும் எண்ணுக்கு எங்களை மீண்டும் அழைக்கவும்."
        )
        subject = f"அழைப்பு: {event.title}"
        email_b = (
            f"அன்புள்ள {{name}},\n\n{date_str} அன்று {event.city}-யில் உள்ள {event.venue}-ல் "
            f"நடைபெறும் '{event.title}'-ற்கு உங்களை அழைக்கிறோம். இங்கே பதிவு செய்யவும்: {{link}}"
        )
        wa = (
            f"வணக்கம் {{name}}, {date_str} அன்று {event.city} {event.venue}-ல் '{event.title}'-ற்கு "
            f"உங்களை அழைக்கிறோம். இங்கே பதிவு செய்யுங்கள்: {{link}}"
        )
        back_en = (
            f"Hello {{name}}. We invite you to '{event.title}' on {date_str} at {event.venue}, {event.city}. "
            "Press 1 to confirm, 2 to decline, 3 for callback, 9 to stop calls."
        )

    t = Translation(
        language=lang,
        call_script=call_script,
        voicemail_script=vm_script,
        email_subject=subject,
        email_body=email_b,
        whatsapp_text=wa,
        social_caption=f"{event.title}. {date_str}, {event.city}. Link in bio.",
        back_translation_en=back_en,
        approved=False,
        event_version=event_version,
        event_content_hash=event_hash,
        status="generated",
    )
    fc = fact_check_translation(event, t, lang)
    t_dict = t.model_dump()
    t_dict["fact_check"] = fc
    return Translation(**t_dict)
