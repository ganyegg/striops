import Link from "next/link";
import type { Action, ActionRegister } from "@/lib/api";
import { formatZAR } from "@/lib/api";

const STATUS_META: Record<string, { label: string; className: string }> = {
  overdue: {
    label: "Overdue",
    className: "bg-helm-bad/15 text-helm-bad border border-helm-bad/30",
  },
  assigned: {
    label: "Assigned",
    className: "bg-helm-warn/15 text-helm-warn border border-helm-warn/30",
  },
  in_progress: {
    label: "In progress",
    className: "bg-helm-accent/15 text-helm-accent border border-helm-accent/30",
  },
  proposed: {
    label: "Proposed",
    className: "bg-white/5 text-white/55 border border-white/15",
  },
  done: {
    label: "Done",
    className: "bg-helm-good/15 text-helm-good border border-helm-good/30",
  },
};

function sourceHref(a: Action): string | null {
  if (a.source_type === "risk") return `/risks/${encodeURIComponent(a.source_ref)}`;
  if (a.source_type === "win") return `/wins/${encodeURIComponent(a.source_ref)}`;
  return null;
}

function ActionCard({ action }: { action: Action }) {
  const meta = STATUS_META[action.status] ?? STATUS_META.proposed;
  const href = sourceHref(action);
  return (
    <div className="card p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <p className="text-sm font-semibold leading-snug text-white/90">{action.title}</p>
        <span className={`shrink-0 rounded-full px-2.5 py-0.5 text-[11px] font-medium ${meta.className}`}>
          {meta.label}
        </span>
      </div>
      <p className="mt-1.5 text-xs text-white/45">
        {action.department} · {action.owner}
        {action.due_date ? ` · due ${action.due_date}` : ""}
      </p>
      {action.expected_impact_note ? (
        <p className="mt-2 text-sm leading-relaxed text-white/60">{action.expected_impact_note}</p>
      ) : null}
      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
        {action.expected_impact_zar != null ? (
          <span className="rounded-full border border-helm-accent/30 bg-helm-accent/10 px-2.5 py-0.5 text-helm-accent">
            {formatZAR(action.expected_impact_zar)} expected
          </span>
        ) : null}
        {href ? (
          <Link
            href={href}
            className="rounded-full border border-white/15 bg-white/5 px-2.5 py-0.5 text-white/55 hover:border-helm-sky/40 hover:text-helm-sky"
          >
            Source {action.source_type} →
          </Link>
        ) : (
          <span className="text-white/35">Source: {action.source_type}</span>
        )}
      </div>
      {action.outcome ? (
        <p className="mt-2 text-xs text-helm-good/80">Outcome: {action.outcome}</p>
      ) : null}
    </div>
  );
}

export default function ActionTracker({ register }: { register: ActionRegister }) {
  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center gap-3 text-xs">
        <span className="rounded-full border border-white/15 bg-white/5 px-3 py-1 text-white/60">
          {register.open_count} open
        </span>
        {register.overdue_count > 0 ? (
          <span className="rounded-full border border-helm-bad/30 bg-helm-bad/10 px-3 py-1 text-helm-bad">
            {register.overdue_count} overdue
          </span>
        ) : null}
        <span className="rounded-full border border-helm-good/30 bg-helm-good/10 px-3 py-1 text-helm-good">
          {register.done_count} done
        </span>
        {register.total_expected_impact_zar > 0 ? (
          <span className="text-white/45">
            {formatZAR(register.total_expected_impact_zar)} expected impact on open actions
          </span>
        ) : null}
      </div>
      <p className="mb-4 max-w-2xl text-sm text-white/55">{register.note}</p>
      <div className="grid gap-3 md:grid-cols-2">
        {register.actions.map((a) => (
          <ActionCard key={a.id} action={a} />
        ))}
      </div>
    </div>
  );
}
