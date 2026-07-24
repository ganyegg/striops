"""Load and serve deep-dive domain profiles + the municipality registry."""
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

from striops.core.logging import get_logger
from striops.core.models import DomainId, DomainProfile, Municipality
from striops.core.paths import cache_dir, seed_dir
from striops.domains.registry import catalog_entry, domain_catalog, load_municipalities

log = get_logger("striops.domains")


def _apply_overlay(profile: DomainProfile, overlay: dict) -> DomainProfile:
    """Merge cache overlay indicators/sources onto a seed domain profile."""
    data = profile.model_dump()
    by_key = {i["key"]: i for i in data.get("indicators") or []}
    for raw in overlay.get("indicators") or []:
        by_key[raw["key"]] = {**by_key.get(raw["key"], {}), **raw}
    data["indicators"] = list(by_key.values())
    src_by_id = {s["id"]: s for s in data.get("sources") or []}
    for raw in overlay.get("sources") or []:
        src_by_id[raw["id"]] = {**src_by_id.get(raw["id"], {}), **raw}
    data["sources"] = list(src_by_id.values())
    merged = DomainProfile(**data)
    validate_profile(merged)
    return merged


def _overlay_for(code: str) -> dict:
    path = cache_dir() / f"domain_overlay_{code.upper()}.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


@lru_cache
def _municipalities() -> list[Municipality]:
    return load_municipalities()


def list_municipalities() -> list[Municipality]:
    return _municipalities()


def get_municipality(code: str) -> Municipality | None:
    code = code.upper()
    return next((m for m in _municipalities() if m.code == code), None)


@lru_cache
def _profiles(code: str) -> dict[str, DomainProfile]:
    path = seed_dir() / "domains" / f"{code.upper()}.json"
    if not path.exists():
        return {}
    out: dict[str, DomainProfile] = {}
    for raw in json.loads(path.read_text()):
        profile = DomainProfile(**raw)
        validate_profile(profile)
        out[profile.id.value] = profile
    return out


def validate_profile(profile: DomainProfile) -> None:
    """Guarantee provenance integrity: every indicator/policy resolves to a source."""
    source_ids = {s.id for s in profile.sources}
    for ind in profile.indicators:
        if ind.source_id not in source_ids:
            raise ValueError(
                f"{profile.municipality}/{profile.id.value}: indicator '{ind.key}' "
                f"references unknown source '{ind.source_id}'"
            )
    for pol in profile.policies:
        if pol.source_id not in source_ids:
            raise ValueError(
                f"{profile.municipality}/{profile.id.value}: policy '{pol.title}' "
                f"references unknown source '{pol.source_id}'"
            )


def list_domains(code: str) -> list[dict]:
    """Catalog of all domains, annotated with availability for this municipality."""
    profiles = _profiles(code)
    muni = get_municipality(code)
    available = {d.value for d in (muni.domains_available if muni else [])}
    rows: list[dict] = []
    for entry in domain_catalog():
        profile = profiles.get(entry.id.value)
        is_available = entry.id.value in available and profile is not None
        rows.append(
            {
                "id": entry.id.value,
                "name": entry.name,
                "description": entry.description,
                "icon": entry.icon,
                "order": entry.order,
                "available": is_available,
                "summary": profile.summary if profile else None,
                "indicator_count": len(profile.indicators) if profile else 0,
                "verified_share": profile.verified_share if profile else 0.0,
            }
        )
    return rows


def get_domain(code: str, domain_id: str) -> DomainProfile:
    profiles = _profiles(code)
    profile = profiles.get(domain_id)
    if profile is None:
        entry = catalog_entry(DomainId(domain_id)) if domain_id in {d.value for d in DomainId} else None
        raise KeyError(
            f"Domain '{domain_id}' not available for {code.upper()}"
            + (f" ({entry.name} is on the roadmap)" if entry else "")
        )
    overlay = _overlay_for(code).get(domain_id)
    if overlay:
        try:
            return _apply_overlay(deepcopy(profile), overlay)
        except Exception as exc:
            log.warning(
                "domain overlay skipped",
                extra={"context": {"code": code, "domain": domain_id, "error": str(exc)}},
            )
    return profile
