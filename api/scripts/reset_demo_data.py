"""Reset demo data script for EventReach demo presentations.

Creates:
1. `cmp_001`: A fully populated campaign with 14 contacts in English, Hindi, Malayalam, and Tamil,
   with realistic call outcomes and conversion stages for Aleena (F2)'s dashboard demo.
2. `cmp_002`: A clean draft campaign ready for live voice note upload and dispatch during the live presentation.

Works both with PostgreSQL (when DATABASE_URL is set) and memory mock state.
Run with:
    python scripts/reset_demo_data.py
"""
import os
import sys
from pathlib import Path

# Add parent directory to python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db as database, mock_data as db
from app.schemas import Campaign, CampaignStatus, Channel, Language, Outcome, Stage


def reset_mock_state():
    print("Resetting in-memory demo datasets...")
    # Reset cmp_001 contacts and tokens
    db.CONTACTS["cmp_001"] = db._build_contacts()
    db.CONTACTS["cmp_002"] = []
    
    # Re-index tokens
    db.TOKENS.clear()
    for c in db.CONTACTS["cmp_001"]:
        db.TOKENS[f"tok_{c.id}"] = ("cmp_001", c)

    # Set campaign statuses
    db.CAMPAIGNS["cmp_001"].status = CampaignStatus.running
    db.CAMPAIGNS["cmp_001"].contact_count = len(db.CONTACTS["cmp_001"])
    db.CAMPAIGNS["cmp_002"].status = CampaignStatus.draft
    db.CAMPAIGNS["cmp_002"].contact_count = 0
    db.CAMPAIGNS["cmp_002"].event = None

    print(f"[OK] Campaign cmp_001 reset with {len(db.CONTACTS['cmp_001'])} contacts for dashboard.")
    print("[OK] Campaign cmp_002 reset as clean draft for live organizer demo.")


def reset_database_state():
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        return
    print(f"Resetting PostgreSQL database at {url.split('@')[-1]}...")
    try:
        from app import dbsetup
        dbsetup.setup(url, reset=True)
        print("[OK] Database tables reset and seeded with default organizer and 4 presets.")
    except Exception as exc:
        print(f"Notice: Database reset skipped or failed: {exc}")


def main():
    print("=" * 60)
    print(" EventReach Demo Data Reset ")
    print("=" * 60)
    reset_mock_state()
    reset_database_state()
    print("\nDemo environment is ready!")


if __name__ == "__main__":
    main()
