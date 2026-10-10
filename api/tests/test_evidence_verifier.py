"""Unit tests for evidence_verifier module.

Proves that evidence quotes present in transcript/poster are verified, while
hallucinated quotes not in the source text are rejected.
"""
from app.evidence_verifier import verify_evidence


def test_exact_evidence_quote_verified():
    transcript = "We are holding an AI in Healthcare seminar on the fourteenth of November in Kochi."
    quote = "AI in Healthcare seminar"
    assert verify_evidence(quote, transcript) is True


def test_case_and_punctuation_insensitive_evidence_verified():
    transcript = "We are holding an AI in Healthcare seminar, at 10:00 AM."
    quote = "ai in healthcare seminar at 10 00 am"
    assert verify_evidence(quote, transcript) is True


def test_hallucinated_quote_rejected():
    transcript = "We are holding an AI in Healthcare seminar on the fourteenth of November."
    quote = "Registration fee is 500 rupees at Marriott Hotel"
    assert verify_evidence(quote, transcript) is False


def test_empty_quote_rejected():
    transcript = "We are holding an AI in Healthcare seminar."
    assert verify_evidence("", transcript) is False
    assert verify_evidence(None, transcript) is False


def test_empty_source_rejected():
    assert verify_evidence("AI in Healthcare", "") is False
    assert verify_evidence("AI in Healthcare", None) is False
