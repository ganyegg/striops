"""National Treasury Municipal Money API — budget vs actual by function.

API: https://municipaldata.treasury.gov.za/api
Works for any Municipal Demarcation Board code (CPT, JHB, ETH, …).

Maps mSCOA function codes into Striops ``BudgetLine.function_name`` values that
match ``datasets/seed/service_areas.json``. Falls back to seed on any failure.
"""
from __future__ import annotations

import json
from collections import defaultdict

import httpx

from striops.core.config import get_settings
from striops.core.logging import get_logger
from striops.core.models import BudgetLine
from striops.core.paths import cache_dir, seed_dir

log = get_logger("striops.ingestion.treasury")

TREASURY_BASE = "https://municipaldata.treasury.gov.za/api"
CUBE = "incexp_v2"

SOURCE = {
    "id": "src-municipal-money",
    "publisher": "National Treasury",
    "title": "Municipal Money (Section 71 / mSCOA)",
    "url": "https://municipaldata.treasury.gov.za/",
}

# Expense-side line items (operating expenditure), summed per function.
# Exclude 2900 ("Other expenditure") — on audited returns it often behaves like a
# roll-up and would double-count against the detailed expense codes below.
_EXPENSE_ITEMS = (
    "3000",
    "3100",
    "3200",
    "3300",
    "3400",
    "3500",
    "3600",
    "3700",
    "3800",
    "3900",
    "4000",
    "4100",
    "4200",
    "4300",
)

# Striops budget_function → mSCOA function.code list
_FUNCTION_GROUPS: dict[str, tuple[str, ...]] = {
    "Electricity": ("4101",),
    "Water and Sanitation": ("4201", "4202", "4203", "4302", "4303", "4304"),
    "Solid Waste Management": ("4402", "4403", "4404"),
    "Roads and Transport": ("3203", "3204", "3205"),
    "Health": ("2502", "2505"),
    "Finance": ("1204",),
    "Community and Libraries": ("2106", "2114", "2117", "2203", "2204", "2205"),
}

# Prefer adjusted budget, then original; prefer audited actual, then actual.
_BUDGET_TYPES = ("ADJB", "ORGB", "TABB")
_ACTUAL_TYPES = ("AUDA", "ACT", "PAUD")


def _seed_budget_lines() -> list[BudgetLine]:
    path = seed_dir() / "budget_lines.json"
    if not path.exists():
        return []
    return [BudgetLine(**d) for d in json.loads(path.read_text())]


def _aggregate_by_function(
    client: httpx.Client,
    *,
    municipality: str,
    year: int,
    amount_type: str,
) -> dict[str, float]:
    """Return {function.code: opex_sum} for one amount type / FY."""
    totals: dict[str, float] = defaultdict(float)
    for item in _EXPENSE_ITEMS:
        resp = client.get(
            f"{TREASURY_BASE}/cubes/{CUBE}/aggregate",
            params={
                "cut": (
                    f'demarcation.code:"{municipality}"'
                    f"|financial_year_end.year:{year}"
                    f'|amount_type.code:"{amount_type}"'
                    f'|period_length.length:"year"'
                    f'|item.code:"{item}"'
                ),
                "drilldown": "function.code",
                "aggregates": "amount.sum",
                "page_size": 200,
            },
        )
        resp.raise_for_status()
        for cell in resp.json().get("cells") or []:
            code = cell.get("function.code")
            amt = cell.get("amount.sum")
            if code and amt is not None:
                totals[str(code)] += float(amt)
    return dict(totals)


def _pick_amount_type(
    client: httpx.Client,
    *,
    municipality: str,
    year: int,
    candidates: tuple[str, ...],
) -> tuple[str, dict[str, float]] | None:
    for amount_type in candidates:
        totals = _aggregate_by_function(
            client, municipality=municipality, year=year, amount_type=amount_type
        )
        if any(v > 0 for v in totals.values()):
            return amount_type, totals
    return None


def _available_years(client: httpx.Client, municipality: str) -> list[int]:
    resp = client.get(
        f"{TREASURY_BASE}/cubes/{CUBE}/members/financial_year_end",
        params={"cut": f'demarcation.code:"{municipality}"', "page_size": 50},
    )
    resp.raise_for_status()
    years = sorted(
        {
            int(row["financial_year_end.year"])
            for row in resp.json().get("data") or []
            if row.get("financial_year_end.year") is not None
        }
    )
    return years


def _map_groups(by_code: dict[str, float]) -> dict[str, float]:
    out: dict[str, float] = {}
    for name, codes in _FUNCTION_GROUPS.items():
        total = sum(by_code.get(c, 0.0) for c in codes)
        if total > 0:
            out[name] = total
    return out


def fetch_budget_lines(municipality: str | None = None, timeout: float = 90.0) -> list[BudgetLine]:
    """Fetch budget vs actual per Striops function; fall back to seed on any issue."""
    municipality = municipality or get_settings().striops_municipality
    cache_path = cache_dir() / f"treasury_budget_{municipality}.json"
    try:
        with httpx.Client(timeout=timeout) as client:
            years = _available_years(client, municipality)
            # Use the last 3 financial years that have usable data.
            years = years[-3:] if years else []
            lines: list[BudgetLine] = []
            for year in years:
                budget_pick = _pick_amount_type(
                    client, municipality=municipality, year=year, candidates=_BUDGET_TYPES
                )
                actual_pick = _pick_amount_type(
                    client, municipality=municipality, year=year, candidates=_ACTUAL_TYPES
                )
                if not budget_pick and not actual_pick:
                    continue
                budget_map = _map_groups(budget_pick[1]) if budget_pick else {}
                actual_map = _map_groups(actual_pick[1]) if actual_pick else {}
                for function_name in sorted(set(budget_map) | set(actual_map)):
                    budget = budget_map.get(function_name, 0.0)
                    actual = actual_map.get(function_name, 0.0)
                    if budget <= 0 and actual <= 0:
                        continue
                    lines.append(
                        BudgetLine(
                            function_name=function_name,
                            financial_year=year,
                            budget=budget,
                            actual=actual if actual > 0 else budget,
                            source="treasury",
                        )
                    )
            if not lines:
                raise RuntimeError("Treasury returned no mappable budget lines")

        cache_path.write_text(json.dumps([ln.model_dump() for ln in lines], indent=2))
        log.info(
            "treasury budget lines ingested",
            extra={"context": {"muni": municipality, "count": len(lines), "years": years}},
        )
        return lines
    except Exception as exc:
        log.warning("treasury fetch failed, using seed", extra={"context": {"error": str(exc)}})
        if cache_path.exists():
            try:
                return [BudgetLine(**d) for d in json.loads(cache_path.read_text())]
            except Exception:
                pass
        return _seed_budget_lines()
