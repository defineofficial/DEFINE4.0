"""Monthly spending cap on AI calls (transcription, extraction, translation).

Every call to a paid AI provider goes through `guard`:

    with ai_budget.guard("translation", estimated_usd=0.02) as call:
        result = provider.translate(...)
        call.actual_usd = cost_from_provider_response(result)   # optional, defaults to the estimate

Before the call, `guard` checks that this month's spend plus the estimate fits under
LLM_MONTHLY_BUDGET_USD and reserves the estimate. If it does not fit, it raises
AiBudgetExceeded and the provider is never called. If the call fails, the reservation is
released so a failed call costs nothing. After a successful call the real cost replaces the
estimate.

Budget rules
- LLM_MONTHLY_BUDGET_USD unset or not a number: the default below (20 USD) applies.
- LLM_MONTHLY_BUDGET_USD=0: every AI call is refused (a kill switch).
- The month is the calendar month in UTC.

Where spend is kept
- DATABASE_URL set: in the `ai_usage` table, so a restart does not reset the cap.
- Mock mode: in memory, reset on restart.
"""
import os
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterator, Optional, Protocol

DEFAULT_MONTHLY_BUDGET_USD = 20.0
WARN_AT = 0.8  # share of the budget at which status() reports "warning"

KINDS = {"transcription", "extraction", "translation", "back_translation"}


class AiBudgetExceeded(Exception):
    """Raised before a provider call when it would take this month over the cap."""

    def __init__(self, kind: str, spent: float, estimate: float, budget: float):
        self.kind, self.spent, self.estimate, self.budget = kind, spent, estimate, budget
        super().__init__(
            f"AI budget reached: ${spent:.2f} of ${budget:.2f} used this month, "
            f"and this {kind} call needs about ${estimate:.2f}."
        )


def monthly_budget_usd() -> float:
    raw = os.getenv("LLM_MONTHLY_BUDGET_USD", "").strip()
    try:
        value = float(raw)
    except ValueError:
        return DEFAULT_MONTHLY_BUDGET_USD
    return value if value >= 0 else DEFAULT_MONTHLY_BUDGET_USD


def current_month(now: Optional[datetime] = None) -> str:
    return (now or datetime.now(timezone.utc)).strftime("%Y-%m")


# ---------- stores ----------

class Store(Protocol):
    def spent(self, month: str) -> float: ...
    def add(self, month: str, kind: str, usd: float) -> None: ...


class MemoryStore:
    def __init__(self) -> None:
        self._spent: dict[str, float] = {}

    def spent(self, month: str) -> float:
        return self._spent.get(month, 0.0)

    def add(self, month: str, kind: str, usd: float) -> None:
        self._spent[month] = max(0.0, self._spent.get(month, 0.0) + usd)


class PostgresStore:
    """One row per (month, kind). Creates its table on first use, so existing databases need no migration."""

    DDL = """
    CREATE TABLE IF NOT EXISTS ai_usage (
      month      text NOT NULL,
      kind       text NOT NULL,
      usd        numeric(12, 6) NOT NULL DEFAULT 0,
      updated_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY (month, kind)
    )
    """

    def __init__(self, get_pool):
        self._get_pool = get_pool
        self._ready = False

    def _conn(self):
        return self._get_pool().connection()  # commits when the with-block ends

    def _ensure(self, conn) -> None:
        if not self._ready:
            conn.execute(self.DDL)
            self._ready = True

    def spent(self, month: str) -> float:
        with self._conn() as conn:
            self._ensure(conn)
            row = conn.execute("SELECT COALESCE(SUM(usd), 0) AS total FROM ai_usage WHERE month = %s", (month,)).fetchone()
            return float(row["total"])

    def add(self, month: str, kind: str, usd: float) -> None:
        with self._conn() as conn:
            self._ensure(conn)
            conn.execute(
                """
                INSERT INTO ai_usage (month, kind, usd) VALUES (%s, %s, GREATEST(%s, 0))
                ON CONFLICT (month, kind) DO UPDATE SET
                  usd = GREATEST(ai_usage.usd + %s, 0), updated_at = now()
                """,
                (month, kind, usd, usd),
            )


_memory = MemoryStore()
_postgres: Optional[PostgresStore] = None
_lock = threading.Lock()


def _store() -> Store:
    global _postgres
    from . import db  # imported here so this module works without psycopg in unit tests

    if db.enabled():
        if _postgres is None:
            _postgres = PostgresStore(db.get_pool)
        return _postgres
    return _memory


# ---------- public API ----------

@dataclass
class Call:
    kind: str
    estimate_usd: float
    actual_usd: Optional[float] = None  # set this inside the `with` block when the real cost is known


@contextmanager
def guard(kind: str, estimated_usd: float, store: Optional[Store] = None,
          now: Optional[datetime] = None) -> Iterator[Call]:
    if kind not in KINDS:
        raise ValueError(f"Unknown AI call kind {kind!r}. Use one of {sorted(KINDS)}.")
    if estimated_usd < 0:
        raise ValueError("estimated_usd cannot be negative.")
    store = store or _store()
    month = current_month(now)
    budget = monthly_budget_usd()

    # Check and reserve under one lock so two parallel calls cannot both squeeze under the cap.
    with _lock:
        spent = store.spent(month)
        if spent + estimated_usd > budget:
            raise AiBudgetExceeded(kind, spent, estimated_usd, budget)
        store.add(month, kind, estimated_usd)

    call = Call(kind, estimated_usd)
    try:
        yield call
    except BaseException:
        with _lock:
            store.add(month, kind, -estimated_usd)  # failed call: give the reservation back
        raise
    else:
        if call.actual_usd is not None and call.actual_usd != estimated_usd:
            with _lock:
                store.add(month, kind, call.actual_usd - estimated_usd)


def status(store: Optional[Store] = None, now: Optional[datetime] = None) -> dict:
    """Numbers for an admin page or the health check."""
    store = store or _store()
    budget = monthly_budget_usd()
    spent = store.spent(current_month(now))
    if spent >= budget:
        level = "exhausted"
    elif budget > 0 and spent >= WARN_AT * budget:
        level = "warning"
    else:
        level = "ok"
    return {
        "month": current_month(now),
        "budget_usd": round(budget, 2),
        "spent_usd": round(spent, 4),
        "remaining_usd": round(max(budget - spent, 0.0), 4),
        "level": level,
    }
