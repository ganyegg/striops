import Link from "next/link";
import type { Decision, DecisionRegister } from "@/lib/api";

const STATUS_META: Record<string, { label: string; className: string }> = {
  overdue: {
    label: "Overdue",
    className: "bg-helm-bad/15 text-helm-bad border border-helm-bad/30",
  },
  pending: {
    label: "Awaiting decision",
    className: "bg-helm-warn/15 text-helm-warn border border-helm-warn/30",
  },
  in_progress: {
    label: "In progress",
    className: "bg-helm-accent/15 text-helm-accent border border-helm-accent/30",
  },
  decided: {
    label: "Decided",
    className: "bg-helm-good/15 text-helm-good border border-helm-good/30",
  },
};

function DecisionRow({ decision }: { decision: Decision }) {
  const meta = STATUS_META[decision.status] ?? STATUS_META.decided;
  return (
    <div className="card p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold leading-snug text-white/90">{decision.title}</p>
          <p className="mt-1 text-xs text-white/45">
            {decision.owner}
            {decision.date ? ` · ${decision.date}` : ""}
            {decision.review_by ? ` · review by ${decision.review_by}` : ""}
          </p>
        </div>
        <span className={`shrink-0 rounded-full px-2.5 py-0.5 text-[11px] font-medium ${meta.className}`}>
          {meta.label}
        </span>
      </div>
      <p className="mt-2 text-sm leading-relaxed text-white/60">{decision.context}</p>
      {decision.outcome ? (
        <p className="mt-1.5 text-xs text-white/45">Outcome: {decision.outcome}</p>
      ) : null}
      {(decision.linked_risk_id || decision.linked_win_id) && (
        <div className="mt-3 flex flex-wrap gap-2 text-xs">
          {decision.linked_risk_id ? (
            <Link
              href={`/risks/${encodeURIComponent(decision.linked_risk_id)}`}
              className="rounded-full border border-white/15 bg-white/5 px-2.5 py-0.5 text-white/55 transition-colors hover:border-helm-accent/40 hover:text-helm-accent"
            >
              Linked risk →
            </Link>
          ) : null}
          {decision.linked_win_id ? (
            <Link
              href={`/wins/${encodeURIComponent(decision.linked_win_id)}`}
              className="rounded-full border border-white/15 bg-white/5 px-2.5 py-0.5 text-white/55 transition-colors hover:border-helm-good/40 hover:text-helm-good"
            >
              Linked win →
            </Link>
          ) : null}
        </div>
      )}
    </div>
  );
}

export default function DecisionLog({ register }: { register: DecisionRegister }) {
  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center gap-3 text-xs">
        <span className="rounded-full border border-white/15 bg-white/5 px-3 py-1 text-white/60">
          {register.open_count} open
        </span>
        {register.overdue_count > 0 ? (
          <span className="rounded-full border border-helm-bad/30 bg-helm-bad/10 px-3 py-1 text-helm-bad">
            {register.overdue_count} overdue review{register.overdue_count > 1 ? "s" : ""}
          </span>
        ) : null}
        <span className="text-white/40">{register.note}</span>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        {register.decisions.map((d) => (
          <DecisionRow key={d.id} decision={d} />
        ))}
      </div>
    </div>
  );
}
