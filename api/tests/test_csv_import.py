import pytest

from app.csv_import import CsvImportError, MAX_ROWS, normalize_phone, parse_contacts_csv
from app.privacy import phone_hash
from app.schemas import Language


def parse(text: str, **kwargs):
    return parse_contacts_csv(text.encode("utf-8"), **kwargs)


# ---------- phone numbers ----------

@pytest.mark.parametrize("raw,expected", [
    ("98765 43210", "+919876543210"),
    ("+91 98765-43210", "+919876543210"),
    ("09876543210", "+919876543210"),
    ("919876543210", "+919876543210"),
    ("(98765) 43210", "+919876543210"),
    ("0091 98765 43210", "+919876543210"),
    ("+44 7700 900123", "+447700900123"),
])
def test_valid_phone_formats_become_e164(raw, expected):
    assert normalize_phone(raw) == (expected, None)


@pytest.mark.parametrize("raw,reason", [
    ("", "missing"),
    ("9876543", "7 digits"),
    ("5876543210", "start with 6"),
    ("9.8765E+09", "scientific notation"),
    ("98765abc10", "letters or symbols"),
    ("+91 98765", "10 digits"),
])
def test_bad_phone_numbers_say_why(raw, reason):
    number, problem = normalize_phone(raw)
    assert number is None and reason in problem


# ---------- file handling ----------

def test_accepts_excel_marker_semicolons_and_alternative_headers():
    text = "﻿Full Name;Mobile No;Lang\nAsha;9000000011;Hindi\n"
    result = parse(text)
    person = result.contacts[0]
    assert person.name == "Asha" and person.language == Language.hi and person.segment == "General"
    assert result.report.warnings == []


def test_indian_language_names_survive():
    result = parse("name,phone\nഅഞ്ജലി,9000000011\n")
    assert result.contacts[0].name == "അഞ്ജലി"


def test_missing_required_column_is_a_file_error():
    with pytest.raises(CsvImportError, match="phone"):
        parse("name,city\nAsha,Kochi\n")


def test_file_not_in_utf8_is_explained():
    with pytest.raises(CsvImportError, match="UTF-8"):
        parse_contacts_csv(b"name,phone\n\xe0sha,9000000011\n")


@pytest.mark.parametrize("content", [b"", b"   \n\n"])
def test_empty_file(content):
    with pytest.raises(CsvImportError, match="empty"):
        parse_contacts_csv(content)


def test_header_only_file_imports_nobody():
    result = parse("name,phone\n")
    assert result.report.total_rows == 0 and result.contacts == []


def test_too_many_rows():
    with pytest.raises(CsvImportError, match=str(MAX_ROWS)):
        parse("name,phone\n" + "A,9000000011\n" * (MAX_ROWS + 1))


def test_blank_lines_are_ignored_and_short_rows_are_handled():
    result = parse("name,phone,language\n\nAsha,9000000011\n\n")
    assert result.report.total_rows == 1 and result.report.imported == 1


# ---------- row rules ----------

def test_duplicates_inside_the_file_point_to_the_first_row():
    result = parse("name,phone\nAsha,9000000011\nAsha again,+91 90000 00011\n")
    assert result.report.imported == 1
    assert result.report.errors[0].row == 3
    assert "Duplicate of row 2" in result.report.errors[0].message


def test_existing_and_opted_out_numbers_are_skipped():
    existing = {phone_hash("+919000000011")}
    opted_out = {phone_hash("+919000000012")}
    result = parse("name,phone\nA,9000000011\nB,9000000012\nC,9000000013\n",
                   existing_hashes=existing, opted_out_hashes=opted_out)
    assert [c.name for c in result.contacts] == ["C"]
    messages = [e.message for e in result.report.errors]
    assert "Already in this campaign." in messages and "This number has opted out." in messages


def test_unsupported_language_and_bad_email_are_warnings_not_errors():
    result = parse("name,phone,language,email\nAsha,9000000011,Telugu,not-an-email\n")
    assert result.report.imported == 1 and result.report.errors == []
    assert {w.field for w in result.report.warnings} == {"language", "email"}
    assert result.contacts[0].language == Language.en and result.contacts[0].email is None


def test_default_language_applies_when_the_column_is_missing():
    result = parse("name,phone\nAsha,9000000011\n", default_language=Language.hi)
    assert result.contacts[0].language == Language.hi
    assert len(result.report.warnings) == 1


def test_full_phone_numbers_never_appear_in_the_report_or_in_logs():
    result = parse("name,phone\nAsha,9000000011\n")
    assert "9000000011" not in result.report.model_dump_json()
    assert "9000000011" not in repr(result.contacts)
    assert "•" in result.contacts[0].phone_masked
