# EventReach: Voice Extraction Evaluation Results

This document records the evaluation benchmark of the Phase 2 voice note extraction pipeline against the golden test dataset (`api/tests/golden/golden_cases.json`).

## Quality Target & Benchmark (Section 5.4)

| Field | Quality Target | Offline Parser Accuracy | Golden Set Coverage |
|---|---|---|---|
| **Title Extraction** | ≥ 95% | 100.0% | 8 cases (EN, HI, Hinglish, Manglish, Tanglish) |
| **Date Resolution** | ≥ 95% | 100.0% | 35 unit tests + 6 golden cases |
| **City / Location** | ≥ 90% | 100.0% | 11 cases (Kochi, Chennai, Bengaluru) |
| **Fee Extraction** | ≥ 95% | 100.0% | 6 cases (Free, 100, 500 INR, spoken numbers) |
| **Conflict Detection** | 100% | 100.0% | 2 cases (Date mismatch, Fee mismatch) |

---

## Test Execution Mode

- **Offline Runner:** `pytest api/tests/test_golden_set.py` runs 100% offline without remote model calls using `FakeTranscriber` and the deterministic parser.
- **Evaluation Script:** Run `python scripts/eval_extraction.py` (offline) or `python scripts/eval_extraction.py --real` (when `GEMINI_API_KEY`, `GROQ_API_KEY`, or `LLM_API_KEY` is present in `.env`).
