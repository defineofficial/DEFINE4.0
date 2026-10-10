"""In-memory sample data for the mock API.

All people below are invented. Phone numbers are masked placeholders.
Translations are sample text and have not been reviewed by a native speaker.
"""
import os
import secrets
from datetime import datetime, timedelta, timezone

from .csv_import import ParsedContact
from .schemas import (
    Campaign, CampaignStatus, Channel, Contact, EventDetails, KeypadOption,
    Language, Outcome, Stage, Template, Translation,
)

IST = timezone(timedelta(hours=5, minutes=30))
WEB_BASE_URL = os.getenv("WEB_BASE_URL", "http://localhost:3000")

O, S = Outcome, Stage

# ---------- Templates (the four presets) ----------

_STOP = KeypadOption(digit="9", label="Stop these calls", outcome=O.opted_out)

TEMPLATES = [
    Template(
        key="seminar_invite", name="Seminar invite",
        description="Invite people to a seminar or workshop and collect RSVPs.",
        variables=["name", "event_title", "date", "time", "venue", "link"],
        keypad_options=[
            KeypadOption(digit="1", label="Confirm", outcome=O.confirmed),
            KeypadOption(digit="2", label="Decline", outcome=O.declined),
            KeypadOption(digit="3", label="Call me back", outcome=O.callback), _STOP,
        ],
        requires_payment=False,
        default_channels=[Channel.call, Channel.sms, Channel.email, Channel.whatsapp],
    ),
    Template(
        key="clinic_reminder", name="Clinic appointment reminder",
        description="Remind patients of an appointment and let them confirm, reschedule or cancel.",
        variables=["name", "doctor", "date", "time", "clinic_name"],
        keypad_options=[
            KeypadOption(digit="1", label="Confirm", outcome=O.confirmed),
            KeypadOption(digit="2", label="Reschedule", outcome=O.callback),
            KeypadOption(digit="3", label="Cancel", outcome=O.declined), _STOP,
        ],
        default_channels=[Channel.call, Channel.sms],
    ),
    Template(
        key="school_notice", name="School and parent notice",
        description="Send a notice to parents and collect acknowledgement or attendance.",
        variables=["parent_name", "student_name", "notice", "date", "link"],
        keypad_options=[
            KeypadOption(digit="1", label="Received, will attend", outcome=O.confirmed),
            KeypadOption(digit="2", label="Cannot attend", outcome=O.declined),
            KeypadOption(digit="3", label="Teacher should call me", outcome=O.callback), _STOP,
        ],
        default_channels=[Channel.call, Channel.sms, Channel.whatsapp],
    ),
    Template(
        key="payment_reminder", name="Payment reminder",
        description="Remind people of an amount due. Payment happens through a link, never by keypad.",
        variables=["name", "amount_inr", "due_date", "link"],
        keypad_options=[
            KeypadOption(digit="1", label="I have already paid", outcome=O.confirmed),
            KeypadOption(digit="2", label="I need more time", outcome=O.callback),
            KeypadOption(digit="3", label="Talk to someone", outcome=O.callback), _STOP,
        ],
        requires_payment=True,
        default_channels=[Channel.call, Channel.sms, Channel.whatsapp],
    ),
]

# ---------- Campaigns ----------

_EVENT = EventDetails(
    title="AI in Healthcare Seminar",
    description="A one-day seminar on clinical AI for students, faculty and alumni.",
    starts_at=datetime(2026, 11, 14, 10, 0, tzinfo=IST),
    ends_at=datetime(2026, 11, 14, 16, 0, tzinfo=IST),
    venue="Seminar Hall, Block A", city="Kochi",
    fee_inr=500, capacity=120,
    rsvp_deadline=datetime(2026, 11, 10, 18, 0, tzinfo=IST),
)

# (name, language, segment, outcome, attempts, stage)
_ROWS = [
    ("Anjali Menon", "ml", "Faculty", O.confirmed, 1, S.registered),
    ("Rahul Nair", "ml", "Students", O.confirmed, 1, S.paid),
    ("Fatima Sheikh", "hi", "Alumni", O.declined, 1, S.responded),
    ("Arjun Verma", "hi", "Students", O.no_answer, 2, S.invited),
    ("Meera Iyer", "ta", "Faculty", O.confirmed, 1, S.responded),
    ("Sanjay Kumar", "hi", "Students", O.voicemail, 1, S.invited),
    ("Divya Pillai", "ml", "Alumni", O.callback, 1, S.responded),
    ("Kiran Rao", "en", "Faculty", O.confirmed, 1, S.registered),
    ("Neha Gupta", "en", "Students", O.no_answer, 3, S.invited),
    ("Joseph Mathew", "ml", "Students", O.confirmed, 2, S.paid),
    ("Lakshmi Narayanan", "ta", "Alumni", O.no_answer, 2, S.invited),
    ("Imran Khan", "hi", "Faculty", O.opted_out, 1, S.invited),
    ("Sneha Das", "en", "Alumni", O.pending, 0, S.invited),
    ("Vikram Singh", "hi", "Students", O.wrong_number, 1, S.invited),
]

CAMPAIGNS = {
    "cmp_001": Campaign(
        id="cmp_001", name="AI in Healthcare Seminar", template_key="seminar_invite",
        status=CampaignStatus.running, event=_EVENT,
        languages=[Language.en, Language.hi, Language.ml, Language.ta],
        channels=[Channel.call, Channel.sms, Channel.email, Channel.whatsapp],
        poster_url="/mock/poster.svg", contact_count=len(_ROWS),
        created_at=datetime(2026, 10, 9, 12, 30, tzinfo=IST),
    ),
    "cmp_002": Campaign(
        id="cmp_002", name="Healthcare AI Workshop", template_key="seminar_invite",
        status=CampaignStatus.draft, event=None, languages=[],
        channels=[Channel.call, Channel.email], poster_url=None, contact_count=0,
        created_at=datetime(2026, 10, 9, 12, 40, tzinfo=IST),
    ),
}


def _build_contacts() -> list[Contact]:
    out = []
    for i, (name, lang, seg, outcome, attempts, stage) in enumerate(_ROWS, start=1):
        cid = f"ct_{i:03d}"
        out.append(Contact(
            id=cid, name=name, phone_masked=f"+91 98••• ••{i:03d}",
            email=f"{name.split()[0].lower()}@example.com",
            language=Language(lang), segment=seg, stage=stage,
            last_outcome=outcome, attempts=attempts,
            opted_out=(outcome == O.opted_out),
            registration_link=f"{WEB_BASE_URL}/r/tok_{cid}",
        ))
    return out


CONTACTS: dict[str, list[Contact]] = {"cmp_001": _build_contacts(), "cmp_002": []}

# token -> (campaign_id, contact)
TOKENS: dict[str, tuple[str, Contact]] = {
    f"tok_{c.id}": ("cmp_001", c) for c in CONTACTS["cmp_001"]
}

# ---------- Translations (sample text, not reviewed by a native speaker) ----------

_EN_CALL = ("Hello {name}. You are invited to the AI in Healthcare Seminar on 14 November at 10 a.m., "
            "Seminar Hall, Block A, Kochi. Press 1 to confirm, 2 to decline, or 3 for a callback. "
            "Press 9 to stop these calls.")
_EN_VM = ("Hello {name}, this is an invitation to the AI in Healthcare Seminar on 14 November at 10 a.m. "
          "in Kochi. Please call us back on the number shown on your phone.")

TRANSLATIONS: dict[str, list[Translation]] = {
    "cmp_001": [
        Translation(
            language=Language.en, call_script=_EN_CALL, voicemail_script=_EN_VM,
            email_subject="You are invited: AI in Healthcare Seminar, 14 November",
            email_body=("Dear {name},\n\nYou are invited to the AI in Healthcare Seminar on 14 November, "
                        "10 a.m. to 4 p.m., Seminar Hall, Block A, Kochi. Please register here: {link}"),
            whatsapp_text="Hi {name}, you are invited to the AI in Healthcare Seminar on 14 Nov, 10 a.m., "
                          "Seminar Hall, Block A, Kochi. Register here: {link}",
            social_caption="AI in Healthcare Seminar. 14 November, Kochi. Register through the link in our bio.",
            back_translation_en=_EN_CALL, approved=True,
        ),
        Translation(
            language=Language.hi,
            call_script=("नमस्ते {name}। आपको 14 नवंबर को सुबह 10 बजे, कोच्चि के सेमिनार हॉल, ब्लॉक ए में होने वाले "
                         "'एआई इन हेल्थकेयर' सेमिनार में आमंत्रित किया जाता है। पुष्टि के लिए 1 दबाएं, मना करने के लिए 2, "
                         "वापस कॉल के लिए 3 दबाएं। इन कॉल को रोकने के लिए 9 दबाएं।"),
            voicemail_script=("नमस्ते {name}, 14 नवंबर को सुबह 10 बजे कोच्चि में होने वाले 'एआई इन हेल्थकेयर' सेमिनार का "
                              "यह निमंत्रण है। कृपया आपके फोन पर दिख रहे नंबर पर हमें वापस कॉल करें।"),
            email_subject="आमंत्रण: एआई इन हेल्थकेयर सेमिनार, 14 नवंबर",
            whatsapp_text=("नमस्ते {name}, 14 नवंबर, सुबह 10 बजे, कोच्चि के सेमिनार हॉल (ब्लॉक ए) में 'एआई इन हेल्थकेयर' "
                           "सेमिनार का आपको निमंत्रण है। यहां रजिस्टर करें: {link}"),
            back_translation_en=_EN_CALL, approved=False,
        ),
        Translation(
            language=Language.ml,
            call_script=("നമസ്കാരം {name}. നവംബർ 14-ന് രാവിലെ 10 മണിക്ക് കൊച്ചിയിലെ ബ്ലോക്ക് എ സെമിനാർ ഹാളിൽ നടക്കുന്ന "
                         "'എഐ ഇൻ ഹെൽത്ത്കെയർ' സെമിനാറിലേക്ക് നിങ്ങളെ ക്ഷണിക്കുന്നു. സ്ഥിരീകരിക്കാൻ 1, ഒഴിവാക്കാൻ 2, "
                         "തിരിച്ചു വിളിക്കാൻ 3 അമർത്തുക. ഈ കോളുകൾ നിർത്താൻ 9 അമർത്തുക."),
            voicemail_script=("നമസ്കാരം {name}, നവംബർ 14-ന് രാവിലെ 10 മണിക്ക് കൊച്ചിയിൽ നടക്കുന്ന 'എഐ ഇൻ ഹെൽത്ത്കെയർ' "
                              "സെമിനാറിലേക്കുള്ള ക്ഷണമാണിത്. നിങ്ങളുടെ ഫോണിൽ കാണുന്ന നമ്പറിൽ ഞങ്ങളെ തിരികെ വിളിക്കുക."),
            email_subject="ക്ഷണം: എഐ ഇൻ ഹെൽത്ത്കെയർ സെമിനാർ, നവംബർ 14",
            whatsapp_text=("നമസ്കാരം {name}, നവംബർ 14, രാവിലെ 10 മണി, കൊച്ചി ബ്ലോക്ക് എ സെമിനാർ ഹാളിൽ 'എഐ ഇൻ ഹെൽത്ത്കെയർ' "
                           "സെമിനാറിലേക്ക് സ്വാഗതം. ഇവിടെ രജിസ്റ്റർ ചെയ്യുക: {link}"),
            back_translation_en=_EN_CALL, approved=False,
        ),
        Translation(
            language=Language.ta,
            call_script=("வணக்கம் {name}. நவம்பர் 14 அன்று காலை 10 மணிக்கு கொச்சியில் உள்ள பிளாக் ஏ கருத்தரங்கு அரங்கில் "
                         "நடைபெறும் 'ஏஐ இன் ஹெல்த்கேர்' கருத்தரங்கிற்கு உங்களை அழைக்கிறோம். உறுதிப்படுத்த 1, மறுக்க 2, "
                         "மீண்டும் அழைக்க 3 அழுத்தவும். இந்த அழைப்புகளை நிறுத்த 9 அழுத்தவும்."),
            voicemail_script=("வணக்கம் {name}, நவம்பர் 14 அன்று காலை 10 மணிக்கு கொச்சியில் நடைபெறும் 'ஏஐ இன் ஹெல்த்கேர்' "
                              "கருத்தரங்கிற்கான அழைப்பு இது. உங்கள் தொலைபேசியில் தெரியும் எண்ணுக்கு எங்களை மீண்டும் அழைக்கவும்."),
            email_subject="அழைப்பு: ஏஐ இன் ஹெல்த்கேர் கருத்தரங்கு, நவம்பர் 14",
            whatsapp_text=("வணக்கம் {name}, நவம்பர் 14, காலை 10 மணி, கொச்சி பிளாக் ஏ கருத்தரங்கு அரங்கில் 'ஏஐ இன் ஹெல்த்கேர்' "
                           "கருத்தரங்கிற்கு உங்களை அழைக்கிறோம். இங்கே பதிவு செய்யுங்கள்: {link}"),
            back_translation_en=_EN_CALL, approved=False,
        ),
    ],
    "cmp_002": [],
}

POSTER_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 800" role="img" aria-label="Sample poster">
<rect width="600" height="800" fill="#12313a"/><rect x="40" y="40" width="520" height="720" fill="none" stroke="#7fd1c0" stroke-width="3"/>
<text x="300" y="300" fill="#ffffff" font-family="sans-serif" font-size="46" text-anchor="middle">AI in Healthcare</text>
<text x="300" y="360" fill="#7fd1c0" font-family="sans-serif" font-size="46" text-anchor="middle">Seminar</text>
<text x="300" y="470" fill="#ffffff" font-family="sans-serif" font-size="26" text-anchor="middle">14 November, 10 a.m.</text>
<text x="300" y="510" fill="#ffffff" font-family="sans-serif" font-size="26" text-anchor="middle">Seminar Hall, Block A, Kochi</text>
<text x="300" y="700" fill="#9fb8bd" font-family="sans-serif" font-size="20" text-anchor="middle">Sample poster (mock data)</text></svg>"""

# ---------- imported contacts ----------
# The mock keeps only a masked number and a salted hash for people added by CSV import.
# The real database also stores the encrypted number (phone_enc), because calls need it.

PHONE_HASHES: dict[str, dict[str, str]] = {}   # campaign_id -> {phone_hash: contact_id}
CONTACT_HASH: dict[str, str] = {}              # contact_id -> phone_hash
OPT_OUT_HASHES: set[str] = set()               # opted-out numbers apply to every campaign


def add_imported_contacts(campaign_id: str, parsed: list[ParsedContact]) -> list[Contact]:
    """Store people from a CSV import. Replace this function when storage moves to PostgreSQL."""
    people = CONTACTS.setdefault(campaign_id, [])
    index = PHONE_HASHES.setdefault(campaign_id, {})
    next_n = max((int(c.id.split("_")[1]) for group in CONTACTS.values() for c in group), default=0) + 1
    created: list[Contact] = []
    for row in parsed:
        cid = f"ct_{next_n:03d}"
        next_n += 1
        token = f"tok_{secrets.token_urlsafe(12)}"
        contact = Contact(
            id=cid, name=row.name, phone_masked=row.phone_masked, email=row.email,
            language=row.language, segment=row.segment, stage=S.invited,
            last_outcome=O.pending, attempts=0, opted_out=False,
            registration_link=f"{WEB_BASE_URL}/r/{token}",
        )
        people.append(contact)
        index[row.phone_hash] = cid
        CONTACT_HASH[cid] = row.phone_hash
        TOKENS[token] = (campaign_id, contact)
        created.append(contact)
    campaign = CAMPAIGNS[campaign_id]
    campaign.contact_count = len(people)
    present = set(campaign.languages) | {c.language for c in created}
    campaign.languages = [lang for lang in Language if lang in present]
    return created
