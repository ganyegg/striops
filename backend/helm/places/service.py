"""Place dossiers — let Ask Helm resolve area names to related facts + gaps."""
from __future__ import annotations

import json
from functools import lru_cache

from pydantic import BaseModel, Field

from helm.core.paths import seed_dir
from helm.wins import list_initiatives


class PlaceDossier(BaseModel):
    id: str
    name: str
    region: str | None = None
    summary: str
    population_estimate: float | None = None
    population_unit: str = "residents"
    population_confidence: float = 0.0
    population_note: str | None = None
    themes: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    related_win_ids: list[str] = Field(default_factory=list)
    related_domain_ids: list[str] = Field(default_factory=list)
    related_sector_ids: list[str] = Field(default_factory=list)
    ask_prompt: str | None = None
    matched_alias: str | None = None


@lru_cache
def _load(municipality: str) -> list[dict]:
    path = seed_dir() / "places" / f"{municipality.upper()}.json"
    if not path.exists():
        return []
    return json.loads(path.read_text()).get("places", [])


def clear_places_cache() -> None:
    _load.cache_clear()


def detect_places(question: str, municipality: str = "CPT") -> list[PlaceDossier]:
    q = question.lower().strip()
    hits: list[PlaceDossier] = []
    for raw in _load(municipality):
        aliases = [a.lower() for a in raw.get("aliases", [])] + [raw["name"].lower()]
        matched = next((a for a in aliases if a and a in q), None)
        if not matched:
            continue
        hits.append(
            PlaceDossier(
                id=raw["id"],
                name=raw["name"],
                region=raw.get("region"),
                summary=raw.get("summary", ""),
                population_estimate=raw.get("population_estimate"),
                population_unit=raw.get("population_unit", "residents"),
                population_confidence=float(raw.get("population_confidence") or 0),
                population_note=raw.get("population_note"),
                themes=raw.get("themes") or [],
                gaps=raw.get("gaps") or [],
                related_win_ids=raw.get("related_win_ids") or [],
                related_domain_ids=raw.get("related_domain_ids") or [],
                related_sector_ids=raw.get("related_sector_ids") or [],
                ask_prompt=raw.get("ask_prompt"),
                matched_alias=matched,
            )
        )
    # Prefer more specific places over parent regions when both match
    hits.sort(key=lambda p: (0 if p.id != "cape-flats" else 1, -len(p.matched_alias or "")))
    return hits


def place_related_evidence(place: PlaceDossier, municipality: str = "CPT") -> dict:
    """Pull wins / text hits that mention the place — still grounded, no invention."""
    wins = list_initiatives(municipality)
    related_wins = []
    for w in wins:
        blob = " ".join(
            [
                w.title,
                w.headline,
                w.plain_language,
                w.why_it_matters,
                " ".join(e.value for e in (w.evidence or []) if getattr(e, "value", None)),
            ]
        ).lower()
        name_hit = place.name.lower() in blob or any(a in blob for a in (place.matched_alias or "",))
        id_hit = w.id in place.related_win_ids
        if name_hit or id_hit:
            dated = [
                f"{m.label}: {m.value} ({m.as_of})"
                for m in (w.metrics or [])[:4]
            ]
            evidence_bits = [
                f"{e.label}: {e.value}" + (f" — {e.source}" if getattr(e, "source", None) else "")
                for e in (w.evidence or [])[:2]
            ]
            related_wins.append(
                {
                    "id": w.id,
                    "title": w.title,
                    "headline": w.headline,
                    "href": f"/wins/{w.id}",
                    "status": w.status,
                    "plain_language": w.plain_language,
                    "dated_metrics": dated,
                    "evidence": evidence_bits,
                }
            )
    return {
        "place": place.model_dump(),
        "related_wins": related_wins,
        "domain_hrefs": [f"/{municipality}/domains/{d}" for d in place.related_domain_ids],
        "geo_grain_note": (
            f"Helm has a place dossier for {place.name}, plus metro facts that name it. "
            "It does not yet have Khayelitsha-only monthly metric series — "
            "summaries must say what is place-named vs metro-wide."
        ),
    }
