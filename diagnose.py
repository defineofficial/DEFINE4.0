#!/usr/bin/env python
"""EventReach diagnostic. Finds what is broken and tells you where and how to fix it.

Run from the repo root with the api virtual environment active (needs only Python):

    python diagnose.py                          # checks setup, code and the running API
    python diagnose.py --email you@x.com --password '...'     # if the API uses the database
    python diagnose.py --no-write               # do not create a test campaign

Start the API first (cd api; uvicorn app.main:app --reload --port 8000) for the live checks.
Everything is printed and also saved to diagnostic-report.txt. Paste the FAIL and WARN lines
back into the chat; they are short on purpose.

It never prints passwords or keys. With the API in database mode it creates one campaign named
"[diagnostic] ..." (skip that with --no-write). It never launches a campaign or calls anyone.
"""
import argparse
import base64
import difflib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

FINDINGS = []     # (level, area, title, where, fix)


def add(level, area, title, where="", fix=""):
    FINDINGS.append((level, area, title, where, fix))


def ok(area, title):
    add("OK", area, title)


# ---------------------------------------------------------------- helpers
def http(method, url, body=None, headers=None, data=None, timeout=15):
    h = dict(headers or {})
    payload = data
    if body is not None:
        payload = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=payload, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return 0, {}, str(e).encode()


def jd(raw):
    try:
        return json.loads(raw)
    except Exception:
        return None


def snip(raw, n=160):
    return " ".join(raw.decode("utf-8", "replace").split())[:n]


def multipart(files, fields=None):
    b = uuid.uuid4().hex
    out = b""
    for k, v in (fields or {}).items():
        out += f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    for k, (fn, data, ct) in files.items():
        out += (f'--{b}\r\nContent-Disposition: form-data; name="{k}"; filename="{fn}"\r\n'
                f'Content-Type: {ct}\r\n\r\n').encode() + data + b"\r\n"
    out += f"--{b}--\r\n".encode()
    return out, {"Content-Type": f"multipart/form-data; boundary={b}"}


def read_env(path):
    vals = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals


SKIP = {"node_modules", ".next", "dist", "build", ".git", ".venv", "venv", "__pycache__", "out", ".turbo", "coverage"}
SRC_EXT = {".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte", ".html"}


def source_files(root):
    for f in root.rglob("*"):
        if f.is_file() and f.suffix in SRC_EXT and not any(p in SKIP for p in f.parts) and f.stat().st_size < 400_000:
            yield f


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


# ---------------------------------------------------------------- A. environment
def check_environment(root, env, args):
    a = "Setup"
    if sys.version_info < (3, 10):
        add("FAIL", a, f"Python {sys.version_info.major}.{sys.version_info.minor} is too old (need 3.10+)", "",
            "Install Python 3.12 from python.org, then recreate the venv: python -m venv .venv")
    else:
        ok(a, f"Python {sys.version_info.major}.{sys.version_info.minor}")
    if sys.prefix == getattr(sys, "base_prefix", sys.prefix):
        add("WARN", a, "Not running inside the virtual environment", "",
            "In api folder: .venv\\Scripts\\Activate.ps1   (then run this script again)")
    missing = []
    for mod, pkg in [("fastapi", "fastapi"), ("uvicorn", "uvicorn"), ("psycopg", "psycopg[binary,pool]"),
                     ("argon2", "argon2-cffi"), ("jwt", "PyJWT"), ("dotenv", "python-dotenv"),
                     ("multipart", "python-multipart"), ("pytest", "pytest"), ("httpx", "httpx")]:
        try:
            __import__(mod)
        except Exception:
            missing.append(pkg)
    if missing:
        add("FAIL", a, "Missing Python packages: " + ", ".join(missing), "",
            "cd api ; pip install -r requirements-dev.txt")
    else:
        ok(a, "Python packages installed")

    if not (root / ".env").exists():
        add("FAIL", a, "No .env file in the repo root", str(root),
            "Copy .env.example to .env (copy .env.example .env) and fill it in")
        return
    gi = (root / ".gitignore").read_text(errors="ignore") if (root / ".gitignore").exists() else ""
    if ".env" not in gi.split():
        add("FAIL", a, ".gitignore does not list .env: secrets could be committed", ".gitignore", "Add a line: .env")
    try:
        tracked = subprocess.run(["git", "ls-files", ".env"], cwd=root, capture_output=True, text=True, timeout=10).stdout.strip()
        if tracked:
            add("FAIL", a, ".env is tracked by git: your secrets are in the repo history", ".env",
                "git rm --cached .env ; git commit -m 'stop tracking .env' ; then change every key in it")
    except Exception:
        pass

    sk = env.get("SECRET_KEY", "")
    if len(sk) < 32:
        add("FAIL", a, f"SECRET_KEY is {len(sk)} characters (needs 32+). Everyone is logged out on each restart", ".env",
            'python -c "import secrets; print(secrets.token_urlsafe(48))"  then paste the result after SECRET_KEY=')
    else:
        ok(a, "SECRET_KEY length")
    ek = env.get("ENCRYPTION_KEY", "")
    try:
        good = len(base64.b64decode(ek)) == 32
    except Exception:
        good = False
    if not good:
        add("FAIL" if env.get("DATABASE_URL") else "WARN", a, "ENCRYPTION_KEY is empty or not a 32-byte base64 key",
            ".env", 'python -c "import base64,os; print(base64.b64encode(os.urandom(32)).decode())"  then paste after ENCRYPTION_KEY=')
    else:
        ok(a, "ENCRYPTION_KEY valid")
    if len(env.get("PHONE_HASH_PEPPER", "")) < 16:
        add("FAIL" if env.get("DATABASE_URL") else "WARN", a, "PHONE_HASH_PEPPER is empty or short", ".env",
            'python -c "import secrets; print(secrets.token_urlsafe(48))"  then paste after PHONE_HASH_PEPPER=')
    else:
        ok(a, "PHONE_HASH_PEPPER set")
    if not env.get("CORS_ORIGINS"):
        add("FAIL", a, "CORS_ORIGINS is empty: the browser will block every request from the frontend", ".env",
            "CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000   (match the port your frontend uses)")
    if not env.get("PROCESSING_REGION"):
        add("WARN", a, "PROCESSING_REGION is empty. The problem statement asks you to state where voice/language processing runs", ".env",
            "Set it, for example PROCESSING_REGION=India (Mumbai), and write the same in the data protection note")
    if env.get("MOCK_CHANNELS", "true").lower() == "false" and not env.get("SMTP_HOST"):
        add("WARN", a, "MOCK_CHANNELS=false but SMTP_HOST is empty: real email cannot send", ".env",
            "Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_FROM (Gmail: use an App password)")
    du, tu = env.get("DATABASE_URL", ""), env.get("TEST_DATABASE_URL", "")
    if du and tu and du == tu:
        add("FAIL", a, "TEST_DATABASE_URL equals DATABASE_URL: running the tests DELETES your real data", ".env",
            "Point TEST_DATABASE_URL at the eventreach_test database")
    if "your-password" in du or "choose-a-password" in du:
        add("FAIL", a, "DATABASE_URL still contains the placeholder password", ".env", "Put the real password for the eventreach user")


# ---------------------------------------------------------------- B. database
def check_database(root, env):
    a = "Database"
    url = env.get("DATABASE_URL", "")
    if not url:
        add("INFO", a, "DATABASE_URL is empty: the API runs in mock mode (sample data, any login works)", ".env",
            "Fine for the demo if pages work in mock mode. Set it only if you need real saved data")
        return
    try:
        import psycopg
    except Exception:
        return
    try:
        with psycopg.connect(url, connect_timeout=5) as conn:
            enc = conn.execute("show server_encoding").fetchone()[0]
            if enc.upper() != "UTF8":
                add("FAIL", a, f"Database encoding is {enc}, not UTF8: Hindi/Malayalam/Tamil names cannot be saved", "PostgreSQL",
                    "In psql as postgres: DROP DATABASE eventreach; CREATE DATABASE eventreach OWNER eventreach ENCODING 'UTF8' TEMPLATE template0; then python api/scripts/init_db.py")
            else:
                ok(a, "Connected, UTF8")
            have = {r[0] for r in conn.execute("select table_name from information_schema.tables where table_schema='public'")}
            sql = root / "db" / "schema.sql"
            want = set(re.findall(r"create table (?:if not exists )?(\w+)", sql.read_text(errors="ignore"), re.I)) if sql.exists() else set()
            gone = sorted(want - have)
            if gone:
                add("FAIL", a, "Tables missing: " + ", ".join(gone), "db/schema.sql", "cd api ; python scripts/init_db.py")
            elif want:
                ok(a, f"All {len(want)} tables exist")
            if "organizers" in have:
                n = conn.execute("select count(*) from organizers").fetchone()[0]
                if n == 0:
                    add("FAIL", a, "No organizer accounts: nobody can log in", "organizers table",
                        'cd api ; python scripts/create_organizer.py --email you@example.com --name "Your Name" --admin')
                else:
                    ok(a, f"{n} organizer account(s)")
    except Exception as e:
        add("FAIL", a, "Cannot connect to PostgreSQL: " + " ".join(str(e).split())[:140], "DATABASE_URL in .env",
            "Windows key > Services > start postgresql-x64-NN. Check user, password, port 5432 and database name in DATABASE_URL")


# ---------------------------------------------------------------- C. backend + live
def backend_spec(base, root):
    st, _, raw = http("GET", base + "/openapi.json", timeout=8)
    if st == 200 and jd(raw):
        return jd(raw), True
    p = root / "docs" / "openapi.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8")), False
    return None, False


def norm(p):
    p = re.sub(r"^\$\{[^}]*\}", "", p)
    p = re.sub(r"^https?://[^/]+", "", p).split("?")[0].split("#")[0]
    p = re.sub(r"^/api(?=/)", "", p)
    p = re.sub(r"\$\{[^}]*\}", "{x}", p)
    p = re.sub(r"\{[^}]*\}", "{x}", p)
    p = re.sub(r"/(?:\d+|[0-9a-f]{8,}|cmp_\w+|ct_\w+|tok_\w+)(?=/|$)", "/{x}", p)
    return p.rstrip("/") or "/"


def check_backend(base, env, origin, args):
    a = "API"
    st, _, raw = http("GET", base + "/health", timeout=6)
    if st != 200:
        add("FAIL", a, f"API is not reachable at {base} ({snip(raw, 80)})", base,
            "cd api ; .venv\\Scripts\\Activate.ps1 ; uvicorn app.main:app --reload --port 8000   (read the error it prints)")
        return False
    h = jd(raw) or {}
    ok(a, f"API is up. Health: {h}")
    st, hd, _ = http("OPTIONS", base + "/campaigns", headers={
        "Origin": origin, "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "authorization,content-type"})
    allow = {k.lower(): v for k, v in hd.items()}.get("access-control-allow-origin", "")
    if allow not in (origin, "*"):
        add("FAIL", a, f"CORS blocks the frontend origin {origin} (browser console shows 'blocked by CORS policy')", "CORS_ORIGINS in .env",
            f"Set CORS_ORIGINS={origin} (comma separated for several, include both localhost and 127.0.0.1 versions), then restart uvicorn")
    else:
        ok(a, "CORS allows the frontend origin")
    return True


def live_probe(base, root, env, args, spec):
    a = "Workflow"
    paths = spec["paths"] if spec else {}
    bp = {norm(p): {m.upper() for m in ops} for p, ops in paths.items()}

    # login
    st, _, raw = http("POST", base + "/auth/login", {"email": args.email, "password": args.password})
    if st != 200:
        add("FAIL" if st != 0 else "FAIL", a, f"Login failed ({st}): {snip(raw, 100)}", "POST /auth/login",
            "Database mode: run python diagnose.py --email you@example.com --password '...'. No account? "
            'cd api ; python scripts/create_organizer.py --email you@example.com --name "You" --admin')
        return
    tok = (jd(raw) or {}).get("access_token")
    H = {"Authorization": "Bearer " + tok} if tok else {}
    ok(a, "Login works")

    if "/campaigns/{x}/email/test" not in bp:
        add("WARN", a, "Email endpoints are not installed in the API", "api/app/main.py",
            "Copy mailer.py and email_routes.py into api/app/, then in main.py add: from . import email_routes  and  app.include_router(email_routes.router)")
    if not any("feedback" in p for p in bp):
        add("FAIL", a, "The backend has NO feedback endpoint, so 'Submit feedback' has nothing to call", "api/app/main.py",
            "Add to main.py (works in mock mode; swap the list for a table later):\n"
            "    FEEDBACK: list[dict] = []\n"
            "    class FeedbackIn(BaseModel):\n"
            "        rating: int = Field(ge=1, le=5)\n"
            "        comment: Optional[str] = None\n"
            "    @app.post('/r/{token}/feedback', tags=['Registration (public)'])\n"
            "    def feedback(token: str, body: FeedbackIn) -> dict:\n"
            "        camp, contact = _by_token(token)\n"
            "        FEEDBACK.append({'campaign_id': camp.id, 'contact_id': contact.id, **body.model_dump()})\n"
            "        return {'ok': True}\n"
            "  and make the frontend POST {rating, comment} to /r/<token>/feedback")

    if args.no_write:
        add("INFO", a, "Skipped the write checks (--no-write)")
        return

    name = "[diagnostic] " + datetime.now().strftime("%H:%M:%S")
    st, _, raw = http("POST", base + "/campaigns", {"name": name, "template_key": "seminar_invite"}, H)
    camp = jd(raw) or {}
    cid = camp.get("id")
    if st not in (200, 201) or not cid:
        add("FAIL", a, f"Creating a campaign fails ({st}): {snip(raw)}", "POST /campaigns",
            "Frontend must send {name, template_key}. A 422 lists the missing field names; a 401 means no Authorization header")
        return
    ok(a, f"Campaign created ({cid})")

    lst = jd(http("GET", base + "/campaigns", headers=H)[2])
    items = lst.get("items", lst) if isinstance(lst, dict) else lst
    if not any(isinstance(c, dict) and c.get("id") == cid for c in (items or [])):
        add("FAIL", a, "A new campaign does not appear in GET /campaigns (this is the 'not in sync' bug)", "GET /campaigns vs POST /campaigns",
            "POST writes to one place and GET reads another (database vs api/app/mock_data.py CAMPAIGNS). Make both use the same store")
    else:
        ok(a, "New campaign appears in the list")
    st, _, raw = http("GET", f"{base}/campaigns/{cid}", headers=H)
    if st != 200:
        add("FAIL", a, f"GET /campaigns/{{id}} fails for a new campaign ({st})", "api/app/main.py get_campaign / _campaign()",
            "The lookup helper only knows the sample campaigns. Make _campaign() read the same store that POST /campaigns writes to")

    soon = (datetime.now(timezone.utc) + timedelta(days=30)).replace(microsecond=0)
    ev = {"title": "Diagnostic Seminar", "description": "test", "starts_at": soon.isoformat(),
          "ends_at": (soon + timedelta(hours=3)).isoformat(), "venue": "Hall A", "city": "Kochi", "fee_inr": 500, "capacity": 100}
    st, _, raw = http("PUT", f"{base}/campaigns/{cid}/event", ev, H)
    if st != 200:
        add("FAIL", a, f"Saving event details fails ({st}): {snip(raw)}", "PUT /campaigns/{id}/event",
            "Fields must be title, starts_at (ISO 8601 with offset), venue, city, fee_inr. Check the frontend sends exactly these names")
    else:
        got = jd(http("GET", f"{base}/campaigns/{cid}", headers=H)[2]) or {}
        if (got.get("event") or {}).get("title") != "Diagnostic Seminar":
            add("FAIL", a, "Saved event details are not returned by GET /campaigns/{id}", "PUT /event vs GET /campaigns/{id}",
                "PUT writes somewhere GET does not read. Use one store for both")
        else:
            ok(a, "Event details save and read back")

    sample = root / "docs" / "samples" / "sample-contacts.csv"
    csvb = sample.read_bytes() if sample.exists() else (
        b"name,phone,email,language,segment\nAsha Nair,+919876543210,asha@example.com,en,Faculty\n"
        b"Ravi Kumar,+919812345678,ravi@example.com,hi,Students\n")
    body, hh = multipart({"file": ("contacts.csv", csvb, "text/csv")})
    st, _, raw = http("POST", f"{base}/campaigns/{cid}/audience", headers={**H, **hh}, data=body)
    if st != 200:
        add("FAIL", a, f"CSV upload to the new campaign fails ({st}): {snip(raw)}", "POST /campaigns/{id}/audience",
            "404 'Campaign not found' means the import code looks the campaign up in sample data only. Use the same lookup as GET /campaigns/{id}")
    else:
        ok(a, "CSV import works on the new campaign")
    cts = jd(http("GET", f"{base}/campaigns/{cid}/contacts?limit=200", headers=H)[2]) or {}
    rows = cts.get("items", []) if isinstance(cts, dict) else cts
    if not rows:
        add("FAIL", a, "Imported contacts do not show up for the new campaign", "GET /campaigns/{id}/contacts",
            "Import and listing must use the same store. Check add_imported_contacts() writes to what list_contacts reads")
    else:
        ok(a, f"{len(rows)} contacts listed")

    for path, label in [("translations", "Translations"), ("analytics/funnel", "Funnel"),
                        ("analytics/by-language", "By-language table"), ("analytics/by-segment", "By-segment table")]:
        st, _, raw = http("GET", f"{base}/campaigns/{cid}/{path}", headers=H)
        if st != 200:
            add("FAIL", a, f"{label} page fails for a new campaign ({st}): {snip(raw, 100)}", f"GET /campaigns/{{id}}/{path}",
                "The handler only handles the sample campaign id. Make it look up the campaign you pass in")
        elif path == "translations" and not jd(raw):
            add("WARN", a, "A new campaign has no translations, so the translation screen will be empty", "GET /campaigns/{id}/translations",
                "Generate the 4 language messages from the template when the event is saved (even simple templates with the facts inserted)")

    link = (rows[0].get("registration_link") if rows else "") or ""
    token = link.rstrip("/").split("/")[-1]
    if not token:
        add("FAIL", a, "Contacts have no registration_link, so there is nothing for 'Register now' to open", "Contact.registration_link", "Generate a token per contact on import")
        return
    pub = lambda m, p, b=None: http(m, base + p, b)
    st, _, raw = pub("GET", f"/r/{token}")
    if st != 200:
        add("FAIL", a, f"Registration page for a new campaign's link fails ({st}): {snip(raw, 100)}", "GET /r/{token}",
            "Token lookup (_by_token) must search the campaign contacts you just imported, not only sample tokens")
        return
    ok(a, "Registration link opens")
    st, _, raw = pub("POST", f"/r/{token}/register", {"name": "Diag", "email": "diag@example.com", "party_size": 1, "consent": False})
    if st != 400:
        add("FAIL", a, f"Registering WITHOUT consent was accepted/failed oddly ({st})", "POST /r/{token}/register", "Return 400 when consent is false")
    st, _, raw = pub("POST", f"/r/{token}/register", {"name": "Diag", "email": "diag@example.com", "party_size": 1, "consent": True})
    if st != 200:
        add("FAIL", a, f"'Register now' fails ({st}): {snip(raw, 140)}", "POST /r/{token}/register",
            "422 = the frontend body is wrong. It must be {name, email, party_size (number), consent (true/false)}, snake_case")
    else:
        ok(a, "Registration works")
        st, _, raw = pub("POST", f"/r/{token}/pay")
        order = jd(raw) or {}
        if st != 200 or not order.get("order_id"):
            add("FAIL", a, f"Payment order fails ({st}): {snip(raw, 140)}", "POST /r/{token}/pay",
                "No JSON body is needed. If the frontend calls another path (/payments, /create-order) change it to /r/<token>/pay")
        else:
            st, _, raw = pub("POST", "/webhooks/payment", {"order_id": order["order_id"], "status": "paid"})
            if st != 200:
                add("FAIL", a, f"Payment webhook fails ({st}): {snip(raw)}", "POST /webhooks/payment", "Body is {order_id, status:'paid'}")
            stage = (jd(pub("GET", f"/r/{token}")[2]) or {}).get("stage")
            if stage != "paid":
                add("FAIL", a, f"After payment the stage is '{stage}', not 'paid'", "payment webhook",
                    "The webhook must update the same contact the registration page reads")
            else:
                ok(a, "Payment marks the person paid")
        f = jd(http("GET", f"{base}/campaigns/{cid}/analytics/funnel", headers=H)[2]) or {}
        if f.get("registered", 0) < 1:
            add("FAIL", a, f"Dashboard funnel did not count the new registration: {f}", "GET /campaigns/{id}/analytics/funnel",
                "Funnel must read the same stages the registration page writes")
        else:
            ok(a, "Dashboard counts the registration")
    st, _, raw = http("POST", f"{base}/campaigns/{cid}/retry", {"target": "non_responders", "fallback_channel": "whatsapp"}, H)
    if st != 200:
        add("FAIL", a, f"Retry non-responders fails ({st}): {snip(raw, 100)}", "POST /campaigns/{id}/retry", "Body: {target:'non_responders', fallback_channel:'whatsapp'|'sms'|'email'}")
    else:
        ok(a, "Retry works")
    if "/campaigns/{x}/email/test" in bp:
        st, _, raw = http("POST", f"{base}/campaigns/{cid}/email/test", {"to": "diag@example.com"}, H)
        if st != 200:
            add("FAIL", a, f"Email test fails ({st}): {snip(raw, 120)}", "POST /campaigns/{id}/email/test", "Read the message; for 400 save event details first")
        else:
            ok(a, f"Email test status: {(jd(raw) or {}).get('status')}")
    add("INFO", a, f"A campaign named '{name}' was created for this test", "", "Ignore or delete it later; it is only test data")


# ---------------------------------------------------------------- D. frontend static scan
PATH_RE = re.compile(r"""[`'"]((?:\$\{[^}]*\})?(?:https?://[^/`'"]+)?(?:/api)?/(?:campaigns|r|auth|me|templates|contacts|webhooks|audience|health|payments?|registrations?|register|feedback|events?|orders?|checkout|email|rsvp)[^`'"\s]*)[`'"]""")


def parse_tag(text, start):
    """Return (attrs, end_index_of_open_tag) for a tag that starts at text[start]."""
    i, depth, quote = start, 0, None
    while i < len(text):
        c = text[i]
        if quote:
            if c == quote and text[i - 1] != "\\":
                quote = None
        elif c in "\"'`":
            quote = c
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif c == ">" and depth <= 0 and text[i - 1] != "=":
            return text[start:i], i
        i += 1
    return text[start:], len(text)


def brace_value(attrs, name):
    m = re.search(name + r"\s*=\s*\{", attrs)
    if not m:
        return None
    i, depth = m.end(), 1
    j = i
    while j < len(attrs) and depth:
        depth += {"{": 1, "}": -1}.get(attrs[j], 0)
        j += 1
    return attrs[i:j - 1].strip()


def func_body(t, pos):
    """Text of the function whose name ends at pos: its braces, or the rest of the line for a short arrow."""
    arrow = t.find("=>", pos)
    brace = t.find("{", pos)
    nl = t.find("\n", pos)
    if brace == -1 or (arrow != -1 and 0 <= nl < brace and arrow < nl and t[arrow + 2:nl].strip() not in ("", "(")):
        return t[pos:nl if nl != -1 else len(t)]
    depth, i = 0, brace
    while i < len(t):
        depth += {"{": 1, "}": -1}.get(t[i], 0)
        i += 1
        if depth == 0:
            break
    return t[pos:i]


NET = re.compile(r"fetch\s*\(|axios|\bapi\w*\s*[.(]|await\s|mutate|useMutation|\.post\(|\.put\(|\.then\(|submit|dispatch|router\.push|navigate|window\.location|\bsend\w*\(|\bcall\w*\(")
KEYWORD = re.compile(r"regist|pay|submit|feedback|launch|retry|send|create|save|upload|approve|confirm|rsvp|book|reserve|join|next|continue", re.I)
HINT = [("pay", "POST /r/{token}/pay, then open the gateway with the returned order_id"),
        ("regist", "POST /r/{token}/register with {name, email, party_size, consent}"),
        ("rsvp", "POST /r/{token}/register with {name, email, party_size, consent}"),
        ("feedback", "POST /r/{token}/feedback with {rating, comment} (add the endpoint first, see the Workflow section)"),
        ("retry", "POST /campaigns/{id}/retry with {target:'non_responders', fallback_channel:'whatsapp'}"),
        ("create", "POST /campaigns with {name, template_key}, then use the returned id for every later page"),
        ("save", "PUT /campaigns/{id}/event with the event fields"),
        ("upload", "POST /campaigns/{id}/audience (multipart, field name 'file')"),
        ("send", "POST /campaigns/{id}/email/send"),
        ("launch", "POST /campaigns/{id}/launch")]


def check_frontend(web, base, spec, env, args):
    a = "Frontend"
    if not web.exists():
        add("FAIL", a, f"No web folder at {web}", "", "Run from the repo root, or pass --web PATH")
        return
    pkg = web / "package.json"
    if not pkg.exists():
        add("FAIL", a, "web/ has no package.json", "web/", "The generated frontend is missing or is in another folder; pass --web PATH")
        return
    p = json.loads(pkg.read_text(encoding="utf-8", errors="ignore") or "{}")
    deps = {**p.get("dependencies", {}), **p.get("devDependencies", {})}
    fw = "Next.js" if "next" in deps else "Vite" if "vite" in deps else "React scripts" if "react-scripts" in deps else "unknown"
    ok(a, f"Framework: {fw}; dev script: {p.get('scripts', {}).get('dev') or p.get('scripts', {}).get('start')}")
    if not (web / "node_modules").exists():
        add("FAIL", a, "node_modules is missing", "web/", "cd web ; npm install")

    envfiles = {}
    for n in (".env", ".env.local", ".env.development", ".env.development.local"):
        envfiles.update(read_env(web / n))
    files = list(source_files(web))
    texts = {f: f.read_text(encoding="utf-8", errors="ignore") for f in files}
    all_text = "\n".join(texts.values())

    # env variables for the API address
    names = set(re.findall(r"process\.env\.((?:NEXT_PUBLIC|REACT_APP)_[A-Z0-9_]+)", all_text)) | \
        set(re.findall(r"import\.meta\.env\.(VITE_[A-Z0-9_]+)", all_text))
    for n in sorted(names):
        if re.search(r"API|URL|BASE|BACKEND|HOST|SERVER", n):
            if n not in envfiles and n not in os.environ:
                add("FAIL", a, f"Frontend reads {n} but it is not defined anywhere: every request goes to the wrong address", "web/.env.local",
                    f"Create web/.env.local containing:  {n}={base}   then STOP and restart npm run dev (env files load only at start)")
            else:
                v = envfiles.get(n, "")
                if v and base.split("//")[-1] not in v:
                    add("WARN", a, f"{n}={v} but the API runs at {base}", "web/.env.local", f"Set {n}={base} and restart npm run dev")
                else:
                    ok(a, f"{n} is set")
    port = re.search(r":(\d+)", base).group(1)
    hard = {}
    for f, t in texts.items():
        for m in re.finditer(r"https?://(?:localhost|127\.0\.0\.1):(\d+)", t):
            if m.group(1) != port and m.group(1) not in ("3000", "3001", "5173"):
                hard.setdefault(m.group(1), []).append(f"{f.relative_to(web)}:{line_of(t, m.start())}")
    for pt, where in hard.items():
        add("FAIL", a, f"Frontend calls localhost:{pt} but the API runs on {port}", ", ".join(where[:3]),
            f"Change it to {base}, or better read it from the env variable")

    # hard-coded demo data
    ids = {}
    for f, t in texts.items():
        if any(s in f.parts for s in ("node_modules",)):
            continue
        for m in re.finditer(r"""['"`](cmp_\w+|ct_\w+|tok_ct_\w+)['"`]""", t):
            ids.setdefault(m.group(1), []).append(f"{f.relative_to(web)}:{line_of(t, m.start())}")
    if ids:
        w = [x for v in ids.values() for x in v][:5]
        add("FAIL", a, "Sample IDs are typed into the frontend (" + ", ".join(sorted(ids)[:4]) +
            "). A new campaign never reaches these pages: THIS IS WHY PAGES ARE OUT OF SYNC", ", ".join(w),
            "Replace each with the id from the URL or one shared place. Next.js: const {id} = useParams(); fetch(`${API}/campaigns/${id}/...`). "
            "After 'Create campaign' do router.push(`/campaigns/${created.id}/...`) using the id the API returned")
    mockf = [f for f in files if re.search(r"mock|sample|dummy|fixture|fake", f.name, re.I) and "test" not in f.name.lower()]
    lit = []
    for f, t in texts.items():
        for m in re.finditer(r"\bconst\s+(campaigns?|contacts?|events?|recipients?|attendees|registrations?|stats|analytics)\w*\s*(?::[^=]+)?=\s*\[", t):
            lit.append(f"{f.relative_to(web)}:{line_of(t, m.start())}")
    if mockf or lit:
        add("WARN", a, "Pages that use typed-in sample data instead of the API (they will never show your real campaign)",
            ", ".join([str(f.relative_to(web)) for f in mockf[:3]] + lit[:4]),
            "Replace the array with a fetch to the API, for example campaigns: GET /campaigns; contacts: GET /campaigns/{id}/contacts; "
            "funnel: GET /campaigns/{id}/analytics/funnel. Keep a loading and an error state")
    ls = set()
    for f, t in texts.items():
        for m in re.finditer(r"""(?:localStorage|sessionStorage)\.(?:get|set)Item\(\s*['"`]([^'"`]*(?:campaign|event|draft)[^'"`]*)['"`]""", t):
            ls.add(m.group(1))
    if ls:
        add("WARN", a, "Campaign data is kept in the browser (localStorage: " + ", ".join(sorted(ls)) + "), not on the server", "",
            "Fine for a draft, but each step must save to the API (PUT /campaigns/{id}/event ...) and later pages must read from the API")

    # API calls vs backend
    if spec:
        bp = {}
        for pth, ops in spec["paths"].items():
            bp.setdefault(norm(pth), set()).update(m.upper() for m in ops)
        used = {}
        for f, t in texts.items():
            for m in PATH_RE.finditer(t):
                before = t[max(0, m.start() - 45):m.start()]
                after = t[m.end():m.end() + 220].split("fetch(")[0].split(");")[0]
                mm = re.search(r"\.(get|post|put|patch|delete)\s*[<(]?[^(]*\(\s*$", before) or re.search(r"\.(get|post|put|patch|delete)\s*\(\s*$", before)
                meth = mm.group(1).upper() if mm else None
                if not meth:
                    am = re.search(r"method\s*:\s*['\"](\w+)['\"]", after)
                    meth = am.group(1).upper() if am else ("GET" if "fetch" in before else None)
                used.setdefault(norm(m.group(1)), []).append((meth, f"{f.relative_to(web)}:{line_of(t, m.start())}"))
        for pth, uses in sorted(used.items()):
            if pth not in bp:
                near = difflib.get_close_matches(pth, list(bp), n=1, cutoff=0.6)
                add("FAIL", a, f"Frontend calls {pth} but the backend has no such endpoint (button fails with 404)", ", ".join(w for _, w in uses[:3]),
                    ("Closest backend path: " + near[0] + ". Change the frontend path to it, or add the endpoint to api/app/main.py") if near
                    else "Add this endpoint to api/app/main.py, or point the button at an existing one (see docs/api-contract.md)")
            else:
                for meth, where in uses:
                    if meth and meth not in bp[pth]:
                        add("FAIL", a, f"Frontend uses {meth} on {pth} but the backend only allows {sorted(bp[pth])} (405 error)", where,
                            f"Change the method to {sorted(bp[pth])[0]}")
        # request field names
        props = {}
        for pth, ops in spec["paths"].items():
            for m_, op in ops.items():
                sch = (((op.get("requestBody") or {}).get("content") or {}).get("application/json") or {}).get("schema") or {}
                ref = sch.get("$ref", "").split("/")[-1]
                if ref and ref in spec.get("components", {}).get("schemas", {}):
                    for k in spec["components"]["schemas"][ref].get("properties", {}):
                        props.setdefault(k, set()).add(f"{m_.upper()} {pth}")
        for k, ends in sorted(props.items()):
            if "_" in k:
                camel = re.sub(r"_([a-z])", lambda m: m.group(1).upper(), k)
                if camel in all_text and not re.search(r"\b" + k + r"\b", all_text):
                    add("FAIL", a, f"Frontend sends '{camel}' but the backend expects '{k}' (422 error or value silently ignored)", sorted(ends)[0],
                        f"Rename '{camel}' to '{k}' in the request body (only in the object you send, you may keep camelCase for local variables)")
            if k in ("consent", "party_size", "template_key", "fee_inr", "starts_at") and not re.search(r"\b" + k + r"\b", all_text):
                camel = re.sub(r"_([a-z])", lambda m: m.group(1).upper(), k)
                if camel not in all_text:
                    add("WARN", a, f"The frontend never sends '{k}', which {sorted(ends)[0]} needs", sorted(ends)[0],
                        f"Add '{k}' to the request body for that call")

    # buttons
    dead = []
    for f, t in texts.items():
        if "components/ui" in str(f).replace("\\", "/"):
            continue
        for m in re.finditer(r"<(button|Button)\b", t):
            attrs, end = parse_tag(t, m.start())
            label = re.sub(r"\s+", " ", re.sub(r"<[^>]*>|\{[^}]*\}", " ", t[end + 1:end + 140].split("</")[0])).strip()[:40]
            where = f"{f.relative_to(web)}:{line_of(t, m.start())}"
            if re.search(r"\bdisabled\s*(=\s*\{\s*true\s*\}|$|\s)", attrs) and "disabled=" not in attrs:
                pass
            click = brace_value(attrs, "onClick")
            submit = re.search(r"type\s*=\s*[\"']submit[\"']", attrs)
            hint = next((h for k, h in HINT if re.search(k, label, re.I)), None)
            if click is None:
                inform = t.rfind("<form", 0, m.start()) > t.rfind("</form", 0, m.start()) and "onSubmit" in t[t.rfind("<form", 0, m.start()):m.start()]
                if re.search(r"\b(href|asChild|onPress|formAction)\b", attrs) or (submit and inform):
                    continue
                if KEYWORD.search(label) or submit:
                    dead.append((where, label, "has no onClick and is not a submit button inside a form with onSubmit", hint))
                continue
            if re.fullmatch(r"\(\s*\)\s*=>\s*\{\s*\}|undefined|null|\(\)\s*=>\s*null|noop", click):
                dead.append((where, label, "onClick does nothing", hint)); continue
            body = click
            if re.fullmatch(r"[A-Za-z_]\w*", click):
                d = re.search(r"(?:function\s+" + click + r"\b|const\s+" + click + r"\s*=)", t)
                if not d:
                    body = "__imported__"
                else:
                    body = func_body(t, d.end())
            if body != "__imported__" and not NET.search(body) and KEYWORD.search(label):
                why = "its handler never calls the API" + (" (only alert/console/toast)" if re.search(r"alert\(|console\.|toast", body) else "")
                dead.append((where, label, why, hint))
    for where, label, why, hint in dead[:25]:
        add("FAIL" if KEYWORD.search(label) and ("API" in why or "nothing" in why or "no onClick" in why) else "WARN", a,
            f"Button '{label or '(no text)'}' will not work: {why}", where, ("Wire it to: " + hint) if hint else
            "Give it an onClick that calls the backend with fetch and shows the result or error")

    tpl = [f"{f.relative_to(web)}:{line_of(t, m.start())}" for f, t in texts.items() for m in re.finditer(r"href\s*=\s*[\"']#[\"']", t)]
    if tpl:
        add("WARN", a, f"{len(tpl)} links point to '#' (they go nowhere)", ", ".join(tpl[:4]), "Replace with the real route or remove them for the demo")
    nocheck = []
    for f, t in texts.items():
        for m in re.finditer(r"await\s+fetch\(", t):
            if not re.search(r"\.ok\b|res(?:ponse)?\.status|catch", t[m.start():m.start() + 500]):
                nocheck.append(f"{f.relative_to(web)}:{line_of(t, m.start())}")
    if nocheck:
        add("WARN", a, f"{len(nocheck)} fetch calls never check for errors, so failures look like 'nothing happens'", ", ".join(nocheck[:4]),
            "After fetch: if (!res.ok) { const e = await res.json().catch(()=>({})); setError(e.detail || 'Something went wrong'); return; }  and show the error on screen")


# ---------------------------------------------------------------- report
def report(path):
    order = {"FAIL": 0, "WARN": 1, "INFO": 2, "OK": 3}
    lines = []
    counts = {k: sum(1 for f in FINDINGS if f[0] == k) for k in order}
    lines.append(f"EventReach diagnostic  {datetime.now():%Y-%m-%d %H:%M}   FAIL {counts['FAIL']}   WARN {counts['WARN']}   OK {counts['OK']}\n")
    n = 0
    for lvl in ("FAIL", "WARN", "INFO"):
        group = [f for f in FINDINGS if f[0] == lvl]
        if not group:
            continue
        lines.append("=" * 70 + f"\n{lvl}\n" + "=" * 70)
        for _, area, title, where, fix in group:
            n += 1
            lines.append(f"[{n}] ({area}) {title}")
            if where:
                lines.append(f"    where: {where}")
            if fix:
                lines.append("    fix:   " + fix.replace("\n", "\n           "))
            lines.append("")
    lines.append("OK: " + "; ".join(f[2] for f in FINDINGS if f[0] == "OK"))
    out = "\n".join(lines)
    print(out)
    try:
        Path(path).write_text(out, encoding="utf-8")
        print(f"\nSaved to {path}. Paste the FAIL and WARN items into the chat.")
    except Exception:
        pass
    return counts["FAIL"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8000")
    ap.add_argument("--web", default=None)
    ap.add_argument("--root", default=".")
    ap.add_argument("--email", default="demo@example.com")
    ap.add_argument("--password", default="demo-password")
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--report", default="diagnostic-report.txt")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    for _ in range(3):
        if (root / "api").exists():
            break
        root = root.parent
    env = read_env(root / ".env")
    web = Path(args.web) if args.web else root / "web"
    origin = (env.get("CORS_ORIGINS", "").split(",")[0].strip() or "http://localhost:3000")
    print(f"Checking repo at {root}\n")

    check_environment(root, env, args)
    check_database(root, env)
    up = check_backend(args.base, env, origin, args)
    spec, live = backend_spec(args.base, root)
    if up:
        live_probe(args.base, root, env, args, spec)
    elif spec is None:
        add("WARN", "API", "No openapi.json to compare the frontend with", "docs/openapi.json", "cd api ; python scripts/export_openapi.py")
    check_frontend(web, args.base, spec, env, args)
    sys.exit(1 if report(args.report) else 0)


if __name__ == "__main__":
    main()
