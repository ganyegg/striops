"""Cost-of-risk and opportunity-gain estimation with sourced assumptions."""
from __future__ import annotations

import json
from functools import lru_cache

from helm.core.models import CostEstimate, MetricSeries, Opportunity, Risk
from helm.core.paths import seed_dir


@lru_cache
def _load(code: str = "CPT") -> dict:
    path = seed_dir() / "valuation" / f"{code}.json"
    if not path.exists():
        return {"metrics": {}, "opportunity_defaults": {}}
    return json.loads(path.read_text())


def valuation_catalog(code: str = "CPT") -> dict:
    return _load(code)


def estimate_risk_cost(risk: Risk, series: MetricSeries | None, code: str = "CPT") -> CostEstimate | None:
    """Annual cost of the risk's current level / worsening trend for its metric."""
    catalog = _load(code)
    metric = risk.forecast.metric if risk.forecast else None
    if not metric and risk.id.startswith("risk-"):
        # id pattern: risk-{entity}-{metric}
        parts = risk.id.split("-", 2)
        if len(parts) == 3:
            metric = parts[2]
    if not metric:
        return None
    profile = catalog.get("metrics", {}).get(metric)
    if not profile:
        return None

    unit_cost = float(profile["rand_per_unit_per_year"])
    if unit_cost <= 0:
        return None

    latest = series.values()[-1] if series and series.values() else None
    # For percentage / backlog metrics, cost the current level; for request/fault
    # counts, cost the month-over-month increase annualised.
    if metric.endswith("_pct") or metric.endswith("_km"):
        amount = unit_cost * (latest or 0)
        basis = "annual_cost_of_current_level"
        unit_note = f"R{unit_cost:,.0f} per {profile['unit']} × current level"
    else:
        values = series.values() if series else []
        delta = (values[-1] - values[-2]) if len(values) >= 2 else 0
        amount = unit_cost * max(0, delta)
        basis = "annual_cost_of_latest_period_increase"
        unit_note = f"R{unit_cost:,.0f} per {profile['unit']} × latest increase"

    return CostEstimate(
        amount_zar=round(amount, 0),
        basis=basis,
        method=profile["method"],
        confidence=float(profile.get("confidence", 0.5)),
        assumptions=list(profile.get("assumptions", [])),
        unit_note=unit_note,
    )


def estimate_opportunity_gain(opp: Opportunity, code: str = "CPT") -> CostEstimate | None:
    catalog = _load(code)
    defaults = catalog.get("opportunity_defaults", {})
    if opp.id.startswith("opp-underspend"):
        rate = float(defaults.get("underspend_redeployment_capture_rate", 0.35))
        amount = opp.value_estimate * rate
        return CostEstimate(
            amount_zar=round(amount, 0),
            basis="redeployable_underspend_capture",
            method=f"underspend × {rate:.0%} capture rate",
            confidence=min(opp.confidence, 0.7),
            assumptions=[
                {
                    "key": "capture_rate",
                    "value": rate,
                    "unit": "fraction",
                    "note": "Share of identified underspend realistically redeployable this cycle.",
                    "source_url": None,
                }
            ],
            unit_note=f"{rate:.0%} of R{opp.value_estimate:,.0f} underspend",
        )
    if opp.id.startswith("opp-efficiency"):
        # Efficiency opportunities keep a modest annualised gain.
        months = float(defaults.get("efficiency_annual_gain_months", 6))
        amount = max(50_000.0, opp.value_estimate * (months / 12) * 0.1) if opp.value_estimate else 50_000.0
        # Prefer metric unit economics when the id embeds a metric.
        for metric, profile in catalog.get("metrics", {}).items():
            if metric in opp.id and float(profile.get("rand_per_unit_per_year", 0)) > 0:
                amount = float(profile["rand_per_unit_per_year"]) * 12  # one unit held for a year
                return CostEstimate(
                    amount_zar=round(amount, 0),
                    basis="efficiency_hold",
                    method=profile["method"],
                    confidence=float(profile.get("confidence", 0.5)),
                    assumptions=list(profile.get("assumptions", [])),
                    unit_note="Holding one unit of improvement for 12 months",
                )
        return CostEstimate(
            amount_zar=round(amount, 0),
            basis="efficiency_hold",
            method="conservative efficiency hold for half a year",
            confidence=0.5,
            assumptions=[],
            unit_note=None,
        )
    return None


def attach_valuations(
    risks: list[Risk],
    opportunities: list[Opportunity],
    series_list: list[MetricSeries],
    code: str = "CPT",
) -> tuple[list[Risk], list[Opportunity]]:
    by_key = {(s.entity_id, s.metric): s for s in series_list}
    enriched_risks: list[Risk] = []
    for r in risks:
        series = None
        if r.forecast:
            series = by_key.get((r.forecast.entity_id, r.forecast.metric))
        if series is None and r.id.startswith("risk-"):
            # risk-svc-water-non_revenue_water_pct
            rest = r.id[len("risk-") :]
            for (eid, metric), s in by_key.items():
                if rest == f"{eid}-{metric}":
                    series = s
                    break
        est = estimate_risk_cost(r, series, code)
        enriched_risks.append(r.model_copy(update={"cost_estimate": est}) if est else r)

    enriched_opps: list[Opportunity] = []
    for o in opportunities:
        est = estimate_opportunity_gain(o, code)
        enriched_opps.append(o.model_copy(update={"gain_estimate": est}) if est else o)
    return enriched_risks, enriched_opps
