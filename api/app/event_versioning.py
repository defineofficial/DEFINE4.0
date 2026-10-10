"""Event record versioning, content hashing, and staleness propagation.

Ensures that whenever an organizer edits event details (title, dates, venue, fee),
all dependent translations and generated content are marked `stale` and launch is blocked
until regenerated.
"""
import hashlib
import json
from typing import List, Tuple, Optional, Any

from app.schemas import EventDetails, Translation


def compute_event_hash(event: EventDetails) -> str:
    """Computes a SHA-256 content hash over meaningful event record fields."""
    payload = {
        "title": event.title.strip(),
        "starts_at": event.starts_at.isoformat(),
        "ends_at": event.ends_at.isoformat() if event.ends_at else None,
        "venue": event.venue.strip(),
        "city": event.city.strip(),
        "fee_inr": event.fee_inr,
        "capacity": event.capacity,
        "description": (event.description or "").strip(),
    }
    raw = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def update_event_record(
    existing_event: Optional[EventDetails],
    existing_version: int,
    existing_hash: Optional[str],
    new_event: EventDetails,
) -> Tuple[int, str, bool]:
    """Updates event record version and hash.
    
    Returns (new_version, new_hash, is_changed).
    """
    new_hash = compute_event_hash(new_event)
    
    if existing_event is None or existing_hash is None:
        return 1, new_hash, True

    if existing_hash != new_hash:
        return existing_version + 1, new_hash, True

    return existing_version, existing_hash, False


def propagate_staleness(
    translations: List[Translation],
    new_version: int,
    new_hash: str,
) -> Tuple[List[Translation], bool]:
    """Marks any translation with an outdated event_version or content_hash as `stale`.
    
    Returns (updated_translations, any_marked_stale).
    """
    updated: List[Translation] = []
    any_stale = False

    for t in translations:
        # If event version or hash differs, mark stale
        if getattr(t, "event_version", 1) < new_version or getattr(t, "event_content_hash", None) != new_hash:
            t_dict = t.model_dump()
            t_dict["approved"] = False
            t_dict["status"] = "stale"
            t_dict["event_version"] = new_version
            t_dict["event_content_hash"] = new_hash
            updated.append(Translation(**t_dict))
            any_stale = True
        else:
            updated.append(t)

    return updated, any_stale
