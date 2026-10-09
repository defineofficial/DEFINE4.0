"""EventReach mock API.

Every endpoint the frontend needs, returning realistic sample data.
State lives in memory and resets when the server restarts.
Real logic replaces these handlers one by one. Keep the schemas in schemas.py the same.
"""
import os
from datetime import datetime, timezone
from typing import Optional

import psycopg
from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, Response
from . import ai_budget, auth, calendar_invite, campaigns_db, channels, payments, qr_checkin, storage, storage_routes, template_engine, translation_engine, voice_pipeline
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
    description=("Campaigns and login use the database when DATABASE_URL is set. Everything else is still mock data. "
                 "Full phone numbers are never returned."),
)
app.add_middleware(
    CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"], allow_headers=["*"],
)

@app.exception_handler(ai_budget.AiBudgetExceeded)
def ai_budget_exceeded(_request, exc: ai_budget.AiBudgetExceeded) -> JSONResponse:
    """A paid AI call was refused because this month's cap is used up."""
    return JSONResponse(status_code=429, content={"detail": str(exc)})
# ---------- helpers ----------

_MOCK_ASSETS: dict[tuple[str, str], str] = {}  # (campaign_id, "poster" | "voice_note") -> storage key, mock mode only


def _campaign(campaign_id: str) -> Campaign:
    c = db.CAMPAIGNS.get(campaign_id)
    if not c:
        raise HTTPException(404, "Campaign not found")
    poster_key = _MOCK_ASSETS.get((campaign_id, "poster"))
    if poster_key:  # links expire, so hand out a fresh one each time
        c.poster_url = storage.signed_path(poster_key)
    return c


async def _store_upload(kind: str, campaign_id: str, file: UploadFile) -> storage.StoredFile:
    """Read an upload (never more than the limit plus one byte) and put it in private storage."""
    data = await file.read(storage.RULES[kind].max_bytes + 1)
    try:
        return storage.save(kind, campaign_id, data)
    except storage.StorageError as err:
        raise HTTPException(err.status_code, str(err)) from None


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

    Campaigns are real when the database is connected. Contacts, translations and analytics are still mock.
    """
    if not database.enabled():
        return {"status": "ok", "database": "not configured", "campaign_data": "mock"}
    try:
        with database.get_pool().connection() as conn:
            conn.execute("SELECT 1")
    except Exception:
        return JSONResponse({"status": "degraded", "database": "unreachable", "campaign_data": "mock"},
                            status_code=503)
    return {"status": "ok", "database": "connected", "campaign_data": "campaigns on database, rest mock"}


@app.get("/mock/poster.svg", tags=["System"], include_in_schema=False)
def poster() -> Response:
    return Response(db.POSTER_SVG, media_type="image/svg+xml")


# ---------- auth (real when DATABASE_URL is set, mock otherwise) ----------

app.include_router(auth.router)
app.include_router(storage_routes.router)


# ---------- templates ----------

@app.get("/templates", response_model=list[Template], tags=["Templates"])
def templates() -> list[Template]:
    return template_engine.list_templates()


# ---------- campaigns ----------

@app.get("/campaigns", response_model=list[Campaign], tags=["Campaigns"])
def list_campaigns(
    me: Me = Depends(auth.current_organizer), conn: Optional[psycopg.Connection] = Depends(database.get_conn),
) -> list[Campaign]:
    """Your campaigns only. Needs login when the database is on."""
    if conn is None:
        return [_campaign(cid) for cid in db.CAMPAIGNS]
    return campaigns_db.list_for(conn, me)


@app.post("/campaigns", response_model=Campaign, status_code=201, tags=["Campaigns"])
def create_campaign(
    body: CampaignCreate, me: Me = Depends(auth.current_organizer),
    conn: Optional[psycopg.Connection] = Depends(database.get_conn),
) -> Campaign:
    if conn is not None:
        return campaigns_db.create_for(conn, me, body)
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
def get_campaign(
    campaign_id: str, me: Me = Depends(auth.current_organizer),
    conn: Optional[psycopg.Connection] = Depends(database.get_conn),
) -> Campaign:
    if conn is None:
        return _campaign(campaign_id)
    return campaigns_db.get_for(conn, me, campaign_id)


@app.put("/campaigns/{campaign_id}/event", response_model=Campaign, tags=["Campaigns"])
def save_event(
    campaign_id: str, event: EventDetails, me: Me = Depends(auth.current_organizer),
    conn: Optional[psycopg.Connection] = Depends(database.get_conn),
) -> Campaign:
    if conn is not None:
        return campaigns_db.save_event_for(conn, me, campaign_id, event)
    camp = _campaign(campaign_id)
    camp.event = event
    return camp


@app.post("/campaigns/{campaign_id}/poster", response_model=PosterResult, tags=["Campaigns"])
async def upload_poster(
    campaign_id: str, file: UploadFile = File(...), me: Me = Depends(auth.current_organizer),
    conn: Optional[psycopg.Connection] = Depends(database.get_conn),
) -> PosterResult:
    """Real. Stores the poster privately (PNG, JPEG, WebP or PDF, up to 10 MB).

    `poster_url` is a signed link that stops working after a few minutes. Fetch the campaign again for a new one.
    """
    if conn is None:
        _campaign(campaign_id)
    else:
        campaigns_db.get_for(conn, me, campaign_id)  # 404 unless it is this organizer's campaign
    stored = await _store_upload("poster", campaign_id, file)
    if conn is None:
        storage.delete(_MOCK_ASSETS.get((campaign_id, "poster")))
        _MOCK_ASSETS[(campaign_id, "poster")] = stored.key
    else:
        try:
            old_key = campaigns_db.set_asset_path(conn, me, campaign_id, "poster", stored.key)
        except Exception:
            storage.delete(stored.key)  # do not leave an orphan file behind
            raise
        storage.delete(old_key)
    return PosterResult(poster_url=storage.signed_path(stored.key))


@app.post("/campaigns/{campaign_id}/voice-note", response_model=EventDraft, tags=["Campaigns"])
async def upload_voice_note(
    campaign_id: str, file: UploadFile = File(...), me: Me = Depends(auth.current_organizer),
    conn: Optional[psycopg.Connection] = Depends(database.get_conn),
) -> EventDraft:
    """The audio is stored privately for real (WAV, MP3, M4A, OGG, WebM or FLAC, up to 25 MB).

    The draft is still mock: transcription and extraction come in the voice note pipeline task.
    """
    if conn is None:
        _campaign(campaign_id)
    else:
        campaigns_db.get_for(conn, me, campaign_id)
    stored = await _store_upload("voice_note", campaign_id, file)
    if conn is None:
        storage.delete(_MOCK_ASSETS.get((campaign_id, "voice_note")))
        _MOCK_ASSETS[(campaign_id, "voice_note")] = stored.key
    else:
        try:
            old_key = campaigns_db.set_asset_path(conn, me, campaign_id, "voice_note", stored.key)
        except Exception:
            storage.delete(stored.key)
            raise
        storage.delete(old_key)
    audio_bytes = storage.read_bytes(stored.key)
    return voice_pipeline.process_voice_note(audio_bytes, filename=file.filename or "voice_note.mp3")


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
    camp = _campaign(campaign_id)
    items = db.TRANSLATIONS.get(campaign_id, [])
    if not items and camp.event and camp.languages:
        items = translation_engine.generate_translations(campaign_id, camp.event, camp.languages)
        db.TRANSLATIONS[campaign_id] = items
    return items


@app.post("/campaigns/{campaign_id}/translations/generate", response_model=list[Translation], tags=["Translations"])
def generate_campaign_translations(campaign_id: str) -> list[Translation]:
    camp = _campaign(campaign_id)
    if not camp.event:
        raise HTTPException(400, "Cannot generate translations without event details")
    langs = camp.languages or [Language.en, Language.hi, Language.ml, Language.ta]
    items = translation_engine.generate_translations(campaign_id, camp.event, langs)
    db.TRANSLATIONS[campaign_id] = items
    return items


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

    now = datetime.now(timezone.utc)
    expired = bool(camp.event.rsvp_deadline and now > camp.event.rsvp_deadline)
    reg_count = sum(c.stage in (Stage.registered, Stage.paid, Stage.attended) for c in _contacts(camp.id))
    event_full = bool(camp.event.capacity and reg_count >= camp.event.capacity)

    return RegistrationPage(
        first_name=contact.name.split()[0],
        language=contact.language,
        event=camp.event,
        poster_url=camp.poster_url,
        fee_inr=camp.event.fee_inr,
        stage=contact.stage,
        already_registered=contact.stage in (Stage.registered, Stage.paid, Stage.attended),
        event_full=event_full,
        expired=expired,
    )


@app.post("/r/{token}/register", response_model=RegisterResult, tags=["Registration (public)"])
def register(token: str, body: RegisterRequest) -> RegisterResult:
    camp, contact = _by_token(token)
    if not body.consent:
        raise HTTPException(400, "Consent is required to register")

    now = datetime.now(timezone.utc)
    if camp.event and camp.event.rsvp_deadline and now > camp.event.rsvp_deadline:
        raise HTTPException(400, "Registration for this event has closed")

    if camp.event and camp.event.capacity:
        reg_count = sum(c.stage in (Stage.registered, Stage.paid, Stage.attended) for c in _contacts(camp.id))
        if reg_count >= camp.event.capacity and contact.stage not in (Stage.registered, Stage.paid, Stage.attended):
            raise HTTPException(409, "This event is at full capacity")

    if contact.stage not in (Stage.paid, Stage.attended):
        contact.stage = Stage.registered
    fee = camp.event.fee_inr if camp.event else 0
    return RegisterResult(
        stage=contact.stage, amount_inr=fee,
        requires_payment=fee > 0 and contact.stage not in (Stage.paid, Stage.attended),
    )


@app.get("/r/{token}/calendar.ics", tags=["Registration (public)"])
def download_calendar_invite(token: str) -> Response:
    """Download standard .ics iCalendar file for the event."""
    camp, contact = _by_token(token)
    if not camp.event:
        raise HTTPException(404, "Event details not found")
    ics_body = calendar_invite.generate_ics(camp.event, contact.name)
    filename = f"{camp.name.replace(' ', '_').lower()}.ics"
    return Response(
        content=ics_body,
        media_type="text/calendar",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/r/{token}/ticket.svg", tags=["Registration (public)"])
def get_ticket_svg(token: str) -> Response:
    """Renders visual SVG admission pass with QR representation."""
    camp, contact = _by_token(token)
    svg_body = qr_checkin.generate_ticket_svg(token, contact.name, camp.name)
    return Response(content=svg_body, media_type="image/svg+xml")


@app.post("/r/{token}/check-in", tags=["Registration (public)"])
def check_in_attendee(token: str) -> dict:
    """Staff QR scan check-in endpoint: marks person as Attended."""
    _, contact = _by_token(token)
    return qr_checkin.process_checkin(contact)


@app.post("/r/{token}/pay", response_model=PaymentOrder, tags=["Registration (public)"])
def create_payment(token: str) -> PaymentOrder:
    camp, contact = _by_token(token)
    fee = camp.event.fee_inr if camp.event else 0
    if fee <= 0:
        raise HTTPException(400, "This event has no fee")
    if contact.stage in (Stage.paid, Stage.attended):
        raise HTTPException(409, "Already paid")
    return payments.create_order(contact.id, fee, camp.id)


@app.post("/webhooks/payment", tags=["Registration (public)"])
async def payment_webhook(
    body: PaymentWebhook,
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None),
) -> dict:
    """Gateway callback. Verifies gateway signature when header is present and safely idempotently marks order paid."""
    if x_razorpay_signature:
        raw_body = await request.body()
        if not payments.verify_webhook_signature(raw_body, x_razorpay_signature):
            raise HTTPException(400, "Invalid webhook signature")

    contact_id = body.order_id.removeprefix("order_mock_")
    matched_contact = None
    order_rec = payments.get_order(body.order_id) or {}
    for _, c in db.TOKENS.values():
        if c.id == contact_id or c.id == order_rec.get("contact_id"):
            matched_contact = c
            break

    if not matched_contact and not payments.get_order(body.order_id):
        raise HTTPException(404, "Order not found")

    result = payments.process_payment_webhook(body.order_id, body.status)
    if matched_contact and body.status.lower() in ("paid", "captured", "success"):
        matched_contact.stage = Stage.paid
        if matched_contact.email:
            channels.send_email(
                to_email=matched_contact.email,
                subject="Payment Receipt: Registration Confirmed",
                body=f"Dear {matched_contact.name},\n\nYour payment for order {body.order_id} has been received. Your registration is confirmed!",
            )
    return result


# ---------- short links ----------

@app.get("/s/{code}", tags=["Short Links"], include_in_schema=False)
def short_link_redirect(code: str) -> RedirectResponse:
    target = channels.resolve_short_link(code)
    if not target:
        raise HTTPException(404, "Short link not found or expired")
    return RedirectResponse(url=target, status_code=307)

