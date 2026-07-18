import Link from "next/link";
import type { GlossaryEntry, Risk } from "@/lib/api";
import { formatZAR, priorityColor } from "@/lib/api";
import ConfidenceBar from "./ConfidenceBar";
import EvidenceList from "./EvidenceList";

export default function RiskCard({
  risk,
  glossary,
}: {
  risk: Risk;
  glossary?: GlossaryEntry | null;
}) {
  return (
    <Link
      href={`/risks/${encodeURIComponent(risk.id)}`}
      className="card-risk block p-5 transition hover:border-striops-bad/40 hover:shadow-glow"
    >
      <div className="flex items-start justify-between gap-3">
        <h3 className="font-display text-[17px] font-semibold text-white">{risk.title}</h3>
        <span className={`pill ${priorityColor(risk.priority)}`}>{risk.priority}</span>
      </div>
      {glossary ? (
        <p className="mt-2 rounded-lg border border-white/10 bg-ink-950/40 px-3 py-2 text-xs leading-relaxed text-striops-sand/80">
          <span className="font-semibold text-striops-sky">{glossary.term}: </span>
          {glossary.in_one_line}
        </p>
      ) : null}
      <div className="mt-3 flex items-center gap-3">
        <span className="font-display text-3xl font-bold tabular-nums text-striops-bad">{risk.score}</span>
        <span className="text-[11px] uppercase tracking-wide text-white/40">risk score</span>
        <span className="ml-auto text-[11px] text-striops-accent">Open report →</span>
      </div>
      <p className="mt-2 text-sm leading-relaxed text-white/65">{risk.reason}</p>
      {risk.cost_estimate ? (
        <div className="mt-3 rounded-lg border border-striops-bad/20 bg-striops-bad/10 px-3 py-2">
          <p className="text-[11px] font-medium uppercase tracking-wide text-striops-bad">
            Estimated annual cost
          </p>
          <p className="mt-0.5 font-display text-xl font-semibold text-striops-bad">
            {formatZAR(risk.cost_estimate.amount_zar)}
            <span className="ml-2 font-sans text-xs font-normal text-white/45">
              {risk.cost_estimate.unit_note}
            </span>
          </p>
        </div>
      ) : null}
      {risk.affected ? (
        <div className="mt-3 rounded-lg border border-striops-sky/20 bg-striops-sky/5 px-3 py-2">
          <p className="text-[11px] font-medium uppercase tracking-wide text-striops-sky">Who is affected</p>
          {risk.affected.population_estimate != null ? (
            <p className="mt-0.5 font-display text-lg font-semibold text-white">
              ~{risk.affected.population_estimate.toLocaleString("en-ZA")}{" "}
              <span className="font-sans text-xs font-normal text-white/45">{risk.affected.unit}</span>
            </p>
          ) : (
            <p className="mt-0.5 text-xs text-white/50">Denominator pending — see gaps</p>
          )}
          <p className="mt-0.5 text-[11px] text-white/45">{risk.affected.geography}</p>
          {risk.affected.gaps?.[0] ? (
            <p className="mt-1 text-[10px] text-white/35">Gap: {risk.affected.gaps[0]}</p>
          ) : null}
        </div>
      ) : null}
      <div className="mt-3 rounded-lg bg-striops-accent/10 p-3 text-sm text-white/75">
        <span className="text-[11px] font-medium uppercase tracking-wide text-striops-accent">
          Mitigation
        </span>
        <p className="mt-0.5">{risk.mitigation}</p>
      </div>
      <div className="mt-3 flex items-center justify-between">
        <span className="text-xs text-white/40">Owner: {risk.owner}</span>
        <ConfidenceBar value={risk.confidence} />
      </div>
      <EvidenceList items={risk.evidence} />
    </Link>
  );
}
