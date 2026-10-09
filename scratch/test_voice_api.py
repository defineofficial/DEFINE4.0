import io
import httpx as requests

BASE_URL = "http://127.0.0.1:8000"

# Login
resp = requests.post(f"{BASE_URL}/auth/login", json={"email": "organizer@example.com", "password": "password123"})
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get campaign
resp = requests.get(f"{BASE_URL}/campaigns", headers=headers)
campaign_id = resp.json()[0]["id"]

# Send mock audio file
fake_audio = io.BytesIO(b"\x1a\x45\xdf\xa3\x01\x00\x00\x00" * 100)
files = {"file": ("test_voicenote.webm", fake_audio, "audio/webm")}
custom_headers = {
    **headers,
    "X-AI-Provider": "gemini",
    "X-AI-Key": "AIzaSyTestKeyExample",
}

resp = requests.post(
    f"{BASE_URL}/campaigns/{campaign_id}/voice-note",
    headers=custom_headers,
    files=files,
)
print("Voice upload status code:", resp.status_code)
print("Voice upload response:", resp.json())
assert resp.status_code == 200
data = resp.json()
assert "transcript" in data
assert "event" in data
print("\nVoice API successfully processed audio!")
