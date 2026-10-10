"""EventReach mock API.

Every endpoint the frontend needs, returning realistic sample data.
State lives in memory and resets when the server restarts.
Real logic replaces these handlers one by one. Keep the schemas in schemas.py the same.
"""
from . import email_routes
from . import feedback_routes

import os
from datetime import datetime, timezone
from typing import Optional

import psycopg
from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, Response
from . import ai_budget, auth, calendar_invite, campaigns_db, channels, contacts_db, event_versioning, glossary, outreach, payments, preflight, qr_checkin, registration_db, storage, storage_routes, template_engine, translation_engine, voice_pipeline
from . import db as database
from . import mock_data as db
from .csv_import import CsvImportError, parse_contacts_csv
from .schemas import (
    BreakdownRow, Campaign, CampaignCreate, CampaignStatus, Channel, Contact, ContactPage,
    EventDetails, EventDraft, Funnel, ImportReport, Language, LaunchResult, LoginRequest, Me,
    Outcome, OutreachItem, OutreachLog, PaymentOrder, PaymentWebhook, PosterResult, PreflightResult, RegisterRequest, RegisterResult,
    RegistrationPage, RetryRequest, RetryResult, RetryTarget, RowError, Stage, TestCallRequest,
    TestCallResult, TestSendRequest, Token, Translation, Template,
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
    # When the database is on, ALL campaign IDs route through campaigns_db.
    # Mock IDs (cmp_001, cmp_002) are only present when DATABASE_URL is empty.
    if conn is not None:
        return campaigns_db.save_event_for(conn, me, campaign_id, event)
    camp = _campaign(campaign_id)
    
    current_ver = getattr(camp, "_event_version", 1)
    current_hash = getattr(camp, "_event_content_hash", None)
    
    new_ver, new_hash, changed = event_versioning.update_event_record(
        existing_event=camp.event,
        existing_version=current_ver,
        existing_hash=current_hash,
        new_event=event,
    )
    
    camp.event = event
    setattr(camp, "_event_version", new_ver)
    setattr(camp, "_event_content_hash", new_hash)
    
    if event.title and event.title.strip():
        camp.name = event.title.strip()
        
    # Check existing translations and propagate staleness
    existing_trans = db.TRANSLATIONS.get(campaign_id, [])
    if existing_trans:
        updated_trans, any_stale = event_versioning.propagate_staleness(existing_trans, new_ver, new_hash)
        db.TRANSLATIONS[campaign_id] = updated_trans
        if any_stale:
            camp.status = CampaignStatus.needs_regeneration
        else:
            camp.status = CampaignStatus.details_approved
    else:
        camp.status = CampaignStatus.details_approved

    return camp


@app.post("/campaigns/{campaign_id}/poster", response_model=PosterResult, tags=["Campaigns"])
async def upload_poster(
    campaign_id: str, file: UploadFile = File(...), me: Me = Depends(auth.current_organizer),
    conn: Optional[psycopg.Connection] = Depends(database.get_conn),
) -> PosterResult:
    """Real. Stores the poster privately (PNG, JPEG, WebP or PDF, up to 10 MB).

    `poster_url` is a signed link that stops working after a few minutes. Fetch the campaign again for a new one.
    """
    is_db_campaign = conn is not None and campaign_id not in db.CAMPAIGNS
    if is_db_campaign:
        campaigns_db.get_for(conn, me, campaign_id)
    else:
        _campaign(campaign_id)
    stored = await _store_upload("poster", campaign_id, file)
    if not is_db_campaign:
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


@app.get("/settings/ai", tags=["Settings"])
def get_ai_settings():
    provider = os.getenv("AI_PROVIDER", "gemini" if os.getenv("GEMINI_API_KEY") else ("groq" if os.getenv("GROQ_API_KEY") else ("openai" if os.getenv("LLM_API_KEY") else "none")))
    has_key = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GROQ_API_KEY") or os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY"))
    return {"provider": provider, "has_key": has_key}


@app.post("/settings/ai", tags=["Settings"])
async def set_ai_settings(request: Request):
    body = await request.json()
    provider = body.get("provider", "gemini")
    api_key = body.get("api_key", "").strip()
    os.environ["AI_PROVIDER"] = provider
    if provider == "gemini":
        os.environ["GEMINI_API_KEY"] = api_key
    elif provider == "groq":
        os.environ["GROQ_API_KEY"] = api_key
    else:
        os.environ["LLM_API_KEY"] = api_key
        os.environ["OPENAI_API_KEY"] = api_key
    return {"status": "ok", "provider": provider, "configured": bool(api_key)}


@app.post("/campaigns/{campaign_id}/voice-note", response_model=EventDraft, tags=["Campaigns"])
async def upload_voice_note(
    campaign_id: str, file: UploadFile = File(...),
    x_ai_key: Optional[str] = Header(None),
    x_ai_provider: Optional[str] = Header(None),
    me: Me = Depends(auth.current_organizer),
    conn: Optional[psycopg.Connection] = Depends(database.get_conn),
) -> EventDraft:
    """The audio is stored privately for real (WAV, MP3, M4A, OGG, WebM or FLAC, up to 25 MB).

    The draft is transcribed and extracted with the AI voice pipeline.
    """
    is_db_campaign = conn is not None and campaign_id not in db.CAMPAIGNS
    if is_db_campaign:
        campaigns_db.get_for(conn, me, campaign_id)
    else:
        _campaign(campaign_id)
    stored = await _store_upload("voice_note", campaign_id, file)
    if not is_db_campaign:
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
    return voice_pipeline.process_voice_note(
        audio_bytes,
        filename=file.filename or "voice_note.mp3",
        custom_key=x_ai_key,
        provider=x_ai_provider,
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
    me: Me = Depends(auth.current_organizer),
    conn: Optional[psycopg.Connection] = Depends(database.get_conn),
) -> ImportReport:
    """Real import. Validates every row, skips bad ones, and adds the rest to the campaign.

    Uploading again adds only people who are not in the campaign yet.
    Numbers that opted out in any campaign are skipped.
    Phone numbers are stored encrypted (phone_enc) and hashed (phone_hash); full numbers never leave this function.
    """
    raw = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "The file is larger than 2 MB. Split it into smaller files.")

    if conn is not None:
        # Database mode: ownership check + dedup from real tables.
        # campaigns_db.get_for raises 404 if the campaign belongs to someone else.
        campaigns_db.get_for(conn, me, campaign_id)
        existing = contacts_db.get_existing_hashes(conn, campaign_id)
        opted_out = contacts_db.get_opted_out_hashes(conn)
        try:
            result = parse_contacts_csv(
                raw, default_language=default_language,
                existing_hashes=existing,
                opted_out_hashes=opted_out,
            )
        except CsvImportError as exc:
            raise HTTPException(422, str(exc))
        try:
            contacts_db.add_contacts_for(conn, me, campaign_id, result.contacts)
        except ValueError as exc:
            raise HTTPException(404, str(exc)) from exc
        return result.report

    # Mock mode: fall back to in-memory store.
    _campaign(campaign_id)
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
    me: Me = Depends(auth.current_organizer),
    conn: Optional[psycopg.Connection] = Depends(database.get_conn),
) -> ContactPage:
    """List contacts for a campaign. Requires login when the database is on."""
    if conn is not None:
        items, total = contacts_db.list_for_campaign(
            conn, me, campaign_id,
            language=language.value if language else None,
            segment=segment,
            outcome=outcome.value if outcome else None,
            stage=stage.value if stage else None,
            limit=limit,
            offset=offset,
        )
        return ContactPage(items=items, total=total)
    # Mock mode.
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

@app.get("/campaigns/{campaign_id}/languages", tags=["Translations"])
def list_campaign_languages(
    campaign_id: str,
    me: Me = Depends(auth.current_organizer),
    conn: Optional[psycopg.Connection] = Depends(database.get_conn),
):
    """Returns languages found in audience with counts."""
    if conn is not None and campaign_id not in db.CAMPAIGNS:
        return contacts_db.count_languages_for(conn, me, campaign_id)
    contacts = _contacts(campaign_id)
    counts: dict[str, int] = {}
    for c in contacts:
        l = c.language.value if hasattr(c.language, "value") else str(c.language)
        counts[l] = counts.get(l, 0) + 1
    return [{"language": k, "count": v} for k, v in counts.items()]


@app.get("/campaigns/{campaign_id}/translations", response_model=list[Translation], tags=["Translations"])
def list_translations(campaign_id: str) -> list[Translation]:
    camp = _campaign(campaign_id)
    items = db.TRANSLATIONS.get(campaign_id, [])
    if not items and camp.event and camp.languages:
        ev_ver = getattr(camp, "_event_version", 1)
        items = translation_engine.generate_translations(campaign_id, camp.event, camp.languages, event_version=ev_ver)
        db.TRANSLATIONS[campaign_id] = items
    return items


@app.post("/campaigns/{campaign_id}/translations/generate", response_model=list[Translation], tags=["Translations"])
def generate_campaign_translations(campaign_id: str) -> list[Translation]:
    camp = _campaign(campaign_id)
    if not camp.event:
        raise HTTPException(400, "Cannot generate translations without event details")
    langs = camp.languages or [Language.en, Language.hi, Language.ml, Language.ta]
    ev_ver = getattr(camp, "_event_version", 1)
    items = translation_engine.generate_translations(campaign_id, camp.event, langs, event_version=ev_ver)
    db.TRANSLATIONS[campaign_id] = items
    return items


@app.put("/campaigns/{campaign_id}/translations/{language}", response_model=Translation, tags=["Translations"])
def save_translation(campaign_id: str, language: Language, body: Translation) -> Translation:
    camp = _campaign(campaign_id)
    items = db.TRANSLATIONS.setdefault(campaign_id, [])
    
    # If edited by hand, set status="edited" unless explicitly approved
    t_dict = body.model_dump()
    if body.approved:
        t_dict["status"] = "approved"
    else:
        t_dict["status"] = "edited"

    saved_translation = Translation(**t_dict)
    found = False
    for i, t in enumerate(items):
        if t.language == language:
            items[i] = saved_translation
            found = True
            break
    if not found:
        items.append(saved_translation)

    # Check if all required languages for this campaign are approved
    req_langs = set(camp.languages) if camp.languages else {Language.en}
    approved_langs = {t.language for t in items if t.approved}
    if req_langs.issubset(approved_langs):
        camp.status = CampaignStatus.translations_approved

    return saved_translation


# ---------- outreach content & test send ----------

@app.post("/campaigns/{campaign_id}/content/generate", response_model=list[OutreachItem], tags=["Content"])
def generate_content(campaign_id: str) -> list[OutreachItem]:
    camp = _campaign(campaign_id)
    if not camp.event:
        raise HTTPException(400, "Cannot generate content without an approved event record")
    langs = camp.languages or [Language.en]
    chans = camp.channels or [Channel.call, Channel.sms, Channel.email, Channel.whatsapp]
    ev_ver = getattr(camp, "_event_version", 1)
    
    items = outreach.generate_campaign_content(
        campaign_id=campaign_id,
        template_key=camp.template_key,
        event=camp.event,
        languages=langs,
        channels=chans,
        poster_url=camp.poster_url,
        event_version=ev_ver,
    )
    return items


@app.get("/campaigns/{campaign_id}/content", response_model=list[OutreachItem], tags=["Content"])
def list_content(campaign_id: str) -> list[OutreachItem]:
    _campaign(campaign_id)
    return outreach.list_campaign_content(campaign_id)


@app.get("/campaigns/{campaign_id}/content/{item_id}", response_model=OutreachItem, tags=["Content"])
def get_content_item(campaign_id: str, item_id: str) -> OutreachItem:
    _campaign(campaign_id)
    items = outreach.list_campaign_content(campaign_id)
    for item in items:
        if item.id == item_id:
            return item
    raise HTTPException(404, "Content item not found")


@app.put("/campaigns/{campaign_id}/content/{item_id}", response_model=OutreachItem, tags=["Content"])
def save_content_item(campaign_id: str, item_id: str, body: OutreachItem) -> OutreachItem:
    camp = _campaign(campaign_id)
    t_dict = body.model_dump()
    if body.approved:
        t_dict["status"] = "approved"
    else:
        t_dict["status"] = "edited"

    saved = OutreachItem(**t_dict)
    updated = outreach.update_content_item(campaign_id, item_id, saved)
    
    # Check if all items for campaign are approved
    all_items = outreach.list_campaign_content(campaign_id)
    if all_items and all(it.approved for it in all_items):
        camp.status = CampaignStatus.content_ready

    return updated


@app.post("/campaigns/{campaign_id}/test-send", tags=["Content"])
def test_send(
    campaign_id: str,
    body: TestSendRequest,
    me: Me = Depends(auth.current_organizer),
) -> dict:
    """Dispatches a test send for non-call channels to organizer's target address/number."""
    camp = _campaign(campaign_id)
    res = outreach.send_test_message(
        channel=body.channel,
        target=body.target,
        subject=f"Test Send: {camp.name}",
        body=f"Test notification for {camp.name}. Venue: {camp.event.venue if camp.event else 'Main Hall'}",
        poster_url=camp.poster_url,
    )
    return res


# ---------- launch, test call, dispatch ----------

@app.post("/campaigns/{campaign_id}/preflight", response_model=PreflightResult, tags=["Launch"])
def preflight_check(
    campaign_id: str,
    me: Me = Depends(auth.current_organizer),
    conn: Optional[psycopg.Connection] = Depends(database.get_conn),
) -> PreflightResult:
    camp = campaigns_db.get_for(conn, me, campaign_id) if conn is not None and campaign_id not in db.CAMPAIGNS else _campaign(campaign_id)
    translations = db.TRANSLATIONS.get(campaign_id, [])
    contact_count = camp.contact_count if hasattr(camp, "contact_count") else len(_contacts(campaign_id))
    return preflight.run_preflight_checks(camp, translations, contact_count)


@app.post("/campaigns/{campaign_id}/test-call", response_model=TestCallResult, tags=["Dispatch (B1)"])
def test_call(campaign_id: str, body: TestCallRequest) -> TestCallResult:
    _campaign(campaign_id)
    return TestCallResult(status="queued", message="Mock: no real call was placed.")


@app.post("/campaigns/{campaign_id}/launch", response_model=LaunchResult, tags=["Dispatch (B1)"])
def launch(
    campaign_id: str,
    me: Me = Depends(auth.current_organizer),
    conn: Optional[psycopg.Connection] = Depends(database.get_conn),
) -> LaunchResult:
    camp = campaigns_db.get_for(conn, me, campaign_id) if conn is not None and campaign_id not in db.CAMPAIGNS else _campaign(campaign_id)
    translations = db.TRANSLATIONS.get(campaign_id, [])
    contact_count = camp.contact_count if hasattr(camp, "contact_count") else len(_contacts(campaign_id))
    
    # Preflight launch gate check
    pf = preflight.run_preflight_checks(camp, translations, contact_count)
    if not pf.can_launch and os.getenv("BYPASS_PREFLIGHT", "false").lower() not in ("true", "1"):
        raise HTTPException(400, f"Launch blocked by preflight checks: {', '.join(pf.blockers)}")

    if conn is not None and campaign_id not in db.CAMPAIGNS:
        c_res = campaigns_db.launch_for(conn, me, campaign_id)
        return LaunchResult(status=c_res.status, queued_contacts=c_res.contact_count)
    
    camp.status = CampaignStatus.launched
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
def funnel(
    campaign_id: str,
    conn: Optional[psycopg.Connection] = Depends(database.get_conn),
) -> Funnel:
    if conn is not None:
        return registration_db.get_funnel_db(conn, campaign_id)
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
def by_language(
    campaign_id: str,
    conn: Optional[psycopg.Connection] = Depends(database.get_conn),
) -> list[BreakdownRow]:
    if conn is not None:
        return registration_db.get_by_language_db(conn, campaign_id)
    return _group(_contacts(campaign_id), lambda c: c.language.value)


@app.get("/campaigns/{campaign_id}/analytics/by-segment", response_model=list[BreakdownRow], tags=["Analytics (B1)"])
def by_segment(
    campaign_id: str,
    conn: Optional[psycopg.Connection] = Depends(database.get_conn),
) -> list[BreakdownRow]:
    if conn is not None:
        return registration_db.get_by_segment_db(conn, campaign_id)
    return _group(_contacts(campaign_id), lambda c: c.segment)


# ---------- public registration (reached from a personal link) ----------

@app.get("/r/{token}", response_model=RegistrationPage, tags=["Registration (public)"])
def registration_page(
    token: str,
    request: Request,
    conn: Optional[psycopg.Connection] = Depends(database.get_conn),
) -> RegistrationPage:
    client_ip = request.client.host if request and request.client else ""
    registration_db.check_rate_limit(client_ip)
    return registration_db.get_public_registration_page(conn, token)


@app.post("/r/{token}/register", response_model=RegisterResult, tags=["Registration (public)"])
def register(
    token: str,
    body: RegisterRequest,
    request: Request,
    conn: Optional[psycopg.Connection] = Depends(database.get_conn),
) -> RegisterResult:
    client_ip = request.client.host if request and request.client else ""
    registration_db.check_rate_limit(client_ip)
    return registration_db.register_public_attendee(conn, token, body)


@app.get("/r/{token}/calendar.ics", tags=["Registration (public)"])
def download_calendar_invite(token: str) -> Response:
    """Download standard .ics iCalendar file for the event."""
    try:
        camp, contact = _by_token(token)
        if not camp.event:
            raise registration_db._not_found_token()
        ics_body = calendar_invite.generate_ics(camp.event, contact.name)
        filename = f"{camp.name.replace(' ', '_').lower()}.ics"
        return Response(
            content=ics_body,
            media_type="text/calendar",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception:
        raise registration_db._not_found_token()


@app.get("/r/{token}/ticket.svg", tags=["Registration (public)"])
def get_ticket_svg(token: str) -> Response:
    """Renders visual SVG admission pass with QR representation."""
    try:
        camp, contact = _by_token(token)
        svg_body = qr_checkin.generate_ticket_svg(token, contact.name, camp.name)
        return Response(content=svg_body, media_type="image/svg+xml")
    except Exception:
        raise registration_db._not_found_token()


@app.post("/r/{token}/check-in", tags=["Registration (public)"])
def check_in_attendee(token: str) -> dict:
    """Staff QR scan check-in endpoint: marks person as Attended."""
    try:
        _, contact = _by_token(token)
        return qr_checkin.process_checkin(contact)
    except Exception:
        raise registration_db._not_found_token()


@app.post("/r/{token}/pay", response_model=PaymentOrder, tags=["Registration (public)"])
def create_payment(
    token: str,
    request: Request,
    conn: Optional[psycopg.Connection] = Depends(database.get_conn),
) -> PaymentOrder:
    client_ip = request.client.host if request and request.client else ""
    registration_db.check_rate_limit(client_ip)
    return registration_db.create_public_payment_order(conn, token)


@app.post("/webhooks/payment", tags=["Registration (public)"])
async def payment_webhook(
    body: PaymentWebhook,
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None),
    conn: Optional[psycopg.Connection] = Depends(database.get_conn),
) -> dict:
    """Gateway callback. Verifies gateway signature when header is present and safely idempotently marks order paid."""
    raw_body = await request.body()
    return registration_db.process_gateway_webhook(
        conn=conn,
        raw_body=raw_body,
        signature_header=x_razorpay_signature,
        body_dict=body.model_dump(),
    )


# ---------- short links ----------

@app.get("/s/{code}", tags=["Short Links"], include_in_schema=False)
def short_link_redirect(code: str) -> RedirectResponse:
    target = channels.resolve_short_link(code)
    if not target:
        raise HTTPException(404, "Short link not found or expired")
    return RedirectResponse(url=target, status_code=307)

app.include_router(email_routes.router)
app.include_router(feedback_routes.router)