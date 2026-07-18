"""City of Cape Town Open Data Portal (ODP) connector — live public feeds.

Portal: https://odp-cctegis.opendata.arcgis.com  (org `cctegis`)
Hosted feature services: https://services6.arcgis.com/nyYfO9SxHU2ChQd9/...

These are **public, aggregate** datasets — no citizen PII, no credentials. Striops
*pulls* on a schedule and never connects into a live source system. Every fetch:
  - has a bounded timeout and paginates safely,
  - caches the raw response so re-runs are offline-friendly and auditable,
  - falls back to the last cache on any network/parse error (never hard-fails),
  - is reduced to a clean monthly ``MetricSeries`` the engines already understand.

Add a new series by writing a small transformer that returns ``MetricSeries``.
"""
from __future__ import annotations

import json
from collections import OrderedDict
from datetime import UTC, date, datetime

import httpx

from striops.core.logging import get_logger
from striops.core.models import MetricPoint, MetricSeries
from striops.core.paths import cache_dir

log = get_logger("striops.ingestion.coct_opendata")

COCT_ORG = "https://services6.arcgis.com/nyYfO9SxHU2ChQd9/arcgis/rest/services"

# Provenance registry entry (mirrored into domain `sources[]` + feeds report).
SOURCE = {
    "id": "src-coct-odp",
    "publisher": "City of Cape Town",
    "title": "City of Cape Town Open Data Portal",
    "url": "https://odp-cctegis.opendata.arcgis.com",
}

_PAGE_SIZE = 2000


def _fetch_features(
    service: str,
    *,
    layer: int = 0,
    out_fields: str = "*",
    where: str = "1=1",
    order_by: str | None = None,
    timeout: float = 25.0,
    use_cache: bool = True,
) -> list[dict]:
    """Return feature attribute dicts from an ODP FeatureServer, with caching."""
    cache_path = cache_dir() / f"coct_{service}_{layer}.json"
    url = f"{COCT_ORG}/{service}/FeatureServer/{layer}/query"
    features: list[dict] = []
    offset = 0
    try:
        with httpx.Client(timeout=timeout) as client:
            while True:
                params = {
                    "where": where,
                    "outFields": out_fields,
                    "returnGeometry": "false",
                    "resultOffset": offset,
                    "resultRecordCount": _PAGE_SIZE,
                    "f": "json",
                }
                if order_by:
                    params["orderByFields"] = order_by
                resp = client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                if "error" in data:
                    raise RuntimeError(str(data["error"]))
                page = [f.get("attributes", {}) for f in data.get("features", [])]
                features.extend(page)
                if len(page) < _PAGE_SIZE or not data.get("exceededTransferLimit"):
                    break
                offset += _PAGE_SIZE
        cache_path.write_text(json.dumps(features))
        log.info("coct odp fetched", extra={"context": {"service": service, "count": len(features)}})
        return features
    except Exception as exc:
        log.warning(
            "coct odp fetch failed, trying cache",
            extra={"context": {"service": service, "error": str(exc)}},
        )
        if use_cache and cache_path.exists():
            return json.loads(cache_path.read_text())
        return []


def _fetch_grouped_sum(
    service: str,
    value_field: str,
    group_field: str,
    *,
    layer: int = 0,
    timeout: float = 25.0,
    use_cache: bool = True,
) -> list[dict]:
    """Server-side monthly aggregation via ArcGIS outStatistics (one request).

    Returns rows like ``{group_field: <date>, "value": <sum>}`` — far lighter than
    pulling every suburb/row and summing client-side.
    """
    cache_path = cache_dir() / f"coct_{service}_{layer}_sum_{value_field}.json"
    url = f"{COCT_ORG}/{service}/FeatureServer/{layer}/query"
    stats = json.dumps(
        [{"statisticType": "sum", "onStatisticField": value_field, "outStatisticFieldName": "value"}]
    )
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(
                url,
                params={
                    "where": "1=1",
                    "outStatistics": stats,
                    "groupByFieldsForStatistics": group_field,
                    "f": "json",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                raise RuntimeError(str(data["error"]))
        rows = [f.get("attributes", {}) for f in data.get("features", [])]
        cache_path.write_text(json.dumps(rows))
        log.info("coct odp aggregated", extra={"context": {"service": service, "groups": len(rows)}})
        return rows
    except Exception as exc:
        log.warning(
            "coct odp aggregate failed, trying cache",
            extra={"context": {"service": service, "error": str(exc)}},
        )
        if use_cache and cache_path.exists():
            return json.loads(cache_path.read_text())
        return []


def _first_of_month(d: date) -> str:
    return date(d.year, d.month, 1).isoformat()


def _monthly_last(pairs: list[tuple[date, float]]) -> list[MetricPoint]:
    """Collapse (date,value) readings to one point per month (last reading wins)."""
    buckets: OrderedDict[str, tuple[date, float]] = OrderedDict()
    for d, v in sorted(pairs, key=lambda x: x[0]):
        key = _first_of_month(d)
        buckets[key] = (d, v)  # later date in the month overwrites
    return [MetricPoint(period=period, value=round(val, 2)) for period, (_, val) in buckets.items()]


def _to_float(v) -> float | None:
    if v is None:
        return None
    try:
        return float(str(v).replace(",", "").replace("%", "").strip())
    except (ValueError, TypeError):
        return None


# ─────────────────────────────── transformers ───────────────────────────────

def dam_storage_series() -> MetricSeries | None:
    """Measured Big-6 dam storage (% full) — replaces synthetic dam_storage.

    Dataset: 'Dam Levels from 2000' (daily). We keep the last reading per month.
    """
    rows = _fetch_features("Dam_Levels_from_2000")
    pairs: list[tuple[date, float]] = []
    for r in rows:
        raw_date = r.get("DATE")
        pct = _to_float(r.get("TOTAL_STORED___BIG_6_Current"))
        if not raw_date or pct is None:
            continue
        try:
            d = datetime.strptime(raw_date, "%d-%b-%y").date()
        except ValueError:
            continue
        # source stores fraction-of-1 in some rows and percent in others; normalise to %
        if pct <= 1.5:
            pct *= 100.0
        pairs.append((d, pct))
    points = _monthly_last(pairs)
    if not points:
        return None
    return MetricSeries(entity_id="svc-water", metric="dam_storage", unit="percent", points=points)


def system_energy_series() -> MetricSeries | None:
    """Monthly total system energy sent out (kWh).

    Dataset: 'System Energy 2017 to ...' — fresh (updated monthly).
    """
    rows = _fetch_features("Open_Data_System_Energy")
    pairs: list[tuple[date, float]] = []
    for r in rows:
        ms = r.get("Date")
        kwh = _to_float(r.get("Total_System_OUT_KWH"))
        if ms is None or kwh is None:
            continue
        try:
            d = datetime.fromtimestamp(int(ms) / 1000, tz=UTC).date()
        except (ValueError, OverflowError, OSError):
            continue
        pairs.append((d, kwh))
    points = _monthly_last(pairs)
    if not points:
        return None
    return MetricSeries(entity_id="svc-energy", metric="system_energy_kwh", unit="kWh", points=points)


def municipal_arrears_series() -> MetricSeries | None:
    """Total municipal debtors / arrears (ZAR) per month.

    Dataset: 'Municipal Arrears Suburbs and Service Type' — sum of the ``Result``
    column grouped by month. A rising trend is a fiscal-distress signal.
    """
    rows = _fetch_grouped_sum(
        "Municipal_Arrears_Suburbs_and_Service_Type_2025_to_Mar2026", "Result", "Date"
    )
    pairs: list[tuple[date, float]] = []
    for r in rows:
        total = _to_float(r.get("value"))
        raw = r.get("Date")
        if total is None or not raw:
            continue
        try:
            d = datetime.strptime(str(raw).split(",")[0].strip(), "%d/%m/%Y").date()
        except ValueError:
            continue
        pairs.append((d, total))
    points = _monthly_last(pairs)
    if not points:
        return None
    return MetricSeries(entity_id="svc-finance", metric="municipal_arrears_zar", unit="ZAR", points=points)


def electricity_billed_series() -> MetricSeries | None:
    """Electricity billed (kWh) per month across the City.

    Dataset: 'Suburb Level Electricity Billing' — sum of ``Quantity`` grouped by
    month. Zero/blank months (not yet billed) are dropped so we never plot a false 0.
    """
    rows = _fetch_grouped_sum(
        "Suburb_Level_Electricity_Billing_2021_to_March_2026", "Quantity", "Date"
    )
    pairs: list[tuple[date, float]] = []
    for r in rows:
        kwh = _to_float(r.get("value"))
        ms = r.get("Date")
        if not kwh or kwh <= 0 or ms is None:
            continue
        try:
            d = datetime.fromtimestamp(int(ms) / 1000, tz=UTC).date()
        except (ValueError, OverflowError, OSError):
            continue
        pairs.append((d, kwh))
    points = _monthly_last(pairs)
    if not points:
        return None
    return MetricSeries(entity_id="svc-energy", metric="electricity_billed_kwh", unit="kWh", points=points)


# Registry of live series transformers. Add new feeds here.
_TRANSFORMERS = (
    dam_storage_series,
    system_energy_series,
    municipal_arrears_series,
    electricity_billed_series,
)


def fetch_live_series() -> list[MetricSeries]:
    """Return every live CoCT ODP series we can currently build (best-effort)."""
    out: list[MetricSeries] = []
    for fn in _TRANSFORMERS:
        try:
            series = fn()
        except Exception as exc:  # never let one feed break the batch
            log.warning("coct series failed", extra={"context": {"fn": fn.__name__, "error": str(exc)}})
            series = None
        if series and series.points:
            out.append(series)
    return out
