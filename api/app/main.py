"""EventReach mock API.

Every endpoint the frontend needs, returning realistic sample data.
State lives in memory and resets when the server restarts.
Real logic replaces these handlers one by one. Keep the schemas in schemas.py the same.
"""
import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from . import auth
from . import db as database
from . import mock_data as db
from .csv_import import CsvImportError, parse_contacts_csv
from .schemas import (
    BreakdownRow, Campaign, CampaignCreate, CampaignStatus, Contact, ContactPage,
    EventDetails, EventDraft, Funnel, ImportReport, Language, LaunchResult, LoginRequest, Me,
    Outcome, PaymentOrder, PaymentWebhook, PosterResult, RegisterRequest, RegisterResult,
    RegistrationPage, RetryRequest, RetryResult, RetryTarget, RowError, Stage, TestCallRequest,
    TestCallResult, Token, Translation, Template,
)

MAX_ATTEMPTS = 3
MAX_UPLOAD_BYTES = 2 * 1024 * 1024
ANSWERED = {Outcome.confirmed, Outcome.declined, Outcome.callback, Outcome.opted_out}
RESPONDED = {Outcome.confirmed, Outcome.declined, Outcome.callback}
NO_RESPONSE = {Outcome.pending, Outcome.no_answer, Outcome.voicemail, Outcome.failed, Outcome.wrong_number}
RETRYABLE = {Outcome.no_answer, Outcome.voicemail, Outcome.failed}

app = FastAPI(
    title="EventReach API (mock)", version="0.1.0",
    description="Mock API with sample data. Auth is not enforced yet. Full phone numbers are never returned.",
)
app.add_middleware(
    CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"], allow_headers=["*"],
)


# ---------- helpers ----------

def _campaign(campaign_id: str) -> Campaign:
    c = db.CAMPAIGNS.get(campaign_id)
    if not c:
        raise HTTPException(404, "Campaign not found")
    return c


def _contacts(campaign_id: str) -> list[Contact]:
    _campaign(campaign_id)
    return db.CONTACTS.get(campaign_id, [])


def _row(key: str, items: list[Contact]) -> BreakdownRow:
    n = len(items)
    confirmed = sum(c.last_outcome == Outcome.confirmed for c in items)
    return BreakdownRow(
        key=key, contacts=n,
        dialed=sum(c.attempts > 0 for c in items),
        answered=sum(c.last_outcome in ANSWERED for c in items),
        confirmed=confirmed,
        declined=sum(c.last_outcome == Outcome.declined for c in items),
        callback=sum(c.last_outcome == Outcome.callback for c in items),
        opted_out=sum(c.last_outcome == Outcome.opted_out for c in items),
        no_response=sum(c.last_outcome in NO_RESPONSE for c in items),
        confirmed_rate=round(confirmed / n, 3) if n else 0.0,
    )


def _group(items: list[Contact], key_fn) -> list[BreakdownRow]:
    groups: dict[str, list[Contact]] = {}
    for c in items:
        groups.setdefault(key_fn(c), []).append(c)
    return [_row(k, groups[k]) for k in sorted(groups)]


def _by_token(token: str) -> tuple[Campaign, Contact]:
    hit = db.TOKENS.get(token)
    if not hit:
        raise HTTPException(404, "This link is not valid")
    return _campaign(hit[0]), hit[1]


# ---------- health and mock assets ----------

@app.get("/health", tags=["System"])
def health():
    """Reports whether the API is up and whether the database is connected.

    Campaign, contact and analytics data are still mock until each endpoint moves to the database.
    """
    if not database.enabled():
        return {"status": "ok", "database": "not configured", "campaign_data": "mock"}
    try:
        with database.get_pool().connection() as conn:
            conn.execute("SELECT 1")
    except Exception:
        return JSONResponse({"status": "degraded", "database": "unreachable", "campaign_data": "mock"},
                            status_code=503)
    return {"status": "ok", "database": "connected", "campaign_data": "mock"}


@app.get("/mock/poster.svg", tags=["System"], include_in_schema=False)
def poster() -> Response:
    return Response(db.POSTER_SVG, media_type="image/svg+xml")


# ---------- auth (real when DATABASE_URL is set, mock otherwise) ----------

app.include_router(auth.router)


# ---------- templates ----------

@app.get("/templates", response_model=list[Template], tags=["Templates"])
def templates() -> list[Template]:
    return db.TEMPLATES


# ---------- campaigns ----------

@app.get("/campaigns", response_model=list[Campaign], tags=["Campaigns"])
def list_campaigns() -> list[Campaign]:
    return list(db.CAMPAIGNS.values())


@app.post("/campaigns", response_model=Campaign, status_code=201, tags=["Campaigns"])
def create_campaign(body: CampaignCreate) -> Campaign:
    if body.template_key not in {t.key for t in db.TEMPLATES}:
        raise HTTPException(422, "Unknown template")
    cid = f"cmp_{len(db.CAMPAIGNS) + 1:03d}"
    camp = Campaign(
        id=cid, name=body.name, template_key=body.template_key, status=CampaignStatus.draft,
        languages=[], channels=[], contact_count=0, created_at=datetime.now().astimezone(),
    )
    db.CAMPAIGNS[cid] = camp
    db.CONTACTS[cid] = []
    db.TRANSLATIONS[cid] = []
    return camp


@app.get("/campaigns/{campaign_id}", response_model=Campaign, tags=["Campaigns"])
def get_campaign(campaign_id: str) -> Campaign:
    return _campaign(campaign_id)


@app.put("/campaigns/{campaign_id}/event", response_model=Campaign, tags=["Campaigns"])
def save_event(campaign_id: str, event: EventDetails) -> Campaign:
    camp = _campaign(campaign_id)
    camp.event = event
    return camp


@app.post("/campaigns/{campaign_id}/poster", response_model=PosterResult, tags=["Campaigns"])
async def upload_poster(campaign_id: str, file: UploadFile = File(...)) -> PosterResult:
    camp = _campaign(campaign_id)
    camp.poster_url = "/mock/poster.svg"
    return PosterResult(poster_url=camp.poster_url)


@app.post("/campaigns/{campaign_id}/voice-note", response_model=EventDraft, tags=["Campaigns"])
async def upload_voice_note(campaign_id: str, file: UploadFile = File(...)) -> EventDraft:
    """Mock: ignores the audio and returns a fixed draft. Real version transcribes then extracts."""
    _campaign(campaign_id)
    return EventDraft(
        transcript=("We are holding an AI in Healthcare seminar on the fourteenth of November at ten in the "
                    "morning, in the Seminar Hall, Block A, in Kochi. Registration is five hundred rupees."),
        detected_language=Language.en,
        event=db.CAMPAIGNS["cmp_001"].event,
        needs_review=["ends_at", "capacity"],
    )


# ---------- audience ----------

@app.get("/audience/template.csv", tags=["Audience"])
def audience_template() -> Response:
    """A starter file the organizer can download, fill in and upload."""
    body = "name,phone,language,segment,email\nAsha Thomas,9000000011,ml,Students,asha@example.com\n"
    return Response(body, media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="contacts-template.csv"'})


@app.post("/campaigns/{campaign_id}/audience", response_model=ImportReport, tags=["Audience"])
async def import_audience(
    campaign_id: str,
    file: UploadFile = File(...),
    default_language: Language = Query(Language.en, description="Used when a row has no language or an unsupported one"),
) -> ImportReport:
    """Real import. Validates every row, skips bad ones, and adds the rest to the campaign.

    Uploading again adds only people who are not in the campaign yet.
    Numbers that opted out in any campaign are skipped.
    """
    _campaign(campaign_id)
    raw = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "The file is larger than 2 MB. Split it into smaller files.")
    try:
        result = parse_contacts_csv(
            raw, default_language=default_language,
            existing_hashes=set(db.PHONE_HASHES.get(campaign_id, {})),
            opted_out_hashes=db.OPT_OUT_HASHES,
        )
    except CsvImportError as exc:
        raise HTTPException(422, str(exc))
    db.add_imported_contacts(campaign_id, result.contacts)
    return result.report


@app.get("/campaigns/{campaign_id}/contacts", response_model=ContactPage, tags=["Audience"])
def list_contacts(
    campaign_id: str,
    language: Optional[Language] = None,
    segment: Optional[str] = None,
    outcome: Optional[Outcome] = None,
    stage: Optional[Stage] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> ContactPage:
    items = _contacts(campaign_id)
    if language:
        items = [c for c in items if c.language == language]
    if segment:
        items = [c for c in items if c.segment == segment]
    if outcome:
        items = [c for c in items if c.last_outcome == outcome]
    if stage:
        items = [c for c in items if c.stage == stage]
    return ContactPage(items=items[offset:offset + limit], total=len(items))


@app.post("/contacts/{contact_id}/opt-out", response_model=Contact, tags=["Audience"])
def opt_out(contact_id: str) -> Contact:
    for people in db.CONTACTS.values():
        for c in people:
            if c.id == contact_id:
                c.opted_out = True
                c.last_outcome = Outcome.opted_out
                phone = db.CONTACT_HASH.get(c.id)
                if phone:
                    db.OPT_OUT_HASHES.add(phone)  # blocks this number in every campaign
                return c
    raise HTTPException(404, "Contact not found")


# ---------- translations ----------

@app.get("/campaigns/{campaign_id}/translations", response_model=list[Translation], tags=["Translations"])
def list_translations(campaign_id: str) -> list[Translation]:
    _campaign(campaign_id)
    return db.TRANSLATIONS.get(campaign_id, [])


@app.put("/campaigns/{campaign_id}/translations/{language}", response_model=Translation, tags=["Translations"])
def save_translation(campaign_id: str, language: Language, body: Translation) -> Translation:
    _campaign(campaign_id)
    items = db.TRANSLATIONS.setdefault(campaign_id, [])
    for i, t in enumerate(items):
        if t.language == language:
            items[i] = body
            return body
    items.append(body)
    return body


# ---------- launch, test call, dispatch (B1 replaces the logic) ----------

@app.post("/campaigns/{campaign_id}/test-call", response_model=TestCallResult, tags=["Dispatch (B1)"])
def test_call(campaign_id: str, body: TestCallRequest) -> TestCallResult:
    _campaign(campaign_id)
    return TestCallResult(status="queued", message="Mock: no real call was placed.")


@app.post("/campaigns/{campaign_id}/launch", response_model=LaunchResult, tags=["Dispatch (B1)"])
def launch(campaign_id: str) -> LaunchResult:
    camp = _campaign(campaign_id)
    camp.status = CampaignStatus.running
    queued = sum(not c.opted_out for c in _contacts(campaign_id))
    return LaunchResult(status=camp.status, queued_contacts=queued)


@app.post("/campaigns/{campaign_id}/retry", response_model=RetryResult, tags=["Dispatch (B1)"])
def retry(campaign_id: str, body: RetryRequest) -> RetryResult:
    targets = RETRYABLE if body.target == RetryTarget.non_responders else {Outcome(body.target.value)}
    queued = skipped_opt = skipped_max = 0
    for c in _contacts(campaign_id):
        if c.last_outcome not in targets:
            continue
        if c.opted_out:
            skipped_opt += 1
        elif c.attempts >= MAX_ATTEMPTS:
            skipped_max += 1
        else:
            queued += 1
    return RetryResult(queued=queued, skipped_opted_out=skipped_opt, skipped_max_attempts=skipped_max)


# ---------- analytics (B1 replaces the logic) ----------

@app.get("/campaigns/{campaign_id}/analytics/funnel", response_model=Funnel, tags=["Analytics (B1)"])
def funnel(campaign_id: str) -> Funnel:
    items = _contacts(campaign_id)
    return Funnel(
        contacts=len(items),
        dialed=sum(c.attempts > 0 for c in items),
        answered=sum(c.last_outcome in ANSWERED for c in items),
        responded=sum(c.last_outcome in RESPONDED for c in items),
        confirmed=sum(c.last_outcome == Outcome.confirmed for c in items),
        registered=sum(c.stage in (Stage.registered, Stage.paid, Stage.attended) for c in items),
        paid=sum(c.stage in (Stage.paid, Stage.attended) for c in items),
    )


@app.get("/campaigns/{campaign_id}/analytics/by-language", response_model=list[BreakdownRow], tags=["Analytics (B1)"])
def by_language(campaign_id: str) -> list[BreakdownRow]:
    return _group(_contacts(campaign_id), lambda c: c.language.value)


@app.get("/campaigns/{campaign_id}/analytics/by-segment", response_model=list[BreakdownRow], tags=["Analytics (B1)"])
def by_segment(campaign_id: str) -> list[BreakdownRow]:
    return _group(_contacts(campaign_id), lambda c: c.segment)


# ---------- public registration (reached from a personal link) ----------

@app.get("/r/{token}", response_model=RegistrationPage, tags=["Registration (public)"])
def registration_page(token: str) -> RegistrationPage:
    camp, contact = _by_token(token)
    if not camp.event:
        raise HTTPException(404, "This event is not published yet")
    return RegistrationPage(
        first_name=contact.name.split()[0], language=contact.language, event=camp.event,
        poster_url=camp.poster_url, fee_inr=camp.event.fee_inr, stage=contact.stage,
        already_registered=contact.stage in (Stage.registered, Stage.paid, Stage.attended),
    )


@app.post("/r/{token}/register", response_model=RegisterResult, tags=["Registration (public)"])
def register(token: str, body: RegisterRequest) -> RegisterResult:
    camp, contact = _by_token(token)
    if not body.consent:
        raise HTTPException(400, "Consent is required to register")
    if contact.stage not in (Stage.paid, Stage.attended):
        contact.stage = Stage.registered
    fee = camp.event.fee_inr if camp.event else 0
    return RegisterResult(
        stage=contact.stage, amount_inr=fee,
        requires_payment=fee > 0 and contact.stage not in (Stage.paid, Stage.attended),
    )


@app.post("/r/{token}/pay", response_model=PaymentOrder, tags=["Registration (public)"])
def create_payment(token: str) -> PaymentOrder:
    camp, contact = _by_token(token)
    fee = camp.event.fee_inr if camp.event else 0
    if fee <= 0:
        raise HTTPException(400, "This event has no fee")
    if contact.stage in (Stage.paid, Stage.attended):
        raise HTTPException(409, "Already paid")
    return PaymentOrder(order_id=f"order_mock_{contact.id}", amount_inr=fee,
                        gateway_key_id="rzp_test_mock", status="created")


@app.post("/webhooks/payment", tags=["Registration (public)"])
def payment_webhook(body: PaymentWebhook) -> dict:
    """Mock of the gateway callback. The real one must verify the gateway signature first."""
    contact_id = body.order_id.removeprefix("order_mock_")
    for _, c in db.TOKENS.values():
        if c.id == contact_id and body.status == "paid":
            c.stage = Stage.paid
            return {"ok": True}
    raise HTTPException(404, "Order not found")
