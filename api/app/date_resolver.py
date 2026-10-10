"""Date and time resolver for voice notes and event details.

Converts spoken/raw date phrases (relative, absolute, multi-lingual) and time text
into timezone-aware ISO datetimes (Asia/Kolkata, UTC+5:30).
"""
import re
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta, timezone
from typing import Optional, List, Tuple

IST = timezone(timedelta(hours=5, minutes=30))

MONTH_MAP = {
    "jan": 1, "january": 1, "जनवरी": 1, "ജനുവരി": 1, "ஜனவரி": 1,
    "feb": 2, "february": 2, "फरवरी": 2, "ഫെബ്രുവരി": 2, "பிப்ரவரி": 2,
    "mar": 3, "march": 3, "मार्च": 3, "മാർച്ച്": 3, "மார்ச்": 3,
    "apr": 4, "april": 4, "अप्रैल": 4, "ഏപ്രിൽ": 4, "ஏப்ரல்": 4,
    "may": 5, "मई": 5, "മേയ്": 5, "மே": 5,
    "jun": 6, "june": 6, "जून": 6, "ജൂൺ": 6, "ஜூன்": 6,
    "jul": 7, "july": 7, "जुलाई": 7, "ജൂലൈ": 7, "ஜூலை": 7,
    "aug": 8, "august": 8, "अगस्त": 8, "ഓഗസ്റ്റ്": 8, "ஆகஸ்ட்": 8,
    "sep": 9, "september": 9, "सितंबर": 9, "സെപ്റ്റംബർ": 9, "செப்டம்பர்": 9,
    "oct": 10, "october": 10, "अक्टूबर": 10, "ഒക്ടോബർ": 10, "அக்டோபர்": 10,
    "nov": 11, "november": 11, "नवंबर": 11, "നവംബർ": 11, "நவம்பர்": 11,
    "dec": 12, "december": 12, "दिसंबर": 12, "ഡിസംബർ": 12, "டிசம்பர்": 12,
}

WEEKDAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

WEEKDAY_NAME_MAP = {
    # English
    "monday": 0, "mon": 0,
    "tuesday": 1, "tue": 1, "tues": 1,
    "wednesday": 2, "wed": 2,
    "thursday": 3, "thu": 3, "thur": 3, "thurs": 3,
    "friday": 4, "fri": 4,
    "saturday": 5, "sat": 5,
    "sunday": 6, "sun": 6,
    # Hindi
    "सोमवार": 0, "मंगलवार": 1, "बुधवार": 2, "गुरुवार": 3, "शुक्रवार": 4, "शनिवार": 5, "रविवार": 6,
    # Malayalam
    "തിങ്കൾ": 0, "ചൊവ്വ": 1, "ബുധൻ": 2, "വ്യാഴം": 3, "വെള്ളി": 4, "ശനി": 5, "ഞായർ": 6,
    "തിങ്കളാഴ്ച": 0, "ചൊവ്വാഴ്ച": 1, "ബുധനാഴ്ച": 2, "വ്യാഴാഴ്ച": 3, "വെള്ളിയാഴ്ച": 4, "ശനിയാഴ്ച": 5, "ഞായറാഴ്ച": 6,
    # Tamil
    "திங்கள்": 0, "செவ்வாய்": 1, "புதன்": 2, "வியாழன்": 3, "வெள்ளி": 4, "சனி": 5, "ஞாயிறு": 6,
    "சனிக்கிழமை": 5, "வெள்ளிக்கிழமை": 4, "வியாழக்கிழமை": 3, "புதன்கிழமை": 2, "செவ்வாய்க்கிழமை": 1, "திங்கள்கிழமை": 0, "ஞாயிற்றுக்கிழமை": 6,
}

SPOKEN_NUMBERS = {
    "first": 1, "1st": 1, "one": 1, "एक": 1, "ഒന്ന്": 1,
    "second": 2, "2nd": 2, "two": 2, "दो": 2, "രണ്ട്": 2,
    "third": 3, "3rd": 3, "three": 3, "तीन": 3, "മൂന്ന്": 3,
    "fourth": 4, "4th": 4, "four": 4, "चार": 4, "നാല്": 4,
    "fifth": 5, "5th": 5, "five": 5, "पांच": 5, "അഞ്ച്": 5,
    "sixth": 6, "6th": 6, "six": 6, "छह": 6, "ആറ്": 6,
    "seventh": 7, "7th": 7, "seven": 7, "सात": 7, "ഏഴ്": 7,
    "eighth": 8, "8th": 8, "eight": 8, "आठ": 8, "എട്ട്": 8,
    "ninth": 9, "9th": 9, "nine": 9, "नौ": 9, "ഒൻപത്": 9,
    "tenth": 10, "10th": 10, "ten": 10, "दस": 10, "പത്ത്": 10,
    "eleventh": 11, "11th": 11, "eleven": 11, "ग्यारह": 11,
    "twelfth": 12, "12th": 12, "twelve": 12, "बारह": 12,
    "thirteenth": 13, "13th": 13, "thirteen": 13, "तेरह": 13,
    "fourteenth": 14, "14th": 14, "fourteen": 14, "चौदह": 14,
    "fifteenth": 15, "15th": 15, "fifteen": 15, "पंद्रह": 15,
    "sixteenth": 16, "16th": 16, "sixteen": 16, "सोलह": 16,
    "seventeenth": 17, "17th": 17, "seventeen": 17, "सत्रह": 17,
    "eighteenth": 18, "18th": 18, "eighteen": 18, "अठारह": 18,
    "nineteenth": 19, "19th": 19, "nineteen": 19, "उन्नीस": 19,
    "twentieth": 20, "20th": 20, "twenty": 20, "बीस": 20,
    "twenty-first": 21, "21st": 21,
    "twenty-second": 22, "22nd": 22,
    "twenty-third": 23, "23rd": 23,
    "twenty-fourth": 24, "24th": 24,
    "twenty-fifth": 25, "25th": 25,
    "thirtieth": 30, "30th": 30, "thirty": 30, "तीस": 30,
    "thirty-first": 31, "31st": 31,
}


@dataclass
class ResolvedDate:
    starts_at: Optional[datetime]
    ends_at: Optional[datetime]
    raw_date_text: Optional[str]
    start_time_text: Optional[str]
    end_time_text: Optional[str]
    display_weekday: Optional[str]
    needs_review: List[str] = field(default_factory=list)
    reason: Optional[str] = None


def resolve_date(
    raw_date_text: Optional[str],
    start_time_text: Optional[str] = None,
    end_time_text: Optional[str] = None,
    base_date: Optional[datetime] = None,
) -> ResolvedDate:
    """Resolves date and time strings relative to base_date in Asia/Kolkata timezone."""
    needs_review: List[str] = []
    
    if base_date is None:
        base_date = datetime.now(IST)
    elif base_date.tzinfo is None:
        base_date = base_date.replace(tzinfo=IST)

    if not raw_date_text or not raw_date_text.strip():
        return ResolvedDate(
            starts_at=None,
            ends_at=None,
            raw_date_text=raw_date_text,
            start_time_text=start_time_text,
            end_time_text=end_time_text,
            display_weekday=None,
            needs_review=["starts_at"],
            reason="missing_date_text",
        )

    date_str = raw_date_text.strip().lower()

    # 1. Parse Date Component
    target_date, date_reason = _parse_date_phrase(date_str, base_date)

    if target_date is None:
        return ResolvedDate(
            starts_at=None,
            ends_at=None,
            raw_date_text=raw_date_text,
            start_time_text=start_time_text,
            end_time_text=end_time_text,
            display_weekday=None,
            needs_review=["starts_at"],
            reason=date_reason or "unresolvable_date",
        )

    # Check if date is in the past
    base_day = base_date.date()
    if target_date < base_day:
        return ResolvedDate(
            starts_at=None,
            ends_at=None,
            raw_date_text=raw_date_text,
            start_time_text=start_time_text,
            end_time_text=end_time_text,
            display_weekday=WEEKDAYS_EN[target_date.weekday()],
            needs_review=["starts_at"],
            reason="date_in_past",
        )

    # 2. Parse Time Component
    start_time, is_start_ambiguous = _parse_time_phrase(start_time_text)
    end_time, is_end_ambiguous = _parse_time_phrase(end_time_text)

    if start_time_text and is_start_ambiguous:
        needs_review.append("starts_at")
    elif not start_time_text:
        # Default to 10:00 AM if no time text given, but flag for review
        start_time = (10, 0)
        needs_review.append("starts_at")

    if start_time is None:
        start_time = (10, 0)

    starts_at = datetime(
        target_date.year, target_date.month, target_date.day,
        start_time[0], start_time[1], 0, tzinfo=IST
    )

    ends_at = None
    if end_time is not None:
        ends_at = datetime(
            target_date.year, target_date.month, target_date.day,
            end_time[0], end_time[1], 0, tzinfo=IST
        )
        if ends_at <= starts_at:
            ends_at = ends_at + timedelta(days=1)
    else:
        # Default 6-hour duration
        ends_at = starts_at + timedelta(hours=6)

    weekday_str = WEEKDAYS_EN[target_date.weekday()]

    return ResolvedDate(
        starts_at=starts_at,
        ends_at=ends_at,
        raw_date_text=raw_date_text,
        start_time_text=start_time_text,
        end_time_text=end_time_text,
        display_weekday=weekday_str,
        needs_review=needs_review,
    )


def _parse_date_phrase(text: str, base_datetime: datetime) -> Tuple[Optional[date], Optional[str]]:
    base_day = base_datetime.date()
    t = text.lower().strip()

    # Relative days: English, Hindi, Malayalam, Tamil
    if t in {"today", "आज", "ഇന്ന്", "இன்று"}:
        return base_day, None

    if t in {"tomorrow", "कल", "നാളെ", "நாளை"}:
        return base_day + timedelta(days=1), None

    if t in {"day after tomorrow", "परसों", "മറ്റന്നാൾ", "நாளை மறுநாள்"}:
        return base_day + timedelta(days=2), None

    # Check for weekdays (e.g. "this Saturday", "next Friday", "Saturday", "അടുത്ത ശനിയാഴ്ച")
    for name, target_wd in WEEKDAY_NAME_MAP.items():
        if name in t:
            is_next = any(kw in t for kw in ["next", "अगले", "അടുത്ത", "அடுத்த"])
            current_wd = base_day.weekday()
            days_ahead = (target_wd - current_wd) % 7
            if days_ahead == 0 or is_next:
                days_ahead += 7
            return base_day + timedelta(days=days_ahead), None

    # Spoken number + month (e.g. "fourteenth of November", "14 November", "14th Nov", "Nov 14")
    # First check month names
    for m_name, m_num in MONTH_MAP.items():
        if m_name in t:
            # Look for numbers or spoken number words
            day_val = None
            # Check digits first
            m_digit = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)?\b", t)
            if m_digit:
                day_val = int(m_digit.group(1))
            else:
                # Check spoken numbers (sorted by length descending to match longest phrase first)
                for word in sorted(SPOKEN_NUMBERS.keys(), key=len, reverse=True):
                    if word in t:
                        day_val = SPOKEN_NUMBERS[word]
                        break

            if day_val and 1 <= day_val <= 31:
                m_yr = re.search(r"\b(20\d{2})\b", t)
                if m_yr:
                    try:
                        return date(int(m_yr.group(1)), m_num, day_val), None
                    except ValueError:
                        return None, "invalid_day_of_month"

                year = base_day.year
                # If date in this year has already passed, use next year
                try:
                    cand = date(year, m_num, day_val)
                    if cand < base_day:
                        cand = date(year + 1, m_num, day_val)
                    return cand, None
                except ValueError:
                    return None, "invalid_day_of_month"

    # Numeric dates: Indian format DD/MM/YYYY or DD-MM-YYYY or DD/MM
    m_num = re.search(r"\b(\d{1,2})[/\.-](\d{1,2})(?:[/\.-](\d{2,4}))?\b", t)
    if m_num:
        d = int(m_num.group(1))
        m = int(m_num.group(2))
        y_raw = m_num.group(3)
        if y_raw:
            y = int(y_raw)
            if y < 100:
                y += 2000
        else:
            y = base_day.year
            try:
                if date(y, m, d) < base_day:
                    y += 1
            except ValueError:
                pass
        try:
            return date(y, m, d), None
        except ValueError:
            return None, "invalid_numeric_date"

    return None, "unrecognized_date_format"


def _parse_time_phrase(text: Optional[str]) -> Tuple[Optional[Tuple[int, int]], bool]:
    """Parses time text into (hour_24, min) and is_ambiguous flag."""
    if not text or not text.strip():
        return None, True

    t = text.strip().lower()

    # Spoken phrases
    if "ten in the morning" in t or "10 in the morning" in t:
        return (10, 0), False
    if "nine in the morning" in t or "9 in the morning" in t:
        return (9, 0), False
    if "four in the evening" in t or "4 in the evening" in t or "4 in the afternoon" in t:
        return (16, 0), False
    if "five in the evening" in t or "5 in the evening" in t:
        return (17, 0), False

    # HH:MM AM/PM or HH AM/PM
    m_ampm = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", t)
    if m_ampm:
        h = int(m_ampm.group(1))
        m = int(m_ampm.group(2) or 0)
        ampm = m_ampm.group(3)
        if ampm == "pm" and h < 12:
            h += 12
        elif ampm == "am" and h == 12:
            h = 0
        return (h, m), False

    # 24-hour time e.g. 16:00, 10:30
    m_24 = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", t)
    if m_24:
        return (int(m_24.group(1)), int(m_24.group(2))), False

    # Bare number without AM/PM e.g. "at 10", "at 4"
    m_bare = re.search(r"\b(\d{1,2})\b", t)
    if m_bare:
        h = int(m_bare.group(1))
        if 1 <= h <= 12:
            # Default morning or afternoon depending on common event times, but flag as ambiguous
            hour_24 = h if h >= 8 and h <= 12 else (h + 12 if h < 8 else h)
            return (hour_24, 0), True

    return None, True
