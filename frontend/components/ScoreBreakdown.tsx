import type { ScoreBreakdown as Breakdown } from "@/lib/api";

export default function ScoreBreakdownPanel({ breakdown }: { breakdown: Breakdown }) {
  const rows = [
    { label: "Likelihood", value: breakdown.likelihood },
    { label: "Impact", value: breakdown.impact },
    { label: "Trend", value: breakdown.trend },
    { label: "Confidence", value: breakdown.confidence },
  ];
  return (
    <div className="card p-5">
      <p className="text-xs uppercase tracking-[0.2em] text-white/40">Score breakdown</p>
      <p className="mt-1 text-3xl font-bold tabular-nums text-striops-bad">{breakdown.score}</p>
      <p className="mt-1 text-[11px] text-white/35">{breakdown.formula}</p>
      <div className="mt-4 space-y-3">
        {rows.map((r) => (
          <div key={r.label}>
            <div className="mb-1 flex justify-between text-xs">
              <span className="text-white/50">{r.label}</span>
              <span className="tabular-nums text-white/80">{r.value.toFixed(2)}</span>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-white/10">
              <div
                className="h-full rounded-full bg-striops-accent"
                style={{ width: `${Math.min(100, r.value * (r.label === "Trend" ? 50 : 100))}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
