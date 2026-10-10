"""Outreach content generation, channel adapters, quiet hours, opt-out checking, and idempotent dispatch.

Handles Email, WhatsApp, SMS, and Instagram content generation from the approved event record.
Supports mock adapters for demo safety and real SMTP dispatch for Email.
"""
import email.message
import logging
import os
import re
import smtplib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.date_resolver import IST
from app import template_engine
from app.schemas import Channel, EventDetails, Language, OutreachItem, OutreachLog

log = logging.getLogger("eventreach.outreach")

# Quiet hours configuration (21:00 to 08:00 local time)
QUIET_HOURS_START = int(os.getenv("QUIET_HOURS_START", "21"))
QUIET_HOURS_END = int(os.getenv("QUIET_HOURS_END", "8"))

# In-memory stores for mock mode
_OUTREACH_ITEMS: Dict[str, List[OutreachItem]] = {}  # campaign_id -> items
_OUTREACH_LOGS: List[OutreachLog] = []
_SENT_KEYS: set[Tuple[str, str]] = set()  # (item_id, contact_id) -> idempotent dedupe

# WhatsApp template registry mapping (preset_key, language) -> pre-approved template_name
WHATSAPP_TEMPLATES: Dict[Tuple[str, Language], str] = {
    ("seminar_invite", Language.en): "seminar_invite_en_v1",
    ("seminar_invite", Language.hi): "seminar_invite_hi_v1",
    ("seminar_invite", Language.ml): "seminar_invite_ml_v1",
    ("seminar_invite", Language.ta): "seminar_invite_ta_v1",
    ("clinic_reminder", Language.en): "clinic_reminder_en_v1",
    ("clinic_reminder", Language.hi): "clinic_reminder_hi_v1",
    ("school_notice", Language.en): "school_notice_en_v1",
    ("payment_reminder", Language.en): "payment_reminder_en_v1",
}


# ---------- 1. Safety Checks: Quiet Hours & Opt-Out ----------

def is_quiet_hours(check_dt: Optional[datetime] = None) -> bool:
    """Returns True if check_dt (in IST timezone) falls within quiet hours (21:00 to 08:00)."""
    if check_dt is None:
        check_dt = datetime.now(IST)
    elif check_dt.tzinfo is None:
        check_dt = check_dt.replace(tzinfo=IST)

    hour = check_dt.hour
    if QUIET_HOURS_START > QUIET_HOURS_END:
        return hour >= QUIET_HOURS_START or hour < QUIET_HOURS_END
    return QUIET_HOURS_START <= hour < QUIET_HOURS_END


def calculate_sms_segments(text: str) -> Tuple[int, str]:
    """Calculates SMS segment count and encoding type (GSM-7 vs Unicode)."""
    # Check if text contains characters outside GSM-7 charset
    is_unicode = any(ord(char) > 127 for char in text)
    length = len(text)

    if not is_unicode:
        if length <= 160:
            return 1, "GSM-7"
        return (length + 152) // 153, "GSM-7"
    else:
        if length <= 70:
            return 1, "Unicode"
        return (length + 66) // 67, "Unicode"


# ---------- 2. Content Generation ----------

def generate_campaign_content(
    campaign_id: str,
    template_key: str,
    event: EventDetails,
    languages: List[Language],
    channels: List[Channel],
    poster_url: Optional[str] = None,
    event_version: int = 1,
) -> List[OutreachItem]:
    """Generates OutreachItem records for each (channel, language) pair from approved event details."""
    items: List[OutreachItem] = []

    date_formatted = event.starts_at.strftime("%d %B %Y at %I:%M %p")

    for lang in languages:
        for ch in channels:
            if ch == Channel.call:
                continue  # Call channel handled separately by call dispatcher

            # Variables for template interpolation
            vars_dict = {
                "name": "{name}",
                "event_title": event.title,
                "date": event.starts_at.strftime("%d %B %Y"),
                "time": event.starts_at.strftime("%I:%M %p"),
                "venue": event.venue,
                "city": event.city,
                "link": "{link}",
                "doctor": "Dr. Smith",
                "clinic_name": event.venue,
                "parent_name": "{name}",
                "student_name": "Student",
                "notice": event.title,
                "amount_inr": event.fee_inr,
                "due_date": event.starts_at.strftime("%d %B %Y"),
                "purpose": event.title,
            }

            rendered = template_engine.render_message(template_key, lang, ch, vars_dict)
            item_id = str(uuid.uuid4())

            if ch == Channel.email:
                subject = rendered.get("subject", f"Invitation: {event.title}")
                body = rendered.get("body", f"Dear {{name}},\n\nYou are invited to {event.title} on {date_formatted} at {event.venue}, {event.city}.\n\nRegister here: {{link}}\n\nReply STOP to unsubscribe.")
                if "Reply STOP" not in body and "unsubscribe" not in body:
                    body += "\n\nReply STOP to unsubscribe."
                
                item = OutreachItem(
                    id=item_id,
                    campaign_id=campaign_id,
                    channel=Channel.email,
                    language=lang,
                    subject=subject,
                    body=body,
                    media_url=poster_url,
                    event_version=event_version,
                    status="draft",
                    approved=False,
                )
            elif ch == Channel.whatsapp:
                tpl_name = WHATSAPP_TEMPLATES.get((template_key, lang), f"{template_key}_{lang.value}_v1")
                body = rendered.get("body", f"Hi {{name}}, you are invited to {event.title} on {date_formatted} at {event.venue}, {event.city}. Link: {{link}}")
                if "STOP" not in body:
                    body += "\n\nReply STOP to opt out."
                
                item = OutreachItem(
                    id=item_id,
                    campaign_id=campaign_id,
                    channel=Channel.whatsapp,
                    language=lang,
                    body=body,
                    whatsapp_template_name=tpl_name,
                    media_url=poster_url,
                    event_version=event_version,
                    status="draft",
                    approved=False,
                )
            elif ch == Channel.sms:
                body = rendered.get("body", f"Hi {{name}}, you're invited to {event.title} on {date_formatted} at {event.venue}. Register: {{link}} Reply STOP to opt out.")
                if "STOP" not in body:
                    body += " Reply STOP to opt out."
                
                seg_count, _ = calculate_sms_segments(body)
                item = OutreachItem(
                    id=item_id,
                    campaign_id=campaign_id,
                    channel=Channel.sms,
                    language=lang,
                    body=body,
                    event_version=event_version,
                    status="draft",
                    approved=False,
                    segment_count=seg_count,
                )
            elif ch == Channel.instagram:
                caption = rendered.get("caption", f"{event.title}! Join us on {date_formatted} at {event.venue}, {event.city}. Link in bio.")
                hashtags = ["#EventReach", "#KochiEvents", f"#{event.city}", "#Seminar", "#CommunityEvent"]
                
                item = OutreachItem(
                    id=item_id,
                    campaign_id=campaign_id,
                    channel=Channel.instagram,
                    language=lang,
                    body=caption,
                    hashtags=hashtags,
                    media_url=poster_url,
                    event_version=event_version,
                    status="draft",
                    approved=False,
                )
            else:
                continue

            items.append(item)

    _OUTREACH_ITEMS[campaign_id] = items
    return items


def list_campaign_content(campaign_id: str) -> List[OutreachItem]:
    """Returns generated outreach content items for campaign."""
    return _OUTREACH_ITEMS.get(campaign_id, [])


def update_content_item(campaign_id: str, item_id: str, updated_item: OutreachItem) -> OutreachItem:
    """Updates or approves an outreach content item."""
    items = _OUTREACH_ITEMS.setdefault(campaign_id, [])
    for i, item in enumerate(items):
        if item.id == item_id:
            items[i] = updated_item
            return updated_item
    items.append(updated_item)
    return updated_item


# ---------- 3. Channel Sending & Test Send ----------

def send_test_message(
    channel: Channel,
    target: str,
    subject: str = "Test Message",
    body: str = "This is a test message from EventReach.",
    poster_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Dispatches a test send to organizer's own email/phone/account."""
    if channel == Channel.email:
        return _dispatch_smtp_email(target, subject, body, poster_url)
    elif channel == Channel.whatsapp:
        return {
            "channel": "whatsapp",
            "target": target,
            "body": body,
            "status": "mock_sent",
            "message": "Mock WhatsApp test sent successfully.",
        }
    elif channel == Channel.sms:
        return {
            "channel": "sms",
            "target": target,
            "body": body,
            "status": "mock_sent",
            "message": "Mock SMS test sent successfully.",
        }
    elif channel == Channel.instagram:
        return {
            "channel": "instagram",
            "target": target,
            "caption": body,
            "status": "mock_preview",
            "manual_download_url": poster_url,
            "copyable_caption": body,
            "message": "Instagram manual post preview ready.",
        }
    return {"status": "error", "message": f"Unsupported channel {channel}"}


def dispatch_item_to_recipient(
    item: OutreachItem,
    contact_id: str,
    recipient_email_or_phone: str = "",
    phone_hash: Optional[str] = None,
    opted_out_hashes: Optional[set[str]] = None,
    recipient_masked: Optional[str] = None,
    current_time: Optional[datetime] = None,
) -> OutreachLog:
    """Idempotent dispatch of an OutreachItem to a recipient."""
    rec_target = recipient_masked or recipient_email_or_phone
    key = (item.id, contact_id)
    if key in _SENT_KEYS:
        return OutreachLog(
            id=str(uuid.uuid4()),
            item_id=item.id,
            contact_id=contact_id,
            channel=item.channel,
            recipient_masked=rec_target,
            status="skipped_duplicate",
        )

    # Opt-out check
    if phone_hash and opted_out_hashes and phone_hash in opted_out_hashes:
        log_entry = OutreachLog(
            id=str(uuid.uuid4()),
            item_id=item.id,
            contact_id=contact_id,
            channel=item.channel,
            recipient_masked=rec_target,
            status="skipped_opted_out",
        )
        _OUTREACH_LOGS.append(log_entry)
        return log_entry

    # Quiet hours check
    if is_quiet_hours(check_dt=current_time):
        log_entry = OutreachLog(
            id=str(uuid.uuid4()),
            item_id=item.id,
            contact_id=contact_id,
            channel=item.channel,
            recipient_masked=rec_target,
            status="skipped_quiet_hours",
        )
        _OUTREACH_LOGS.append(log_entry)
        return log_entry

    # Dispatch
    if item.channel == Channel.email:
        res = _dispatch_smtp_email(
            to_email=recipient_email_or_phone,
            subject=item.subject or "Event Invitation",
            body=item.body,
            poster_url=item.media_url,
        )
        status_val = res.get("status", "mocked")
    else:
        status_val = "mocked"

    _SENT_KEYS.add(key)
    log_entry = OutreachLog(
        id=str(uuid.uuid4()),
        item_id=item.id,
        contact_id=contact_id,
        channel=item.channel,
        recipient_masked=recipient_email_or_phone,
        status=status_val,
    )
    _OUTREACH_LOGS.append(log_entry)
    return log_entry


def _dispatch_smtp_email(
    to_email: str,
    subject: str,
    body: str,
    poster_url: Optional[str] = None,
) -> Dict[str, Any]:
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_pass = os.getenv("SMTP_PASSWORD", "").strip()
    email_from = os.getenv("EMAIL_FROM", "events@eventreach.local")
    mock_mode = os.getenv("MOCK_CHANNELS", "true").lower() in ("1", "true", "yes")

    payload = {
        "channel": "email",
        "to": to_email,
        "from": email_from,
        "subject": subject,
        "body": body,
        "poster_url": poster_url,
    }

    if not smtp_host or mock_mode:
        payload["status"] = "mocked"
        log.info("Mock Email to %s: %s", to_email, subject)
        return payload

    msg = email.message.EmailMessage()
    msg["Subject"] = subject
    msg["From"] = email_from
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls()
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        payload["status"] = "sent"
        log.info("Real SMTP email sent to %s", to_email)
        return payload
    except Exception as exc:
        log.error("Failed to send real SMTP email to %s: %s", to_email, exc)
        payload["status"] = "failed"
        payload["error"] = str(exc)
        return payload
