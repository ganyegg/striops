"""Data feed transparency — what is live, what is cached, what is curated.

Striops' credibility rests on never pretending. This module reports, per feed,
exactly where the numbers on screen come from right now and what a pilot
integration would upgrade.
"""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

from striops.core.config import Settings, get_settings
from striops.core.paths import cache_dir, seed_dir
from striops.persistence import Repository, get_repository


class FeedStatus(BaseModel):
    id: str
    name: str
    publisher: str
    status: str  # live | cached | curated | seed
    status_label: str
    cadence: str
    description: str
    unlocks: str
    last_refreshed: str | None = None  # ISO or human note
    last_refreshed_label: str  # display string


class FeedsReport(BaseModel):
    generated_at: str
    honesty_note: str
    feeds: list[FeedStatus] = Field(default_factory=list)
    live_count: int = 0
    total_count: int = 0


_STATUS_LABELS = {
    "live": "Live connection",
    "cached": "Cached from live source",
    "curated": "Curated from public sources",
    "seed": "Seed / demonstration series",
}


def _mtime_iso(path: Path) -> str | None:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).isoformat()


def _mtime_label(path: Path | None, fallback: str) -> tuple[str | None, str]:
    if path is None or not path.exists():
        return None, fallback
    ts = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    return ts.isoformat(), ts.strftime("%d %b %Y %H:%M UTC")


def build_feeds_report(
    repo: Repository | None = None,
    settings: Settings | None = None,
) -> FeedsReport:
    settings = settings or get_settings()
    repo = repo or get_repository(settings)
    muni = settings.striops_municipality

    treasury_path = cache_dir() / f"treasury_budget_{muni}.json"
    treasury_cached = treasury_path.exists()
    metrics_status = "live" if repo.backend == "postgres" else "seed"
    metrics_seed = seed_dir() / "metrics.json"
    domains_seed = seed_dir() / "domains" / f"{muni}.json"
    wins_seed = seed_dir() / "wins" / f"{muni}.json"
    arcgis_files = list(cache_dir().glob("arcgis_layer_*.json"))
    arcgis_path = max(arcgis_files, key=lambda p: p.stat().st_mtime) if arcgis_files else None
    saps_path = cache_dir() / f"saps_crime_{muni}.json"
    if not saps_path.exists():
        seed_saps = seed_dir() / "national" / f"saps_crime_{muni}.json"
        saps_path = seed_saps if seed_saps.exists() else saps_path
    dws_path = cache_dir() / f"dws_system_{muni}.json"
    census_path = cache_dir() / f"census_{muni}.json"
    if not census_path.exists():
        seed_census = seed_dir() / "national" / "census_2022_metros.json"
        census_path = seed_census if seed_census.exists() else census_path
    audit_path = cache_dir() / f"audit_opinions_{muni}.json"

    if metrics_status == "live":
        metrics_refreshed, metrics_label = None, "Live from Postgres"
    else:
        metrics_refreshed, metrics_label = _mtime_label(metrics_seed, "n/a — seed")

    treasury_refreshed, treasury_label = (
        _mtime_label(treasury_path, "n/a — seed")
        if treasury_cached
        else (None, "n/a — seed")
    )
    domains_refreshed, domains_label = _mtime_label(domains_seed, "n/a — curated seed")
    wins_refreshed, wins_label = _mtime_label(wins_seed, "n/a — curated seed")
    arcgis_refreshed, arcgis_label = (
        _mtime_label(arcgis_path, "n/a — seed") if arcgis_path else (None, "n/a — seed")
    )
    saps_refreshed, saps_label = _mtime_label(saps_path, "n/a — seed extract")
    dws_refreshed, dws_label = _mtime_label(dws_path, "n/a — not yet fetched")
    census_refreshed, census_label = _mtime_label(census_path, "n/a — seed")
    audit_refreshed, audit_label = _mtime_label(audit_path, "n/a — not yet fetched")

    feeds = [
        FeedStatus(
            id="metrics",
            name="Operational metric series",
            publisher="City departments (SAP / service requests / telemetry)",
            status=metrics_status,
            status_label=_STATUS_LABELS[metrics_status],
            cadence="Monthly (pilot target: daily)",
            description=(
                "The time series behind risks and forecasts: water losses, road "
                "backlog, refuse requests, lighting faults, library visits."
            ),
            unlocks="Risks and forecasts recompute from real departmental data every morning.",
            last_refreshed=metrics_refreshed,
            last_refreshed_label=metrics_label,
        ),
        FeedStatus(
            id="treasury",
            name="Municipal budget & spend",
            publisher="National Treasury (municipaldata.treasury.gov.za)",
            status="cached" if treasury_cached else "seed",
            status_label=_STATUS_LABELS["cached" if treasury_cached else "seed"],
            cadence="Quarterly (s71 reporting)",
            description="Budget vs actual per function — powers underspend opportunities and utilisation evidence.",
            unlocks="Every rand on screen reconciles to Treasury's published s71 returns.",
            last_refreshed=treasury_refreshed,
            last_refreshed_label=treasury_label,
        ),
        FeedStatus(
            id="domains",
            name="Domain profiles & headline indicators",
            publisher="City of Cape Town, DWS, SAPS, Stats SA (public documents)",
            status="curated",
            status_label=_STATUS_LABELS["curated"],
            cadence="Per publication, with verification badges",
            description=(
                "Budget book figures, dam levels, safety allocations — each indicator "
                "carries a resolvable public source and a verification status."
            ),
            unlocks="Automated re-verification: Striops flags when a published source changes.",
            last_refreshed=domains_refreshed,
            last_refreshed_label=domains_label,
        ),
        FeedStatus(
            id="wins",
            name="Delivery wins & initiatives",
            publisher="City of Cape Town announcements and reports",
            status="curated",
            status_label=_STATUS_LABELS["curated"],
            cadence="As announced, source-linked",
            description="The good-news register: initiatives with metrics, owners and evidence links.",
            unlocks="Wins update automatically as departmental metrics move.",
            last_refreshed=wins_refreshed,
            last_refreshed_label=wins_label,
        ),
        FeedStatus(
            id="arcgis",
            name="Spatial & asset layers",
            publisher="City of Cape Town Open Data Portal (ArcGIS)",
            status="cached" if arcgis_path else "seed",
            status_label=_STATUS_LABELS["cached" if arcgis_path else "seed"],
            cadence="Per layer refresh",
            description="Wards, infrastructure and asset layers for the strategic twin graph.",
            unlocks="Risks land on a map: which wards feel a water or roads failure first.",
            last_refreshed=arcgis_refreshed,
            last_refreshed_label=arcgis_label,
        ),
        FeedStatus(
            id="saps",
            name="Crime statistics (SAPS)",
            publisher="SAPS quarterly stats (afrith/crime-stats municipal aggregate)",
            status="cached" if saps_path.exists() else "seed",
            status_label=_STATUS_LABELS["cached" if saps_path.exists() else "seed"],
            cadence="Monthly (from quarterly SAPS releases)",
            description="Murder and contact-crime counts for the metro, rolled up from police stations.",
            unlocks="Safety theme moves from budget headlines to measured crime trend.",
            last_refreshed=saps_refreshed,
            last_refreshed_label=saps_label,
        ),
        FeedStatus(
            id="dws",
            name="National dam storage (DWS)",
            publisher="Department of Water and Sanitation",
            status="cached" if dws_path.exists() else "seed",
            status_label=_STATUS_LABELS["cached" if dws_path.exists() else "seed"],
            cadence="Weekly",
            description="Cape Town water-supply-system storage % from the national weekly dams bulletin.",
            unlocks="National water pulse alongside City Open Data dam levels.",
            last_refreshed=dws_refreshed,
            last_refreshed_label=dws_label,
        ),
        FeedStatus(
            id="census",
            name="Census baselines (Stats SA)",
            publisher="Statistics South Africa — Census 2022",
            status="cached" if census_path.exists() else "seed",
            status_label=_STATUS_LABELS["cached" if census_path.exists() else "seed"],
            cadence="Decennial (baselines)",
            description="Population and household denominators for metros — rates and equity context.",
            unlocks="Per-100k crime rates and service coverage use official Census denominators.",
            last_refreshed=census_refreshed,
            last_refreshed_label=census_label,
        ),
        FeedStatus(
            id="agsa",
            name="Audit opinions (AGSA)",
            publisher="Auditor-General via National Treasury Municipal Money",
            status="cached" if audit_path.exists() else "seed",
            status_label=_STATUS_LABELS["cached" if audit_path.exists() else "seed"],
            cadence="Annual (MFMA cycle)",
            description="Latest municipal audit outcome for the active demarcation code.",
            unlocks="Fiscal theme shows verified AGSA outcome, not a placeholder.",
            last_refreshed=audit_refreshed,
            last_refreshed_label=audit_label,
        ),
    ]

    live_count = sum(1 for f in feeds if f.status in ("live", "cached"))
    return FeedsReport(
        generated_at=datetime.now(UTC).isoformat(),
        honesty_note=(
            "Striops never hides its sources. Feeds marked Seed are demonstration "
            "series; the 90-day pilot replaces them with live departmental connections. "
            "Each feed shows when it was last refreshed."
        ),
        feeds=feeds,
        live_count=live_count,
        total_count=len(feeds),
    )
