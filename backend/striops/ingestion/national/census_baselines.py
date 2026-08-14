"""Stats SA Census 2022 municipal baselines.

Official figures curated from the Census 2022 Municipal Fact Sheet / SuperWEB
extracts into ``datasets/seed/national/census_2022_metros.json``. Connector
exposes a population metric series and a domain overlay for housing_population.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from striops.core.logging import get_logger
from striops.core.models import MetricPoint, MetricSeries
from striops.core.paths import cache_dir, seed_dir

log = get_logger("striops.ingestion.national.census_baselines")

SOURCE = {
    "id": "src-statssa-census",
    "publisher": "Statistics South Africa",
    "title": "Census 2022 — municipal baselines",
    "url": "https://census.statssa.gov.za/",
}


def _baselines_path() -> Path:
    return seed_dir() / "national" / "census_2022_metros.json"


def _load_row(municipality: str) -> dict | None:
    path = _baselines_path()
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    for row in data.get("municipalities") or []:
        if row.get("code") == municipality.upper():
            return row
    return None


def fetch_census_series(municipality: str = "CPT") -> MetricSeries | None:
    row = _load_row(municipality)
    if not row or row.get("population") is None:
        return None
    # Annual points: Census 2011 (if present) + Census 2022
    points: list[MetricPoint] = []
    if row.get("population_2011") is not None:
        points.append(MetricPoint(period=date(2011, 10, 1), value=float(row["population_2011"])))
    points.append(MetricPoint(period=date(2022, 2, 1), value=float(row["population"])))
    cache_dir().joinpath(f"census_{municipality.upper()}.json").write_text(
        json.dumps({"municipality": municipality.upper(), **row, "source": SOURCE}, indent=2)
    )
    log.info(
        "census baseline loaded",
        extra={"context": {"muni": municipality, "population": row["population"]}},
    )
    return MetricSeries(
        entity_id="svc-population",
        metric="population",
        unit="people",
        points=points,
    )


def write_census_overlay(municipality: str = "CPT") -> bool:
    row = _load_row(municipality)
    if not row:
        return False
    pop = int(row["population"])
    hh = row.get("households")
    indicators = [
        {
            "key": "population",
            "label": "Metro population",
            "value": f"{pop:,}",
            "numeric": float(pop),
            "unit": "people",
            "as_of": "Census 2022",
            "trend": "up",
            "verification": "verified",
            "source_id": "src-statssa-census",
            "confidence": 0.95,
            "method": "Stats SA Census 2022 municipal fact sheet.",
        }
    ]
    if hh is not None:
        indicators.append(
            {
                "key": "households",
                "label": "Households",
                "value": f"{int(hh):,}",
                "numeric": float(hh),
                "unit": "households",
                "as_of": "Census 2022",
                "trend": "up",
                "verification": "verified",
                "source_id": "src-statssa-census",
                "confidence": 0.9,
            }
        )
    path = cache_dir() / f"domain_overlay_{municipality.upper()}.json"
    existing: dict = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text())
        except Exception:
            existing = {}
    # merge housing_population indicators carefully
    hp = existing.get("housing_population") or {}
    existing_inds = {i["key"]: i for i in hp.get("indicators") or []}
    for ind in indicators:
        existing_inds[ind["key"]] = ind
    hp["indicators"] = list(existing_inds.values())
    srcs = {s["id"]: s for s in hp.get("sources") or []}
    srcs[SOURCE["id"]] = SOURCE
    hp["sources"] = list(srcs.values())
    existing["housing_population"] = hp
    path.write_text(json.dumps(existing, indent=2))
    return True
