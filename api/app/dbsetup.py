"""Create the database tables from db/schema.sql and load the template presets."""
from pathlib import Path

import psycopg
from psycopg.conninfo import conninfo_to_dict
from psycopg.types.json import Jsonb

SCHEMA_FILE = Path(__file__).resolve().parents[2] / "db" / "schema.sql"
LOCAL_HOSTS = {"", "localhost", "127.0.0.1", "::1"}


def _host(url: str) -> str:
    return conninfo_to_dict(url).get("host") or ""


def setup(url: str, reset: bool = False, allow_remote_reset: bool = False) -> str:
    """Create the tables if they are missing. Returns "created" or "already existed".

    reset=True deletes everything this database user owns first. It is for development only,
    so it refuses to run against a database on another machine unless allow_remote_reset is set.
    """
    if reset and _host(url) not in LOCAL_HOSTS and not allow_remote_reset:
        raise RuntimeError("Refusing to reset a database on another machine.")
    with psycopg.connect(url, autocommit=True) as conn:
        encoding = conn.execute("SHOW server_encoding").fetchone()[0]
        if isinstance(encoding, bytes):  # psycopg returns bytes when the database is SQL_ASCII
            encoding = encoding.decode("ascii")
        if encoding != "UTF8":
            raise RuntimeError(
                f"This database uses {encoding} encoding, so Hindi, Malayalam and Tamil names would fail to save. "
                "Create it with ENCODING 'UTF8' (see docs/database-setup-windows.md)."
            )
        exists = conn.execute("SELECT to_regclass('public.organizers') IS NOT NULL").fetchone()[0]
        if reset:
            conn.execute("DROP OWNED BY CURRENT_USER CASCADE")
            exists = False
        if not exists:
            conn.execute(SCHEMA_FILE.read_text(encoding="utf-8"))
        else:
            _migrate_schema(conn)
        seed_templates(conn)
    return "already existed" if exists else "created"


def _migrate_schema(conn: psycopg.Connection) -> None:
    """Ensure optional/new columns exist on existing tables."""
    conn.execute("ALTER TABLE campaign_contacts ADD COLUMN IF NOT EXISTS token_hash text")
    conn.execute("ALTER TABLE campaign_contacts ADD COLUMN IF NOT EXISTS token_expires_at timestamptz")
    conn.execute("ALTER TABLE campaign_contacts ADD COLUMN IF NOT EXISTS token_used_at timestamptz")
    conn.execute("ALTER TABLE payments ADD COLUMN IF NOT EXISTS currency text NOT NULL DEFAULT 'INR'")
    conn.execute("ALTER TABLE payments ADD COLUMN IF NOT EXISTS gateway_key_id text")
    conn.execute("ALTER TABLE payments ADD COLUMN IF NOT EXISTS gateway_payment_id text")
    conn.execute("ALTER TABLE payments ADD COLUMN IF NOT EXISTS gateway_event_id text")
    conn.execute("ALTER TABLE payments ADD COLUMN IF NOT EXISTS hold_expires_at timestamptz")
    conn.execute("ALTER TABLE payments ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now()")


def seed_templates(conn: psycopg.Connection) -> None:
    """Insert or update the four presets. Safe to run again."""
    from .mock_data import TEMPLATES  # the presets are defined once, in mock_data.py

    for template in TEMPLATES:
        t = template.model_dump(mode="json")
        conn.execute(
            """
            INSERT INTO templates (key, name, description, variables, keypad_options, requires_payment, default_channels)
            VALUES (%s, %s, %s, %s, %s, %s, %s::text[]::channel[])
            ON CONFLICT (key) DO UPDATE SET
              name = EXCLUDED.name, description = EXCLUDED.description,
              variables = EXCLUDED.variables, keypad_options = EXCLUDED.keypad_options,
              requires_payment = EXCLUDED.requires_payment, default_channels = EXCLUDED.default_channels
            """,
            (t["key"], t["name"], t["description"], Jsonb(t["variables"]), Jsonb(t["keypad_options"]),
             t["requires_payment"], t["default_channels"]),
        )
