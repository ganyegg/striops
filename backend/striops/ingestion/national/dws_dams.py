"""Department of Water and Sanitation — weekly water supply system storage.

Cape Town system: https://www.dws.gov.za/Hydrology/Weekly/RiverSystems.aspx?river=CT
Works for other systems by mapping municipality → river code (see ``_RIVER_BY_MUNI``).
"""
from __future__ import annotations

import json
import re
from datetime import date

import httpx

from striops.core.logging import get_logger
from striops.core.models import MetricPoint, MetricSeries
from striops.core.paths import cache_dir

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


def _parse_system_page(html: str) -> tuple[date | None, float | None, float | None]:
    """Return (as_of, this_week_pct, last_week_pct) from a RiverSystems page."""
    lines = _plain_lines(html)
    as_of: date | None = None
    for ln in lines:
        m = re.search(r"State of Dams on (\d{4}-\d{2}-\d{2})", ln, re.I)
        if m:
            as_of = date.fromisoformat(m.group(1))
            break

    # The system total row is the last FSC block: FSC, This Week %, Last Week %, Last Year %
    # Identify by finding the largest FSC (Cape Town ~889) near the end.
    nums: list[float] = []
    for ln in lines:
        if re.fullmatch(r"\d+(?:\.\d+)?", ln):
            nums.append(float(ln))

    this_week = last_week = None
    # Walk number groups of 4 after headers FSC / This Week / Last Week
    # Prefer the last quartet where second+third look like percentages (0–120).
    for i in range(len(nums) - 3):
        fsc, tw, lw, ly = nums[i], nums[i + 1], nums[i + 2], nums[i + 3]
        if fsc >= 50 and 0 <= tw <= 120 and 0 <= lw <= 120 and 0 <= ly <= 130:
            this_week, last_week = tw, lw
    return as_of, this_week, last_week


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


def dws_series_from_cache(municipality: str = "CPT") -> MetricSeries | None:
    """Read the weekly-storage series from cache only.

    Callable from request paths — ``fetch_dws_dam_series`` hits the network and
    must stay in the ingest path.
    """
    hist_path = cache_dir() / f"dws_system_{municipality.upper()}_history.json"
    if not hist_path.exists():
        return None
    try:
        return _series_from_history(json.loads(hist_path.read_text()))
    except Exception as exc:
        log.warning("dws cache unreadable", extra={"context": {"error": str(exc)}})
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
            as_of, this_week, last_week = _parse_system_page(resp.text)
        if this_week is None or as_of is None:
            raise RuntimeError("could not parse DWS system storage")
        payload = {
            "municipality": municipality.upper(),
            "river": river,
            "as_of": as_of.isoformat(),
            "this_week_pct": this_week,
            "last_week_pct": last_week,
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
        last_week = payload.get("last_week_pct")

    period = as_of.replace(day=1)
    # Weekly readings are folded into a monthly history file so Pulse has the
    # two points it needs for a month-over-month direction.
    hist_path = cache_dir() / f"dws_system_{municipality.upper()}_history.json"
    history: list[dict] = []
    if hist_path.exists():
        try:
            history = json.loads(hist_path.read_text())
        except Exception:
            history = []
    history = [h for h in history if h.get("period") != period.isoformat()]
    history.append({"period": period.isoformat(), "value": float(this_week)})
    history = sorted(history, key=lambda h: h["period"])[-24:]
    hist_path.write_text(json.dumps(history, indent=2))

    log.info(
        "dws system storage",
        extra={"context": {"muni": municipality, "pct": this_week, "as_of": as_of.isoformat()}},
    )
    return _series_from_history(history)
