"""Call automation interface slot (Section 10).

Defines the CallDispatcher Protocol interface and MockCallDispatcher slot.
Full phone call automation is left blank as a clearly marked slot.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Protocol


@dataclass
class PreparedCalls:
    campaign_id: str
    script_by_language: Dict[str, str]
    contact_count: int
    configured: bool = False


class CallDispatcher(Protocol):
    def prepare(self, campaign_id: str) -> PreparedCalls: ...
    def launch(self, campaign_id: str) -> None: ...
    def test_call(self, campaign_id: str, to_number: str) -> None: ...


class MockCallDispatcher:
    """Mock dispatcher recording fake call attempts without placing real calls."""

    def __init__(self, configured: bool = False):
        self.configured = configured

    def prepare(self, campaign_id: str) -> PreparedCalls:
        return PreparedCalls(
            campaign_id=campaign_id,
            script_by_language={"en": "Mock call script"},
            contact_count=0,
            configured=self.configured,
        )

    def launch(self, campaign_id: str) -> None:
        raise NotImplementedError("Phone call automation is not configured yet (Section 10 slot).")

    def test_call(self, campaign_id: str, to_number: str) -> None:
        raise NotImplementedError("Phone call automation is not configured yet (Section 10 slot).")
