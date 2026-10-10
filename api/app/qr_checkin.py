"""QR Ticket generation and venue check-in verification for EventReach.

Provides:
- Check-in scanner endpoint logic: marks contact as Attended.
- QR / Ticket identification payload generation.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from app.schemas import Contact, Stage


def process_checkin(contact: Contact) -> Dict[str, Any]:
    """Marks attendee as Attended on check-in scan. Idempotent if already checked in."""
    was_already = (contact.stage == Stage.attended)
    contact.stage = Stage.attended
    return {
        "status": "already_checked_in" if was_already else "checked_in",
        "contact_id": contact.id,
        "name": contact.name,
        "stage": contact.stage.value,
        "checked_in_at": datetime.now(timezone.utc).isoformat(),
    }


def generate_ticket_svg(token: str, attendee_name: str, event_title: str) -> str:
    """Generates an SVG admission ticket with stylized QR/code representation."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 200" width="400" height="200">
  <rect width="400" height="200" rx="12" fill="#12313a"/>
  <rect x="15" y="15" width="370" height="170" rx="8" fill="none" stroke="#7fd1c0" stroke-width="2" stroke-dasharray="6,4"/>
  <text x="30" y="55" fill="#7fd1c0" font-family="sans-serif" font-size="14" font-weight="bold">EVENTPASS · ADMIT ONE</text>
  <text x="30" y="85" fill="#ffffff" font-family="sans-serif" font-size="20" font-weight="bold">{event_title[:28]}</text>
  <text x="30" y="115" fill="#e0e0e0" font-family="sans-serif" font-size="16">{attendee_name}</text>
  <text x="30" y="155" fill="#9fb8bd" font-family="monospace" font-size="12">TOKEN: {token}</text>
  <!-- Stylized QR Placeholder box -->
  <rect x="290" y="45" width="80" height="80" fill="#ffffff" rx="4"/>
  <rect x="300" y="55" width="25" height="25" fill="#12313a"/>
  <rect x="335" y="55" width="25" height="25" fill="#12313a"/>
  <rect x="300" y="90" width="25" height="25" fill="#12313a"/>
  <rect x="335" y="90" width="25" height="25" fill="#7fd1c0"/>
</svg>"""
