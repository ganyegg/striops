"""SAPS crime statistics aggregated to municipality.

Primary extract: https://github.com/afrith/crime-stats (SAPS quarterly sheets).
Full CSV is ~200MB (Git LFS); we ship a CPT seed extract and optionally refresh
by streaming the LFS media URL when ``STRIOPS_REFRESH_CRIME=1``.
"""
from __future__ import annotations

import csv
import json
import os
import urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path

from striops.core.logging import get_logger
from striops.core.models import MetricPoint, MetricSeries
from striops.core.paths import cache_dir, seed_dir

log = get_logger("striops.ingestion.national.saps_crime")

SOURCE = {
    "id": "src-saps",
    "publisher": "South African Police Service (via afrith/crime-stats)",
    "title": "Quarterly crime statistics — station → municipality",
    "url": "https://www.saps.gov.za/services/crimestats.php",
}

_STATIONS_URL = "https://raw.githubusercontent.com/afrith/crime-stats/main/police_stations.csv"
_CRIME_URL = "https://media.githubusercontent.com/media/afrith/crime-stats/main/crime-stats.csv"


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


def _stream_refresh(municipality: str) -> dict | None:
    """Stream the full crime CSV and aggregate for one municipality (slow)."""
    muni = municipality.upper()
    req = urllib.request.Request(_STATIONS_URL, headers={"User-Agent": "striops-ingest/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        stations = list(csv.DictReader(resp.read().decode().splitlines()))
    codes = {r["code"] for r in stations if r.get("muni_code") == muni}
    if not codes:
        return None
    pop = sum(int(float(r.get("population") or 0)) for r in stations if r.get("muni_code") == muni)

    murder: dict[tuple[int, int], int] = defaultdict(int)
    contact: dict[tuple[int, int], int] = defaultdict(int)
    crs: dict[tuple[int, int], int] = defaultdict(int)

    req = urllib.request.Request(_CRIME_URL, headers={"User-Agent": "striops-ingest/1.0"})
    with urllib.request.urlopen(req, timeout=600) as resp:
        reader = csv.DictReader((line.decode("utf-8") for line in resp))
        for row in reader:
            if row.get("station_code") not in codes:
                continue
            key = (int(row["year"]), int(row["month"]))
            cnt = int(float(row.get("crime_count") or 0))
            code = row.get("crime_code")
            if code == "1":
                murder[key] += cnt
            elif code == "Cat 01":
                contact[key] += cnt
            elif code == "Full 17":
                crs[key] += cnt

    payload = {
        "municipality": muni,
        "source": "afrith/crime-stats (SAPS quarterly extracts)",
        "source_url": "https://github.com/afrith/crime-stats",
        "saps_portal": SOURCE["url"],
        "stations": len(codes),
        "population_census_2022_stations": pop,
        "murder_monthly": [{"year": y, "month": m, "count": c} for (y, m), c in sorted(murder.items())],
        "contact_crime_monthly": [
            {"year": y, "month": m, "count": c} for (y, m), c in sorted(contact.items())
        ],
        "community_reported_serious_monthly": [
            {"year": y, "month": m, "count": c} for (y, m), c in sorted(crs.items())
        ],
    }
    _cache_path(muni).write_text(json.dumps(payload, indent=2))
    return payload


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
            payload = _stream_refresh(muni)
            log.info("saps crime refreshed from LFS", extra={"context": {"muni": muni}})
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
            "method": "Sum of SAPS station counts mapped to the municipality from afrith/crime-stats.",
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
