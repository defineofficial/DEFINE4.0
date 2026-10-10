"""Preflight check engine and launch gate.

Verifies every requirement before a campaign can be launched, blocking launch
if any blocker is present and reporting helpful warnings.
"""
from typing import List, Optional

from app import outreach
from app.date_resolver import IST
from app.outreach import is_quiet_hours
from app.schemas import Campaign, Channel, Language, PreflightResult, Translation


def run_preflight_checks(
    campaign: Campaign,
    translations: List[Translation],
    contact_count: int,
) -> PreflightResult:
    """Evaluates campaign against launch criteria.
    
    Returns PreflightResult with blockers and warnings lists.
    """
    blockers: List[str] = []
    warnings: List[str] = []

    # 1. Check Event Record
    if not campaign.event:
        blockers.append("No approved event record")
    else:
        ev = campaign.event
        if not ev.title or not ev.title.strip():
            blockers.append("Event title is missing")
        if not ev.starts_at:
            blockers.append("Event start date/time is missing")
        if not ev.venue or not ev.venue.strip():
            blockers.append("Event venue is missing")
        if not ev.city or not ev.city.strip():
            blockers.append("Event city is missing")

    # 2. Check Audience
    if contact_count <= 0:
        blockers.append("Audience list is empty")

    # 3. Check Translations
    required_langs = set(campaign.languages) if campaign.languages else {Language.en}
    approved_langs = {t.language for t in translations if t.approved}

    for lang in required_langs:
        if lang not in approved_langs:
            blockers.append(f"Language '{lang.value}' has no approved translation")

    for t in translations:
        if t.status == "stale":
            blockers.append(f"Translation for '{t.language.value}' is stale and needs regeneration")
        if t.fact_check and not t.fact_check.get("passed", True):
            blockers.append(f"Translation for '{t.language.value}' failed automatic fact check")

    # 4. Check Content Items
    content_items = outreach.list_campaign_content(campaign.id)
    selected_channels = set(campaign.channels) if campaign.channels else {Channel.call}

    for ch in selected_channels:
        if ch == Channel.call:
            warnings.append("Call channel is not configured (Section 10 empty slot)")
            continue
        
        # Check if non-call channel has approved content
        ch_items = [it for it in content_items if it.channel == ch]
        if not ch_items:
            blockers.append(f"Selected channel '{ch.value}' has no generated content")
        elif not any(it.approved for it in ch_items):
            blockers.append(f"Selected channel '{ch.value}' content is not approved")

    # 5. Check Quiet Hours
    if is_quiet_hours():
        blockers.append("Current time is inside quiet hours (21:00 to 08:00 IST)")

    # 6. Warnings
    warnings.append("Channel mock mode is active (MOCK_CHANNELS=true)")

    can_launch = len(blockers) == 0
    return PreflightResult(can_launch=can_launch, blockers=blockers, warnings=warnings)
