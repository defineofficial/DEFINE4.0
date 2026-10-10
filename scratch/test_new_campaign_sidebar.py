import httpx as requests
import psycopg

BASE_URL = "http://127.0.0.1:8000"

# 1. Login
resp = requests.post(f"{BASE_URL}/auth/login", json={"email": "organizer@example.com", "password": "password123"})
assert resp.status_code == 200, f"Login failed: {resp.text}"
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("1. Logged in successfully!")

# 2. Create NEW campaign with user-provided title
new_event_title = "Kochi AI Healthcare Symposium 2026"
resp = requests.post(f"{BASE_URL}/campaigns", headers=headers, json={"name": new_event_title, "template_key": "seminar_invite"})
assert resp.status_code == 201, f"Create campaign failed: {resp.text}"
new_campaign = resp.json()
new_id = new_campaign["id"]
print(f"2. Created brand new campaign: ID={new_id}, Name='{new_campaign['name']}'")

# 3. Save Event Details provided by user
event_payload = {
    "title": new_event_title,
    "description": "State-of-the-art medical intelligence conference",
    "starts_at": "2026-11-18T10:00:00+05:30",
    "ends_at": "2026-11-18T17:00:00+05:30",
    "venue": "Grand Hyatt Lulu Hall",
    "city": "Kochi",
    "fee_inr": 650,
    "capacity": 200,
}
resp = requests.put(f"{BASE_URL}/campaigns/{new_id}/event", headers=headers, json=event_payload)
assert resp.status_code == 200, f"Save event failed: {resp.text}"
saved = resp.json()
print("3. Event data saved to campaign:", saved["event"]["title"], "at", saved["event"]["venue"], f"(INR {saved['event']['fee_inr']})")

# 4. Launch Campaign
resp = requests.post(f"{BASE_URL}/campaigns/{new_id}/launch", headers=headers)
assert resp.status_code == 200, f"Launch failed: {resp.text}"
print("4. Campaign launched, status is now:", resp.json()["status"])

# 5. Verify PostgreSQL database row
conn = psycopg.connect("postgresql://eventreach:Al0h0mora@localhost:5432/eventreach")
cur = conn.execute("SELECT id, name, status, event FROM campaigns WHERE id = %s", (new_id,))
row = cur.fetchone()
print(f"5. Verified in PostgreSQL: ID={row[0]}, Name='{row[1]}', Status='{row[2]}'")
assert row[1] == new_event_title
assert row[2] == "running"
assert row[3]["venue"] == "Grand Hyatt Lulu Hall"
assert row[3]["fee_inr"] == 650

# 6. Check GET /campaigns lists this new campaign for sidebar rendering
resp = requests.get(f"{BASE_URL}/campaigns", headers=headers)
all_camps = resp.json()
print(f"6. Total campaigns available for sidebar: {len(all_camps)}")
matched = [c for c in all_camps if c["id"] == new_id]
assert len(matched) == 1, "New campaign not found in GET /campaigns list!"
found = matched[0]
print("   Sidebar Item Preview:")
print(f"   -> Title: {found['name']}")
print(f"   -> Status: {found['status'].upper()}")
print(f"   -> Date: {found['event']['starts_at']}")
print(f"   -> Venue: {found['event']['venue']}, {found['event']['city']}")
print(f"   -> Fee: INR {found['event']['fee_inr']}")

print("\nALL VERIFICATIONS PASSED: NEW CAMPAIGN APPEARS ON SIDEBAR WITH USER DATA!")
