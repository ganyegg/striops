"""Action tracker — who owns what, by when, linked to the insight that caused it."""
from __future__ import annotations

import json
from datetime import date
from functools import lru_cache

from pydantic import BaseModel, Field

from helm.core.paths import seed_dir


class Action(BaseModel):
    id: str
    title: str
    source_type: str  # risk | opportunity | recommendation | win
    source_ref: str
    department: str
    owner: str
    due_date: str | None = None
    status: str  # proposed | assigned | in_progress | done | overdue
    expected_impact_zar: float | None = None
    expected_impact_note: str | None = None
    outcome: str | None = None
    created_at: str | None = None


class ActionRegister(BaseModel):
    municipality: str
    actions: list[Action] = Field(default_factory=list)
    open_count: int = 0
    overdue_count: int = 0
    done_count: int = 0
    total_expected_impact_zar: float = 0
    note: str


@lru_cache
def _load(code: str) -> list[Action]:
    path = seed_dir() / "actions" / f"{code}.json"
    if not path.exists():
        return []
    return [Action(**d) for d in json.loads(path.read_text())]


def _effective_status(a: Action) -> str:
    if a.status == "done":
        return "done"
    if a.due_date:
        try:
            if date.fromisoformat(a.due_date) < date.today() and a.status != "done":
                return "overdue"
        except ValueError:
            pass
    return a.status


def build_action_register(code: str = "CPT") -> ActionRegister:
    actions = [a.model_copy(update={"status": _effective_status(a)}) for a in _load(code)]
    order = {"overdue": 0, "assigned": 1, "in_progress": 2, "proposed": 3, "done": 4}
    actions.sort(key=lambda a: (order.get(a.status, 5), a.due_date or "9999"))
    open_statuses = {"proposed", "assigned", "in_progress", "overdue"}
    return ActionRegister(
        municipality=code,
        actions=actions,
        open_count=sum(1 for a in actions if a.status in open_statuses),
        overdue_count=sum(1 for a in actions if a.status == "overdue"),
        done_count=sum(1 for a in actions if a.status == "done"),
        total_expected_impact_zar=sum(a.expected_impact_zar or 0 for a in actions if a.status != "done"),
        note=(
            "Every action has a department, an owner, and a due date — linked to the "
            "risk, opportunity or win that triggered it. Overdue is computed, not declared."
        ),
    )


def get_action(code: str, action_id: str) -> Action | None:
    for a in build_action_register(code).actions:
        if a.id == action_id:
            return a
    return None


def actions_for_source(code: str, source_ref: str) -> list[Action]:
    return [a for a in build_action_register(code).actions if a.source_ref == source_ref or source_ref in a.source_ref]
