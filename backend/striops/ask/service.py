"""Ask Striops — grounded natural-language answers over retrieved facts."""
from __future__ import annotations

import json
import re
from typing import Literal

from pydantic import BaseModel, Field

from striops.comparatives import build_comparatives
from striops.core.config import Settings, get_settings
from striops.core.logging import get_logger
from striops.executive_brief import build_executive_brief
from striops.health_score import build_health_breakdown
from striops.persistence import get_repository
from striops.places import detect_places, place_related_evidence
from striops.pulse import build_city_pulse
from striops.reasoning import get_llm
from striops.reasoning.llm import GeminiError
from striops.sectors import build_sectors_report

log = get_logger("striops.ask")


class AskCitation(BaseModel):
    label: str
    href: str


class DataGap(BaseModel):
    sector_id: str
    sector_name: str
    blocker: str
    ask_prompt: str


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    mode: Literal["answer", "report"] = "answer"


class AskResponse(BaseModel):
    question: str
    mode: str
    answer: str
    report_markdown: str | None = None
    citations: list[AskCitation] = Field(default_factory=list)
    used_facts: list[str] = Field(default_factory=list)
    data_gaps: list[DataGap] = Field(default_factory=list)
    ai_role: str = (
        "Narrator over retrieved Striops facts — engines own the numbers; "
        "AI does not invent metrics. Missing data is stated as a gap, not filled in."
    )
    model: str
    narrator: str = "gemini"  # gemini | deterministic
    dynamic_note: str = (
        "Striops surfaces whatever is in the facts store after each ingest/refresh. "
        "New series, domains, or feeds appear automatically once loaded — "
        "use Refresh now to pull the latest."
    )


_SECTOR_KEYWORDS = {
    "health": ["health", "clinic", "hospital", "ems", "ambulance", "phc"],
    "water": ["water", "dam", "nrw", "sanitation", "leak"],
    "safety": ["safety", "crime", "leap", "police", "murder"],
    "housing": ["housing", "backlog", "informal", "settlement"],
    "energy": ["energy", "electricity", "load-shedding", "loadshedding", "eskom"],
    "transport": ["road", "transport", "myciti", "mobility", "pothole"],
    "waste": ["waste", "refuse", "dumping", "collection"],
    "fiscal": ["budget", "fiscal", "afford", "underspend", "treasury"],
    "libraries": ["library", "libraries"],
}


def _matching_gaps(question: str, gaps: list[DataGap]) -> list[DataGap]:
    q = question.lower()
    hit: list[DataGap] = []
    for g in gaps:
        keys = _SECTOR_KEYWORDS.get(g.sector_id, [g.sector_id])
        if any(k in q for k in keys):
            hit.append(g)
    return hit


def _retrieve_context(
    question: str,
    municipality: str = "CPT",
) -> tuple[str, list[AskCitation], list[str], list[DataGap]]:
    brief = build_executive_brief()
    breakdown = build_health_breakdown(municipality)
    pulse = build_city_pulse()
    comps = build_comparatives(municipality=municipality)
    sectors = build_sectors_report(municipality)
    repo = get_repository()
    places = detect_places(question, municipality)
    place_packs = [place_related_evidence(p, municipality) for p in places]

    citations: list[AskCitation] = [
        AskCitation(label="Strategic health breakdown", href="/health"),
        AskCitation(label="Critical sectors", href="/#sectors"),
        AskCitation(label="City pulse", href="/#pulse"),
        AskCitation(label="Compare trends", href="/compare"),
        AskCitation(label="Ask Striops", href="/ask"),
    ]
    facts: list[str] = [
        f"health_score={breakdown.health_score}",
        f"risk_penalty={breakdown.risk_penalty_capped}",
        f"opportunity_bonus={breakdown.opportunity_bonus_capped}",
        f"data_through={pulse.data_through}",
        f"p0_sectors_ready={sectors.p0_ready_count}/{sectors.p0_total}",
        f"places_detected={[p.name for p in places]}",
    ]

    gaps: list[DataGap] = []
    for s in sectors.sectors:
        facts.append(
            f"sector:{s.id}:priority={s.priority}:status={s.status}:"
            f"ops={s.ops_series_count}:domain={s.domain_available}:blocker={s.blocker or 'none'}"
        )
        if s.affected:
            facts.append(
                f"affected:{s.id}:estimate={s.affected.population_estimate} "
                f"{s.affected.unit} @ {s.affected.geography} (conf {s.affected.confidence})"
            )
            for g in s.affected.gaps[:3]:
                facts.append(f"gap:{s.id}:{g}")
        if s.blocker and s.priority in ("P0", "P1"):
            gaps.append(
                DataGap(
                    sector_id=s.id,
                    sector_name=s.name,
                    blocker=s.blocker,
                    ask_prompt=s.ask_prompt,
                )
            )
        if s.domain_id and s.domain_available:
            citations.append(AskCitation(label=s.name, href=s.href))

    # Place dossiers — related wins + geo gaps
    for pack in place_packs:
        place = pack["place"]
        facts.append(f"place:{place['id']}:{place['name']}:region={place.get('region')}")
        facts.append(f"place_summary:{place['summary'][:240]}")
        for theme in place.get("themes", [])[:6]:
            facts.append(f"place_theme:{place['id']}:{theme}")
        for g in place.get("gaps", []):
            facts.append(f"place_gap:{place['id']}:{g}")
            gaps.append(
                DataGap(
                    sector_id=f"place:{place['id']}",
                    sector_name=place["name"],
                    blocker=g,
                    ask_prompt=place.get("ask_prompt") or f"What does Striops know about {place['name']}?",
                )
            )
        for w in pack.get("related_wins", []):
            dated = "; ".join(w.get("dated_metrics") or [])
            facts.append(
                f"place_win:{w['id']}:{w['title']}:{w['headline']}"
                + (f"|{dated}" if dated else "")
            )
            citations.append(AskCitation(label=w["title"], href=w["href"]))
        for href in pack.get("domain_hrefs", []):
            citations.append(AskCitation(label=href.split("/")[-1], href=href))

        # Pull sector snapshots linked to the place
        for sid in place.get("related_sector_ids", []):
            sec = next((s for s in sectors.sectors if s.id == sid), None)
            if sec:
                facts.append(
                    f"place_sector:{place['id']}:{sec.id}:status={sec.status}:headline={sec.headline}"
                )

    for r in brief.top_risks[:5]:
        citations.append(AskCitation(label=f"Risk: {r.title}", href=f"/risks/{r.id}"))
        facts.append(f"risk:{r.id}:score={r.score}:priority={r.priority.value}")
        if r.affected:
            facts.append(
                f"risk_affected:{r.id}:{r.affected.population_estimate} {r.affected.unit} "
                f"({r.affected.geography})"
            )
    for o in brief.top_opportunities[:4]:
        facts.append(f"opportunity:{o.id}:value={o.value_estimate}")
    for item in pulse.items[:10]:
        facts.append(
            f"pulse:{item.metric}:{item.direction}:"
            f"{item.latest}@{item.latest_period}->{item.previous}@{item.previous_period} "
            f"({item.change_pct}%)"
        )
        citations.append(AskCitation(label=item.label, href=item.href))
    for pack in comps.packs:
        facts.append(f"comparative:{pack.id}")
        if pack.ratio:
            facts.append(f"ratio:{pack.ratio.key}={pack.ratio.value} {pack.ratio.unit}")

    metrics_summary = []
    for s in repo.metric_series():
        vals = s.values()
        pts = sorted(s.points, key=lambda p: p.period)
        if vals and pts:
            last = pts[-1]
            period = last.period.isoformat() if hasattr(last.period, "isoformat") else str(last.period)[:10]
            metrics_summary.append(
                f"{s.entity_id}/{s.metric}={vals[-1]} {s.unit or ''} @ {period}".strip()
            )
    facts.extend(metrics_summary[:20])

    context = {
        "question": question,
        "as_of": {
            "ops_data_through": pulse.data_through,
            "ops_previous_period": pulse.previous_period,
            "period_note": pulse.period_note,
            "comparatives_through": comps.data_through,
        },
        "strategic_summary": brief.strategic_summary,
        "health_narrative": brief.health_narrative,
        "health_breakdown": breakdown.model_dump(),
        "places": place_packs,
        "place_protocol": (
            "If places[] is non-empty, lead with a place briefing: what Striops can evidence "
            "(named wins/themes with dates), which linked metro sectors are worsening, and explicit "
            "place_gap lines. Never say 'no information' when a place dossier exists. "
            "Distinguish place-named facts from metro-wide series. Do not invent ward KPIs."
        ),
        "format_protocol": (
            "Respond in compact markdown with REAL line breaks (use \\n). "
            "Never put the whole answer on one line. Never put body text on the same line as ### headings. "
            "Never put multiple bullets on one line. "
            "Include concrete dates/timelines (FY, MTREF, month labels from as_of / pulse / dated_metrics). "
            "Never say 'recently' or 'last period' without naming the period. "
            "Exact shape (copy this spacing):\n"
            "### Snapshot\n"
            "One or two short sentences.\n"
            "\n"
            "### Evidence\n"
            "- **Topic**: fact with date\n"
            "- **Topic**: fact with date\n"
            "\n"
            "### Watch (metro-wide through <month year>)\n"
            "- **Topic**: trend with Jan → Feb figures\n"
            "\n"
            "### Gaps\n"
            "- missing fact\n"
            "Answer mode: max ~160 words / ~10 bullets. Report mode: same sections, max ~350 words."
        ),
        "critical_sectors": [s.model_dump() for s in sectors.sectors],
        "data_gaps": [g.model_dump() for g in gaps],
        "gap_protocol": (
            "If the question needs a sector with blocker/unknown status, say clearly that "
            "the facts store does not have it yet, quote the blocker, and do NOT invent numbers. "
            "Hospitals are provincial (Western Cape DoH), not City-owned."
        ),
        "top_risks": [
            {
                "id": r.id,
                "title": r.title,
                "score": r.score,
                "mitigation": r.mitigation,
                "affected": r.affected.model_dump() if r.affected else None,
            }
            for r in brief.top_risks
        ],
        "top_opportunities": [
            {"id": o.id, "title": o.title, "value_estimate": o.value_estimate, "action": o.action}
            for o in brief.top_opportunities
        ],
        "recommended_decisions": [
            {"id": r.id, "title": r.title, "rationale": r.rationale} for r in brief.recommended_decisions[:5]
        ],
        "pulse": [
            {
                "label": i.label,
                "sentence": i.sentence,
                "direction": i.direction,
                "latest": i.latest,
                "previous": i.previous,
                "latest_period": i.latest_period,
                "previous_period": i.previous_period,
                "change_pct": i.change_pct,
            }
            for i in pulse.items
        ],
        "comparatives": [
            {
                "id": p.id,
                "title": p.title,
                "why": p.why_it_matters,
                "decision": p.decision_anchor,
                "ratio": p.ratio.model_dump() if p.ratio else None,
            }
            for p in comps.packs
        ],
        "metrics_latest": metrics_summary,
    }
    return json.dumps(context, indent=2, default=str), citations, facts, gaps


def _mock_place_brief(ctx: dict) -> str:
    as_of = ctx.get("as_of") or {}
    through = as_of.get("ops_data_through") or "latest ops month"
    prev = as_of.get("ops_previous_period")
    sections: list[str] = []

    for pack in ctx.get("places") or []:
        place = pack.get("place") or {}
        name = place.get("name", "This area")
        bits: list[str] = [f"### Snapshot — {name}"]
        pop = place.get("population_estimate")
        if pop is not None:
            bits.append(
                f"**{name}** (~{pop:,.0f} {place.get('population_unit', 'residents')}, "
                f"order-of-magnitude; conf {place.get('population_confidence', 0)}). "
                f"{place.get('region') or 'Cape Town'} growth edge."
            )
        else:
            bits.append(f"**{name}** — {place.get('summary', '')[:160]}")

        bits.append("### Evidence (dated)")
        wins = pack.get("related_wins") or []
        if wins:
            for w in wins[:3]:
                dated = w.get("dated_metrics") or []
                if dated:
                    metric_line = "; ".join(dated[:2])
                    bits.append(f"- **{w['title']}** — {metric_line}")
                else:
                    bits.append(f"- **{w['title']}** — {w.get('headline', '')}")
        for theme in (place.get("themes") or [])[:3]:
            if not any(theme.split("—")[0].strip().lower() in (w.get("title") or "").lower() for w in wins):
                bits.append(f"- {theme}")

        bits.append(f"### Watch (metro-wide through {through})")
        worsen = [p for p in ctx.get("pulse") or [] if p.get("direction") == "worsening"][:3]
        if worsen:
            for p in worsen:
                lp = p.get("latest_period") or through
                pp = p.get("previous_period") or prev or "prior month"
                bits.append(
                    f"- {p.get('label')}: {p.get('latest')} ({lp}) vs {p.get('previous')} ({pp}) — "
                    f"{p.get('direction')}"
                )
        else:
            bits.append("- No worsening pulse items in the current store.")
        bits.append("_These series are metro totals — not yet split to this place._")

        gaps = place.get("gaps") or []
        if gaps:
            bits.append("### Gaps")
            for g in gaps[:3]:
                bits.append(f"- {g}")

        sections.append("\n".join(bits))
    return "\n\n".join(sections)


def _mock_answer(question: str, context_json: str, mode: str, gaps: list[DataGap]) -> tuple[str, str | None]:
    ctx = json.loads(context_json)
    health = ctx.get("health_breakdown", {})
    risks = ctx.get("top_risks", [])
    pulse = ctx.get("pulse", [])
    comps = ctx.get("comparatives", [])
    sectors = ctx.get("critical_sectors", [])
    as_of = ctx.get("as_of") or {}
    through = as_of.get("ops_data_through") or "latest ops month"
    q = question.lower()

    matched_gaps = _matching_gaps(question, gaps)

    if ctx.get("places"):
        answer = _mock_place_brief(ctx)
    else:
        lines: list[str] = ["### Snapshot"]
        if matched_gaps and any(
            s.get("id") == g.sector_id and s.get("ops_series_count", 0) == 0 and s.get("status") == "unknown"
            for g in matched_gaps
            for s in sectors
            if not str(g.sector_id).startswith("place:")
        ):
            g = matched_gaps[0]
            lines.append(f"**Gap:** {g.sector_name} — {g.blocker}")
        lines.append(
            f"Strategic health **{health.get('health_score')}/100** "
            f"(penalty {health.get('risk_penalty_capped')}, bonus {health.get('opportunity_bonus_capped')}). "
            f"Ops through **{through}**."
        )

        lines.append("### Evidence")
        if "hospital" in q:
            lines.append(
                "- Acute hospitals are Western Cape DoH (not City-owned). "
                "City Health in Striops = clinics + EMS. Hospital occupancy = provincial extract gap."
            )
        if "clinic" in q or "ems" in q or ("health" in q and "strategic" not in q and "hospital" not in q):
            health_pack = next((p for p in comps if p.get("id") == "health_access"), None)
            if health_pack:
                lines.append(f"- Health access — {health_pack.get('why')}")
                lines.append(f"- Decision: {health_pack.get('decision')}")
        if "dam" in q or "water" in q or "nrw" in q:
            water = next((p for p in comps if p.get("id") == "water_stress"), None)
            if water and water.get("ratio"):
                r = water["ratio"]
                lines.append(f"- Water — **{r['label']}**: {r['value']} {r['unit']} ({through})")
                lines.append(f"- {r['interpretation']}")
        if "library" in q:
            lines.append("- Libraries are P3 in Striops — brief Health, Water, Safety, Housing first.")
        if risks:
            top = risks[0]
            lines.append(f"- Top risk: **{top['title']}** (score {top['score']})")
        worsen = [p for p in pulse if p.get("direction") == "worsening"][:3]
        if worsen:
            lines.append(f"### Watch ({through})")
            for p in worsen:
                lines.append(
                    f"- {p.get('label')}: {p.get('latest')} ({p.get('latest_period')}) vs "
                    f"{p.get('previous')} ({p.get('previous_period')})"
                )
        if matched_gaps:
            lines.append("### Gaps")
            for g in matched_gaps[:3]:
                lines.append(f"- {g.sector_name}: {g.blocker}")
        answer = "\n".join(lines)

    report = None
    if mode == "report":
        report = "\n".join(
            [
                "## Striops briefing note",
                "",
                f"**Question:** {question}",
                f"**Ops through:** {through}",
                "",
                answer,
                "",
                "_Place-named facts vs metro series distinguished; ward KPIs not invented._",
            ]
        )
    return answer, report


_FORMAT_SYSTEM = (
    "You are Striops, the City of Cape Town strategic intelligence OS. "
    "Answer ONLY using the JSON context. Follow place_protocol, gap_protocol, and format_protocol. "
    "Never claim there is no information about a place that has a dossier. "
    "Distinguish place-named evidence from metro-wide series. "
    "Never invent ward-level or hospital numbers. "
    "Be brief, specific, and mayor-ready — dates and figures over adjectives. "
    "CRITICAL: output valid multi-line markdown. Each ### heading on its own line; "
    "each bullet (- ) on its own line; blank line between sections."
)

_SECTION_NAMES = (
    r"Snapshot",
    r"Evidence(?:\s*\([^)]*\))?",
    r"Watch(?:\s*\([^)]*\))?",
    r"Gaps",
)


def normalize_answer_markdown(text: str) -> str:
    """Repair smashed Gemini markdown so headings/bullets are scannable."""
    t = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not t:
        return t

    # Insert breaks before headings even when jammed mid-line
    t = re.sub(r"\s*(###\s+)", r"\n\n\1", t)
    # Bullets jammed after text or after another bullet
    t = re.sub(r"\s+([*•]\s+\*\*)", r"\n- **", t)
    t = re.sub(r"\s+(-\s+\*\*)", r"\n- **", t)
    t = re.sub(r"(?<!\n)\s+([*•]\s+)", r"\n- ", t)
    t = re.sub(r"(?<!\n)\s+(-\s+)(?!\*)", r"\n- ", t)
    t = t.lstrip()

    # "### Snapshot Khayelitsha…" → heading on its own line
    for name in _SECTION_NAMES:
        t = re.sub(
            rf"(###\s+{name})\s+(?=[A-Za-z0-9*•\-])",
            r"\1\n\n",
            t,
            flags=re.IGNORECASE,
        )

    # Normalise bullet markers
    t = re.sub(r"(?m)^[*•]\s+", "- ", t)

    # Collapse 3+ blank lines
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip() + "\n"


def ask_striops(req: AskRequest, settings: Settings | None = None) -> AskResponse:
    settings = settings or get_settings()
    llm = get_llm(settings)
    context_json, citations, facts, gaps = _retrieve_context(req.question, settings.striops_municipality)

    place_gaps = [g for g in gaps if str(g.sector_id).startswith("place:")]
    relevant_gaps = place_gaps or _matching_gaps(req.question, gaps) or gaps[:3]

    if req.mode == "report":
        prompt = (
            f"Write a short executive briefing in multi-line markdown answering:\n{req.question}\n\n"
            f"Context JSON:\n{context_json}\n\n"
            "Follow format_protocol exactly (newlines required). "
            "Sections: Snapshot → Evidence → Watch → Gaps. Max ~350 words."
        )
    else:
        prompt = (
            f"Answer this leadership question in multi-line markdown:\n{req.question}\n\n"
            f"Context JSON:\n{context_json}\n\n"
            "Follow format_protocol exactly. Put each ### heading and each - bullet on its own line. "
            "Max ~160 words / ~10 bullets. Every number needs a date/FY/period from context."
        )

    report_md = None
    narrator = "deterministic"
    model_label = getattr(llm, "_model_name", None) or llm.name

    if llm.name == "mock":
        answer, report_md = _mock_answer(req.question, context_json, req.mode, gaps)
        model_label = "deterministic (engines + retrieved facts)"
    else:
        try:
            text = llm.generate(prompt, system=_FORMAT_SYSTEM, temperature=0.1)
            # Guard against any provider that still emits the old mock sentinel.
            if not text or text.lstrip().startswith("[mock:"):
                raise GeminiError("unusable Gemini response")
            if req.mode == "report":
                report_md = normalize_answer_markdown(text)
                parts = re.split(r"\n(?=### )", report_md.strip())
                answer = parts[0][:700] if parts else report_md[:700]
                if len(parts) > 1 and "### Evidence" in report_md:
                    answer = "\n\n".join(parts[:2])[:900]
            else:
                answer = text.strip()
            narrator = "gemini"
        except Exception as exc:
            log.warning(
                "gemini ask failed; using grounded deterministic answer",
                extra={"context": {"error": str(exc)}},
            )
            answer, report_md = _mock_answer(req.question, context_json, req.mode, gaps)
            model_label = f"{model_label} · deterministic fallback"
            narrator = "deterministic"

    answer = normalize_answer_markdown(answer)
    if report_md:
        report_md = normalize_answer_markdown(report_md)

    seen: set[str] = set()
    uniq: list[AskCitation] = []
    for c in citations:
        if c.href in seen:
            continue
        seen.add(c.href)
        uniq.append(c)

    return AskResponse(
        question=req.question,
        mode=req.mode,
        answer=answer,
        report_markdown=report_md,
        citations=uniq[:16],
        used_facts=facts[:60],
        data_gaps=relevant_gaps,
        model=model_label,
        narrator=narrator,
    )
