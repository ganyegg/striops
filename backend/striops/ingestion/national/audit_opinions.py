"""AGSA audit opinions via National Treasury Municipal Money cube.

Cube: https://municipaldata.treasury.gov.za/api/cubes/audit_opinions
"""
from __future__ import annotations

import json

import httpx

from striops.core.logging import get_logger
from striops.core.paths import cache_dir

log = get_logger("striops.ingestion.national.audit_opinions")

SOURCE = {
    "id": "src-agsa",
    "publisher": "Auditor-General of South Africa / National Treasury",
    "title": "MFMA audit opinions (Municipal Money)",
    "url": "https://mfma-2025.agsa.co.za/",
}

_URL = "https://municipaldata.treasury.gov.za/api/cubes/audit_opinions/facts"


def fetch_audit_overlay(municipality: str = "CPT", timeout: float = 30.0) -> bool:
    muni = municipality.upper()
    cache_path = cache_dir() / f"audit_opinions_{muni}.json"
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(
                _URL,
                params={
                    "cut": f'demarcation.code:"{muni}"',
                    "order": "financial_year_end.year:desc",
                    "page_size": 20,
                },
            )
            resp.raise_for_status()
            rows = resp.json().get("data") or []
        if not rows:
            raise RuntimeError("no audit opinions")
        cache_path.write_text(json.dumps(rows, indent=2))
    except Exception as exc:
        log.warning("audit opinions fetch failed", extra={"context": {"error": str(exc)}})
        if not cache_path.exists():
            return False
        rows = json.loads(cache_path.read_text())

    latest = rows[0]
    year = latest.get("financial_year_end.year")
    label = latest.get("opinion.label") or latest.get("opinion.code") or "Unknown"
    report_url = latest.get("opinion.report_url") or SOURCE["url"]
    code = (latest.get("opinion.code") or "").lower()
    # Clean = unqualified with no findings
    is_clean = code in {"unqualified", "unqualified_no_findings"}

    overlay_path = cache_dir() / f"domain_overlay_{muni}.json"
    existing: dict = {}
    if overlay_path.exists():
        try:
            existing = json.loads(overlay_path.read_text())
        except Exception:
            existing = {}

    fiscal = existing.get("fiscal") or {}
    inds = {i["key"]: i for i in fiscal.get("indicators") or []}
    inds["audit"] = {
        "key": "audit",
        "label": "Latest audit outcome",
        "value": label,
        "as_of": f"FY{year}" if year else "latest",
        "trend": "flat" if is_clean else "down",
        "verification": "verified",
        "source_id": "src-agsa",
        "confidence": 0.95,
        "method": "National Treasury audit_opinions cube (AGSA).",
    }
    fiscal["indicators"] = list(inds.values())
    srcs = {s["id"]: s for s in fiscal.get("sources") or []}
    srcs[SOURCE["id"]] = {**SOURCE, "url": report_url}
    fiscal["sources"] = list(srcs.values())
    existing["fiscal"] = fiscal
    overlay_path.write_text(json.dumps(existing, indent=2))
    log.info(
        "audit opinion overlay",
        extra={"context": {"muni": muni, "year": year, "opinion": label}},
    )
    return True
