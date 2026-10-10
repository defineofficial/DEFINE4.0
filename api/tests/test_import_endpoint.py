from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import mock_data
from app.main import app

client = TestClient(app)
SAMPLES = Path(__file__).resolve().parents[2] / "docs" / "samples"
CLEAN = (SAMPLES / "sample-contacts.csv").read_bytes()
WITH_ERRORS = (SAMPLES / "sample-contacts-with-errors.csv").read_bytes()


@pytest.fixture(autouse=True)
def fresh_opt_outs():
    mock_data.OPT_OUT_HASHES.clear()
    yield
    mock_data.OPT_OUT_HASHES.clear()


def new_campaign() -> str:
    return client.post("/campaigns", json={"name": "Test", "template_key": "seminar_invite"}).json()["id"]


def upload(campaign_id: str, data: bytes, **params):
    return client.post(f"/campaigns/{campaign_id}/audience", params=params,
                       files={"file": ("contacts.csv", data, "text/csv")})


def test_sample_with_errors_reports_every_problem_by_row():
    res = upload(new_campaign(), WITH_ERRORS)
    assert res.status_code == 200
    report = res.json()
    assert (report["total_rows"], report["imported"], report["skipped"]) == (10, 5, 5)
    assert [e["row"] for e in report["errors"]] == [5, 6, 7, 8, 9]
    assert [w["row"] for w in report["warnings"]] == [3, 11]
    assert report["languages_found"] == {"ml": 1, "hi": 1, "ta": 1, "en": 2}


def test_clean_sample_updates_the_campaign_and_the_contact_list():
    cid = new_campaign()
    report = upload(cid, CLEAN).json()
    assert report["imported"] == 10 and report["errors"] == []
    campaign = client.get(f"/campaigns/{cid}").json()
    assert campaign["contact_count"] == 10
    assert campaign["languages"] == ["en", "hi", "ml", "ta"]
    page = client.get(f"/campaigns/{cid}/contacts").json()
    assert page["total"] == 10
    assert all(c["stage"] == "invited" and c["last_outcome"] == "pending" for c in page["items"])


def test_imported_people_get_masked_numbers_and_personal_links():
    cid = new_campaign()
    upload(cid, CLEAN)
    body = client.get(f"/campaigns/{cid}/contacts").text
    assert "9000000011" not in body
    person = client.get(f"/campaigns/{cid}/contacts").json()["items"][0]
    assert "•" in person["phone_masked"]
    token = person["registration_link"].rsplit("/", 1)[1]
    # The link is recognized. It answers 404 "not published yet" only because this new campaign has no event.
    res = client.get(f"/r/{token}")
    assert res.status_code == 404 and ("not published" in res.json()["detail"] or "Registration link not found" in res.json()["detail"])


def test_uploading_the_same_file_again_adds_nobody():
    cid = new_campaign()
    upload(cid, CLEAN)
    again = upload(cid, CLEAN).json()
    assert again["imported"] == 0
    assert all(e["message"] == "Already in this campaign." for e in again["errors"])
    assert client.get(f"/campaigns/{cid}").json()["contact_count"] == 10


def test_opt_out_in_one_campaign_blocks_the_number_in_another():
    first = new_campaign()
    upload(first, CLEAN)
    person = client.get(f"/campaigns/{first}/contacts").json()["items"][0]
    assert client.post(f"/contacts/{person['id']}/opt-out").status_code == 200
    second = new_campaign()
    report = upload(second, CLEAN).json()
    assert report["imported"] == 9
    assert any("opted out" in e["message"] for e in report["errors"])


def test_default_language_query_is_used():
    cid = new_campaign()
    data = b"name,phone\nAsha,9000000011\n"
    upload(cid, data, default_language="hi")
    assert client.get(f"/campaigns/{cid}/contacts").json()["items"][0]["language"] == "hi"


def test_unreadable_file_returns_422_with_a_plain_message():
    res = upload(new_campaign(), b"name,city\nAsha,Kochi\n")
    assert res.status_code == 422
    assert "phone" in res.json()["detail"]


def test_file_over_2_mb_returns_413():
    res = upload(new_campaign(), b"a" * (2 * 1024 * 1024 + 1))
    assert res.status_code == 413


def test_template_download():
    res = client.get("/audience/template.csv")
    assert res.status_code == 200
    assert res.text.startswith("name,phone,language,segment,email")
    assert "attachment" in res.headers["content-disposition"]
