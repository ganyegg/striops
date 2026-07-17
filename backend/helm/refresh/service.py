"""On-demand refresh — clear caches, re-ingest public feeds, rebuild brief."""
from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from helm.core.cache import cache_clear
from helm.core.config import Settings, get_settings
from helm.core.logging import get_logger

log = get_logger("helm.refresh")


class RefreshResult(BaseModel):
    ok: bool
    refreshed_at: str
    brief_cache_cleared: bool = True
    domain_cache_cleared: bool = True
    ingestion: dict = Field(default_factory=dict)
    ingestion_error: str | None = None
    feeds_live_count: int | None = None
    feeds_total_count: int | None = None
    note: str = (
        "Helm is dynamic: new metrics, domains, and feed updates appear after ingest. "
        "Scheduled/nightly ingest keeps the twin current; Refresh now pulls on demand."
    )


def run_refresh(settings: Settings | None = None, *, run_ingest: bool = True) -> RefreshResult:
    settings = settings or get_settings()
    cache_clear()

    try:
        from helm.domains import service as domains_service

        domains_service._profiles.cache_clear()
        domains_service._municipalities.cache_clear()
    except Exception as exc:  # pragma: no cover
        log.warning("domain cache clear failed", extra={"context": {"error": str(exc)}})

    try:
        from helm.demographics import clear_affected_cache

        clear_affected_cache()
    except Exception:
        pass

    try:
        from helm.places import clear_places_cache

        clear_places_cache()
    except Exception:
        pass

    # Force repository reconnect so Postgres picks up new rows after ingest.
    try:
        import helm.persistence.repository as repo_mod

        repo_mod._repository = None
    except Exception:
        pass

    ingestion: dict = {}
    ingest_error = None
    if run_ingest:
        try:
            from helm.ingestion.pipeline import run as ingest_run

            ingestion = ingest_run() or {}
        except Exception as exc:
            ingest_error = str(exc)
            log.warning("ingest during refresh failed", extra={"context": {"error": ingest_error}})

    live = total = None
    try:
        from helm.feeds import build_feeds_report
        from helm.persistence import get_repository

        feeds = build_feeds_report(repo=get_repository(settings), settings=settings)
        live, total = feeds.live_count, feeds.total_count
    except Exception:
        pass

    # Warm brief cache with a fresh build
    try:
        from helm.executive_brief import build_executive_brief

        build_executive_brief(settings=settings)
    except Exception as exc:
        log.warning("brief rebuild after refresh failed", extra={"context": {"error": str(exc)}})

    return RefreshResult(
        ok=ingest_error is None,
        refreshed_at=datetime.now(timezone.utc).isoformat(),
        ingestion=ingestion,
        ingestion_error=ingest_error,
        feeds_live_count=live,
        feeds_total_count=total,
    )
