import httpx as requests
import psycopg

BASE_URL = "http://127.0.0.1:8000"

# 1. Login
resp = requests.post(f"{BASE_URL}/auth/login", json={"email": "organizer@example.com", "password": "password123"})
assert resp.status_code == 200, f"Login failed: {resp.text}"
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("1. Logged in successfully!")

# 2. Get Campaigns
resp = requests.get(f"{BASE_URL}/campaigns", headers=headers)
assert resp.status_code == 200, f"Get campaigns failed: {resp.text}"
campaigns = resp.json()
print(f"2. Found {len(campaigns)} campaigns in database:")
for c in campaigns:
    print(f"   ID: {c['id']}, Name: {c['name']}, Status: {c['status']}, Event: {c.get('event')}")

campaign_id = campaigns[0]["id"]

# 3. Save Event Details (PUT /campaigns/{campaign_id}/event)
event_data = {
    "title": "Define Healthcare & AI Seminar 2026",
    "description": "Comprehensive healthcare symposium and workshop in Kochi",
    "starts_at": "2026-10-23T10:00:00+05:30",
    "ends_at": "2026-10-23T16:00:00+05:30",
    "venue": "Grand Hall, Block A",
    "city": "Kochi",
    "fee_inr": 500,
    "capacity": 150,
}

resp = requests.put(f"{BASE_URL}/campaigns/{campaign_id}/event", headers=headers, json=event_data)
assert resp.status_code == 200, f"Save event failed: {resp.text}"
saved_campaign = resp.json()
print("3. Successfully saved event via API:", saved_campaign.get("event"))

# 4. Verify Directly in PostgreSQL Database
conn = psycopg.connect("postgresql://eventreach:Al0h0mora@localhost:5432/eventreach")
cur = conn.execute("SELECT id, name, status, event FROM campaigns WHERE id = %s", (campaign_id,))
row = cur.fetchone()
print("4. Directly verified in PostgreSQL:")
print(f"   ID: {row[0]}")
print(f"   Name: {row[1]}")
print(f"   Status: {row[2]}")
print(f"   Event JSONB in DB: {row[3]}")
assert row[3] is not None, "Event was not saved in PostgreSQL!"
assert row[3]["title"] == "Define Healthcare & AI Seminar 2026", "Title mismatch!"

# 5. Launch Campaign (POST /campaigns/{campaign_id}/launch)
resp = requests.post(f"{BASE_URL}/campaigns/{campaign_id}/launch", headers=headers)
assert resp.status_code == 200, f"Launch failed: {resp.text}"
print("5. Launch API response:", resp.json())

# 6. Verify status updated to 'running' in PostgreSQL
cur = conn.execute("SELECT status FROM campaigns WHERE id = %s", (campaign_id,))
updated_status = cur.fetchone()[0]
print(f"6. PostgreSQL status after launch: {updated_status}")
assert updated_status == "running", f"Expected running status, got {updated_status}"

# 7. Test AI Settings endpoint
resp = requests.post(f"{BASE_URL}/settings/ai", headers=headers, json={"provider": "gemini", "api_key": "AIzaSyDemoKeyForTest"})
assert resp.status_code == 200, f"AI settings failed: {resp.text}"
resp = requests.get(f"{BASE_URL}/settings/ai", headers=headers)
print("7. AI Settings API check:", resp.json())

print("\nALL PERSISTENCE AND API CHECKS PASSED PERFECTLY!")
