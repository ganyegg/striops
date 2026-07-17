"""Value ledger — what Helm surfaced, what action ensued, what it was worth."""
from __future__ import annotations

import json
from functools import lru_cache

from pydantic import BaseModel, Field

from helm.core.paths import seed_dir


class ValueEntry(BaseModel):
    id: str
    surfaced_at: str
    insight: str
    action_id: str | None = None
    outcome: str
    value_zar: float
    value_basis: str  # realised | projected | avoided_cost
    verification: str  # verified | needs_verification | estimate
    note: str | None = None


class ValueLedger(BaseModel):
    municipality: str
    entries: list[ValueEntry] = Field(default_factory=list)
    cumulative_projected_zar: float = 0
    cumulative_realised_zar: float = 0
    cumulative_avoided_zar: float = 0
    cumulative_attributed_zar: float = 0
    note: str


@lru_cache
def _load(code: str) -> list[ValueEntry]:
    path = seed_dir() / "value_ledger" / f"{code}.json"
    if not path.exists():
        return []
    return [ValueEntry(**d) for d in json.loads(path.read_text())]


def build_value_ledger(code: str = "CPT") -> ValueLedger:
    entries = sorted(_load(code), key=lambda e: e.surfaced_at, reverse=True)
    projected = sum(e.value_zar for e in entries if e.value_basis == "projected")
    realised = sum(e.value_zar for e in entries if e.value_basis == "realised")
    avoided = sum(e.value_zar for e in entries if e.value_basis == "avoided_cost")
    return ValueLedger(
        municipality=code,
        entries=entries,
        cumulative_projected_zar=projected,
        cumulative_realised_zar=realised,
        cumulative_avoided_zar=avoided,
        cumulative_attributed_zar=projected + realised + avoided,
        note=(
            "Attributed value is honest about basis: realised (confirmed in the metric), "
            "projected (awaiting confirmation), or avoided cost. Pilot starts near zero "
            "realised — that is the point of the ledger."
        ),
    )
