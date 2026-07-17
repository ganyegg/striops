import Link from "next/link";
import MetricTrendChart from "@/components/MetricTrendChart";
import ReferencesPanel from "@/components/ReferencesPanel";
import ScoreBreakdownPanel from "@/components/ScoreBreakdown";
import { getRiskReport, priorityColor, type RiskReport } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function RiskReportPage({
  params,
}: {
  params: { riskId: string };
}) {
  const riskId = decodeURIComponent(params.riskId);
  let report: RiskReport;
  try {
    report = await getRiskReport(riskId);
  } catch (e) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-24">
        <Link href="/" className="text-sm text-helm-accent hover:underline">
          ← Back to briefing
        </Link>
        <h1 className="mt-6 text-2xl font-semibold text-white/90">Report unavailable</h1>
        <p className="mt-3 text-white/60">
          {e instanceof Error ? e.message : String(e)}
        </p>
      </main>
    );
  }

  const { risk, metric_report: mr } = report;

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <header className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          <Link href="/" className="font-display font-semibold tracking-wide text-white/80 hover:text-white">
            Helm
          </Link>
          <span className="text-white/25">/</span>
          <span className="text-white/50">Risk report</span>
          <span className="text-white/25">/</span>
          <span className="text-white/80">{risk.title}</span>
        </div>
        <Link href="/" className="text-xs text-helm-accent hover:underline">
          ← Briefing
        </Link>
      </header>

      <div className="mt-8">
        <p className="text-xs uppercase tracking-[0.25em] text-white/35">Risk report</p>
        <div className="mt-1 flex flex-wrap items-center gap-3">
          <h1 className="text-3xl font-semibold tracking-tight text-white">{risk.title}</h1>
          <span className={`pill ${priorityColor(risk.priority)}`}>{risk.priority}</span>
        </div>
        {report.plain_language ? (
          <div className="mt-4 rounded-2xl border border-helm-sky/20 bg-helm-sky/10 p-5">
            <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-helm-sky">
              What is {report.term}?
            </p>
            <p className="mt-2 text-[15px] leading-relaxed text-white/85">{report.plain_language}</p>
            {report.in_one_line ? (
              <p className="mt-2 text-sm text-helm-sand/80">In one line: {report.in_one_line}</p>
            ) : null}
          </div>
        ) : null}
        <p className="mt-4 max-w-3xl text-[15px] leading-relaxed text-white/65">{report.narrative}</p>
        <div className="mt-3 flex flex-wrap gap-3 text-xs text-white/40">
          <span>Owner: {risk.owner}</span>
          {report.related_budget_function ? (
            <span>· Budget: {report.related_budget_function}</span>
          ) : null}
          {report.related_domain_id ? (
            <Link
              href={`/CPT/domains/${report.related_domain_id}`}
              className="text-helm-accent hover:underline"
            >
              · Domain deep dive ↗
            </Link>
          ) : null}
        </div>
      </div>

      <div className="mt-8 grid gap-4 md:grid-cols-[280px_1fr]">
        <ScoreBreakdownPanel breakdown={report.score_breakdown} />
        <div className="card p-5">
          <p className="text-xs uppercase tracking-[0.2em] text-white/40">What changed</p>
          <ul className="mt-3 space-y-2">
            {report.what_changed.map((w, i) => (
              <li key={i} className="flex gap-2 text-sm text-white/65">
                <span className="text-helm-warn">•</span>
                {w}
              </li>
            ))}
          </ul>
          <div className="mt-5 rounded-lg bg-helm-accent/5 p-3 text-sm text-white/70">
            <span className="text-[11px] font-medium uppercase tracking-wide text-helm-accent">
              Mitigation
            </span>
            <p className="mt-0.5">{risk.mitigation}</p>
          </div>
        </div>
      </div>

      {mr ? (
        <section className="mt-8 space-y-4">
          <div className="flex items-end justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-white/90">Data trend</h2>
              <p className="text-sm text-white/50">
                {mr.metric_label} · {mr.entity_name}
                {mr.stats.change_pct != null
                  ? ` · MoM ${mr.stats.change_pct > 0 ? "+" : ""}${mr.stats.change_pct}%`
                  : ""}
              </p>
            </div>
            <Link
              href={`/metrics/${mr.entity_id}/${mr.metric}`}
              className="text-xs text-helm-accent hover:underline"
            >
              Full metric report ↗
            </Link>
          </div>
          <MetricTrendChart
            series={mr.series}
            projected={mr.projected}
            unit={mr.unit}
            label={mr.metric_label}
          />
          <div className="grid gap-3 sm:grid-cols-4">
            {[
              { label: "Latest", value: mr.stats.latest.toLocaleString() },
              {
                label: "Projected next",
                value: mr.forecast?.projected_next?.toLocaleString() ?? "—",
              },
              { label: "Min / Max", value: `${mr.stats.min_value?.toLocaleString()} – ${mr.stats.max_value?.toLocaleString()}` },
              { label: "Periods", value: String(mr.stats.n_points) },
            ].map((s) => (
              <div key={s.label} className="card p-4">
                <p className="text-[11px] uppercase tracking-wide text-white/40">{s.label}</p>
                <p className="mt-1 text-lg font-semibold tabular-nums text-white/90">{s.value}</p>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <section className="mt-8">
        <h2 className="mb-3 text-lg font-semibold text-white/90">Recommended actions</h2>
        <ol className="space-y-2">
          {report.recommended_actions.map((a, i) => (
            <li key={i} className="card flex gap-3 p-4 text-sm text-white/70">
              <span className="font-mono text-helm-accent">{String(i + 1).padStart(2, "0")}</span>
              {a}
            </li>
          ))}
        </ol>
      </section>

      {risk.evidence?.length ? (
        <section className="mt-8">
          <h2 className="mb-3 text-lg font-semibold text-white/90">Evidence</h2>
          <div className="card divide-y divide-white/5 p-2">
            {risk.evidence.map((e, i) => (
              <div key={i} className="flex justify-between gap-4 px-3 py-3 text-sm">
                <span className="text-white/45">{e.label}</span>
                <span className="text-right text-white/80">
                  {e.value}
                  {e.source ? <span className="ml-1 text-white/30">· {e.source}</span> : null}
                </span>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <section className="mt-8">
        <ReferencesPanel references={report.references} />
      </section>
    </main>
  );
}
