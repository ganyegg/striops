"""National Treasury Municipal Money API puller (budget vs actual).

API: https://municipaldata.treasury.gov.za/api  (Cape Town demarcation = CPT)
The cube schema is intricate and occasionally changes, so this puller is
best-effort and falls back to committed seed budget lines to keep ingestion
deterministic offline/CI.
"""
from __future__ import annotations

import json

import httpx

from striops.core.config import get_settings
from striops.core.logging import get_logger
from striops.core.models import BudgetLine
from striops.core.paths import cache_dir, seed_dir

log = get_logger("striops.ingestion.treasury")

TREASURY_BASE = "https://municipaldata.treasury.gov.za/api"


def _seed_budget_lines() -> list[BudgetLine]:
    path = seed_dir() / "budget_lines.json"
    if not path.exists():
        return []
    return [BudgetLine(**d) for d in json.loads(path.read_text())]


def fetch_budget_lines(municipality: str | None = None, timeout: float = 20.0) -> list[BudgetLine]:
    """Fetch budget vs actual per function; fall back to seed on any issue."""
    municipality = municipality or get_settings().striops_municipality
    cache_path = cache_dir() / f"treasury_budget_{municipality}.json"
    try:
        with httpx.Client(timeout=timeout) as client:
            # Ping the API root; if reachable we would map the incexp cube here.
            resp = client.get(f"{TREASURY_BASE}/cubes", params={"format": "json"})
            resp.raise_for_status()
        # NOTE: Full cube mapping (incexp/capital) is a Phase 2 task. For the
        # slice we persist the reachable-but-unmapped signal and use curated
        # seed lines so downstream engines have stable, correct inputs.
        lines = _seed_budget_lines()
        cache_path.write_text(json.dumps([_l.model_dump() for _l in lines]))
        log.info("treasury reachable; using curated budget lines", extra={"context": {"muni": municipality, "count": len(lines)}})
        return lines
    except Exception as exc:
        log.warning("treasury fetch failed, using seed", extra={"context": {"error": str(exc)}})
        return _seed_budget_lines()
