"""EventReach API schemas.

These Pydantic models are the API contract. FastAPI turns them into
docs/openapi.json, which the frontend and code generation read.
If you change a field here, re-export the OpenAPI file and tell the team.
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


# ---------- Shared vocabulary (same words as docs/data-model.md) ----------

class Language(str, Enum):
    en = "en"
    hi = "hi"
    ml = "ml"
    ta = "ta"


class Outcome(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    declined = "declined"
    callback = "callback"
    no_answer = "no_answer"
    voicemail = "voicemail"
    opted_out = "opted_out"
    wrong_number = "wrong_number"
    failed = "failed"


class Stage(str, Enum):
    invited = "invited"
    responded = "responded"
    registered = "registered"
    paid = "paid"
    attended = "attended"


class Channel(str, Enum):
    call = "call"
    sms = "sms"
    email = "email"
    whatsapp = "whatsapp"
    instagram = "instagram"


class CampaignStatus(str, Enum):
    draft = "draft"
    ready = "ready"
    running = "running"
    completed = "completed"


# ---------- Auth ----------

class LoginRequest(BaseModel):
    email: str = Field(max_length=254, examples=["organizer@example.com"])
    password: str = Field(max_length=128)


class OrganizerSignup(BaseModel):
    name: str = Field(min_length=1, max_length=100, examples=["Asha Thomas"])
    email: str = Field(max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", examples=["organizer@example.com"])
    password: str = Field(min_length=8, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class Me(BaseModel):
    id: str
    name: str
    email: str
    role: str


# ---------- Templates ----------

class KeypadOption(BaseModel):
    digit: str = Field(examples=["1"])
    label: str = Field(examples=["Confirm"])
    outcome: Outcome


class Template(BaseModel):
    key: str = Field(examples=["seminar_invite"])
    name: str
    description: str
    variables: list[str]
    keypad_options: list[KeypadOption]
    requires_payment: bool = False
    default_channels: list[Channel]


# ---------- Campaigns and events ----------

class EventDetails(BaseModel):
    title: str
    description: Optional[str] = None
    starts_at: datetime
    ends_at: Optional[datetime] = None
    venue: str
    city: str
    fee_inr: int = Field(default=0, ge=0)
    capacity: Optional[int] = Field(default=None, ge=1)
    rsvp_deadline: Optional[datetime] = None

    @model_validator(mode="after")
    def _ends_after_start(self):
        if self.ends_at is not None:
            try:
                if self.ends_at < self.starts_at:
                    raise ValueError("ends_at must be after starts_at")
            except TypeError:
                raise ValueError("Send both times with a time zone, for example +05:30") from None
        return self


class CampaignCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200, examples=["AI in Healthcare Seminar"])
    template_key: str = Field(examples=["seminar_invite"])


class Campaign(BaseModel):
    id: str
    name: str
    template_key: str
    status: CampaignStatus
    event: Optional[EventDetails] = None
    languages: list[Language]
    channels: list[Channel]
    poster_url: Optional[str] = None
    contact_count: int
    created_at: datetime


class PosterResult(BaseModel):
    poster_url: str


class EventDraft(BaseModel):
    """Result of voice note transcription and extraction. The organizer reviews it before saving."""
    transcript: str
    detected_language: Language
    event: EventDetails
    needs_review: list[str] = Field(description="Field names the model was unsure about")


# ---------- Audience ----------

class RowError(BaseModel):
    row: int
    field: str
    message: str


class ImportReport(BaseModel):
    total_rows: int
    imported: int
    skipped: int
    errors: list[RowError] = Field(description="Rows that were skipped, with the reason")
    warnings: list[RowError] = Field(
        default_factory=list,
        description="Rows that were imported but need a look, for example an unsupported language or invalid email",
    )
    languages_found: dict[str, int]
    segments_found: dict[str, int]


class Contact(BaseModel):
    id: str
    name: str
    phone_masked: str = Field(description="The API never returns a full phone number")
    email: Optional[str] = None
    language: Language
    segment: str
    stage: Stage
    last_outcome: Outcome
    attempts: int
    opted_out: bool
    registration_link: str


class ContactPage(BaseModel):
    items: list[Contact]
    total: int


# ---------- Translations ----------

class Translation(BaseModel):
    language: Language
    call_script: str = Field(description="Text-to-speech script. {name} is replaced per contact")
    voicemail_script: str
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    whatsapp_text: Optional[str] = Field(default=None, description="{name} and {link} are replaced per contact")
    social_caption: Optional[str] = None
    back_translation_en: str = Field(description="English rendering of the translation, so the organizer can check it")
    approved: bool = False


# ---------- Launch and test ----------

class TestCallRequest(BaseModel):
    phone: str = Field(examples=["+919800000000"])
    language: Language


class TestCallResult(BaseModel):
    status: str
    message: str


class LaunchResult(BaseModel):
    status: CampaignStatus
    queued_contacts: int


# ---------- Analytics and retry (B1 owns the real logic) ----------

class Funnel(BaseModel):
    contacts: int
    dialed: int
    answered: int
    responded: int
    confirmed: int
    registered: int
    paid: int


class BreakdownRow(BaseModel):
    key: str = Field(description="Language code or segment name")
    contacts: int
    dialed: int
    answered: int
    confirmed: int
    declined: int
    callback: int
    opted_out: int
    no_response: int = Field(description="no_answer, voicemail, failed, wrong_number or pending")
    confirmed_rate: float = Field(description="confirmed divided by contacts, 0 to 1")


class RetryTarget(str, Enum):
    non_responders = "non_responders"
    no_answer = "no_answer"
    voicemail = "voicemail"
    failed = "failed"


class RetryRequest(BaseModel):
    target: RetryTarget = RetryTarget.non_responders
    fallback_channel: Optional[Channel] = Field(default=None, description="Also send this channel to people who cannot be called")


class RetryResult(BaseModel):
    queued: int
    skipped_opted_out: int
    skipped_max_attempts: int


# ---------- Public registration page (reached by personal link) ----------

class RegistrationPage(BaseModel):
    first_name: str
    language: Language
    event: EventDetails
    poster_url: Optional[str] = None
    fee_inr: int
    stage: Stage
    already_registered: bool
    event_full: bool = False
    expired: bool = False


class RegisterRequest(BaseModel):
    name: str
    email: Optional[str] = None
    party_size: int = Field(default=1, ge=1, le=10)
    consent: bool = Field(description="Must be true. The person agrees to the privacy notice")


class RegisterResult(BaseModel):
    stage: Stage
    requires_payment: bool
    amount_inr: int


class PaymentOrder(BaseModel):
    order_id: str
    amount_inr: int
    currency: str = "INR"
    gateway_key_id: str
    status: str


class PaymentWebhook(BaseModel):
    order_id: str
    status: str = Field(examples=["paid"])
