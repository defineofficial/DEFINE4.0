"""Sending email. One function to send, one to build the invitation, no other dependencies.

Real sending needs SMTP_HOST, SMTP_USER, SMTP_PASSWORD, EMAIL_FROM in .env and MOCK_CHANNELS=false.
Otherwise every email is only recorded in OUTBOX (status "mocked") so the demo never breaks.

Gmail: turn on 2-step verification, create an "App password", then
  SMTP_HOST=smtp.gmail.com  SMTP_PORT=587  SMTP_USER=you@gmail.com
  SMTP_PASSWORD=<the 16 character app password>  EMAIL_FROM=you@gmail.com
"""
import logging
import os
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import formataddr
from html import escape

log = logging.getLogger("eventreach.mailer")
IST = timezone(timedelta(hours=5, minutes=30))
OUTBOX: list[dict] = []          # what was (or would have been) sent, newest last


def _cfg():
    return {
        "host": os.getenv("SMTP_HOST", "").strip(),
        "port": int(os.getenv("SMTP_PORT", "587") or 587),
        "user": os.getenv("SMTP_USER", "").strip(),
        "password": os.getenv("SMTP_PASSWORD", ""),
        "sender": os.getenv("EMAIL_FROM", "").strip() or os.getenv("SMTP_USER", "").strip(),
        "mock": os.getenv("MOCK_CHANNELS", "true").strip().lower() != "false",
    }


def is_live() -> bool:
    c = _cfg()
    return bool(c["host"] and c["sender"] and not c["mock"])


def send_email(to: str, subject: str, text: str, html: str | None = None,
               attachments: list[tuple[str, bytes, str]] | None = None) -> dict:
    """Send one email. Returns {"status": "sent"|"mocked"|"failed", "error": str|None}. Never raises."""
    record = {"to": to, "subject": subject, "text": text, "html": html,
              "at": datetime.now(IST).isoformat(timespec="seconds"), "status": "mocked", "error": None}
    c = _cfg()
    try:
        if "@" not in (to or "") or " " in to:
            raise ValueError("That is not an email address")
        if not is_live():
            OUTBOX.append(record)
            return {"status": "mocked", "error": None}
        msg = EmailMessage()
        msg["Subject"], msg["To"] = subject, to
        msg["From"] = formataddr(("EventReach", c["sender"]))
        msg.set_content(text)
        if html:
            msg.add_alternative(html, subtype="html")
        for name, data, mime in attachments or []:
            main, _, sub = mime.partition("/")
            msg.add_attachment(data, maintype=main, subtype=sub or "octet-stream", filename=name)
        with smtplib.SMTP(c["host"], c["port"], timeout=20) as s:
            s.starttls()
            if c["user"]:
                s.login(c["user"], c["password"])
            s.send_message(msg)
        record["status"] = "sent"
    except Exception as exc:                                    # report, do not crash the request
        record["status"], record["error"] = "failed", " ".join(str(exc).split())[:200]
        log.warning("email to %s failed: %s", to[:3] + "***", record["error"])
    OUTBOX.append(record)
    return {"status": record["status"], "error": record["error"]}


# Short wrapper lines. Facts (title, date, venue, fee) are inserted by code, never translated.
# Have a native speaker check these before a real send.
_WORDS = {
    "en": dict(hi="Hello {name},", invite="You are invited to", when="When", where="Where", fee="Fee",
               free="Free", reg="Register here", stop="If you do not want these emails, reply STOP."),
    "hi": dict(hi="नमस्ते {name},", invite="आपको आमंत्रित किया जाता है:", when="कब", where="कहाँ", fee="शुल्क",
               free="निःशुल्क", reg="यहाँ पंजीकरण करें", stop="ये ईमेल न चाहिए हों तो STOP लिखकर उत्तर दें।"),
    "ml": dict(hi="നമസ്കാരം {name},", invite="നിങ്ങളെ ക്ഷണിക്കുന്നു:", when="എപ്പോൾ", where="എവിടെ", fee="ഫീസ്",
               free="സൗജന്യം", reg="ഇവിടെ രജിസ്റ്റർ ചെയ്യുക", stop="ഈ ഇമെയിലുകൾ വേണ്ടെങ്കിൽ STOP എന്ന് മറുപടി നൽകുക."),
    "ta": dict(hi="வணக்கம் {name},", invite="உங்களை அழைக்கிறோம்:", when="எப்போது", where="எங்கே", fee="கட்டணம்",
               free="இலவசம்", reg="இங்கே பதிவு செய்யுங்கள்", stop="இந்த மின்னஞ்சல்கள் வேண்டாம் என்றால் STOP என பதிலளிக்கவும்."),
}


def _when(starts_at, ends_at=None) -> str:
    s = starts_at.astimezone(IST)
    out = s.strftime("%A, %d %B %Y, %I:%M %p IST")
    if ends_at:
        out += " to " + ends_at.astimezone(IST).strftime("%I:%M %p")
    return out


def build_invitation(*, name: str, language: str, title: str, starts_at, ends_at=None, venue: str,
                     city: str, fee_inr: int = 0, link: str, description: str | None = None) -> dict:
    """Returns {"subject", "text", "html"}. All facts come from the arguments, wording from _WORDS."""
    w = _WORDS.get(language, _WORDS["en"])
    when = _when(starts_at, ends_at)
    where = f"{venue}, {city}"
    fee = w["free"] if not fee_inr else f"Rs {fee_inr}"
    subject = f"{title} - {starts_at.astimezone(IST).strftime('%d %b %Y')}"
    hi = w["hi"].format(name=name)
    lines = [hi, "", f"{w['invite']} {title}", ""]
    if description:
        lines += [description, ""]
    lines += [f"{w['when']}: {when}", f"{w['where']}: {where}", f"{w['fee']}: {fee}", "",
              f"{w['reg']}: {link}", "", w["stop"]]
    text = "\n".join(lines)
    e = escape
    html = (f"<div style='font-family:Arial,sans-serif;max-width:560px;margin:auto;line-height:1.5'>"
            f"<p>{e(hi)}</p><h2 style='margin:8px 0'>{e(title)}</h2>"
            + (f"<p>{e(description)}</p>" if description else "") +
            f"<p><b>{e(w['when'])}:</b> {e(when)}<br><b>{e(w['where'])}:</b> {e(where)}<br>"
            f"<b>{e(w['fee'])}:</b> {e(fee)}</p>"
            f"<p><a href='{e(link, quote=True)}' style='background:#1a56db;color:#fff;padding:10px 18px;"
            f"border-radius:6px;text-decoration:none;display:inline-block'>{e(w['reg'])}</a></p>"
            f"<p style='color:#666;font-size:12px'>{e(w['stop'])}</p></div>")
    return {"subject": subject, "text": text, "html": html}


def build_confirmation(*, name: str, title: str, starts_at, venue: str, city: str,
                       amount_inr: int = 0, paid: bool = False) -> dict:
    when = _when(starts_at)
    status = ("Payment received: Rs %d." % amount_inr) if paid else (
        ("Please complete your payment of Rs %d to confirm your seat." % amount_inr) if amount_inr else "No payment is needed.")
    text = f"Hello {name},\n\nYou are registered for {title}.\nWhen: {when}\nWhere: {venue}, {city}\n{status}\n"
    e = escape
    html = (f"<div style='font-family:Arial,sans-serif;max-width:560px;margin:auto'><p>Hello {e(name)},</p>"
            f"<p>You are registered for <b>{e(title)}</b>.</p><p>When: {e(when)}<br>Where: {e(venue)}, {e(city)}</p>"
            f"<p>{e(status)}</p></div>")
    return {"subject": f"Registration confirmed: {title}", "text": text, "html": html}
