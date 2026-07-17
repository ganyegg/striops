"""Decision register — institutional memory that survives turnover.

Cities forget: why a budget was cut, who owned a mitigation, what was promised
for review. The register keeps every strategic decision linked to the risk or
win it addressed, with a review-by date that Helm can flag when it lapses.
"""
from __future__ import annotations

import json
from datetime import date
from functools import lru_cache

from pydantic import BaseModel, Field

from helm.core.paths import seed_dir


class Decision(BaseModel):
    id: str
    date: str | None = None
    title: str
    status: str  # decided | in_progress | pending | overdue
    owner: str
    context: str
    outcome: str | None = None
    linked_risk_id: str | None = None
    linked_win_id: str | None = None
    review_by: str | None = None


class DecisionRegister(BaseModel):
    municipality: str
    decisions: list[Decision] = Field(default_factory=list)
    open_count: int = 0
    overdue_count: int = 0
    note: str


@lru_cache
def _load(code: str) -> list[Decision]:
    path = seed_dir() / "decisions" / f"{code}.json"
    if not path.exists():
        return []
    return [Decision(**d) for d in json.loads(path.read_text())]


def _effective_status(d: Decision) -> str:
    if d.status in ("pending", "in_progress") and d.review_by:
        try:
            if date.fromisoformat(d.review_by) < date.today():
                return "overdue"
        except ValueError:
            pass
    return d.status


def build_decision_register(code: str = "CPT") -> DecisionRegister:
    decisions = [
        d.model_copy(update={"status": _effective_status(d)}) for d in _load(code)
    ]
    order = {"overdue": 0, "pending": 1, "in_progress": 2, "decided": 3}
    decisions.sort(key=lambda d: (order.get(d.status, 4), d.date or "9999"))
    return DecisionRegister(
        municipality=code,
        decisions=decisions,
        open_count=sum(1 for d in decisions if d.status in ("pending", "in_progress", "overdue")),
        overdue_count=sum(1 for d in decisions if d.status == "overdue"),
        note=(
            "Every strategic decision, its owner, and its review date — linked to the "
            "risk or win it addresses. Helm flags what lapses; nothing depends on memory."
        ),
    )
