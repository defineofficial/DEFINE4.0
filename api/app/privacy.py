"""Helpers for handling phone numbers as personal data.

The API never returns a full phone number. Two derived forms are used instead:
- a masked form for display, like +91 90••• ••013
- a salted hash for finding duplicates and opt-outs without keeping the number readable

Set PHONE_HASH_PEPPER in .env. The default below is for local development only.
"""
import hashlib
import hmac
import os

_PEPPER = os.getenv("PHONE_HASH_PEPPER", "dev-only-pepper-change-me").encode()


def phone_hash(e164: str) -> str:
    """Stable salted hash of a phone number in E.164 form (for example +919000000013)."""
    return hmac.new(_PEPPER, e164.encode(), hashlib.sha256).hexdigest()


def mask_phone(e164: str) -> str:
    """Show only the country code, two digits and the last three digits."""
    return f"{e164[:3]} {e164[3:5]}••• ••{e164[-3:]}"
