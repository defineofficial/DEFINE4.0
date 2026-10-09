"""Calendar invite (.ics) generator and Google Calendar URL builder for EventReach."""
from datetime import datetime, timezone
from urllib.parse import quote
from typing import Optional
from app.schemas import EventDetails


def format_ics_datetime(dt: datetime) -> str:
    """Formats datetime to UTC iCalendar format YYYYMMDDTHHMMSSZ."""
    utc_dt = dt.astimezone(timezone.utc)
    return utc_dt.strftime("%Y%m%dT%H%M%SZ")


def generate_ics(event: EventDetails, attendee_name: Optional[str] = None) -> str:
    """Generates standard RFC 5545 iCalendar (.ics) content."""
    start_str = format_ics_datetime(event.starts_at)
    end_dt = event.ends_at or event.starts_at
    end_str = format_ics_datetime(end_dt)
    now_str = format_ics_datetime(datetime.now(timezone.utc))

    summary = event.title
    location = f"{event.venue}, {event.city}"
    description = event.description or f"Admission for {event.title} at {location}."

    ics_content = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//EventReach//Multilingual Outreach//EN\r\n"
        "CALSCALE:GREGORIAN\r\n"
        "METHOD:PUBLISH\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:eventreach-{event.starts_at.timestamp()}@eventreach.local\r\n"
        f"DTSTAMP:{now_str}\r\n"
        f"DTSTART:{start_str}\r\n"
        f"DTEND:{end_str}\r\n"
        f"SUMMARY:{summary}\r\n"
        f"DESCRIPTION:{description}\r\n"
        f"LOCATION:{location}\r\n"
        "STATUS:CONFIRMED\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )
    return ics_content


def generate_google_calendar_url(event: EventDetails) -> str:
    """Generates one-tap Google Calendar add URL."""
    start_str = format_ics_datetime(event.starts_at)
    end_dt = event.ends_at or event.starts_at
    end_str = format_ics_datetime(end_dt)
    
    title = quote(event.title)
    location = quote(f"{event.venue}, {event.city}")
    details = quote(event.description or f"Join us for {event.title} in {event.city}.")

    return (
        f"https://calendar.google.com/calendar/render?action=TEMPLATE"
        f"&text={title}"
        f"&dates={start_str}/{end_str}"
        f"&details={details}"
        f"&location={location}"
    )
