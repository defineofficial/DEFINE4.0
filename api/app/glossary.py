"""Glossary for fixed event outreach terms across supported languages.

Ensures consistent terminology for call keypads, registration, and opt-outs in English, Hindi,
Malayalam, and Tamil.
"""
from typing import Dict, List
from app.schemas import Language

GLOSSARY: Dict[Language, Dict[str, str]] = {
    Language.en: {
        "seminar": "seminar",
        "workshop": "workshop",
        "registration": "registration",
        "confirm": "press 1 to confirm",
        "decline": "press 2 to decline",
        "callback": "press 3 for a callback",
        "stop": "press 9 to stop",
    },
    Language.hi: {
        "seminar": "सेमिनार",
        "workshop": "कार्यशाला",
        "registration": "पंजीकरण",
        "confirm": "पुष्टि के लिए 1 दबाएं",
        "decline": "मना करने के लिए 2 दबाएं",
        "callback": "वापस कॉल के लिए 3 दबाएं",
        "stop": "इन कॉल को रोकने के लिए 9 दबाएं",
    },
    Language.ml: {
        "seminar": "സെമിനാർ",
        "workshop": "വർക്ക്ഷോപ്പ്",
        "registration": "രജിസ്ട്രേഷൻ",
        "confirm": "സ്ഥിരീകരിക്കാൻ 1 അമർത്തുക",
        "decline": "ഒഴിവാക്കാൻ 2 അമർത്തുക",
        "callback": "തിരിച്ചു വിളിക്കാൻ 3 അമർത്തുക",
        "stop": "കോളുകൾ നിർത്താൻ 9 അമർത്തുക",
    },
    Language.ta: {
        "seminar": "கருத்தரங்கு",
        "workshop": "பயிற்சிப் பட்டறை",
        "registration": "பதிவு",
        "confirm": "உறுதிப்படுத்த 1 அழுத்தவும்",
        "decline": "மறுக்க 2 அழுத்தவும்",
        "callback": "மீண்டும் அழைக்க 3 அழுத்தவும்",
        "stop": "அழைப்புகளை நிறுத்த 9 அழுத்தவும்",
    },
}


def get_glossary(lang: Language) -> Dict[str, str]:
    """Returns the term dictionary for the given language."""
    return GLOSSARY.get(lang, GLOSSARY[Language.en])


def check_glossary_compliance(text: str, lang: Language) -> List[str]:
    """Checks if key call options (keypad 1, 2, 9) are present in the script text."""
    missing: List[str] = []
    t_lower = text.lower()

    if "1" not in t_lower:
        missing.append("keypad_option_1_confirm")
    if "2" not in t_lower:
        missing.append("keypad_option_2_decline")
    if "9" not in t_lower:
        missing.append("keypad_option_9_stop")

    return missing
