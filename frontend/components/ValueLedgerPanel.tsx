import type { ValueLedger } from "@/lib/api";
import { formatZAR } from "@/lib/api";

const BASIS_META: Record<string, { label: string; className: string }> = {
  realised: {
    label: "Realised",
    className: "bg-striops-good/15 text-striops-good border border-striops-good/30",
  },
  projected: {
    label: "Projected",
    className: "bg-striops-accent/15 text-striops-accent border border-striops-accent/30",
  },
  avoided_cost: {
    label: "Avoided cost",
    className: "bg-striops-sky/15 text-striops-sky border border-striops-sky/30",
  },
};

export default function ValueLedgerPanel({ ledger }: { ledger: ValueLedger }) {
  return (
    <div>
      <div className="mb-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card border-striops-accent/30 p-4">
          <p className="text-[11px] uppercase tracking-[0.16em] text-white/40">Attributed total</p>
          <p className="mt-1 font-display text-3xl font-semibold text-striops-accent">
            {formatZAR(ledger.cumulative_attributed_zar)}
          </p>
        </div>
        <div className="card p-4">
          <p className="text-[11px] uppercase tracking-[0.16em] text-white/40">Projected</p>
          <p className="mt-1 font-display text-2xl font-semibold text-white/85">
            {formatZAR(ledger.cumulative_projected_zar)}
          </p>
        </div>
        <div className="card p-4">
          <p className="text-[11px] uppercase tracking-[0.16em] text-white/40">Avoided cost</p>
          <p className="mt-1 font-display text-2xl font-semibold text-striops-sky">
            {formatZAR(ledger.cumulative_avoided_zar)}
          </p>
        </div>
        <div className="card p-4">
          <p className="text-[11px] uppercase tracking-[0.16em] text-white/40">Realised</p>
          <p className="mt-1 font-display text-2xl font-semibold text-striops-good">
            {formatZAR(ledger.cumulative_realised_zar)}
          </p>
        </div>
      </div>
      <p className="mb-4 max-w-2xl text-sm text-white/55">{ledger.note}</p>
      <ol className="space-y-3">
        {ledger.entries.map((e) => {
          const meta = BASIS_META[e.value_basis] ?? BASIS_META.projected;
          return (
            <li key={e.id} className="card p-4">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <p className="text-xs text-white/40">{e.surfaced_at}</p>
                  <p className="mt-1 text-sm font-semibold text-white/90">{e.insight}</p>
                </div>
                <div className="text-right">
                  <p className="font-display text-xl font-semibold text-striops-accent">
                    {formatZAR(e.value_zar)}
                  </p>
                  <span className={`mt-1 inline-block rounded-full px-2.5 py-0.5 text-[11px] ${meta.className}`}>
                    {meta.label}
                  </span>
                </div>
              </div>
              <p className="mt-2 text-sm text-white/60">{e.outcome}</p>
              {e.note ? <p className="mt-1.5 text-xs text-white/40">{e.note}</p> : null}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
