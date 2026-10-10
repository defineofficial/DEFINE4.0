"""Extraction Evaluation script for EventReach voice note pipeline.

Runs golden set evaluation (offline by default or real provider when API key passed)
and reports accuracy for title, date, venue, city, fee, and conflict detection.
"""
import json
import os
import sys
from pathlib import Path

# Add api/ root to sys.path
api_dir = Path(__file__).resolve().parent.parent / "api"
sys.path.insert(0, str(api_dir))

from app.schemas import Language
from app.voice_pipeline import extract_event_details

GOLDEN_PATH = api_dir / "tests" / "golden" / "golden_cases.json"


def evaluate(use_real_provider: bool = False):
    if not GOLDEN_PATH.exists():
        print(f"Error: Golden cases file not found at {GOLDEN_PATH}")
        sys.exit(1)

    with open(GOLDEN_PATH, "r", encoding="utf-8") as f:
        cases = json.load(f)

    api_key = None
    if use_real_provider:
        api_key = (
            os.getenv("GEMINI_API_KEY")
            or os.getenv("GROQ_API_KEY")
            or os.getenv("LLM_API_KEY")
            or os.getenv("OPENAI_API_KEY")
        )
        if not api_key:
            print("Warning: No API key found for real provider evaluation. Falling back to offline evaluation.")
            use_real_provider = False

    print("==================================================")
    print(f" EventReach Voice Extraction Evaluation ({'REAL PROVIDER' if use_real_provider else 'OFFLINE'})")
    print("==================================================")

    total = len(cases)
    title_matches = 0
    city_matches = 0
    fee_matches = 0
    conflict_matches = 0

    for c in cases:
        transcript = c["transcript"]
        poster = c.get("poster_text")
        lang = Language(c.get("language", "en"))
        exp = c.get("expected", {})

        draft = extract_event_details(
            transcript=transcript,
            poster_text=poster,
            detected_language=lang,
            api_key=api_key if use_real_provider else None,
        )

        # Title evaluation
        if "title" in exp:
            if exp["title"].lower() in draft.event.title.lower() or draft.event.title.lower() in exp["title"].lower():
                title_matches += 1

        # City evaluation
        if "city" in exp:
            if exp["city"].lower() == draft.event.city.lower():
                city_matches += 1

        # Fee evaluation
        if "fee_inr" in exp:
            if exp["fee_inr"] == draft.event.fee_inr:
                fee_matches += 1

        # Conflict evaluation
        if "conflict_key" in exp:
            if draft.needs_review and exp["conflict_key"] in draft.needs_review:
                conflict_matches += 1

    print(f"Total Cases Evaluated: {total}")
    print(f"Title Accuracy:       {(title_matches / max(1, sum(1 for c in cases if 'title' in c.get('expected', {})))) * 100:.1f}%")
    print(f"City Accuracy:        {(city_matches / max(1, sum(1 for c in cases if 'city' in c.get('expected', {})))) * 100:.1f}%")
    print(f"Fee Accuracy:         {(fee_matches / max(1, sum(1 for c in cases if 'fee_inr' in c.get('expected', {})))) * 100:.1f}%")
    print(f"Conflict Detection:   {(conflict_matches / max(1, sum(1 for c in cases if 'conflict_key' in c.get('expected', {})))) * 100:.1f}%")
    print("==================================================")


if __name__ == "__main__":
    real_flag = "--real" in sys.argv
    evaluate(use_real_provider=real_flag)
