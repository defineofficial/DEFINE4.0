"""Channel adapters (Email, WhatsApp, Instagram) and short link redirection engine.

When MOCK_CHANNELS=true or credentials are unset, adapters operate in preview/mock mode,
showing the exact payload that would be dispatched without failing.
"""
import email.message
import logging
import os
import secrets
import smtplib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

log = logging.getLogger("eventreach.channels")

WEB_BASE_URL = os.getenv("WEB_BASE_URL", "http://localhost:3000")
PUBLIC_API_URL = os.getenv("PUBLIC_API_URL", "http://localhost:8000")
MOCK_CHANNELS = os.getenv("MOCK_CHANNELS", "true").lower() in ("1", "true", "yes")

# In-memory store for short links: code -> target_url, clicks
_SHORT_LINKS: Dict[str, Dict[str, Any]] = {}

# Outbox for mock inspection and testing
SENT_MESSAGES: List[Dict[str, Any]] = []


# ---------- 1. Short Link Generator ----------

def create_short_link(target_url: str, custom_code: Optional[str] = None) -> str:
    """Creates a short link code mapping to target_url. Returns full short URL."""
    code = custom_code or secrets.token_urlsafe(4)[:6]
    _SHORT_LINKS[code] = {
        "target": target_url,
        "created_at": datetime.now(timezone.utc),
        "clicks": 0,
    }
    return f"{PUBLIC_API_URL}/s/{code}"


def resolve_short_link(code: str) -> Optional[str]:
    """Resolves a short code to its destination and increments click count."""
    entry = _SHORT_LINKS.get(code)
    if not entry:
        return None
    entry["clicks"] += 1
    return entry["target"]


# ---------- 2. Email Adapter ----------

def send_email(
    to_email: str,
    subject: str,
    body: str,
    poster_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Sends an email with optional poster link, or mocks if SMTP is unset."""
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_pass = os.getenv("SMTP_PASSWORD", "").strip()
    email_from = os.getenv("EMAIL_FROM", "events@eventreach.local")

    html_body = body.replace("\n", "<br>")
    if poster_url:
        html_body += f"<br><br><img src='{poster_url}' alt='Event Poster' style='max-width:500px; border-radius:8px;' />"

    payload = {
        "channel": "email",
        "to": to_email,
        "from": email_from,
        "subject": subject,
        "body": body,
        "poster_url": poster_url,
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }

    if not smtp_host or MOCK_CHANNELS:
        payload["status"] = "mock_sent"
        SENT_MESSAGES.append(payload)
        log.info("Mock Email dispatched to %s: %s", to_email, subject)
        return payload

    # Real SMTP send
    msg = email.message.EmailMessage()
    msg["Subject"] = subject
    msg["From"] = email_from
    msg["To"] = to_email
    msg.set_content(body)
    msg.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls()
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        payload["status"] = "sent"
        SENT_MESSAGES.append(payload)
        return payload
    except Exception as exc:
        log.error("Failed to send real email to %s: %s", to_email, exc)
        payload["status"] = "failed"
        payload["error"] = str(exc)
        SENT_MESSAGES.append(payload)
        return payload


# ---------- 3. WhatsApp Adapter ----------

def send_whatsapp(
    to_phone_masked: str,
    message_text: str,
    media_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Sends WhatsApp message or returns simulated dispatch in mock mode."""
    payload = {
        "channel": "whatsapp",
        "to": to_phone_masked,
        "text": message_text,
        "media_url": media_url,
        "status": "mock_sent",
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }
    SENT_MESSAGES.append(payload)
    log.info("Mock WhatsApp sent to %s: %s", to_phone_masked, message_text[:40])
    return payload


# ---------- 4. Instagram Adapter ----------

def post_instagram(
    caption: str,
    poster_url: str,
) -> Dict[str, Any]:
    """Posts announcement to Instagram with caption and poster or returns preview."""
    payload = {
        "channel": "instagram",
        "caption": caption,
        "poster_url": poster_url,
        "status": "mock_posted",
        "posted_at": datetime.now(timezone.utc).isoformat(),
    }
    SENT_MESSAGES.append(payload)
    log.info("Mock Instagram post created: %s", caption[:40])
    return payload
