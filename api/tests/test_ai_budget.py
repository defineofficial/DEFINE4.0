from datetime import datetime, timezone

import pytest

from app import ai_budget
from app.ai_budget import AiBudgetExceeded, MemoryStore, guard, status

JAN = datetime(2026, 1, 15, tzinfo=timezone.utc)
FEB = datetime(2026, 2, 1, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def ten_dollar_budget(monkeypatch):
    monkeypatch.setenv("LLM_MONTHLY_BUDGET_USD", "10")


def test_call_within_budget_is_recorded():
    store = MemoryStore()
    with guard("translation", 0.5, store=store, now=JAN):
        pass
    assert store.spent("2026-01") == 0.5


def test_actual_cost_replaces_the_estimate():
    store = MemoryStore()
    with guard("extraction", 1.0, store=store, now=JAN) as call:
        call.actual_usd = 0.25
    assert store.spent("2026-01") == 0.25


def test_call_over_budget_is_refused_and_provider_not_run():
    store = MemoryStore()
    ran = []
    with guard("transcription", 9.0, store=store, now=JAN):
        ran.append("first")
    with pytest.raises(AiBudgetExceeded) as err:
        with guard("transcription", 2.0, store=store, now=JAN):
            ran.append("second")
    assert ran == ["first"]
    assert store.spent("2026-01") == 9.0
    assert "9.00 of $10.00" in str(err.value)


def test_exactly_reaching_the_budget_is_allowed():
    store = MemoryStore()
    with guard("translation", 10.0, store=store, now=JAN):
        pass
    assert status(store, JAN)["level"] == "exhausted"


def test_failed_call_costs_nothing():
    store = MemoryStore()
    with pytest.raises(RuntimeError):
        with guard("translation", 3.0, store=store, now=JAN):
            raise RuntimeError("provider down")
    assert store.spent("2026-01") == 0.0


def test_new_month_starts_at_zero():
    store = MemoryStore()
    with guard("translation", 10.0, store=store, now=JAN):
        pass
    with guard("translation", 1.0, store=store, now=FEB):
        pass
    assert store.spent("2026-02") == 1.0


def test_zero_budget_is_a_kill_switch(monkeypatch):
    monkeypatch.setenv("LLM_MONTHLY_BUDGET_USD", "0")
    with pytest.raises(AiBudgetExceeded):
        with guard("extraction", 0.01, store=MemoryStore(), now=JAN):
            pass


def test_bad_budget_value_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("LLM_MONTHLY_BUDGET_USD", "twenty")
    assert ai_budget.monthly_budget_usd() == ai_budget.DEFAULT_MONTHLY_BUDGET_USD


def test_status_levels():
    store = MemoryStore()
    assert status(store, JAN)["level"] == "ok"
    with guard("translation", 8.5, store=store, now=JAN):
        pass
    s = status(store, JAN)
    assert s["level"] == "warning" and s["remaining_usd"] == 1.5


def test_unknown_kind_is_rejected():
    with pytest.raises(ValueError):
        with guard("poetry", 0.1, store=MemoryStore(), now=JAN):
            pass
