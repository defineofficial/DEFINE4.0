"""Private storage for posters and voice notes, served only through signed, expiring links.

Nothing here is public. Files live in STORAGE_DIR (default: api/uploads/, git-ignored) and no static
route points at that folder. The only way to read a file over HTTP is a link made by `signed_path`:

    /files/posters/<campaign>/<random>.png?exp=1767225600&sig=<hmac>

The link is valid until `exp` (Unix seconds) and cannot be changed: the signature covers the file key and
the expiry, so editing either one, or asking for a different file, fails.

Choices worth knowing
- Uploads are checked by their first bytes, never by the filename or the Content-Type the browser sends.
  Only the formats in RULES are accepted. SVG is left out on purpose, because an SVG can carry script.
- File names are made by the server (random), so a user-supplied name can never reach the disk path.
- Signing uses a key derived from SECRET_KEY for this purpose only, so a link signature can never be
  replayed as a login token or the other way round.
- Links expire after STORAGE_LINK_TTL_SECONDS (default 900 = 15 minutes), never less than 30 seconds
  or more than 7 days.
- The module uses only the standard library, so it can be tested without FastAPI.

The S3-compatible version (for deployment) would keep the same functions and swap `LocalStorage`.
"""
import hashlib
import hmac
import logging
import os
import re
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import quote
from uuid import uuid4

log = logging.getLogger("eventreach.storage")

MB = 1024 * 1024
DEFAULT_TTL_SECONDS = 15 * 60
MIN_TTL_SECONDS = 30
MAX_TTL_SECONDS = 7 * 24 * 3600
_SIGNING_PURPOSE = b"eventreach/storage-link/v1"
_SAFE_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_SAFE_KEY = re.compile(
    r"^(posters|voice-notes)/[A-Za-z0-9_-]{1,64}/[0-9a-f]{32}\.(png|jpg|webp|pdf|wav|mp3|m4a|ogg|webm|flac)$"
)


# ---------- errors (each carries a plain sentence the API can return) ----------

class StorageError(Exception):
    status_code = 400


class UnsupportedFile(StorageError):
    status_code = 415


class FileTooLarge(StorageError):
    status_code = 413


class EmptyFile(StorageError):
    status_code = 422


class LinkInvalid(StorageError):
    status_code = 403


class LinkExpired(StorageError):
    status_code = 410


class FileMissing(StorageError):
    status_code = 404


# ---------- what is accepted ----------

@dataclass(frozen=True)
class Rule:
    folder: str
    max_bytes: int
    label: str        # shown in error messages


# 10 MB posters and a 3-minute voice note (a 3-minute stereo WAV at 44.1 kHz is about 31 MB, so the
# limit is 25 MB; ask the browser to record mono or compressed audio).
RULES = {
    "poster": Rule("posters", 10 * MB, "poster (PNG, JPEG, WebP or PDF)"),
    "voice_note": Rule("voice-notes", 25 * MB, "voice note (WAV, MP3, M4A, OGG, WebM or FLAC)"),
}

# extension -> content type served back
CONTENT_TYPES = {
    "png": "image/png", "jpg": "image/jpeg", "webp": "image/webp", "pdf": "application/pdf",
    "wav": "audio/wav", "mp3": "audio/mpeg", "m4a": "audio/mp4", "ogg": "audio/ogg",
    "webm": "audio/webm", "flac": "audio/flac",
}
_ALLOWED_EXTENSIONS = {
    "poster": {"png", "jpg", "webp", "pdf"},
    "voice_note": {"wav", "mp3", "m4a", "ogg", "webm", "flac"},
}


def sniff_extension(data: bytes) -> Optional[str]:
    """Work out the real file type from its first bytes. None when it is not a format we accept."""
    head = data[:16]
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if head.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if head.startswith(b"RIFF") and head[8:12] == b"WEBP":
        return "webp"
    if head.startswith(b"RIFF") and head[8:12] == b"WAVE":
        return "wav"
    if head.startswith(b"%PDF-"):
        return "pdf"
    if head.startswith(b"OggS"):
        return "ogg"
    if head.startswith(b"fLaC"):
        return "flac"
    if head.startswith(b"\x1a\x45\xdf\xa3") or b"\x1a\x45\xdf\xa3" in data[:32]:
        return "webm"
    if head[4:8] == b"ftyp":
        return "m4a"
    if head.startswith(b"ID3") or (len(head) >= 2 and head[0] == 0xFF and head[1] & 0xE0 == 0xE0) or b"ID3" in data[:32]:
        return "mp3"
    return None


# ---------- saving and reading ----------

def storage_root() -> Path:
    configured = os.getenv("STORAGE_DIR", "").strip()
    root = Path(configured) if configured else Path(__file__).resolve().parent.parent / "uploads"
    return root.resolve()


@dataclass(frozen=True)
class StoredFile:
    key: str
    content_type: str
    size: int


def save(kind: str, owner_id: str, data: bytes) -> StoredFile:
    """Check an upload and write it to private storage. `owner_id` is the campaign ID.

    Raises EmptyFile, FileTooLarge or UnsupportedFile with a plain sentence for the organizer.
    """
    rule = RULES[kind]
    if not _SAFE_ID.fullmatch(owner_id):
        raise StorageError("That campaign ID cannot be used for storage.")
    if not data:
        raise EmptyFile("The file is empty. Choose the file again.")
    if len(data) > rule.max_bytes:
        raise FileTooLarge(f"That file is over the {rule.max_bytes // MB} MB limit for a {rule.label}.")
    ext = sniff_extension(data)
    if ext is None or ext not in _ALLOWED_EXTENSIONS[kind]:
        raise UnsupportedFile(f"That file type is not supported. Upload a {rule.label}.")

    key = f"{rule.folder}/{owner_id}/{uuid4().hex}.{ext}"
    path = _path_for(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    tmp.write_bytes(data)
    os.replace(tmp, path)  # a half-written file is never visible under its real name
    return StoredFile(key=key, content_type=CONTENT_TYPES[ext], size=len(data))


def _path_for(key: str) -> Path:
    """Disk path for a key. Refuses anything that is not a key this module could have made."""
    if not _SAFE_KEY.fullmatch(key):
        raise FileMissing("File not found.")
    root = storage_root()
    path = (root / key).resolve()
    if root not in path.parents:  # belt and braces against any path trick
        raise FileMissing("File not found.")
    return path


def locate(key: str) -> tuple[Path, str]:
    """Path and content type of a stored file. Raises FileMissing."""
    path = _path_for(key)
    if not path.is_file():
        raise FileMissing("File not found.")
    return path, CONTENT_TYPES[path.suffix.lstrip(".")]


def read_bytes(key: str) -> bytes:
    """For server-side use, such as sending the audio to transcription. No link needed."""
    return locate(key)[0].read_bytes()


def delete(key: Optional[str]) -> None:
    """Remove a file. Quietly does nothing for an empty or unknown key."""
    if not key:
        return
    try:
        _path_for(key).unlink(missing_ok=True)
    except StorageError:
        log.warning("Ignored delete of an invalid storage key")


# ---------- signed, expiring links ----------

_temporary_secret = secrets.token_bytes(32)
_warned = False


def _signing_key() -> bytes:
    global _warned
    secret = os.getenv("SECRET_KEY", "")
    if len(secret) >= 32:
        base = secret.encode()
    else:
        if not _warned:
            log.warning("SECRET_KEY is missing or shorter than 32 characters. File links use a temporary key, "
                        "so every link stops working when the server restarts.")
            _warned = True
        base = _temporary_secret
    return hmac.new(base, _SIGNING_PURPOSE, hashlib.sha256).digest()


def link_ttl_seconds() -> int:
    try:
        ttl = int(os.getenv("STORAGE_LINK_TTL_SECONDS", "").strip())
    except ValueError:
        return DEFAULT_TTL_SECONDS
    return max(MIN_TTL_SECONDS, min(ttl, MAX_TTL_SECONDS))


def _signature(key: str, expires: int) -> str:
    return hmac.new(_signing_key(), f"{key}\n{expires}".encode(), hashlib.sha256).hexdigest()


def signed_path(key: str, ttl: Optional[int] = None, now: Optional[float] = None) -> str:
    """A relative link, such as /files/posters/abc/0123.png?exp=...&sig=..., valid for `ttl` seconds."""
    _path_for(key)  # refuse to sign a key this module did not make
    seconds = link_ttl_seconds() if ttl is None else max(MIN_TTL_SECONDS, min(int(ttl), MAX_TTL_SECONDS))
    expires = int((time.time() if now is None else now) + seconds)
    return f"/files/{quote(key)}?exp={expires}&sig={_signature(key, expires)}"


def signed_url(key: str, ttl: Optional[int] = None, now: Optional[float] = None) -> str:
    """Like signed_path, with PUBLIC_API_URL in front when it is set (needed for email and SMS links)."""
    base = os.getenv("PUBLIC_API_URL", "").strip().rstrip("/")
    return base + signed_path(key, ttl, now)


def verify(key: str, exp: str, sig: str, now: Optional[float] = None) -> None:
    """Accept a link or raise. The signature is checked first, so a forged link learns nothing about expiry."""
    try:
        expires = int(exp)
    except (TypeError, ValueError):
        raise LinkInvalid("This link is not valid.") from None
    if not isinstance(sig, str) or not hmac.compare_digest(_signature(key, expires), sig):
        raise LinkInvalid("This link is not valid.")
    if (time.time() if now is None else now) >= expires:
        raise LinkExpired("This link has expired. Ask for a new one.")
