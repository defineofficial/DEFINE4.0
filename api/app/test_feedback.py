from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_feedback_roundtrip_and_replace():
    assert client.post("/r/tok_ct_004/feedback", json={"rating": 5, "comment": "Great"}).status_code == 200
    assert client.post("/r/tok_ct_004/feedback", json={"rating": 3}).status_code == 200      # replaces, not duplicates
    r = client.get("/campaigns/cmp_001/feedback", headers={"Authorization": "Bearer x"}).json()
    mine = [f for f in r["items"] if f["contact_id"] == "ct_004"]
    assert len(mine) == 1 and mine[0]["rating"] == 3


def test_feedback_validation_and_unknown_link():
    assert client.post("/r/tok_ct_004/feedback", json={"rating": 9}).status_code == 422
    assert client.post("/r/nope/feedback", json={"rating": 4}).status_code == 404
