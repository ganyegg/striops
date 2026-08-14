"""Load Cape Town (and later other metros) wins/initiatives from seed.

Wins are curated narrative, but the ones that cite a metric are re-tested
against that live series on every read. A hand-written claim goes stale the
moment the feed behind it moves, and a product whose Wins page contradicts its
own Pulse has no credibility left to spend.
"""
from __future__ import annotations

import json
from functools import lru_cache

from striops.core.anomaly import describe_break, is_suspect
from striops.core.models import (
    Initiative,
    InitiativeReport,
    Priority,
    ReferenceLink,
    Source,
    Trend,
)
from striops.core.paths import seed_dir
from striops.forecasting import forecast_series
from striops.persistence import get_repository
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


_CLAIMED_TREND: dict[str, Trend] = {
    "improving": Trend.IMPROVING,
    "worsening": Trend.WORSENING,
}


def _checked(init: Initiative) -> Initiative:
    """Re-test a win's claim against the series it cites."""
    if not init.related_metric:
        return init
    claimed = _CLAIMED_TREND.get(init.status.strip().lower())
    if claimed is None:
        return init

    entity_id = init.related_metric.get("entity_id")
    metric = init.related_metric.get("metric")
    series = next(
        (
            s
            for s in get_repository().metric_series()
            if s.entity_id == entity_id and s.metric == metric
        ),
        None,
    )
    if series is None or len(series.points) < 2:
        return init

    values = series.values()
    if is_suspect(values, len(values) - 1):
        return init.model_copy(
            update={
                "data_check": "unverified",
                "data_check_note": (
                    f"Cannot confirm this claim: {describe_break(values, len(values) - 1)}"
                ),
            }
        )

    actual = forecast_series(series).direction
    if actual == claimed:
        return init.model_copy(update={"data_check": "confirmed"})
    if actual == Trend.STABLE:
        return init.model_copy(
            update={
                "data_check": "unverified",
                "data_check_note": (
                    f"The {metric} series is now flat, so the "
                    f"{init.status.lower()} claim is no longer supported by its own metric."
                ),
            }
        )
    return init.model_copy(
        update={
            "data_check": "contradicted",
            "data_check_note": (
                f"This claim says {init.status.lower()}, but {metric} is currently "
                f"{actual.value} on the live series. The curated headline predates the feed "
                f"and must be restated before it is used."
            ),
        }
    )


def list_initiatives(code: str = "CPT") -> list[Initiative]:
    initiatives, _ = _load(code)
    order = {"high": 0, "medium": 1, "low": 2}
    checked = [_checked(i) for i in initiatives]
    return sorted(
        checked,
        key=lambda i: (
            # A contradicted claim never leads the Wins page.
            1 if i.data_check in {"contradicted", "unverified"} else 0,
            order.get(i.priority.value, 9),
            -i.confidence,
        ),
    )


def build_initiative_report(code: str, initiative_id: str) -> InitiativeReport:
    initiatives, sources = _load(code)
    init = next((i for i in initiatives if i.id == initiative_id), None)
    if init is None:
        raise KeyError(f"Unknown initiative: {initiative_id}")
    init = _checked(init)

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
