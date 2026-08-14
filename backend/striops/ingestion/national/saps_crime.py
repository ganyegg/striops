"""SAPS crime statistics aggregated to municipality.

History (Jan 2020 – Sep 2025) came from https://github.com/afrith/crime-stats,
which stopped being updated in December 2025. Current quarters are read
straight from the SAPS releases instead — see ``saps_quarterly`` — so the
series no longer depends on a third party keeping pace with SAPS.

Refresh (adds any newly-published quarters to the cached extract):

    python -m striops.ingestion.national.saps_crime CPT

Crime codes used, as published in the SAPS workbooks:

===========  ==========================================
``1``        Murder
``Cat 01``   Contact crime (crimes against the person)
``Full 17``  17 community-reported serious crimes
===========  ==========================================
"""
from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

from striops.core.logging import get_logger
from striops.core.models import MetricPoint, MetricSeries
from striops.core.paths import cache_dir, seed_dir
from striops.ingestion.national.saps_quarterly import (
    fetch_workbook,
    normalise_station,
    parse_station_counts,
)

log = get_logger("striops.ingestion.national.saps_crime")

SOURCE = {
    "id": "src-saps",
    "publisher": "South African Police Service",
    "title": "Quarterly crime statistics — station → municipality",
    "url": "https://www.saps.gov.za/services/crimestats.php",
}

# SAPS crime code -> key in the cached payload.
_SERIES_BY_CODE = {
    "1": "murder_monthly",
    "Cat 01": "contact_crime_monthly",
    "Full 17": "community_reported_serious_monthly",
}


def _stations_path() -> Path:
    return seed_dir() / "national" / "saps_stations.json"


def station_keys(municipality: str) -> set[str]:
    """Normalised station names for a municipality, from the shipped register."""
    path = _stations_path()
    if not path.exists():
        return set()
    payload = json.loads(path.read_text())
    entry = (payload.get("municipalities") or {}).get(municipality.upper())
    if not entry:
        return set()
    return {
        s.get("key") or normalise_station(s.get("name")) for s in entry.get("stations") or []
    }


def station_population(municipality: str) -> float | None:
    path = _stations_path()
    if not path.exists():
        return None
    payload = json.loads(path.read_text())
    entry = (payload.get("municipalities") or {}).get(municipality.upper())
    if not entry:
        return None
    return float(entry.get("population_census_2022") or 0) or None


def _seed_path(municipality: str) -> Path:
    return seed_dir() / "national" / f"saps_crime_{municipality.upper()}.json"


def _cache_path(municipality: str) -> Path:
    return cache_dir() / f"saps_crime_{municipality.upper()}.json"


def _load_payload(municipality: str) -> dict | None:
    for path in (_cache_path(municipality), _seed_path(municipality)):
        if path.exists():
            try:
                return json.loads(path.read_text())
            except Exception:
                continue
    return None


def _merge_monthly(rows: list[dict], counts: dict[date, float]) -> list[dict]:
    """Merge SAPS counts into a monthly list, letting SAPS win on overlap."""
    by_period = {(int(r["year"]), int(r["month"])): int(r["count"]) for r in rows}
    for period, value in counts.items():
        by_period[(period.year, period.month)] = int(value)
    return [
        {"year": y, "month": m, "count": c} for (y, m), c in sorted(by_period.items())
    ]


def refresh_from_saps(
    municipality: str = "CPT",
    quarters: list[tuple[int, int]] | None = None,
) -> dict | None:
    """Add published SAPS quarters to the cached extract.

    ``quarters`` is a list of ``(financial_year_start, quarter)`` pairs; SAPS
    financial years run 1 April to 31 March, so ``(2025, 4)`` is January to
    March 2026. Existing months are overwritten because SAPS is the publisher
    of record and does revise counts between releases.
    """
    muni = municipality.upper()
    keys = station_keys(muni)
    if not keys:
        log.warning("no station register for municipality", extra={"context": {"muni": muni}})
        return None

    payload = _load_payload(muni) or {"municipality": muni}
    quarters = quarters or _default_quarters()
    added: list[str] = []

    for fy_start, quarter in quarters:
        try:
            counts = parse_station_counts(fetch_workbook(fy_start, quarter), keys)
        except Exception as exc:
            log.warning(
                "saps quarter skipped",
                extra={"context": {"fy": fy_start, "quarter": quarter, "error": str(exc)}},
            )
            continue
        for code, series_key in _SERIES_BY_CODE.items():
            if code not in counts:
                continue
            payload[series_key] = _merge_monthly(payload.get(series_key) or [], counts[code])
        added.append(f"{fy_start}/{fy_start + 1} Q{quarter}")

    if not added:
        return None

    pop = station_population(muni)
    payload.update(
        {
            "municipality": muni,
            "source": "SAPS quarterly crime statistics (RAW Data sheet, station level)",
            "source_url": SOURCE["url"],
            "saps_portal": SOURCE["url"],
            "stations": len(keys),
            "quarters_ingested": added,
        }
    )
    if pop:
        payload["population_census_2022_stations"] = int(pop)

    _cache_path(muni).write_text(json.dumps(payload, indent=2) + "\n")
    log.info(
        "saps crime refreshed from SAPS",
        extra={"context": {"muni": muni, "quarters": added}},
    )
    return payload


def _default_quarters() -> list[tuple[int, int]]:
    """Every quarter of the current and previous SAPS financial year.

    Unpublished quarters simply fail to download and are skipped, so this needs
    no knowledge of the release calendar.
    """
    today = date.today()
    fy_start = today.year if today.month >= 4 else today.year - 1
    return [(fy, q) for fy in (fy_start - 1, fy_start) for q in (1, 2, 3, 4)]


def _monthly_to_points(rows: list[dict]) -> list[MetricPoint]:
    points: list[MetricPoint] = []
    for row in rows:
        points.append(
            MetricPoint(
                period=date(int(row["year"]), int(row["month"]), 1),
                value=float(row["count"]),
            )
        )
    return points


def fetch_crime_series(municipality: str = "CPT") -> list[MetricSeries]:
    muni = municipality.upper()
    payload = None
    if os.environ.get("STRIOPS_REFRESH_CRIME") == "1":
        try:
            payload = refresh_from_saps(muni)
        except Exception as exc:
            log.warning("saps crime refresh failed", extra={"context": {"error": str(exc)}})
    if payload is None:
        payload = _load_payload(muni)
    if not payload:
        return []

    # Ensure cache copy exists for feeds report
    cache = _cache_path(muni)
    if not cache.exists():
        cache.write_text(json.dumps(payload, indent=2))

    out: list[MetricSeries] = []
    murder_pts = _monthly_to_points(payload.get("murder_monthly") or [])
    contact_pts = _monthly_to_points(payload.get("contact_crime_monthly") or [])
    if len(murder_pts) >= 2:
        out.append(
            MetricSeries(
                entity_id="svc-safety",
                metric="murder_count",
                unit="incidents/month",
                points=murder_pts,
            )
        )
    if len(contact_pts) >= 2:
        out.append(
            MetricSeries(
                entity_id="svc-safety",
                metric="contact_crime_count",
                unit="incidents/month",
                points=contact_pts,
            )
        )
    return out


def write_crime_overlay(municipality: str = "CPT") -> bool:
    """Patch safety domain indicators from the latest crime month."""
    payload = _load_payload(municipality)
    if not payload:
        return False
    murder = payload.get("murder_monthly") or []
    contact = payload.get("contact_crime_monthly") or []
    if not murder or not contact:
        return False
    latest_m, latest_c = murder[-1], contact[-1]
    period = f"{latest_m['year']}-{int(latest_m['month']):02d}"
    pop = float(payload.get("population_census_2022_stations") or 0) or None
    murder_rate = None
    if pop:
        # annualise last 12 months if available
        last12 = murder[-12:] if len(murder) >= 12 else murder
        annual = sum(r["count"] for r in last12)
        murder_rate = round(annual / pop * 100_000, 1)

    new_inds = [
        {
            "key": "murder_monthly",
            "label": "Murders (metro, monthly)",
            "value": f"{int(latest_m['count']):,}",
            "numeric": float(latest_m["count"]),
            "unit": "incidents",
            "as_of": period,
            "trend": "flat",
            "verification": "verified",
            "source_id": "src-saps",
            "confidence": 0.8,
            "method": (
                "Sum of SAPS station-level counts (RAW Data sheet of the quarterly release) "
                "for the 62 police stations mapped to the municipality."
            ),
        },
        {
            "key": "contact_crime_monthly",
            "label": "Contact crime (metro, monthly)",
            "value": f"{int(latest_c['count']):,}",
            "numeric": float(latest_c["count"]),
            "unit": "incidents",
            "as_of": period,
            "trend": "flat",
            "verification": "verified",
            "source_id": "src-saps",
            "confidence": 0.8,
            "method": "SAPS Cat 01 Contact crime, stations mapped to municipality.",
        },
    ]
    if murder_rate is not None:
        new_inds.append(
            {
                "key": "murder_rate",
                "label": "Murder rate (approx. annualised)",
                "value": f"{murder_rate} per 100k",
                "numeric": murder_rate,
                "unit": "per 100k",
                "as_of": f"12m to {period}",
                "trend": "flat",
                "verification": "verified",
                "source_id": "src-saps",
                "confidence": 0.7,
                "method": "Last-12-month murders ÷ Census 2022 station-mapped population × 100,000.",
            }
        )
    path = cache_dir() / f"domain_overlay_{municipality.upper()}.json"
    existing: dict = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text())
        except Exception:
            existing = {}
    safety = existing.get("safety_policing") or {}
    by_key = {i["key"]: i for i in safety.get("indicators") or []}
    for ind in new_inds:
        by_key[ind["key"]] = ind
    safety["indicators"] = list(by_key.values())
    srcs = {s["id"]: s for s in safety.get("sources") or []}
    srcs[SOURCE["id"]] = SOURCE
    safety["sources"] = list(srcs.values())
    existing["safety_policing"] = safety
    path.write_text(json.dumps(existing, indent=2))
    return True


if __name__ == "__main__":  # pragma: no cover
    import sys

    muni = sys.argv[1] if len(sys.argv) > 1 else "CPT"
    result = refresh_from_saps(muni)
    if not result:
        print(f"No SAPS quarters ingested for {muni}.")
        raise SystemExit(1)
    murders = result.get("murder_monthly") or []
    latest = murders[-1] if murders else None
    print(f"{muni}: quarters {', '.join(result['quarters_ingested'])}")
    if latest:
        print(f"latest month {latest['year']}-{latest['month']:02d}, {latest['count']} murders")
