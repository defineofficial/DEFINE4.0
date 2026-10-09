"""Campaigns in PostgreSQL.

Every query here is scoped to the signed-in organizer, so one organizer can never read or change
another organizer's campaign, even by guessing its ID. A campaign that belongs to someone else
gets the same 404 as one that does not exist, so IDs cannot be probed.
"""
from uuid import UUID

import psycopg
from fastapi import HTTPException
from psycopg.types.json import Jsonb

from .schemas import Campaign, CampaignCreate, EventDetails, Me

# psycopg returns arrays of custom enum types as text, so enum arrays are cast to text[] on the way out.
_SELECT = """
    SELECT c.id, c.name, c.template_key, c.status::text AS status, c.event, c.languages,
           c.channels::text[] AS channels, c.created_at,
           (SELECT count(*) FROM campaign_contacts cc WHERE cc.campaign_id = c.id) AS contact_count
    FROM campaigns c
"""


def _not_found() -> HTTPException:
    return HTTPException(404, "Campaign not found")


def _uuid(value: str) -> UUID:
    try:
        return UUID(value)
    except ValueError:
        raise _not_found() from None  # not a valid ID, so it cannot exist


def _to_campaign(row: dict) -> Campaign:
    return Campaign(
        id=str(row["id"]), name=row["name"], template_key=row["template_key"], status=row["status"],
        event=row["event"], languages=row["languages"], channels=row["channels"],
        poster_url=None,  # posters move to private storage in a later task
        contact_count=row["contact_count"], created_at=row["created_at"],
    )


def list_for(conn: psycopg.Connection, me: Me) -> list[Campaign]:
    rows = conn.execute(
        _SELECT + " WHERE c.organizer_id = %s ORDER BY c.created_at DESC", (UUID(me.id),)
    ).fetchall()
    return [_to_campaign(r) for r in rows]


def get_for(conn: psycopg.Connection, me: Me, campaign_id: str) -> Campaign:
    row = conn.execute(
        _SELECT + " WHERE c.id = %s AND c.organizer_id = %s", (_uuid(campaign_id), UUID(me.id))
    ).fetchone()
    if row is None:
        raise _not_found()
    return _to_campaign(row)


def create_for(conn: psycopg.Connection, me: Me, body: CampaignCreate) -> Campaign:
    name = body.name.strip()
    if not name:
        raise HTTPException(422, "Give the campaign a name")
    template = conn.execute(
        "SELECT default_channels::text[] AS channels FROM templates WHERE key = %s", (body.template_key,)
    ).fetchone()
    if template is None:
        raise HTTPException(422, "Unknown template")
    row = conn.execute(
        "INSERT INTO campaigns (organizer_id, template_key, name, channels) "
        "VALUES (%s, %s, %s, %s::text[]::channel[]) RETURNING id",
        (UUID(me.id), body.template_key, name, template["channels"]),
    ).fetchone()
    campaign = get_for(conn, me, str(row["id"]))
    conn.commit()
    return campaign


def save_event_for(conn: psycopg.Connection, me: Me, campaign_id: str, event: EventDetails) -> Campaign:
    updated = conn.execute(
        "UPDATE campaigns SET event = %s WHERE id = %s AND organizer_id = %s RETURNING id",
        (Jsonb(event.model_dump(mode="json")), _uuid(campaign_id), UUID(me.id)),
    ).fetchone()
    if updated is None:
        conn.rollback()
        raise _not_found()
    campaign = get_for(conn, me, campaign_id)
    conn.commit()
    return campaign
