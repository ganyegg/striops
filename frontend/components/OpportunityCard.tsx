import type { Opportunity } from "@/lib/api";
import { formatZAR, priorityColor } from "@/lib/api";
import ConfidenceBar from "./ConfidenceBar";
import EvidenceList from "./EvidenceList";

export default function OpportunityCard({ opp }: { opp: Opportunity }) {
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-[15px] font-semibold text-white/90">{opp.title}</h3>
        <span className={`pill ${priorityColor(opp.priority)}`}>{opp.priority}</span>
      </div>
      {opp.unit === "ZAR" && opp.value_estimate > 0 ? (
        <div className="mt-2 flex items-center gap-3">
          <span className="text-2xl font-bold tabular-nums text-helm-good">
            {formatZAR(opp.value_estimate)}
          </span>
          <span className="text-[11px] uppercase tracking-wide text-white/40">estimated value</span>
        </div>
      ) : null}
      <p className="mt-2 text-sm leading-relaxed text-white/60">{opp.reason}</p>
      <div className="mt-3 rounded-lg bg-helm-good/5 p-3 text-sm text-white/70">
        <span className="text-[11px] font-medium uppercase tracking-wide text-helm-good">Action</span>
        <p className="mt-0.5">{opp.action}</p>
      </div>
      <div className="mt-3 flex items-center justify-between">
        <span className="text-xs text-white/40">Owner: {opp.owner}</span>
        <ConfidenceBar value={opp.confidence} />
      </div>
      <EvidenceList items={opp.evidence} />
    </div>
  );
}
