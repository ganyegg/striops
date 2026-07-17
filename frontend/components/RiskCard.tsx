import type { Risk } from "@/lib/api";
import { priorityColor } from "@/lib/api";
import ConfidenceBar from "./ConfidenceBar";
import EvidenceList from "./EvidenceList";

export default function RiskCard({ risk }: { risk: Risk }) {
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-[15px] font-semibold text-white/90">{risk.title}</h3>
        <span className={`pill ${priorityColor(risk.priority)}`}>{risk.priority}</span>
      </div>
      <div className="mt-2 flex items-center gap-3">
        <span className="text-2xl font-bold tabular-nums text-helm-bad">{risk.score}</span>
        <span className="text-[11px] uppercase tracking-wide text-white/40">risk score</span>
      </div>
      <p className="mt-2 text-sm leading-relaxed text-white/60">{risk.reason}</p>
      <div className="mt-3 rounded-lg bg-helm-accent/5 p-3 text-sm text-white/70">
        <span className="text-[11px] font-medium uppercase tracking-wide text-helm-accent">Mitigation</span>
        <p className="mt-0.5">{risk.mitigation}</p>
      </div>
      <div className="mt-3 flex items-center justify-between">
        <span className="text-xs text-white/40">Owner: {risk.owner}</span>
        <ConfidenceBar value={risk.confidence} />
      </div>
      <EvidenceList items={risk.evidence} />
    </div>
  );
}
