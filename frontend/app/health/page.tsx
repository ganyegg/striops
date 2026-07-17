import Link from "next/link";
import HealthGauge from "@/components/HealthGauge";
import OpportunityCard from "@/components/OpportunityCard";
import PageChrome from "@/components/PageChrome";
import RiskCard from "@/components/RiskCard";
import {
  formatZAR,
  getBrief,
  getGlossary,
  getHealthBreakdown,
  glossaryForRisk,
} from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function HealthPage() {
  let brief;
  let glossary;
  let breakdown;
  try {
    [brief, glossary, breakdown] = await Promise.all([
      getBrief(),
      getGlossary(),
      getHealthBreakdown(),
    ]);
  } catch (e) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-24">
        <Link href="/" className="text-sm text-helm-accent hover:underline">
          ← Back to briefing
        </Link>
        <h1 className="mt-6 font-display text-2xl font-semibold text-white">Health report unavailable</h1>
        <p className="mt-3 text-white/60">{e instanceof Error ? e.message : String(e)}</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-5xl px-6 py-10 pb-24">
      <PageChrome
        backHref="/#command"
        crumbs={
          <>
            <Link href="/" className="font-display font-semibold text-white/80 hover:text-white">
              Helm
            </Link>
            <span className="text-white/25">/</span>
            <span className="text-white/80">Strategic health</span>
          </>
        }
      />

      <div className="mt-8 grid gap-8 lg:grid-cols-[minmax(280px,340px)_1fr]">
        <div className="card border-helm-accent/30 bg-ink-950/60 p-6 shadow-glow">
          <p className="text-[11px] font-medium uppercase tracking-[0.2em] text-helm-accent/90">
            Composite score
          </p>
          <HealthGauge score={breakdown.health_score} />
          <p className="mt-2 text-center text-sm leading-relaxed text-white/65">
            {breakdown.health_narrative || brief.health_narrative}
          </p>
        </div>

        <div className="card p-6">
          <h1 className="font-display text-2xl font-semibold text-white">How this score is built</h1>
          <p className="mt-3 text-sm leading-relaxed text-white/60">{breakdown.engines_note}</p>
          <dl className="mt-6 grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
              <dt className="text-[11px] uppercase tracking-wide text-white/40">Base</dt>
              <dd className="mt-1 font-display text-2xl font-semibold text-white">{breakdown.base}</dd>
            </div>
            <div className="rounded-xl border border-helm-bad/20 bg-helm-bad/5 p-4">
              <dt className="text-[11px] uppercase tracking-wide text-white/40">Risk penalty</dt>
              <dd className="mt-1 font-display text-2xl font-semibold text-helm-bad">
                −{breakdown.risk_penalty_capped.toFixed(1)}
              </dd>
              {breakdown.risk_cap_applied ? (
                <p className="mt-1 text-[10px] text-white/35">
                  raw {breakdown.risk_penalty_raw.toFixed(1)} · capped at {breakdown.risk_cap}
                </p>
              ) : (
                <p className="mt-1 text-[10px] text-white/35">
                  Σ score × {breakdown.risk_weight}
                </p>
              )}
            </div>
            <div className="rounded-xl border border-helm-good/20 bg-helm-good/5 p-4">
              <dt className="text-[11px] uppercase tracking-wide text-white/40">Opportunity bonus</dt>
              <dd className="mt-1 font-display text-2xl font-semibold text-helm-good">
                +{breakdown.opportunity_bonus_capped.toFixed(1)}
              </dd>
              {breakdown.opportunity_cap_applied ? (
                <p className="mt-1 text-[10px] text-white/35">
                  raw {breakdown.opportunity_bonus_raw.toFixed(1)} · capped at {breakdown.opportunity_cap}
                </p>
              ) : (
                <p className="mt-1 text-[10px] text-white/35">
                  +{breakdown.opportunity_unit_bonus} per valued opportunity
                </p>
              )}
            </div>
          </dl>
          <p className="mt-4 rounded-lg border border-white/10 bg-white/[0.02] px-3 py-2 font-mono text-xs text-white/55">
            {breakdown.formula_plain_language}
          </p>
          <p className="mt-2 text-xs text-white/40">
            Pre-round {breakdown.pre_round} → score {breakdown.health_score} (clamped 0–100).
          </p>
        </div>
      </div>

      <section className="mt-10">
        <h2 className="font-display text-xl font-semibold text-white">Risk penalty ledger</h2>
        <p className="mt-1 text-sm text-white/50">
          Top five risks by score. Contribution = risk score × {breakdown.risk_weight}.
        </p>
        <div className="mt-4 overflow-x-auto rounded-2xl border border-white/10">
          <table className="w-full min-w-[560px] text-left text-sm">
            <thead className="bg-white/[0.03] text-[11px] uppercase tracking-wide text-white/40">
              <tr>
                <th className="px-4 py-3">#</th>
                <th className="px-4 py-3">Risk</th>
                <th className="px-4 py-3">Score</th>
                <th className="px-4 py-3">Contribution</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.06]">
              {breakdown.risk_lines.map((line) => (
                <tr key={line.risk_id} className="hover:bg-white/[0.02]">
                  <td className="px-4 py-3 text-white/40">{line.rank}</td>
                  <td className="px-4 py-3">
                    <Link href={line.href} className="text-white/85 hover:text-helm-accent">
                      {line.title}
                    </Link>
                  </td>
                  <td className="px-4 py-3 tabular-nums text-helm-bad">{line.score}</td>
                  <td className="px-4 py-3 tabular-nums text-white/70">−{line.contribution.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="border-t border-white/10 bg-white/[0.03] font-medium">
                <td className="px-4 py-3" colSpan={3}>
                  Penalty {breakdown.risk_cap_applied ? "(capped)" : "(sum)"}
                </td>
                <td className="px-4 py-3 tabular-nums text-helm-bad">
                  −{breakdown.risk_penalty_capped.toFixed(2)}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </section>

      <section className="mt-10">
        <h2 className="font-display text-xl font-semibold text-white">Opportunity bonus ledger</h2>
        <p className="mt-1 text-sm text-white/50">
          Each opportunity with value &gt; 0 adds +{breakdown.opportunity_unit_bonus} (cap{" "}
          {breakdown.opportunity_cap}).
        </p>
        <div className="mt-4 overflow-x-auto rounded-2xl border border-white/10">
          <table className="w-full min-w-[560px] text-left text-sm">
            <thead className="bg-white/[0.03] text-[11px] uppercase tracking-wide text-white/40">
              <tr>
                <th className="px-4 py-3">Opportunity</th>
                <th className="px-4 py-3">Value</th>
                <th className="px-4 py-3">Qualifies</th>
                <th className="px-4 py-3">Bonus</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.06]">
              {breakdown.opportunity_lines.map((line) => (
                <tr key={line.opportunity_id} className="hover:bg-white/[0.02]">
                  <td className="px-4 py-3 text-white/85">{line.title}</td>
                  <td className="px-4 py-3 tabular-nums text-white/70">
                    {formatZAR(line.value_estimate)}
                  </td>
                  <td className="px-4 py-3">{line.qualifies ? "Yes" : "No"}</td>
                  <td className="px-4 py-3 tabular-nums text-helm-good">
                    {line.qualifies ? `+${line.contribution.toFixed(1)}` : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="border-t border-white/10 bg-white/[0.03] font-medium">
                <td className="px-4 py-3" colSpan={3}>
                  Bonus {breakdown.opportunity_cap_applied ? "(capped)" : "(sum)"}
                </td>
                <td className="px-4 py-3 tabular-nums text-helm-good">
                  +{breakdown.opportunity_bonus_capped.toFixed(1)}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </section>

      <section className="mt-12">
        <h2 className="font-display text-xl font-semibold text-white">Top risks driving the score</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          {brief.top_risks.slice(0, 5).map((r) => (
            <RiskCard key={r.id} risk={r} glossary={glossaryForRisk(r.id, glossary)} />
          ))}
        </div>
      </section>

      {brief.top_opportunities.length > 0 ? (
        <section className="mt-12">
          <h2 className="font-display text-xl font-semibold text-white">Opportunities lifting the score</h2>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            {brief.top_opportunities.map((o) => (
              <OpportunityCard key={o.id} opp={o} />
            ))}
          </div>
        </section>
      ) : null}

      <p className="mt-10 text-sm text-white/45">
        Looking for <strong className="text-white/70">City Health</strong> (clinics / EMS)? That is the{" "}
        <Link href="/CPT/domains/health" className="text-helm-accent hover:underline">
          Health domain
        </Link>
        , also in{" "}
        <Link href="/compare" className="text-helm-accent hover:underline">
          Compare → Health access
        </Link>
        .
      </p>
    </main>
  );
}
