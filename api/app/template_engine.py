"""Template engine for EventReach.

Translates (template_key + variables + language + channel) into final dispatchable messages.
Includes the 4 standard presets:
1. seminar_invite
2. clinic_reminder
3. school_notice
4. payment_reminder
"""
import re
from typing import Any, Dict, List, Optional
from app.schemas import Channel, KeypadOption, Language, Outcome, Template

O = Outcome
_STOP = KeypadOption(digit="9", label="Stop these calls", outcome=O.opted_out)


# ---------- Template Presets Definitions ----------

PRESETS: Dict[str, Template] = {
    "seminar_invite": Template(
        key="seminar_invite",
        name="Seminar invite",
        description="Invite people to a seminar or workshop and collect RSVPs.",
        variables=["name", "event_title", "date", "time", "venue", "city", "link"],
        keypad_options=[
            KeypadOption(digit="1", label="Confirm", outcome=O.confirmed),
            KeypadOption(digit="2", label="Decline", outcome=O.declined),
            KeypadOption(digit="3", label="Call me back", outcome=O.callback),
            _STOP,
        ],
        requires_payment=False,
        default_channels=[Channel.call, Channel.sms, Channel.email, Channel.whatsapp],
    ),
    "clinic_reminder": Template(
        key="clinic_reminder",
        name="Clinic appointment reminder",
        description="Remind patients of an appointment and let them confirm, reschedule or cancel.",
        variables=["name", "doctor", "date", "time", "clinic_name", "link"],
        keypad_options=[
            KeypadOption(digit="1", label="Confirm", outcome=O.confirmed),
            KeypadOption(digit="2", label="Reschedule", outcome=O.callback),
            KeypadOption(digit="3", label="Cancel", outcome=O.declined),
            _STOP,
        ],
        requires_payment=False,
        default_channels=[Channel.call, Channel.sms, Channel.whatsapp],
    ),
    "school_notice": Template(
        key="school_notice",
        name="School and parent notice",
        description="Send a notice to parents and collect acknowledgement or attendance.",
        variables=["parent_name", "student_name", "notice", "date", "link"],
        keypad_options=[
            KeypadOption(digit="1", label="Received, will attend", outcome=O.confirmed),
            KeypadOption(digit="2", label="Cannot attend", outcome=O.declined),
            KeypadOption(digit="3", label="Teacher should call me", outcome=O.callback),
            _STOP,
        ],
        requires_payment=False,
        default_channels=[Channel.call, Channel.sms, Channel.whatsapp],
    ),
    "payment_reminder": Template(
        key="payment_reminder",
        name="Payment reminder",
        description="Remind people of an amount due. Payment happens through a link, never by keypad.",
        variables=["name", "amount_inr", "due_date", "purpose", "link"],
        keypad_options=[
            KeypadOption(digit="1", label="I have already paid", outcome=O.confirmed),
            KeypadOption(digit="2", label="I need more time", outcome=O.callback),
            KeypadOption(digit="3", label="Talk to someone", outcome=O.callback),
            _STOP,
        ],
        requires_payment=True,
        default_channels=[Channel.call, Channel.sms, Channel.whatsapp],
    ),
}


# ---------- Channel Templates per Preset and Language ----------

MESSAGES: Dict[str, Dict[Language, Dict[Channel, Dict[str, str]]]] = {
    "seminar_invite": {
        Language.en: {
            Channel.call: {
                "script": "Hello {name}. You are invited to the {event_title} on {date} at {time}, {venue}, {city}. Press 1 to confirm, 2 to decline, 3 for callback, 9 to stop calls.",
                "voicemail": "Hello {name}, invitation to {event_title} on {date} in {city}. Please call us back on the number displayed on your phone.",
            },
            Channel.sms: {
                "body": "Hi {name}, you're invited to {event_title} on {date} at {time}. Venue: {venue}. Register: {link}",
            },
            Channel.whatsapp: {
                "body": "Hi *{name}*,\n\nYou are invited to *{event_title}*.\n📅 Date: {date} at {time}\n📍 Venue: {venue}, {city}\n\n👉 Register here: {link}",
            },
            Channel.email: {
                "subject": "Invitation: {event_title} on {date}",
                "body": "Dear {name},\n\nYou are cordially invited to attend {event_title} on {date} at {time}, held at {venue}, {city}.\n\nPlease secure your place using this link: {link}\n\nBest regards,\nEvent Organizer",
            },
            Channel.instagram: {
                "caption": "{event_title}! Join us on {date} at {venue}, {city}. Registration link in bio. #Seminar #EventReach",
            },
        },
        Language.hi: {
            Channel.call: {
                "script": "नमस्ते {name}। आपको {date} को {time} बजे, {city} के {venue} में होने वाले '{event_title}' में आमंत्रित किया जाता है। पुष्टि के लिए 1, मना करने के लिए 2, वापस कॉल के लिए 3 और रोकने के लिए 9 दबाएं।",
                "voicemail": "नमस्ते {name}, {date} को {city} में होने वाले '{event_title}' का आमंत्रण है। कृपया स्क्रीन पर दिए नंबर पर कॉल करें।",
            },
            Channel.sms: {
                "body": "नमस्ते {name}, {date} को {event_title} में शामिल हों ({venue})। रजिस्टर करें: {link}",
            },
            Channel.whatsapp: {
                "body": "नमस्ते *{name}*,\n\nआपको *{event_title}* में आमंत्रित किया जाता है।\n📅 दिनांक: {date}, {time}\n📍 स्थान: {venue}, {city}\n\n👉 रजिस्टर करें: {link}",
            },
            Channel.email: {
                "subject": "आमंत्रण: {event_title}, {date}",
                "body": "प्रिय {name},\n\nआपको {date} को {time} बजे {venue}, {city} में आयोजित '{event_title}' में सादर आमंत्रित किया जाता है।\n\nकृपया यहां रजिस्टर करें: {link}",
            },
            Channel.instagram: {
                "caption": "{event_title}! {date} को {venue}, {city} में मिलते हैं। बायो में दिए लिंक से रजिस्टर करें।",
            },
        },
        Language.ml: {
            Channel.call: {
                "script": "നമസ്കാരം {name}. {date}-ന് {time}-ന് {city}യിലെ {venue}-ൽ നടക്കുന്ന '{event_title}'-ലേക്ക് നിങ്ങളെ ക്ഷണിക്കുന്നു. സ്ഥിരീകരിക്കാൻ 1, ഒഴിവാക്കാൻ 2, തിരിച്ചു വിളിക്കാൻ 3, നിർത്താൻ 9 അമർത്തുക.",
                "voicemail": "നമസ്കാരം {name}, {date}-ന് {city}യിൽ നടക്കുന്ന '{event_title}'-ലേക്കുള്ള ക്ഷണമാണിത്. ഈ നമ്പറിലേക്ക് തിരികെ വിളിക്കുക.",
            },
            Channel.sms: {
                "body": "നമസ്കാരം {name}, {date}-ന് നടക്കുന്ന {event_title}-ലേക്ക് സ്വാഗതം. സ്ഥലം: {venue}. രജിസ്റ്റർ ചെയ്യാൻ: {link}",
            },
            Channel.whatsapp: {
                "body": "നമസ്കാരം *{name}*,\n\n*{event_title}*-ലേക്ക് നിങ്ങളെ സ്നേഹപൂർവ്വം ക്ഷണിക്കുന്നു.\n📅 തീയതി: {date}, {time}\n📍 സ്ഥലം: {venue}, {city}\n\n👉 രജിസ്റ്റർ ചെയ്യാൻ: {link}",
            },
            Channel.email: {
                "subject": "ക്ഷണം: {event_title}, {date}",
                "body": "പ്രിയപ്പെട്ട {name},\n\n{date}-ന് {time}-ന് {venue}, {city}-ൽ നടക്കുന്ന '{event_title}'-ലേക്ക് സ്വാഗതം.\n\nരജിസ്റ്റർ ചെയ്യാൻ സന്ദർശിക്കുക: {link}",
            },
            Channel.instagram: {
                "caption": "{event_title}! {date}-ന് {venue}, {city}-ൽ. പ്രവേശനത്തിനായി ബയോയിലെ ലിങ്ക് കാണുക.",
            },
        },
        Language.ta: {
            Channel.call: {
                "script": "வணக்கம் {name}. {date} அன்று {time} மணிக்கு {city}-யில் உள்ள {venue}-ல் நடைபெறும் '{event_title}'-ற்கு உங்களை அழைக்கிறோம். உறுதிப்படுத்த 1, மறுக்க 2, மீண்டும் அழைக்க 3, நிறுத்த 9 அழுத்தவும்.",
                "voicemail": "வணக்கம் {name}, {date} அன்று {city}-யில் நடைபெறும் '{event_title}'-ற்கான அழைப்பு இது. திரையில் தெரியும் எண்ணுக்கு அழைக்கவும்.",
            },
            Channel.sms: {
                "body": "வணக்கம் {name}, {date} அன்று நடைபெறும் {event_title}-ற்கு வருக. இடம்: {venue}. பதிவு செய்ய: {link}",
            },
            Channel.whatsapp: {
                "body": "வணக்கம் *{name}*,\n\n*{event_title}* நிகழ்விற்கு உங்களை அன்புடன் அழைக்கிறோம்.\n📅 தேதி: {date}, {time}\n📍 இடம்: {venue}, {city}\n\n👉 பதிவு செய்ய: {link}",
            },
            Channel.email: {
                "subject": "அழைப்பு: {event_title}, {date}",
                "body": "அன்புள்ள {name},\n\n{date} அன்று {time} மணிக்கு {venue}, {city}-யில் நடைபெறும் '{event_title}'-ற்கு உங்களை அழைக்கிறோம்.\n\nபதிவு செய்ய: {link}",
            },
            Channel.instagram: {
                "caption": "{event_title}! {date} அன்று {venue}, {city}. பதிவுக்கு பயோவில் உள்ள இணைப்பை கிளிக் செய்யவும்.",
            },
        },
    },
    "clinic_reminder": {
        Language.en: {
            Channel.call: {
                "script": "Hello {name}. This is a reminder for your appointment with Dr. {doctor} on {date} at {time} at {clinic_name}. Press 1 to confirm, 2 to reschedule, 3 to cancel, 9 to stop calls.",
                "voicemail": "Hello {name}, appointment reminder with Dr. {doctor} on {date} at {clinic_name}. Call us back to confirm.",
            },
            Channel.sms: {
                "body": "Hi {name}, reminder for your appointment with Dr. {doctor} on {date} at {time} at {clinic_name}. Manage: {link}",
            },
            Channel.whatsapp: {
                "body": "Hello *{name}*,\n\nAppointment reminder with *Dr. {doctor}*:\n🏥 Clinic: {clinic_name}\n📅 Date: {date} at {time}\n\nManage appointment: {link}",
            },
        },
        Language.hi: {
            Channel.call: {
                "script": "नमस्ते {name}। यह {clinic_name} में डॉ. {doctor} के साथ {date} को {time} बजे आपके अपॉइंटमेंट का रिमाइंडर है। पुष्टि के लिए 1, रीशेड्यूल के लिए 2, रद्द के लिए 3 दबाएं।",
                "voicemail": "नमस्ते {name}, {clinic_name} में डॉ. {doctor} के अपॉइंटमेंट की याददाश्त। कृपया हमें कॉल करें।",
            },
            Channel.sms: {
                "body": "नमस्ते {name}, {date} को डॉ. {doctor} ({clinic_name}) के अपॉइंटमेंट का रिमाइंडर। लिंक: {link}",
            },
            Channel.whatsapp: {
                "body": "नमस्ते *{name}*,\n\n*डॉ. {doctor}* के साथ अपॉइंटमेंट रिमाइंडर:\n🏥 क्लिनिक: {clinic_name}\n📅 दिनांक: {date}, {time}\n\nअपॉइंटमेंट लिंक: {link}",
            },
        },
        Language.ml: {
            Channel.call: {
                "script": "നമസ്കാരം {name}. {clinic_name}-ൽ ഡോക്ടർ {doctor}-മായി {date}-ന് {time}-നുള്ള അപ്പോയിന്റ്മെന്റ് ഓർമ്മപ്പെടുത്തലാണിത്. സ്ഥിരീകരിക്കാൻ 1, മാറ്റിവെക്കാൻ 2, റദ്ദാക്കാൻ 3 അമർത്തുക.",
                "voicemail": "നമസ്കാരം {name}, {clinic_name}-ൽ ഡോക്ടറുമായുള്ള അപ്പോയിന്റ്മെന്റ് ഓർമ്മപ്പെടുത്തലാണിത്. ദയവായി തിരിച്ചു വിളിക്കുക.",
            },
            Channel.sms: {
                "body": "നമസ്കാരം {name}, {date}-ന് ഡോക്ടർ {doctor}-മായി ({clinic_name}) അപ്പോയിന്റ്മെന്റ് ഉണ്ട്. വിവരങ്ങൾക്ക്: {link}",
            },
            Channel.whatsapp: {
                "body": "നമസ്കാരം *{name}*,\n\n*ഡോക്ടർ {doctor}*-മായുള്ള അപ്പോയിന്റ്മെന്റ്:\n🏥 ക്ലിനിക്ക്: {clinic_name}\n📅 തീയതി: {date}, {time}\n\nവിവരങ്ങൾക്ക്: {link}",
            },
        },
        Language.ta: {
            Channel.call: {
                "script": "வணக்கம் {name}. {clinic_name}-ல் மருத்துவர் {doctor}-உடன் {date} அன்று {time} மணிக்கு உங்கள் சந்திப்பு பற்றிய நினைவூட்டல். உறுதி செய்ய 1, மாற்ற 2, ரத்து செய்ய 3 அழுத்தவும்.",
                "voicemail": "வணக்கம் {name}, மருத்துவர் {doctor}-உடனான சந்திப்பு நினைவூட்டல். திரையில் உள்ள எண்ணுக்கு அழைக்கவும்.",
            },
            Channel.sms: {
                "body": "வணக்கம் {name}, {date} அன்று மருத்துவர் {doctor} ({clinic_name}) சந்திப்பு நினைவூட்டல். விவரங்களுக்கு: {link}",
            },
            Channel.whatsapp: {
                "body": "வணக்கம் *{name}*,\n\n*மருத்துவர் {doctor}* சந்திப்பு நினைவூட்டல்:\n🏥 மருத்துவமனை: {clinic_name}\n📅 தேதி: {date}, {time}\n\nவிவரங்களுக்கு: {link}",
            },
        },
    },
    "school_notice": {
        Language.en: {
            Channel.call: {
                "script": "Hello {parent_name}. Important notice regarding {student_name}: {notice} scheduled on {date}. Press 1 to acknowledge, 2 if unable to attend, 3 for teacher callback, 9 to opt out.",
                "voicemail": "Hello {parent_name}, notice regarding {student_name} on {date}. Please call back or check details online.",
            },
            Channel.sms: {
                "body": "Dear {parent_name}, notice for {student_name}: {notice} on {date}. Details: {link}",
            },
            Channel.whatsapp: {
                "body": "Dear *{parent_name}*,\n\nSchool notice for *{student_name}*:\n📌 Notice: {notice}\n📅 Date: {date}\n\nRead details: {link}",
            },
        },
        Language.hi: {
            Channel.call: {
                "script": "नमस्ते {parent_name}। {student_name} के लिए आवश्यक सूचना: {date} को {notice}। पुष्टि के लिए 1, असमर्थ होने पर 2, शिक्षक से बात के लिए 3 दबाएं।",
                "voicemail": "नमस्ते {parent_name}, {student_name} के लिए विद्यालय सूचना। कृपया संपर्क करें।",
            },
            Channel.sms: {
                "body": "प्रिय {parent_name}, {student_name} के लिए सूचना: {notice} ({date})। लिंक: {link}",
            },
            Channel.whatsapp: {
                "body": "नमस्ते *{parent_name}*,\n\n*{student_name}* के लिए स्कूल सूचना:\n📌 सूचना: {notice}\n📅 दिनांक: {date}\n\nविवरण: {link}",
            },
        },
        Language.ml: {
            Channel.call: {
                "script": "നമസ്കാരം {parent_name}. {student_name}-ന്റെ സ്കൂൾ അറിയിപ്പ്: {date}-ന് {notice}. പങ്കെടുക്കുമെങ്കിൽ 1, ഇല്ലെങ്കിൽ 2, അധ്യാപകനുമായി സംസാരിക്കാൻ 3 അമർത്തുക.",
                "voicemail": "നമസ്കാരം {parent_name}, {student_name}-ന്റെ സ്കൂൾ അറിയിപ്പ്. ദയവായി തിരിച്ചു വിളിക്കുക.",
            },
            Channel.sms: {
                "body": "പ്രിയ {parent_name}, {student_name}-ന്റെ സ്കൂൾ അറിയിപ്പ്: {notice} ({date}). വിവരങ്ങൾക്ക്: {link}",
            },
            Channel.whatsapp: {
                "body": "പ്രിയപ്പെട്ട *{parent_name}*,\n\n*{student_name}*-ന്റെ സ്കൂൾ അറിയിപ്പ്:\n📌 അറിയിപ്പ്: {notice}\n📅 തീയതി: {date}\n\nവിവരങ്ങൾ: {link}",
            },
        },
        Language.ta: {
            Channel.call: {
                "script": "வணக்கம் {parent_name}. {student_name} பற்றிய பள்ளி அறிவிப்பு: {date} அன்று {notice}. வருகையை உறுதி செய்ய 1, இயலாவிடில் 2, ஆசிரியருடன் பேச 3 அழுத்தவும்.",
                "voicemail": "வணக்கம் {parent_name}, {student_name} பற்றிய பள்ளி அறிவிப்பு. எங்களை அழைக்கவும்.",
            },
            Channel.sms: {
                "body": "அன்புள்ள {parent_name}, {student_name} பள்ளி அறிவிப்பு: {notice} ({date}). இணைப்பு: {link}",
            },
            Channel.whatsapp: {
                "body": "அன்புள்ள *{parent_name}*,\n\n*{student_name}* பள்ளி அறிவிப்பு:\n📌 அறிவிப்பு: {notice}\n📅 தேதி: {date}\n\nவிவரங்கள்: {link}",
            },
        },
    },
    "payment_reminder": {
        Language.en: {
            Channel.call: {
                "script": "Hello {name}. This is a payment reminder of {amount_inr} rupees for {purpose}, due on {due_date}. Press 1 if already paid, 2 for more time, 3 to talk to an agent, 9 to opt out.",
                "voicemail": "Hello {name}, reminder for payment of {amount_inr} rupees due on {due_date}. Please pay using the link sent to your phone.",
            },
            Channel.sms: {
                "body": "Hi {name}, payment reminder of Rs. {amount_inr} for {purpose} is due on {due_date}. Pay online securely: {link}",
            },
            Channel.whatsapp: {
                "body": "Hello *{name}*,\n\nPayment Reminder:\n💰 Amount: ₹{amount_inr}\n📝 Purpose: {purpose}\n⏰ Due Date: {due_date}\n\n👉 Pay securely: {link}",
            },
        },
        Language.hi: {
            Channel.call: {
                "script": "नमस्ते {name}। यह {purpose} के लिए {amount_inr} रुपये के भुगतान का रिमाइंडर है, जो {due_date} तक देय है। पहले ही भुगतान कर दिया हो तो 1, समय चाहिए तो 2, बात करने के लिए 3 दबाएं।",
                "voicemail": "नमस्ते {name}, {due_date} तक देय {amount_inr} रुपये के भुगतान की याददाश्त। भेजे गए लिंक से भुगतान करें।",
            },
            Channel.sms: {
                "body": "नमस्ते {name}, {purpose} के ₹{amount_inr} का भुगतान {due_date} तक करें। सुरक्षित भुगतान लिंक: {link}",
            },
            Channel.whatsapp: {
                "body": "नमस्ते *{name}*,\n\nभुगतान रिमाइंडर:\n💰 राशि: ₹{amount_inr}\n📝 विवरण: {purpose}\n⏰ अंतिम तिथि: {due_date}\n\n👉 सुरक्षित भुगतान करें: {link}",
            },
        },
        Language.ml: {
            Channel.call: {
                "script": "നമസ്കാരം {name}. {purpose}-നായി {amount_inr} രൂപയുടെ പേയ്‌മെന്റ് {due_date}-നകം നൽകേണ്ടതുണ്ട്. ഇതിനകം നൽകിയെങ്കിൽ 1, സമയം വേണമെങ്കിൽ 2, സംസാരിക്കാൻ 3 അമർത്തുക.",
                "voicemail": "നമസ്കാരം {name}, {due_date}-നകം നൽകേണ്ട {amount_inr} രൂപയുടെ പേയ്‌മെന്റ് ഓർമ്മപ്പെടുത്തൽ. അയച്ച ലിങ്ക് വഴി അടയ്ക്കുക.",
            },
            Channel.sms: {
                "body": "നമസ്കാരം {name}, {purpose}-നായി ₹{amount_inr} {due_date}-നകം നൽകുക. ലിങ്ക്: {link}",
            },
            Channel.whatsapp: {
                "body": "നമസ്കാരം *{name}*,\n\nപേയ്‌മെന്റ് ഓർമ്മപ്പെടുത്തൽ:\n💰 തുക: ₹{amount_inr}\n📝 കാരണം: {purpose}\n⏰ അവസാന തീയതി: {due_date}\n\n👉 അടയ്ക്കാൻ: {link}",
            },
        },
        Language.ta: {
            Channel.call: {
                "script": "வணக்கம் {name}. {purpose}-க்காக {amount_inr} ரூபாய் செலுத்துவதற்கான நினைவூட்டல். செலுத்த வேண்டிய தேதி {due_date}. ஏற்கனவே செலுத்தியிருந்தால் 1, அவகாசத்திற்கு 2, பேச 3 அழுத்தவும்.",
                "voicemail": "வணக்கம் {name}, {due_date}-க்குள் செலுத்த வேண்டிய {amount_inr} ரூபாய் நினைவூட்டல். அனுப்பிய இணைப்பு மூலம் செலுத்தவும்.",
            },
            Channel.sms: {
                "body": "வணக்கம் {name}, {purpose}-க்காக ₹{amount_inr} தொகையை {due_date}-க்குள் செலுத்தவும். இணைப்பு: {link}",
            },
            Channel.whatsapp: {
                "body": "வணக்கம் *{name}*,\n\nகட்டண நினைவூட்டல்:\n💰 தொகை: ₹{amount_inr}\n📝 காரணம்: {purpose}\n⏰ கடைசி தேதி: {due_date}\n\n👉 கட்டணம் செலுத்த: {link}",
            },
        },
    },
}


# ---------- Rendering Logic ----------

def render_message(
    template_key: str,
    language: Language,
    channel: Channel,
    variables: Dict[str, Any],
) -> Dict[str, str]:
    """Interpolates variables into the preset channel template for the requested language.
    
    Returns a dictionary of rendered strings, for example:
    - Call channel: {"script": "...", "voicemail": "..."}
    - SMS channel: {"body": "..."}
    - WhatsApp channel: {"body": "..."}
    - Email channel: {"subject": "...", "body": "..."}
    - Instagram channel: {"caption": "..."}
    """
    preset_messages = MESSAGES.get(template_key, MESSAGES["seminar_invite"])
    lang_messages = preset_messages.get(language, preset_messages.get(Language.en, {}))
    channel_content = lang_messages.get(channel, {})

    rendered: Dict[str, str] = {}
    for key, text_template in channel_content.items():
        # Safe format: replace known {var} patterns, leave unmatched ones or empty string
        formatted = text_template
        for var_name, var_val in variables.items():
            formatted = formatted.replace(f"{{{var_name}}}", str(var_val))
        rendered[key] = formatted

    return rendered


def list_templates() -> List[Template]:
    """Returns the four standard templates."""
    return list(PRESETS.values())


def get_template(key: str) -> Optional[Template]:
    """Returns the template preset for the given key."""
    return PRESETS.get(key)
