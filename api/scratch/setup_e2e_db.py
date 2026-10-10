"""Sets up a test campaign with event and contacts for e2e_workflow test."""
import json
import os
import secrets
import sys
from datetime import datetime, timedelta, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import auth, db, dbsetup, campaigns_db, contacts_db, privacy
from app.csv_import import parse_contacts_csv
from app.schemas import CampaignCreate, EventDetails, Language, Me

def main():
    with db.get_pool().connection() as conn:
        dbsetup._migrate_schema(conn)
        row = conn.execute("SELECT id, name, email, role FROM organizers WHERE email = 'demo@example.com'").fetchone()
        if not row:
            row = auth.create_organizer(conn, "Demo Organizer", "demo@example.com", "demo-password")
        
        me = Me(id=str(row["id"]), name=row["name"], email=row["email"], role=row["role"])
        
        # Clear existing campaigns for demo@example.com
        conn.execute("DELETE FROM campaigns WHERE organizer_id = %s::uuid", (me.id,))
        
        c_create = CampaignCreate(name="Healthcare AI Seminar 2026", template_key="seminar_invite")
        camp = campaigns_db.create_for(conn, me, c_create)
        cid = camp.id

        ev = EventDetails(
            title="Healthcare AI Seminar 2026",
            description="Seminar on AI in Healthcare",
            starts_at=datetime.now(timezone.utc) + timedelta(days=5),
            ends_at=datetime.now(timezone.utc) + timedelta(days=5, hours=4),
            venue="Grand Auditorium, Block B",
            city="Kochi",
            fee_inr=500,
            capacity=100,
            rsvp_deadline=datetime.now(timezone.utc) + timedelta(days=3),
        )
        conn.execute(
            "UPDATE campaigns SET event = %s, status = 'running'::campaign_status, languages = '{en}' WHERE id = %s::uuid",
            (psycopg_json(ev.model_dump(mode="json")), cid),
        )

        csv_text = "Name,Phone,Language,Segment,Email\nRahul Nair,+919876543210,en,Students,rahul@example.com\nAnjali Menon,+919876543211,en,Faculty,anjali@example.com\n"
        res = parse_contacts_csv(csv_text.encode("utf-8"))
        if res.contacts:
            contacts_db.add_contacts_for(conn, me, cid, res.contacts)

        conn.commit()
        print(f"Setup complete for campaign {cid}")

def psycopg_json(obj):
    from psycopg.types.json import Jsonb
    return Jsonb(obj)

if __name__ == "__main__":
    main()
