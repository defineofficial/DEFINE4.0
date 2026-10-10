"""Helpers for handling phone numbers and personal data with privacy by design.

Principles:
1. Phone numbers are encrypted at rest using AES-128-CBC/HMAC (Fernet) via `ENCRYPTION_KEY`.
2. Phone numbers are hashed using a salted HMAC-SHA256 (`PHONE_HASH_PEPPER`) for deduplication and opt-out indexing without storing plaintext.
3. The API never returns full phone numbers; only masked forms (e.g. +91 90••• ••013).
"""
import base64
import hashlib
import hmac
import os
import re
from typing import Optional
from cryptography.fernet import Fernet

_DEFAULT_DEV_PEPPER = "dev-only-pepper-change-me"
_PEPPER = os.getenv("PHONE_HASH_PEPPER", _DEFAULT_DEV_PEPPER).strip().encode() or _DEFAULT_DEV_PEPPER.encode()


def _get_fernet() -> Fernet:
    raw_key = os.getenv("ENCRYPTION_KEY", "").strip()
    if raw_key:
        try:
            return Fernet(raw_key.encode())
        except Exception:
            # Fallback to key derived from raw string
            key_32 = hashlib.sha256(raw_key.encode()).digest()
            b64_key = base64.urlsafe_b64encode(key_32)
            return Fernet(b64_key)
    # Fallback to key derived from SECRET_KEY or dev secret
    secret = os.getenv("SECRET_KEY", "dev-secret-change-me-32-chars-long-minimum").encode()
    key_32 = hashlib.sha256(secret).digest()
    b64_key = base64.urlsafe_b64encode(key_32)
    return Fernet(b64_key)


def encrypt_phone(e164: str) -> bytes:
    """Encrypts an E.164 phone number at rest for database storage."""
    return _get_fernet().encrypt(e164.encode("utf-8"))


def decrypt_phone(phone_enc: bytes) -> str:
    """Decrypts stored ciphertext back to E.164 string."""
    return _get_fernet().decrypt(phone_enc).decode("utf-8")


def phone_hash(e164: str) -> str:
    """Stable salted hash of an E.164 phone number (for deduplication and opt-out matching)."""
    return hmac.new(_PEPPER, e164.encode("utf-8"), hashlib.sha256).hexdigest()


def mask_phone(e164: str) -> str:
    """Show only the country code, two digits and the last three digits."""
    if len(e164) < 7:
        return e164
    return f"{e164[:3]} {e164[3:5]}••• ••{e164[-3:]}"
