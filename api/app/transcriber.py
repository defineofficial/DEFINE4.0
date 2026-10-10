"""Transcriber interface and providers for speech-to-text.

Provides a pluggable Transcriber Protocol with a FakeTranscriber for offline tests
and real API provider wrappers (Whisper / OpenAI / Groq).
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, Union


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str


@dataclass
class Transcript:
    text: str
    detected_language: str = "en"
    language_confidence: float = 1.0
    segments: List[TranscriptSegment] = field(default_factory=list)
    provider: str = "fake"


class Transcriber(Protocol):
    def transcribe(self, audio_data: Union[str, bytes], language_hint: Optional[str] = None) -> Transcript:
        ...


class FakeTranscriber:
    """Offline mock transcriber for tests and local development."""

    def __init__(
        self,
        default_transcript: Optional[str] = None,
        default_language: str = "en",
        canned_responses: Optional[Dict[str, Transcript]] = None,
    ):
        self.default_transcript = default_transcript or (
            "We are holding an AI in Healthcare seminar on the fourteenth of November at ten in the "
            "morning, in the Seminar Hall, Block A, in Kochi. Registration is five hundred rupees."
        )
        self.default_language = default_language
        self.canned_responses = canned_responses or {}

    def transcribe(self, audio_data: Union[str, bytes], language_hint: Optional[str] = None) -> Transcript:
        # If audio_data matches a canned response key (filename, text, or string identifier)
        key = audio_data.decode("utf-8", errors="ignore") if isinstance(audio_data, bytes) else str(audio_data)
        if key in self.canned_responses:
            return self.canned_responses[key]
        
        # Check substring keys in canned_responses
        for k, resp in self.canned_responses.items():
            if k in key:
                return resp

        lang = language_hint or self.default_language
        return Transcript(
            text=self.default_transcript,
            detected_language=lang,
            language_confidence=0.98,
            segments=[
                TranscriptSegment(start=0.0, end=5.0, text=self.default_transcript)
            ],
            provider="fake",
        )
