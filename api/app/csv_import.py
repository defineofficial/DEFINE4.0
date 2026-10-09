"""Real CSV import for the audience list.

Pure functions: bytes in, clean rows and a report out. Nothing here touches the database,
so the same code keeps working when storage moves from memory to PostgreSQL.

Row numbers follow the spreadsheet: the header is row 1, the first person is row 2.
"""
import csv
import io
import re
from dataclasses import dataclass, field
from typing import Optional

from .privacy import mask_phone, phone_hash
from .schemas import ImportReport, Language, RowError

MAX_ROWS = 5000
MAX_NAME_LENGTH = 100


class CsvImportError(Exception):
    """The whole file cannot be used, as opposed to one bad row."""


# Accepted header names, after lower-casing and removing spaces, dashes and underscores.
_ALIASES = {
    "name": {"name", "fullname", "contactname"},
    "phone": {"phone", "phonenumber", "mobile", "mobilenumber", "mobileno", "contactnumber", "number"},
    "language": {"language", "lang", "preferredlanguage"},
    "segment": {"segment", "group", "category"},
    "email": {"email", "emailaddress", "mail"},
}
_LANGUAGE_NAMES = {"english": Language.en, "hindi": Language.hi, "malayalam": Language.ml, "tamil": Language.ta}
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_SCIENTIFIC = re.compile(r"^\d+(\.\d+)?[eE]\+?\d+$")
_PHONE_CHARS = re.compile(r"^[+\d\s\-().]+$")


@dataclass(frozen=True)
class ParsedContact:
    row: int
    name: str
    phone_hash: str
    phone_masked: str
    email: Optional[str]
    language: Language
    segment: str
    # The real storage layer encrypts this. It is kept out of repr so it never lands in logs.
    phone_e164: str = field(repr=False)


@dataclass
class ParseResult:
    contacts: list[ParsedContact]
    report: ImportReport


# ---------- phone numbers ----------

def _india(national: str) -> tuple[Optional[str], Optional[str]]:
    if len(national) != 10:
        return None, f"Indian numbers need 10 digits after +91, found {len(national)}."
    if national[0] not in "6789":
        return None, "Indian mobile numbers start with 6, 7, 8 or 9."
    return "+91" + national, None


def normalize_phone(raw: str) -> tuple[Optional[str], Optional[str]]:
    """Return (number in +E.164 form, None) or (None, reason it was rejected)."""
    s = (raw or "").strip()
    if not s:
        return None, "Phone number is missing."
    if _SCIENTIFIC.match(s.replace(" ", "")):
        return None, "Excel turned this number into scientific notation. Format the phone column as Text and save again."
    if not _PHONE_CHARS.match(s):
        return None, "Phone number contains letters or symbols."

    international = s.startswith("+") or s.startswith("00")
    digits = re.sub(r"\D", "", s)
    if s.startswith("00"):
        digits = digits[2:]

    if international:
        if digits.startswith("91"):
            return _india(digits[2:])
        if 8 <= len(digits) <= 15:
            return "+" + digits, None
        return None, f"Phone number has {len(digits)} digits. International numbers need 8 to 15."
    if len(digits) == 10:
        return _india(digits)
    if len(digits) == 11 and digits.startswith("0"):
        return _india(digits[1:])
    if len(digits) == 12 and digits.startswith("91"):
        return _india(digits[2:])
    return None, f"Phone number has {len(digits)} digits. Expected 10, or 12 with the country code 91."


# ---------- file level ----------

def _decode(raw: bytes) -> str:
    try:
        return raw.decode("utf-8-sig")  # utf-8-sig also removes the marker Excel adds
    except UnicodeDecodeError:
        raise CsvImportError(
            "The file is not UTF-8, so Hindi, Malayalam and Tamil names would be damaged. "
            "In Excel choose 'CSV UTF-8 (Comma delimited)' when you save."
        ) from None


def _delimiter(text: str) -> str:
    lines = text.splitlines()
    first = lines[0] if lines else ""
    counts = {d: first.count(d) for d in (",", ";", "\t")}
    best = max(counts, key=counts.get)
    return best if counts[best] else ","


def _map_headers(headers: list[str]) -> dict[str, int]:
    found: dict[str, int] = {}
    for index, header in enumerate(headers):
        key = re.sub(r"[\s_\-]+", "", header.strip().lower())
        for field_name, names in _ALIASES.items():
            if key in names and field_name not in found:
                found[field_name] = index
    missing = [f for f in ("name", "phone") if f not in found]
    if missing:
        seen = ", ".join(h.strip() for h in headers if h.strip()) or "none"
        raise CsvImportError(f"Missing required column: {', '.join(missing)}. Columns found: {seen}.")
    return found


def _language(value: str, default: Language) -> tuple[Language, Optional[str]]:
    if not value:
        return default, f"Language is missing. Using {default.value}."
    v = value.strip().lower()
    if v in {lang.value for lang in Language}:
        return Language(v), None
    if v in _LANGUAGE_NAMES:
        return _LANGUAGE_NAMES[v], None
    return default, f"Language '{value}' is not supported yet. Using {default.value}."


# ---------- the importer ----------

def parse_contacts_csv(
    raw: bytes,
    default_language: Language = Language.en,
    existing_hashes: frozenset[str] | set[str] = frozenset(),
    opted_out_hashes: frozenset[str] | set[str] = frozenset(),
) -> ParseResult:
    """Validate a contact file.

    Bad rows are skipped and listed in report.errors. Rows that are kept but need a look
    (unsupported language, invalid email) are listed in report.warnings.
    Raises CsvImportError when the file as a whole cannot be read.
    """
    text = _decode(raw)
    if not text.strip():
        raise CsvImportError("The file is empty.")
    reader = csv.reader(io.StringIO(text), delimiter=_delimiter(text))
    try:
        headers = next(reader)
    except StopIteration:
        raise CsvImportError("The file is empty.") from None
    cols = _map_headers(headers)

    contacts: list[ParsedContact] = []
    errors: list[RowError] = []
    warnings: list[RowError] = []
    first_row_of: dict[str, int] = {}
    languages: dict[str, int] = {}
    segments: dict[str, int] = {}
    total = 0

    if "language" not in cols:
        warnings.append(RowError(row=1, field="language", message=f"No language column. Everyone uses {default_language.value}."))

    for row_no, cells in enumerate(reader, start=2):
        if not any(c.strip() for c in cells):
            continue  # blank line
        total += 1
        if total > MAX_ROWS:
            raise CsvImportError(f"The file has more than {MAX_ROWS} rows. Split it into smaller files.")

        def cell(column: str) -> str:
            i = cols.get(column)
            return cells[i].strip() if i is not None and i < len(cells) else ""

        name = cell("name")
        if not name:
            errors.append(RowError(row=row_no, field="name", message="Name is missing."))
            continue
        if len(name) > MAX_NAME_LENGTH:
            errors.append(RowError(row=row_no, field="name", message=f"Name is longer than {MAX_NAME_LENGTH} characters."))
            continue

        e164, problem = normalize_phone(cell("phone"))
        if problem:
            errors.append(RowError(row=row_no, field="phone", message=problem))
            continue
        h = phone_hash(e164)
        if h in first_row_of:
            errors.append(RowError(row=row_no, field="phone", message=f"Duplicate of row {first_row_of[h]}."))
            continue
        if h in existing_hashes:
            errors.append(RowError(row=row_no, field="phone", message="Already in this campaign."))
            continue
        if h in opted_out_hashes:
            errors.append(RowError(row=row_no, field="phone", message="This number has opted out."))
            continue
        first_row_of[h] = row_no

        if "language" in cols:
            language, note = _language(cell("language"), default_language)
            if note:
                warnings.append(RowError(row=row_no, field="language", message=note))
        else:
            language = default_language

        email: Optional[str] = cell("email") or None
        if email and not _EMAIL.match(email):
            warnings.append(RowError(row=row_no, field="email", message="Email looks invalid and was left out."))
            email = None

        segment = cell("segment") or "General"
        contacts.append(ParsedContact(
            row=row_no, name=name, phone_hash=h, phone_masked=mask_phone(e164),
            email=email, language=language, segment=segment, phone_e164=e164,
        ))
        languages[language.value] = languages.get(language.value, 0) + 1
        segments[segment] = segments.get(segment, 0) + 1

    report = ImportReport(
        total_rows=total, imported=len(contacts), skipped=total - len(contacts),
        errors=errors, warnings=warnings, languages_found=languages, segments_found=segments,
    )
    return ParseResult(contacts=contacts, report=report)
