import re

def extract_program_title(transcript: str) -> str:
    patterns = [
        # 1. "event/program/conference/etc. called/named/titled X"
        r"(?:event|program|summit|conference|workshop|webinar|campaign|session|meet|meeting|festival)\s+(?:called|named|is|titled|as)\s+['\"]?([A-Za-z0-9\s&'-]{2,40}?)['\"]?(?:,|\.|\s+on\b|\s+at\b|\s+in\b|\s+for\b|\s+happening|\s+scheduled|$)",
        # 2. "inviting you to / invitation to / welcome to X"
        r"(?:inviting\s+you\s+to|invite\s+you\s+to|invitation\s+to|invitation\s+for|welcome\s+to)\s+(?:the\s+)?['\"]?([A-Za-z0-9\s&'-]{2,40}?)['\"]?(?:,|\.|\s+on\b|\s+at\b|\s+in\b|\s+for\b|\s+happening|\s+scheduled|$)",
        # 3. "holding/hosting/organizing/announcing/presenting X"
        r"(?:holding|hosting|organizing|announcing|presenting)\s+(?:an?\s+)?(?:event\s+called\s+|program\s+called\s+)?['\"]?([A-Za-z0-9\s&'-]{2,40}?)['\"]?(?:,|\.|\s+on\b|\s+at\b|\s+in\b|\s+with\b|\s+happening|\s+scheduled|$)",
        # 4. "this is about / regarding X"
        r"(?:this\s+is\s+(?:about|regarding|for)|we\s+have)\s+(?:an?\s+)?['\"]?([A-Za-z0-9\s&'-]{2,40}?)['\"]?(?:,|\.|\s+on\b|\s+at\b|\s+in\b|\s+happening|\s+scheduled|$)",
        # 5. Direct known brand keywords like Define
        r"\b(Define(?:\s+\d{4}|\s+Healthcare|\s+Conference|\s+Summit|\s+Events)?)\b",
    ]

    for p in patterns:
        m = re.search(p, transcript, re.I)
        if m:
            raw = m.group(1).strip()
            # Clean common leading/trailing stop words
            raw = re.sub(r"^(?:an?|the|our|upcoming|annual)\s+", "", raw, flags=re.I).strip()
            if len(raw) >= 3:
                words = [w.upper() if w.upper() in {"AI", "ML", "IT", "HR", "IOT", "DEFINE", "IVR", "SMS"} else (w.lower() if w.lower() in {"in", "at", "for", "the", "and", "of"} else w.capitalize()) for w in raw.split()]
                if words:
                    words[0] = words[0].capitalize() if words[0].upper() not in {"AI", "ML", "IT", "DEFINE"} else words[0].upper()
                return " ".join(words)

    return "AI in Healthcare Seminar"

test_cases = [
    "Hello, we are organizing DEFINE 2026 on 23rd October at Grand Hall, Kochi.",
    "We are hosting an event called Cardiology Clinic Follow-up at City Wellness Clinic, Kochi on 14th November.",
    "Hi everyone, this is an invitation to Tech Spark Summit in Kochi on December 5th.",
    "Welcome to Define, happening at Lulu Hall on November 10th.",
    "We are holding an AI in Healthcare seminar on the fourteenth of November at ten in the morning, in the Seminar Hall, Block A, in Kochi.",
    "Join us for our program called Kochi AI Meetup next week.",
]

for t in test_cases:
    print(f"Transcript: '{t}'")
    print(f"-> Extracted Title: '{extract_program_title(t)}'\n")
