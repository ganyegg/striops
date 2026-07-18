"""Attach sourced 'who is affected' denominators to risks — never invent."""
from __future__ import annotations

import json
from functools import lru_cache

from striops.core.models import AffectedPopulation, Risk
from striops.core.paths import seed_dir


@lru_cache
def _load(municipality: str) -> dict:
    path = seed_dir() / "affected" / f"{municipality.upper()}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def clear_affected_cache() -> None:
    _load.cache_clear()


def _metric_from_risk(risk: Risk) -> str | None:
    if risk.forecast and risk.forecast.metric:
        return risk.forecast.metric
    # id pattern: risk-{entity}-{metric}
    if risk.id.startswith("risk-"):
        parts = risk.id.split("-", 2)
        if len(parts) >= 3:
            # entity may contain hyphens: risk-svc-water-non_revenue_water_pct
            rest = risk.id[len("risk-") :]
            for metric_key in (
                "non_revenue_water_pct",
                "road_maintenance_backlog_km",
                "refuse_service_requests",
                "public_lighting_outages",
                "library_visits",
                "dam_storage",
                "clinic_waiting_days",
                "ems_response_minutes",
            ):
                if rest.endswith(metric_key):
                    return metric_key
    return None


def lookup_affected(municipality: str, *, risk_id: str | None = None, metric: str | None = None) -> AffectedPopulation | None:
    data = _load(municipality)
    raw = None
    if risk_id and risk_id in data.get("by_risk_id", {}):
        raw = data["by_risk_id"][risk_id]
    elif metric and metric in data.get("by_metric", {}):
        raw = data["by_metric"][metric]
    if not raw:
        return None
    return AffectedPopulation(**raw)


def domain_affected(municipality: str, domain_id: str) -> AffectedPopulation | None:
    data = _load(municipality)
    raw = data.get("by_domain", {}).get(domain_id)
    return AffectedPopulation(**raw) if raw else None


def attach_affected(risks: list[Risk], municipality: str = "CPT") -> list[Risk]:
    out: list[Risk] = []
    for risk in risks:
        if risk.affected is not None:
            out.append(risk)
            continue
        metric = _metric_from_risk(risk)
        affected = lookup_affected(municipality, risk_id=risk.id, metric=metric)
        out.append(risk.model_copy(update={"affected": affected}) if affected else risk)
    return out
