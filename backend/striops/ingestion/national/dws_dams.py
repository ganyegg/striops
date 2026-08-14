"""Department of Water and Sanitation — weekly water supply system storage.

Cape Town system: https://www.dws.gov.za/Hydrology/Weekly/RiverSystems.aspx?river=CT
Works for other systems by mapping municipality → river code (see ``_RIVER_BY_MUNI``).
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import httpx

from striops.core.logging import get_logger
from striops.core.models import MetricPoint, MetricSeries
from striops.core.paths import cache_dir, seed_dir

log = get_logger("striops.ingestion.national.dws_dams")

SOURCE = {
    "id": "src-dws",
    "publisher": "Department of Water and Sanitation",
    "title": "Weekly State of Dams — water supply systems",
    "url": "https://www.dws.gov.za/Hydrology/Weekly/",
}

_RIVER_BY_MUNI = {
    "CPT": "CT",  # Cape Town system
    "NMA": "AL",  # Algoa (approx — NMB)
    "BUF": "AM",  # Amathole
    "ETH": "UM",  # Umgeni
    "JHB": "IV",  # Integrated Vaal River System (proxy)
    "TSH": "IV",
    "EKU": "IV",
    "MAN": "BF",  # Bloemfontein
}

_URL = "https://www.dws.gov.za/Hydrology/Weekly/RiverSystems.aspx?river={river}"


def _plain_lines(html: str) -> list[str]:
    text = re.sub(r"<script.*?</script>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", "\n", text)
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def _parse_system_page(
    html: str,
) -> tuple[date | None, float | None, float | None, float | None]:
    """Return (as_of, this_week_pct, last_week_pct, last_year_pct).

    The system Total row reads: FSC, This Week %, Last Week %, Last Year % —
    for Cape Town on 2026-08-10 that is 889.3, 78.2, 77.9, 88.1. Last year is
    worth keeping: dam storage barely moves month to month, so the year-on-year
    gap carries the signal a mayor actually needs.
    """
    lines = _plain_lines(html)
    as_of: date | None = None
    for ln in lines:
        m = re.search(r"State of Dams on (\d{4}-\d{2}-\d{2})", ln, re.I)
        if m:
            as_of = date.fromisoformat(m.group(1))
            break

    # The system total row is the last FSC block. Identify by finding the
    # largest FSC (Cape Town ~889) near the end.
    nums: list[float] = []
    for ln in lines:
        if re.fullmatch(r"\d+(?:\.\d+)?", ln):
            nums.append(float(ln))

    this_week = last_week = last_year = None
    # Prefer the last quartet where the three trailing values look like percentages.
    for i in range(len(nums) - 3):
        fsc, tw, lw, ly = nums[i], nums[i + 1], nums[i + 2], nums[i + 3]
        if fsc >= 50 and 0 <= tw <= 120 and 0 <= lw <= 120 and 0 <= ly <= 130:
            this_week, last_week, last_year = tw, lw, ly
    return as_of, this_week, last_week, last_year


def _series_from_history(history: list[dict]) -> MetricSeries | None:
    points = [
        MetricPoint(period=date.fromisoformat(h["period"]), value=float(h["value"]))
        for h in sorted(history, key=lambda h: h["period"])
        if h.get("period") and h.get("value") is not None
    ]
    if not points:
        return None
    return MetricSeries(
        entity_id="svc-water",
        metric="dws_system_storage",
        unit="percent",
        points=points,
    )


def _history_paths(municipality: str) -> tuple[Path, Path]:
    """Cache path (written by ingest) and seed path (shipped in the repo).

    Render's free disk is ephemeral, so a cache-only history resets on every
    deploy and can never accumulate the two points Pulse needs. The seed copy
    means a fresh instance shows the current dam level immediately.
    """
    name = f"dws_system_{municipality.upper()}_history.json"
    return cache_dir() / name, seed_dir() / "national" / name


def dws_series_from_cache(municipality: str = "CPT") -> MetricSeries | None:
    """Read the weekly-storage series without touching the network.

    Callable from request paths — ``fetch_dws_dam_series`` hits the network and
    must stay in the ingest path.
    """
    for path in _history_paths(municipality):
        if not path.exists():
            continue
        try:
            return _series_from_history(json.loads(path.read_text()))
        except Exception as exc:
            log.warning(
                "dws history unreadable",
                extra={"context": {"path": path.name, "error": str(exc)}},
            )
    return None


def fetch_dws_dam_series(municipality: str = "CPT", timeout: float = 40.0) -> MetricSeries | None:
    river = _RIVER_BY_MUNI.get(municipality.upper())
    if not river:
        return None
    cache_path = cache_dir() / f"dws_system_{municipality.upper()}.json"
    url = _URL.format(river=river)
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            as_of, this_week, last_week, last_year = _parse_system_page(resp.text)
        if this_week is None or as_of is None:
            raise RuntimeError("could not parse DWS system storage")
        payload = {
            "municipality": municipality.upper(),
            "river": river,
            "as_of": as_of.isoformat(),
            "this_week_pct": this_week,
            "last_week_pct": last_week,
            "last_year_pct": last_year,
            "url": url,
            "source": SOURCE,
        }
        cache_path.write_text(json.dumps(payload, indent=2))
    except Exception as exc:
        log.warning("dws fetch failed", extra={"context": {"error": str(exc)}})
        if not cache_path.exists():
            return None
        payload = json.loads(cache_path.read_text())
        as_of = date.fromisoformat(payload["as_of"])
        this_week = float(payload["this_week_pct"])
        last_year = payload.get("last_year_pct")

    period = as_of.replace(day=1)
    # Weekly readings are folded into a monthly history file so Pulse has the
    # two points it needs for a month-over-month direction.
    hist_path, _ = _history_paths(municipality)
    history: list[dict] = []
    for path in _history_paths(municipality):
        if path.exists():
            try:
                history = json.loads(path.read_text())
                break
            except Exception:
                history = []
    by_period = {h["period"]: h for h in history if h.get("period")}
    by_period[period.isoformat()] = {"period": period.isoformat(), "value": float(this_week)}
    # Backfill the same month a year ago from the published Last Year column, so
    # a fresh instance has real depth instead of one repeated reading.
    if last_year is not None:
        prior = period.replace(year=period.year - 1).isoformat()
        by_period.setdefault(prior, {"period": prior, "value": float(last_year)})
    history = sorted(by_period.values(), key=lambda h: h["period"])[-24:]
    hist_path.write_text(json.dumps(history, indent=2))

    log.info(
        "dws system storage",
        extra={"context": {"muni": municipality, "pct": this_week, "as_of": as_of.isoformat()}},
    )
    return _series_from_history(history)
