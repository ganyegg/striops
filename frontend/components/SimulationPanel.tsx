"use client";

import { useState } from "react";
import {
  formatZAR,
  runSimulation,
  type ScenarioOption,
  type SimulationResult,
} from "@/lib/api";

const DIMENSION_LABEL: Record<string, string> = {
  financial: "Financial",
  operational: "Operational",
  citizen: "Citizen",
  environmental: "Environmental",
  political: "Political",
  risk: "Risk",
};

export default function SimulationPanel({
  scenarios,
  compact = false,
}: {
  scenarios: ScenarioOption[];
  compact?: boolean;
}) {
  const modelled = scenarios.filter((s) => s.modelled);
  const [fn, setFn] = useState(modelled[0]?.function_name ?? scenarios[0]?.function_name ?? "");
  const [pct, setPct] = useState(10);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selected = scenarios.find((s) => s.function_name === fn);
  const unspent = selected
    ? Math.max(0, selected.current_budget - selected.current_actual)
    : 0;

  async function onRun() {
    setLoading(true);
    setError(null);
    try {
      setResult(await runSimulation(fn, pct));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Simulation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      className={`card relative flex flex-col overflow-hidden ${compact ? "h-[460px] p-4" : "p-6"}`}
    >
      <div
        className="pointer-events-none absolute -right-8 -top-10 h-32 w-32 rounded-full bg-striops-accent/10 blur-2xl"
        aria-hidden
      />
      <div className="relative flex min-h-0 flex-1 flex-col">
        <p className="text-[11px] uppercase tracking-[0.18em] text-striops-accent/80">What if</p>
        <h3 className="mt-1 font-display text-lg font-semibold text-white">Simulator</h3>
        <p className="mt-1 text-xs leading-snug text-white/45">
          Stress a budget line before the mid-year review does.
        </p>

        {selected ? (
          <p className="mt-3 rounded-lg border border-white/8 bg-ink-950/50 px-3 py-2 text-[11px] text-white/55">
            <span className="text-white/75">{formatZAR(selected.current_budget)}</span> budget ·{" "}
            <span className="text-striops-accent">{formatZAR(selected.current_actual)}</span> spent ·{" "}
            <span className="text-striops-gold">{formatZAR(unspent)}</span> unspent
          </p>
        ) : null}

        <div className={`mt-4 flex flex-col gap-3 ${compact ? "" : "md:flex-row md:items-end"}`}>
          <label className="flex-1">
            <span className="mb-1 block text-[10px] uppercase tracking-wide text-white/40">
              Function
            </span>
            <select
              value={fn}
              onChange={(e) => setFn(e.target.value)}
              className="w-full rounded-lg border border-white/10 bg-ink-800 px-3 py-2 text-sm text-white/90 outline-none focus:border-striops-accent"
            >
              {scenarios.map((s) => (
                <option key={s.function_name} value={s.function_name}>
                  {s.function_name}
                  {s.modelled ? "" : " (unmodelled)"}
                </option>
              ))}
            </select>
          </label>
          <label className="flex-1">
            <span className="mb-1 block text-[10px] uppercase tracking-wide text-white/40">
              Change{" "}
              <span className="text-striops-accent">
                {pct > 0 ? "+" : ""}
                {pct}%
              </span>
            </span>
            <input
              type="range"
              min={-30}
              max={30}
              step={5}
              value={pct}
              onChange={(e) => setPct(Number(e.target.value))}
              className="w-full accent-striops-accent"
            />
          </label>
          <button
            onClick={onRun}
            disabled={loading || !fn}
            className="rounded-lg bg-striops-ocean px-4 py-2.5 text-sm font-semibold text-white shadow-glow transition hover:bg-striops-oceanDeep disabled:opacity-50"
          >
            {loading ? "Simulating…" : "Run Simulation"}
          </button>
        </div>

        {error ? <p className="mt-3 text-sm text-striops-bad">{error}</p> : null}

        {result ? (
          <div className={`mt-4 space-y-3 ${compact ? "min-h-0 flex-1 overflow-y-auto pr-1" : ""}`}>
            <p className="text-sm font-medium text-white/80">{result.question}</p>
            <div className={`grid gap-3 ${compact ? "grid-cols-1" : "md:grid-cols-2"}`}>
              {[result.baseline, result.scenario].map((sc, idx) => (
                <div
                  key={idx}
                  className={`rounded-xl border p-3 ${
                    idx === 1
                      ? "border-striops-accent/40 bg-striops-accent/5"
                      : "border-white/10 bg-white/[0.02]"
                  }`}
                >
                  <p className="text-[10px] uppercase tracking-wide text-white/40">
                    {idx === 0 ? "Baseline" : "Scenario"}
                  </p>
                  <p className="mt-0.5 text-sm font-semibold text-white/90">{sc.name}</p>
                  <div className="mt-2 space-y-1.5">
                    {sc.impacts.slice(0, compact ? 3 : undefined).map((im, i) => (
                      <div key={i} className="text-xs">
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-white/50">
                            {DIMENSION_LABEL[im.dimension] ?? im.dimension}
                          </span>
                          <span className="font-medium text-white/85">{im.delta}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <div className="rounded-xl border border-striops-gold/30 bg-striops-gold/5 p-3">
              <div className="flex items-center justify-between gap-2">
                <p className="text-[10px] uppercase tracking-wide text-striops-gold">Recommendation</p>
                <span className="text-[10px] text-white/45">
                  {Math.round(result.confidence * 100)}%
                </span>
              </div>
              <p className="mt-1 text-sm font-semibold text-white/90">{result.recommended}</p>
              {!compact ? (
                <p className="mt-1 text-sm text-white/60">{result.recommendation_detail}</p>
              ) : null}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
