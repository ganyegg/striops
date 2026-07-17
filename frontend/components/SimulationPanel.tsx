"use client";

import { useState } from "react";
import {
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

export default function SimulationPanel({ scenarios }: { scenarios: ScenarioOption[] }) {
  const modelled = scenarios.filter((s) => s.modelled);
  const [fn, setFn] = useState(modelled[0]?.function_name ?? scenarios[0]?.function_name ?? "");
  const [pct, setPct] = useState(10);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    <div className="card p-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-end">
        <label className="flex-1">
          <span className="mb-1 block text-xs uppercase tracking-wide text-white/40">Decision</span>
          <select
            value={fn}
            onChange={(e) => setFn(e.target.value)}
            className="w-full rounded-lg border border-white/10 bg-ink-800 px-3 py-2 text-sm text-white/90 outline-none focus:border-helm-accent"
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
          <span className="mb-1 block text-xs uppercase tracking-wide text-white/40">
            Budget change: <span className="text-helm-accent">{pct > 0 ? "+" : ""}{pct}%</span>
          </span>
          <input
            type="range"
            min={-30}
            max={30}
            step={5}
            value={pct}
            onChange={(e) => setPct(Number(e.target.value))}
            className="w-full accent-helm-accent"
          />
        </label>
        <button
          onClick={onRun}
          disabled={loading || !fn}
          className="rounded-lg bg-helm-ocean px-5 py-2.5 text-sm font-semibold text-white shadow-glow transition hover:bg-helm-oceanDeep disabled:opacity-50"
        >
          {loading ? "Simulating…" : "Run Simulation"}
        </button>
      </div>

      {error ? <p className="mt-4 text-sm text-helm-bad">{error}</p> : null}

      {result ? (
        <div className="mt-6 space-y-5">
          <div>
            <p className="text-sm font-medium text-white/80">{result.question}</p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            {[result.baseline, result.scenario].map((sc, idx) => (
              <div
                key={idx}
                className={`rounded-xl border p-4 ${
                  idx === 1 ? "border-helm-accent/40 bg-helm-accent/5" : "border-white/10 bg-white/[0.02]"
                }`}
              >
                <p className="text-xs uppercase tracking-wide text-white/40">
                  {idx === 0 ? "Baseline" : "Scenario"}
                </p>
                <p className="mt-0.5 text-sm font-semibold text-white/90">{sc.name}</p>
                <p className="mt-1 text-xs text-white/50">{sc.description}</p>
                <div className="mt-3 space-y-2">
                  {sc.impacts.map((im, i) => (
                    <div key={i} className="text-xs">
                      <div className="flex items-center justify-between">
                        <span className="text-white/50">{DIMENSION_LABEL[im.dimension] ?? im.dimension}</span>
                        <span className="font-medium text-white/85">{im.delta}</span>
                      </div>
                      <p className="text-white/40">{im.detail}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="rounded-xl border border-helm-gold/30 bg-helm-gold/5 p-4">
            <div className="flex items-center justify-between">
              <p className="text-xs uppercase tracking-wide text-helm-gold">Recommendation</p>
              <span className="text-xs text-white/50">
                Confidence {Math.round(result.confidence * 100)}%
              </span>
            </div>
            <p className="mt-1 text-sm font-semibold text-white/90">{result.recommended}</p>
            <p className="mt-1 text-sm text-white/60">{result.recommendation_detail}</p>
            {result.alternatives?.length ? (
              <ul className="mt-3 list-disc space-y-1 pl-5 text-xs text-white/50">
                {result.alternatives.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}
