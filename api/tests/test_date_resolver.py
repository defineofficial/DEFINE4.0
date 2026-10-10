"""Unit tests for date_resolver module.

Contains at least 35 test cases verifying:
- Absolute date parsing and Indian DD/MM date order
- Relative date phrases in English, Hindi, Malayalam, and Tamil
- Year rollover and past date detection
- Time parsing (24h, AM/PM, spoken time, ambiguous time flagging)
"""
from datetime import datetime, timedelta, timezone
import pytest

from app.date_resolver import resolve_date, IST, WEEKDAYS_EN


BASE_DATE = datetime(2026, 10, 10, 8, 0, 0, tzinfo=IST)  # Saturday, Oct 10, 2026


def test_01_absolute_date_month_name():
    res = resolve_date("14 November", "10:00 AM", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.starts_at.year == 2026
    assert res.starts_at.month == 11
    assert res.starts_at.day == 14
    assert res.starts_at.hour == 10
    assert res.display_weekday == "Saturday"


def test_02_indian_date_format_slash():
    res = resolve_date("14/11", "10:00 AM", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.starts_at.month == 11
    assert res.starts_at.day == 14


def test_03_indian_date_format_hyphen_year():
    res = resolve_date("14-11-2026", "10:00 AM", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.starts_at.year == 2026
    assert res.starts_at.month == 11
    assert res.starts_at.day == 14


def test_04_ordinal_date_string():
    res = resolve_date("14th of November 2026", "10:00 AM", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.starts_at.month == 11
    assert res.starts_at.day == 14


def test_05_month_abbr_first():
    res = resolve_date("Nov 14", "10:00 AM", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.starts_at.month == 11
    assert res.starts_at.day == 14


def test_06_relative_today():
    res = resolve_date("today", "10:00 AM", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.starts_at.date() == BASE_DATE.date()


def test_07_relative_tomorrow():
    res = resolve_date("tomorrow", "10:00 AM", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.starts_at.date() == BASE_DATE.date() + timedelta(days=1)


def test_08_relative_day_after_tomorrow():
    res = resolve_date("day after tomorrow", "10:00 AM", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.starts_at.date() == BASE_DATE.date() + timedelta(days=2)


def test_09_this_saturday():
    res = resolve_date("this Saturday", "10:00 AM", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.starts_at.weekday() == 5  # Saturday
    assert res.starts_at.date() > BASE_DATE.date()


def test_10_next_friday():
    res = resolve_date("next Friday", "10:00 AM", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.starts_at.weekday() == 4  # Friday
    assert res.starts_at.date() > BASE_DATE.date()


def test_11_hindi_today():
    res = resolve_date("आज", "10:00 AM", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.starts_at.date() == BASE_DATE.date()


def test_12_hindi_tomorrow():
    res = resolve_date("कल", "10:00 AM", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.starts_at.date() == BASE_DATE.date() + timedelta(days=1)


def test_13_hindi_day_after_tomorrow():
    res = resolve_date("परसों", "10:00 AM", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.starts_at.date() == BASE_DATE.date() + timedelta(days=2)


def test_14_hindi_next_saturday():
    res = resolve_date("अगले शनिवार", "10:00 AM", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.starts_at.weekday() == 5


def test_15_hindi_absolute_date():
    res = resolve_date("14 नवंबर", "10:00 AM", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.starts_at.month == 11
    assert res.starts_at.day == 14


def test_16_malayalam_today():
    res = resolve_date("ഇന്ന്", "10:00 AM", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.starts_at.date() == BASE_DATE.date()


def test_17_malayalam_tomorrow():
    res = resolve_date("നാളെ", "10:00 AM", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.starts_at.date() == BASE_DATE.date() + timedelta(days=1)


def test_18_malayalam_day_after_tomorrow():
    res = resolve_date("മറ്റന്നാൾ", "10:00 AM", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.starts_at.date() == BASE_DATE.date() + timedelta(days=2)


def test_19_malayalam_next_saturday():
    res = resolve_date("അടുത്ത ശനിയാഴ്ച", "10:00 AM", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.starts_at.weekday() == 5


def test_20_tamil_today():
    res = resolve_date("இன்று", "10:00 AM", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.starts_at.date() == BASE_DATE.date()


def test_21_tamil_tomorrow():
    res = resolve_date("நாளை", "10:00 AM", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.starts_at.date() == BASE_DATE.date() + timedelta(days=1)


def test_22_tamil_day_after_tomorrow():
    res = resolve_date("நாளை மறுநாள்", "10:00 AM", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.starts_at.date() == BASE_DATE.date() + timedelta(days=2)


def test_23_tamil_next_saturday():
    res = resolve_date("அடுத்த சனிக்கிழமை", "10:00 AM", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.starts_at.weekday() == 5


def test_24_spoken_time_morning():
    res = resolve_date("tomorrow", "ten in the morning", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.starts_at.hour == 10
    assert res.starts_at.minute == 0


def test_25_spoken_time_evening():
    res = resolve_date("tomorrow", "four in the evening", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.starts_at.hour == 16
    assert res.starts_at.minute == 0


def test_26_time_pm_format():
    res = resolve_date("tomorrow", "4:30 PM", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.starts_at.hour == 16
    assert res.starts_at.minute == 30


def test_27_time_24h_format():
    res = resolve_date("tomorrow", "14:00", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.starts_at.hour == 14
    assert res.starts_at.minute == 0


def test_28_ambiguous_time_bare_number():
    res = resolve_date("tomorrow", "at 10", base_date=BASE_DATE)
    assert "starts_at" in res.needs_review


def test_29_missing_time_text_flags_starts_at():
    res = resolve_date("tomorrow", None, base_date=BASE_DATE)
    assert res.starts_at is not None
    assert "starts_at" in res.needs_review


def test_30_date_in_past_rejected():
    past_date = "10 October 2025"
    res = resolve_date(past_date, "10:00 AM", base_date=BASE_DATE)
    assert res.starts_at is None
    assert res.reason == "date_in_past"
    assert "starts_at" in res.needs_review


def test_31_spoken_number_fourteenth():
    res = resolve_date("fourteenth of November", "10:00 AM", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.starts_at.month == 11
    assert res.starts_at.day == 14


def test_32_spoken_number_twenty_fifth():
    res = resolve_date("twenty-fifth of December", "10:00 AM", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.starts_at.month == 12
    assert res.starts_at.day == 25


def test_33_year_rollover_future():
    late_base = datetime(2026, 12, 1, 8, 0, 0, tzinfo=IST)
    res = resolve_date("14 November", "10:00 AM", base_date=late_base)
    assert res.starts_at is not None
    assert res.starts_at.year == 2027
    assert res.starts_at.month == 11
    assert res.starts_at.day == 14


def test_34_unresolvable_date_text():
    res = resolve_date("someday soon", "10:00 AM", base_date=BASE_DATE)
    assert res.starts_at is None
    assert "starts_at" in res.needs_review


def test_35_ends_at_duration_calculated():
    res = resolve_date("14 November", "10:00 AM", end_time_text="4:00 PM", base_date=BASE_DATE)
    assert res.starts_at is not None
    assert res.ends_at is not None
    assert res.starts_at.hour == 10
    assert res.ends_at.hour == 16
