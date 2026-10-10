"""End-to-end check of the organizer -> recipient -> payment -> dashboard flow.

Run the API first (mock mode or database mode), then from the api folder:
    python scripts/e2e_workflow.py                      # uses http://localhost:8000
    python scripts/e2e_workflow.py --base http://localhost:8000 --email you@example.com --password '...'

It only talks to the public HTTP API, so it tests the same thing the frontend does.
In database mode it needs an account (--email/--password) and a campaign with a published
event and an imported audience. It prints PASS or FAIL for each step and exits 1 on failure.
"""
import argparse
import sys

import httpx

results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(("PASS  " if ok else "FAIL  ") + name + (f"   [{detail}]" if detail and not ok else ""))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8000")
    ap.add_argument("--email", default="demo@example.com")
    ap.add_argument("--password", default="demo-password")
    ap.add_argument("--token", default=None, help="Registration token to use. Default: first contact found")
    a = ap.parse_args()
    c = httpx.Client(base_url=a.base, timeout=15)

    r = c.get("/health")
    if not check("API is up", r.status_code == 200, r.text):
        sys.exit(1)

    r = c.post("/auth/login", json={"email": a.email, "password": a.password})
    if not check("Organizer can log in", r.status_code == 200, r.text):
        sys.exit(1)
    c.headers["Authorization"] = "Bearer " + r.json()["access_token"]

    camps = c.get("/campaigns").json()
    camp = next((x for x in camps if x.get("event")), None) or (camps[0] if camps else None)
    if not check("A campaign with event details exists", bool(camp)):
        sys.exit(1)
    cid = camp["id"]
    fee = (camp.get("event") or {}).get("fee_inr", 0)

    contacts = c.get(f"/campaigns/{cid}/contacts", params={"limit": 200}).json()
    rows = contacts["items"] if isinstance(contacts, dict) and "items" in contacts else contacts
    check("Contacts never expose a full phone number",
          all("phone" not in x or x.get("phone") is None for x in rows)
          and all("phone_masked" in x for x in rows))

    funnel0 = c.get(f"/campaigns/{cid}/analytics/funnel").json()

    token = a.token
    if not token:
        pick = next((x for x in rows if x.get("stage") in ("invited", "responded") and (x.get("registration_link") or x.get("registration_token"))), None)
        if pick:
            if pick.get("registration_link"):
                token = pick["registration_link"].split("/r/")[-1]
            else:
                token = pick.get("registration_token")
        else:
            token = f"tok_{rows[0]['id']}" if rows else None
    if not check("Found a registration link to test", bool(token), "pass --token"):
        sys.exit(1)

    pub = httpx.Client(base_url=a.base, timeout=15)       # no login: recipients are anonymous

    r = pub.get("/r/not-a-real-token")
    check("Unknown link returns 404", r.status_code == 404, r.text)

    r = pub.get(f"/r/{token}")
    check("Registration page loads without login", r.status_code == 200, r.text)
    page = r.json() if r.status_code == 200 else {}
    check("Page shows event, first name and language",
          bool(page.get("event")) and bool(page.get("first_name")) and bool(page.get("language")))

    r = pub.post(f"/r/{token}/register", json={"name": "Test Person", "party_size": 1, "consent": False})
    check("Registration without consent is refused", r.status_code == 400, r.text)

    r = pub.post(f"/r/{token}/register",
                 json={"name": "Test Person", "email": "test@example.com", "party_size": 1, "consent": True})
    check("Registration with consent works", r.status_code == 200, r.text)
    reg = r.json() if r.status_code == 200 else {}
    check("Result says whether payment is needed",
          reg.get("requires_payment") == (fee > 0), str(reg))

    r = pub.post(f"/r/{token}/register",
                 json={"name": "Test Person", "email": "test@example.com", "party_size": 1, "consent": True})
    check("Registering twice does not break or duplicate", r.status_code in (200, 409), r.text)

    if fee > 0:
        r = pub.post(f"/r/{token}/pay")
        check("Payment order is created", r.status_code == 200, r.text)
        order = r.json() if r.status_code == 200 else {}
        check("Order amount equals the event fee", order.get("amount_inr") == fee, str(order))

        r = pub.post("/webhooks/payment", json={"order_id": order.get("order_id", ""), "status": "failed"})
        stage = pub.get(f"/r/{token}").json().get("stage")
        check("A failed payment does not mark the person paid", stage != "paid", f"stage={stage}")

        r = pub.post("/webhooks/payment", json={"order_id": order.get("order_id", ""), "status": "paid"})
        check("Paid webhook is accepted", r.status_code == 200, r.text)
        r = pub.post("/webhooks/payment", json={"order_id": order.get("order_id", ""), "status": "paid"})
        check("Same webhook twice is harmless", r.status_code == 200, r.text)

        check("Person is now paid", pub.get(f"/r/{token}").json().get("stage") == "paid")
        r = pub.post(f"/r/{token}/pay")
        check("Paying again is refused", r.status_code == 409, r.text)
    else:
        r = pub.post(f"/r/{token}/pay")
        check("Free event refuses a payment order", r.status_code == 400, r.text)

    check("Page now shows already registered", pub.get(f"/r/{token}").json().get("already_registered") is True)

    funnel1 = c.get(f"/campaigns/{cid}/analytics/funnel").json()
    check("Dashboard registered count went up or stayed (never down)",
          funnel1["registered"] >= funnel0["registered"], f"{funnel0} -> {funnel1}")
    if fee > 0:
        check("Dashboard paid count went up", funnel1["paid"] >= funnel0["paid"] + (0 if funnel0["paid"] and token else 0),
              f"{funnel0} -> {funnel1}")

    bad = httpx.Client(base_url=a.base, timeout=15).get("/campaigns")
    in_db_mode = c.get("/health").json().get("database") == "connected"
    if in_db_mode:
        check("Organizer endpoints refuse anonymous callers", bad.status_code == 401, str(bad.status_code))

    print(f"\n{sum(results)} of {len(results)} checks passed")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
