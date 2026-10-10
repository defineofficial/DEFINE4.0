"""Email endpoints. Add to main.py with:   from . import email_routes ; app.include_router(email_routes.router)

campaign_contacts() is the ONE place that reads campaigns and contacts. It uses the sample data today.
When campaigns move to the database, change only that function.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from . import mailer
from . import mock_data as db
from .auth import current_organizer

router = APIRouter(tags=["Email"])


def campaign_contacts(campaign_id: str):
    """Return (campaign, contacts). Raise 404 if the campaign is not found. Swap for a database query later."""
    camp = db.CAMPAIGNS.get(campaign_id)
    if not camp:
        raise HTTPException(404, "Campaign not found")
    return camp, db.CONTACTS.get(campaign_id, [])


def _invite(camp, contact):
    ev = camp.event
    return mailer.build_invitation(
        name=contact.name.split()[0], language=contact.language, title=ev.title, starts_at=ev.starts_at,
        ends_at=ev.ends_at, venue=ev.venue, city=ev.city, fee_inr=ev.fee_inr,
        link=contact.registration_link, description=ev.description)


class TestEmail(BaseModel):
    to: str
    language: str = "en"


class SendEmails(BaseModel):
    stages: list[str] = Field(default=["invited", "responded"], description="Only people at these stages")
    limit: int = Field(default=500, ge=1, le=2000)


@router.post("/campaigns/{campaign_id}/email/test")
def email_test(campaign_id: str, body: TestEmail, _org=Depends(current_organizer)) -> dict:
    camp, contacts = campaign_contacts(campaign_id)
    if not camp.event:
        raise HTTPException(400, "Save the event details first")
    sample = contacts[0] if contacts else None
    class _C:  # a stand-in so a test works even with an empty audience
        name, language, registration_link = "Test", body.language, "http://localhost:3000/r/test"
    msg = _invite(camp, sample or _C)
    res = mailer.send_email(body.to, "[TEST] " + msg["subject"], msg["text"], msg["html"])
    return {**res, "live": mailer.is_live()}


@router.post("/campaigns/{campaign_id}/email/send")
def email_send(campaign_id: str, body: SendEmails | None = None, _org=Depends(current_organizer)) -> dict:
    body = body or SendEmails()
    camp, contacts = campaign_contacts(campaign_id)
    if not camp.event:
        raise HTTPException(400, "Save the event details first")
    out = {"sent": 0, "mocked": 0, "failed": 0, "skipped_no_email": 0, "skipped_opted_out": 0,
           "skipped_stage": 0, "live": mailer.is_live(), "errors": []}
    done = 0
    for c in contacts:
        if c.opted_out:
            out["skipped_opted_out"] += 1; continue
        if not c.email:
            out["skipped_no_email"] += 1; continue
        if c.stage.value not in body.stages:
            out["skipped_stage"] += 1; continue
        if done >= body.limit:
            break
        msg = _invite(camp, c)
        r = mailer.send_email(c.email, msg["subject"], msg["text"], msg["html"])
        out[r["status"]] += 1
        if r["error"] and len(out["errors"]) < 5:
            out["errors"].append(r["error"])
        done += 1
    return out


@router.get("/campaigns/{campaign_id}/email/outbox")
def email_outbox(campaign_id: str, limit: int = 50, _org=Depends(current_organizer)) -> dict:
    """What was sent or would have been sent. Handy for showing the demo without a real mailbox."""
    campaign_contacts(campaign_id)
    return {"live": mailer.is_live(), "items": [
        {k: v for k, v in m.items() if k != "html"} for m in mailer.OUTBOX[-limit:]][::-1]}
