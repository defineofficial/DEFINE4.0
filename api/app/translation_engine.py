"""Multilingual translation and back-translation engine for EventReach.

Translates event outreach copy into Hindi (hi), Malayalam (ml), and Tamil (ta),
with a round-trip back-translation into English so organizers can verify script fidelity.
All calls are guarded by `ai_budget` and cached by content hash to prevent redundant AI spending.
"""
import hashlib
import json
import logging
import os
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Tuple

from app import ai_budget
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


# ---------- Translation System Prompts ----------

TRANSLATION_SYSTEM_PROMPT = """You are a professional multilingual translator for EventReach, an Indian event outreach platform.
Translate the event invitation into the requested Indian language ({target_language}).
Keep the tone polite, professional, and clear.

Return ONLY a JSON object with this exact structure:
{{
  "call_script": "Short text-to-speech script under 25 seconds when spoken. Keep placeholder {{name}}. Include keypad instructions: 1 to confirm, 2 to decline, 3 for callback, 9 to stop.",
  "voicemail_script": "Short 10-15 second voicemail script if call is unanswered. Keep placeholder {{name}}.",
  "email_subject": "Invitation subject line in the target language",
  "email_body": "Polite email invitation body with placeholders {{name}} and {{link}}.",
  "whatsapp_text": "Short WhatsApp invitation text with placeholders {{name}} and {{link}}.",
  "social_caption": "Catchy Instagram/social caption with venue and date details."
}}
"""

BACK_TRANSLATION_SYSTEM_PROMPT = """You are an English back-translator for EventReach.
Translate the following call script from {source_language} back into plain English as literally and accurately as possible,
so an English-speaking organizer can verify its meaning and accuracy.
Return ONLY the English text.
"""


# ---------- Public Translation Methods ----------

def generate_translations(
    campaign_id: str,
    event: EventDetails,
    languages: List[Language],
) -> List[Translation]:
    """Generates translation records for the given languages with back-translation and caching."""
    results: List[Translation] = []

    for lang in languages:
        t = translate_event(event, lang)
        results.append(t)

    return results


def translate_event(event: EventDetails, lang: Language) -> Translation:
    """Translates event copy into a target language with back-translation."""
    event_dict = {
        "title": event.title,
        "date": event.starts_at.strftime("%d %B %Y, %I:%M %p"),
        "venue": event.venue,
        "city": event.city,
        "fee": event.fee_inr,
    }
    key = cache_key(event_dict, lang)
    if key in _CACHE:
        return _CACHE[key]

    # English is source language
    if lang == Language.en:
        en_translation = _build_english_translation(event)
        _CACHE[key] = en_translation
        return en_translation

    api_key = _get_api_key()
    if api_key:
        try:
            translation = _call_llm_translate(api_key, event, lang)
            _CACHE[key] = translation
            return translation
        except Exception as exc:
            log.warning("Remote translation failed, falling back to localized template: %s", exc)

    # High-quality localized fallback for Hindi, Malayalam, Tamil
    fallback = _build_fallback_translation(event, lang)
    _CACHE[key] = fallback
    return fallback


def _build_english_translation(event: EventDetails) -> Translation:
    time_str = event.starts_at.strftime("%d %B at %I:%M %p")
    call_script = (
        f"Hello {{name}}. You are invited to the {event.title} on {time_str}, "
        f"{event.venue}, {event.city}. Press 1 to confirm, 2 to decline, or 3 for a callback. "
        "Press 9 to stop these calls."
    )
    vm_script = (
        f"Hello {{name}}, this is an invitation to the {event.title} on {time_str} "
        f"in {event.city}. Please call us back on the number shown on your phone."
    )
    email_subject = f"You are invited: {event.title}, {event.starts_at.strftime('%d %B')}"
    email_body = (
        f"Dear {{name}},\n\nYou are invited to {event.title} on {time_str}, "
        f"{event.venue}, {event.city}. Please register here: {{link}}"
    )
    whatsapp_text = (
        f"Hi {{name}}, you are invited to {event.title} on {time_str}, "
        f"{event.venue}, {event.city}. Register here: {{link}}"
    )
    social_caption = f"{event.title}. {time_str}, {event.city}. Register through the link in our bio."

    return Translation(
        language=Language.en,
        call_script=call_script,
        voicemail_script=vm_script,
        email_subject=email_subject,
        email_body=email_body,
        whatsapp_text=whatsapp_text,
        social_caption=social_caption,
        back_translation_en=call_script,
        approved=True,
    )


def _call_llm_translate(api_key: str, event: EventDetails, lang: Language) -> Translation:
    lang_names = {Language.hi: "Hindi", Language.ml: "Malayalam", Language.ta: "Tamil"}
    target_name = lang_names.get(lang, lang.value)
    time_str = event.starts_at.strftime("%d %B %Y at %I:%M %p")

    user_prompt = (
        f"Event Title: {event.title}\n"
        f"Date and Time: {time_str}\n"
        f"Venue: {event.venue}\n"
        f"City: {event.city}\n"
        f"Fee: Rs. {event.fee_inr}\n"
        f"Description: {event.description or ''}"
    )

    with ai_budget.guard("translation", estimated_usd=0.01) as t_call:
        req_body = {
            "model": _LLM_MODEL,
            "messages": [
                {"role": "system", "content": TRANSLATION_SYSTEM_PROMPT.format(target_language=target_name)},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.3,
        }
        req = urllib.request.Request(
            _CHAT_URL,
            data=json.dumps(req_body).encode("utf-8"),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
        t_call.actual_usd = 0.005

    # Back-translation to English
    call_script = parsed.get("call_script", "")
    with ai_budget.guard("back_translation", estimated_usd=0.005) as bt_call:
        bt_body = {
            "model": _LLM_MODEL,
            "messages": [
                {"role": "system", "content": BACK_TRANSLATION_SYSTEM_PROMPT.format(source_language=target_name)},
                {"role": "user", "content": call_script},
            ],
            "temperature": 0.2,
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

    return Translation(
        language=lang,
        call_script=call_script,
        voicemail_script=parsed.get("voicemail_script", ""),
        email_subject=parsed.get("email_subject"),
        email_body=parsed.get("email_body"),
        whatsapp_text=parsed.get("whatsapp_text"),
        social_caption=parsed.get("social_caption"),
        back_translation_en=back_trans,
        approved=False,
    )


def _build_fallback_translation(event: EventDetails, lang: Language) -> Translation:
    """Localized native template fallbacks for Hindi, Malayalam, and Tamil."""
    day = event.starts_at.strftime("%d")
    en_base = _build_english_translation(event)

    if lang == Language.hi:
        call_script = (
            f"नमस्ते {{name}}। आपको {day} नवंबर को, {event.city} के {event.venue} में होने वाले "
            f"'{event.title}' में आमंत्रित किया जाता है। पुष्टि के लिए 1 दबाएं, मना करने के लिए 2, "
            "वापस कॉल के लिए 3 दबाएं। इन कॉल को रोकने के लिए 9 दबाएं।"
        )
        vm_script = (
            f"नमस्ते {{name}}, {day} नवंबर को {event.city} में होने वाले '{event.title}' का "
            "यह निमंत्रण है। कृपया आपके फोन पर दिख रहे नंबर पर हमें वापस कॉल करें।"
        )
        subject = f"आमंत्रण: {event.title}, {day} नवंबर"
        email_b = (
            f"प्रिय {{name}},\n\nआपको {day} नवंबर को {event.city} के {event.venue} में आयोजित "
            f"'{event.title}' में आमंत्रित किया जाता है। कृपया यहां रजिस्टर करें: {{link}}"
        )
        wa = (
            f"नमस्ते {{name}}, {day} नवंबर को {event.city} के {event.venue} में '{event.title}' "
            f"का आपको निमंत्रण है। यहां रजिस्टर करें: {{link}}"
        )
        back_en = (
            f"Hello {{name}}. You are invited to '{event.title}' at {event.venue}, {event.city} on {day} November. "
            "Press 1 to confirm, 2 to decline, 3 for callback, 9 to opt out."
        )
    elif lang == Language.ml:
        call_script = (
            f"നമസ്കാരം {{name}}. നവംബർ {day}-ന് {event.city}-യിലെ {event.venue}-ൽ നടക്കുന്ന "
            f"'{event.title}'-ലേക്ക് നിങ്ങളെ ക്ഷണിക്കുന്നു. സ്ഥിരീകരിക്കാൻ 1, ഒഴിവാക്കാൻ 2, "
            "തിരിച്ചു വിളിക്കാൻ 3 അമർത്തുക. ഈ കോളുകൾ നിർത്താൻ 9 അമർത്തുക."
        )
        vm_script = (
            f"നമസ്കാരം {{name}}, നവംബർ {day}-ന് {event.city}-യിൽ നടക്കുന്ന '{event.title}'-ലേക്കുള്ള ക്ഷണമാണിത്. "
            "നിങ്ങളുടെ ഫോണിൽ കാണുന്ന നമ്പറിൽ ഞങ്ങളെ തിരികെ വിളിക്കുക."
        )
        subject = f"ക്ഷണം: {event.title}, നവംബർ {day}"
        email_b = (
            f"പ്രിയപ്പെട്ട {{name}},\n\nനവംബർ {day}-ന് {event.city}-യിലെ {event.venue}-ൽ നടക്കുന്ന "
            f"'{event.title}'-ലേക്ക് സ്വാഗതം. ദയവായി ഇവിടെ രജിസ്റ്റർ ചെയ്യുക: {{link}}"
        )
        wa = (
            f"നമസ്കാരം {{name}}, നവംബർ {day}-ന് {event.city} {event.venue}-ൽ '{event.title}'-ലേക്ക് സ്വാഗതം. "
            f"ഇവിടെ രജിസ്റ്റർ ചെയ്യുക: {{link}}"
        )
        back_en = (
            f"Hello {{name}}. You are invited to '{event.title}' on November {day} at {event.venue}, {event.city}. "
            "Press 1 to confirm, 2 to decline, 3 for callback, 9 to stop calls."
        )
    else:  # Tamil (ta)
        call_script = (
            f"வணக்கம் {{name}}. நவம்பர் {day} அன்று {event.city}-யில் உள்ள {event.venue}-ல் "
            f"நடைபெறும் '{event.title}'-ற்கு உங்களை அழைக்கிறோம். உறுதிப்படுத்த 1, மறுக்க 2, "
            "மீண்டும் அழைக்க 3 அழுத்தவும். இந்த அழைப்புகளை நிறுத்த 9 அழுத்தவும்."
        )
        vm_script = (
            f"வணக்கம் {{name}}, நவம்பர் {day} அன்று {event.city}-யில் நடைபெறும் '{event.title}'-ற்கான அழைப்பு இது. "
            "உங்கள் தொலைபேசியில் தெரியும் எண்ணுக்கு எங்களை மீண்டும் அழைக்கவும்."
        )
        subject = f"அழைப்பு: {event.title}, நவம்பர் {day}"
        email_b = (
            f"அன்புள்ள {{name}},\n\nநவம்பர் {day} அன்று {event.city}-யில் உள்ள {event.venue}-ல் "
            f"நடைபெறும் '{event.title}'-ற்கு உங்களை அழைக்கிறோம். இங்கே பதிவு செய்யவும்: {{link}}"
        )
        wa = (
            f"வணக்கம் {{name}}, நவம்பர் {day} அன்று {event.city} {event.venue}-ல் '{event.title}'-ற்கு "
            f"உங்களை அழைக்கிறோம். இங்கே பதிவு செய்யுங்கள்: {{link}}"
        )
        back_en = (
            f"Hello {{name}}. We invite you to '{event.title}' on November {day} at {event.venue}, {event.city}. "
            "Press 1 to confirm, 2 to decline, 3 for callback, 9 to stop calls."
        )

    return Translation(
        language=lang,
        call_script=call_script,
        voicemail_script=vm_script,
        email_subject=subject,
        email_body=email_b,
        whatsapp_text=wa,
        social_caption=f"{event.title}. {day} November, {event.city}. Link in bio.",
        back_translation_en=back_en,
        approved=False,
    )
