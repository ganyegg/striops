"""Load Cape Town (and later other metros) wins/initiatives from seed."""
from __future__ import annotations

import json
from functools import lru_cache

from striops.core.models import (
    Initiative,
    InitiativeReport,
    Priority,
    ReferenceLink,
    Source,
)
from striops.core.paths import seed_dir
from striops.reports import build_metric_report


@lru_cache
def _load(code: str) -> tuple[list[Initiative], dict[str, Source]]:
    wins_path = seed_dir() / "wins" / f"{code.upper()}.json"
    src_path = seed_dir() / "wins" / f"{code.upper()}_sources.json"
    if not wins_path.exists():
        return [], {}
    raw = json.loads(wins_path.read_text())
    sources = {}
    if src_path.exists():
        for s in json.loads(src_path.read_text()):
            sources[s["id"]] = Source(**s)
    initiatives: list[Initiative] = []
    for item in raw:
        item = dict(item)
        item["priority"] = Priority(item.get("priority", "medium"))
        initiatives.append(Initiative(**item))
    return initiatives, sources


def list_initiatives(code: str = "CPT") -> list[Initiative]:
    initiatives, _ = _load(code)
    order = {"high": 0, "medium": 1, "low": 2}
    return sorted(initiatives, key=lambda i: (order.get(i.priority.value, 9), -i.confidence))


def build_initiative_report(code: str, initiative_id: str) -> InitiativeReport:
    initiatives, sources = _load(code)
    init = next((i for i in initiatives if i.id == initiative_id), None)
    if init is None:
        raise KeyError(f"Unknown initiative: {initiative_id}")

    used = [sources[sid] for sid in init.source_ids if sid in sources]
    refs = [
        ReferenceLink(
            label=s.title,
            publisher=s.publisher,
            url=s.url,
            as_of=str(s.retrieved_at) if s.retrieved_at else None,
            note=s.coverage,
        )
        for s in used
    ]
    metric_report = None
    if init.related_metric:
        try:
            metric_report = build_metric_report(
                init.related_metric["entity_id"],
                init.related_metric["metric"],
            )
        except KeyError:
            metric_report = None

    narrative = (
        f"{init.headline} {init.plain_language} Why it matters: {init.why_it_matters} "
        f"Owner: {init.owner}. Next: {init.next_step}"
    )
    return InitiativeReport(
        initiative=init,
        sources=used,
        references=refs,
        narrative=narrative,
        metric_report=metric_report,
    )
