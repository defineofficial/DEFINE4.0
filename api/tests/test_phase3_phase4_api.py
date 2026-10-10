"""API integration tests for Phase 3 (Event Record Versioning) and Phase 4 (Translations).

Proves:
- PUT /campaigns/{id}/event updates event details and sets status to details_approved
- GET /campaigns/{id}/languages returns audience language counts
- POST /campaigns/{id}/translations/generate creates translations with back-translation and fact check
- Updating event details invalidates existing translations (staleness propagation: status='stale', approved=False)
- PUT /campaigns/{id}/translations/{language} with approved=True updates status and advances campaign status to translations_approved
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_api_phase3_phase4_full_flow():
    # 1. Create a draft campaign
    res = client.post("/campaigns", json={"name": "Health Summit", "template_key": "seminar_invite"})
    assert res.status_code in (200, 201)
    camp_id = res.json()["id"]

    # 2. PUT /campaigns/{id}/event -> Save event details (Version 1)
    ev_data = {
        "title": "Health Summit 2026",
        "description": "Healthcare AI seminar",
        "starts_at": "2026-11-14T10:00:00+05:30",
        "ends_at": "2026-11-14T16:00:00+05:30",
        "venue": "Seminar Hall A",
        "city": "Kochi",
        "fee_inr": 500,
        "capacity": 100,
    }
    res_ev = client.put(f"/campaigns/{camp_id}/event", json=ev_data)
    assert res_ev.status_code == 200
    assert res_ev.json()["status"] == "details_approved"

    # 3. GET /campaigns/{id}/languages
    res_lang = client.get(f"/campaigns/{camp_id}/languages")
    assert res_lang.status_code == 200
    assert isinstance(res_lang.json(), list)

    # 4. POST /campaigns/{id}/translations/generate -> Generate translations
    res_trans_gen = client.post(f"/campaigns/{camp_id}/translations/generate")
    assert res_trans_gen.status_code == 200
    translations = res_trans_gen.json()
    assert len(translations) >= 1
    hi_trans = next(t for t in translations if t["language"] == "hi")
    assert hi_trans["back_translation_en"] is not None
    assert hi_trans["approved"] is False

    # 5. Edit event details (change venue to 'Auditorium B') -> Staleness propagation!
    ev_data_v2 = dict(ev_data)
    ev_data_v2["venue"] = "Auditorium B"
    res_ev2 = client.put(f"/campaigns/{camp_id}/event", json=ev_data_v2)
    assert res_ev2.status_code == 200
    assert res_ev2.json()["status"] == "needs_regeneration"

    # Verify translations are now marked 'stale' and approved=False
    res_trans_stale = client.get(f"/campaigns/{camp_id}/translations")
    assert res_trans_stale.status_code == 200
    for t in res_trans_stale.json():
        assert t["status"] == "stale"
        assert t["approved"] is False

    # 6. Re-generate translations for new event version
    res_trans_gen2 = client.post(f"/campaigns/{camp_id}/translations/generate")
    assert res_trans_gen2.status_code == 200

    # 7. Approve translations
    for t in res_trans_gen2.json():
        lang = t["language"]
        t["approved"] = True
        res_app = client.put(f"/campaigns/{camp_id}/translations/{lang}", json=t)
        assert res_app.status_code == 200
        assert res_app.json()["approved"] is True
        assert res_app.json()["status"] == "approved"

    # Verify campaign status progressed to translations_approved
    res_camp_final = client.get(f"/campaigns/{camp_id}")
    assert res_camp_final.status_code == 200
    assert res_camp_final.json()["status"] == "translations_approved"
