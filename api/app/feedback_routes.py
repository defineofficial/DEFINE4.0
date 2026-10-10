"""Post-event feedback. Add to main.py with:
    from . import feedback_routes
    app.include_router(feedback_routes.router)

Stored in memory (like the rest of the sample data) so it works in mock mode.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from . import mock_data as db
from .auth import current_organizer

router = APIRouter(tags=["Feedback"])
FEEDBACK: list[dict] = []


class FeedbackIn(BaseModel):
    rating: int = Field(ge=1, le=5, description="1 to 5 stars")
    comment: Optional[str] = Field(default=None, max_length=1000)


@router.post("/r/{token}/feedback")
def submit_feedback(token: str, body: FeedbackIn) -> dict:
    """Public. The personal link identifies the person, no login."""
    found = db.TOKENS.get(token)
    if not found:
        raise HTTPException(404, "Registration link not found")
    campaign_id, contact = found
    FEEDBACK[:] = [f for f in FEEDBACK if not (f["contact_id"] == contact.id and f["campaign_id"] == campaign_id)]
    FEEDBACK.append({"campaign_id": campaign_id, "contact_id": contact.id, "language": contact.language,
                     "rating": body.rating, "comment": body.comment})
    return {"ok": True}


@router.get("/campaigns/{campaign_id}/feedback")
def list_feedback(campaign_id: str, _org=Depends(current_organizer)) -> dict:
    items = [f for f in FEEDBACK if f["campaign_id"] == campaign_id]
    avg = round(sum(f["rating"] for f in items) / len(items), 2) if items else None
    return {"count": len(items), "average_rating": avg, "items": items}
