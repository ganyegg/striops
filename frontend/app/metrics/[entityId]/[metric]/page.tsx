import Link from "next/link";
import MetricTrendChart from "@/components/MetricTrendChart";
import PageChrome from "@/components/PageChrome";
import ReferencesPanel from "@/components/ReferencesPanel";
import { getMetricReport, type MetricReport } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function MetricReportPage({
  params,
}: {
  params: { entityId: string; metric: string };
}) {
  const entityId = decodeURIComponent(params.entityId);
  const metric = decodeURIComponent(params.metric);
  let report: MetricReport;
  try {
    report = await getMetricReport(entityId, metric);
  } catch (e) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-24">
        <Link href="/" className="text-sm text-helm-accent hover:underline">
          ← Back to briefing
        </Link>
        <h1 className="mt-6 text-2xl font-semibold text-white/90">Metric unavailable</h1>
        <p className="mt-3 text-white/60">{e instanceof Error ? e.message : String(e)}</p>
      </main>
    );
  }

  const s = report.stats;

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <PageChrome
        crumbs={
          <>
            <Link href="/" className="font-semibold text-white/80 hover:text-white">
              Helm
            </Link>
            <span className="text-white/25">/</span>
            <span className="text-white/50">Metric report</span>
            <span className="text-white/25">/</span>
            <span className="text-white/80">{report.metric_label}</span>
          </>
        }
      />

      <div className="mt-8">
        <p className="text-xs uppercase tracking-[0.25em] text-white/35">Metric report</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight text-white">
          {report.metric_label}
        </h1>
        <p className="mt-1 text-sm text-white/50">
          {report.entity_name}
          {report.department ? ` · ${report.department}` : ""}
          {report.owner ? ` · ${report.owner}` : ""}
        </p>
        <p className="mt-3 max-w-3xl text-[15px] leading-relaxed text-white/65">{report.narrative}</p>
        <div className="mt-3 flex flex-wrap gap-3 text-xs">
          {report.related_risk_id ? (
            <Link
              href={`/risks/${report.related_risk_id}`}
              className="text-helm-accent hover:underline"
            >
              Related risk report ↗
            </Link>
          ) : null}
          {report.related_domain_id ? (
            <Link
              href={`/CPT/domains/${report.related_domain_id}`}
              className="text-helm-accent hover:underline"
            >
              Domain deep dive ↗
            </Link>
          ) : null}
        </div>
      </div>

      <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {[
          {
            label: "Latest",
            value: `${s.latest.toLocaleString()}${report.unit ? ` ${report.unit}` : ""}`,
          },
          {
            label: "MoM change",
            value:
              s.change_pct != null
                ? `${s.change_pct > 0 ? "+" : ""}${s.change_pct}%`
                : "—",
          },
          {
            label: "Projected next",
            value: report.forecast
              ? report.forecast.projected_next.toLocaleString()
              : "—",
          },
          {
            label: "Trend",
            value: report.forecast?.direction ?? "—",
          },
        ].map((item) => (
          <div key={item.label} className="card p-4">
            <p className="text-[11px] uppercase tracking-wide text-white/40">{item.label}</p>
            <p className="mt-1 text-xl font-semibold tabular-nums capitalize text-white/90">
              {item.value}
            </p>
          </div>
        ))}
      </div>

      <section className="mt-8">
        <MetricTrendChart
          series={report.series}
          projected={report.projected}
          unit={report.unit}
          label={report.metric_label}
        />
      </section>

      <section className="mt-8">
        <h2 className="mb-3 text-lg font-semibold text-white/90">Period detail</h2>
        <div className="card overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-white/10 text-[11px] uppercase tracking-wide text-white/40">
              <tr>
                <th className="px-4 py-3">Period</th>
                <th className="px-4 py-3">Value</th>
                <th className="px-4 py-3">Kind</th>
              </tr>
            </thead>
            <tbody>
              {[...report.series, ...report.projected.slice(1)].map((p, i) => (
                <tr key={i} className="border-b border-white/5 text-white/70">
                  <td className="px-4 py-2.5 font-mono text-xs">{p.period}</td>
                  <td className="px-4 py-2.5 tabular-nums">{p.value.toLocaleString()}</td>
                  <td className="px-4 py-2.5 capitalize text-white/40">{p.kind}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {report.forecast?.contributing_factors?.length ? (
        <section className="mt-8">
          <h2 className="mb-3 text-lg font-semibold text-white/90">Forecast factors</h2>
          <ul className="space-y-2">
            {report.forecast.contributing_factors.map((f, i) => (
              <li key={i} className="card px-4 py-3 text-sm text-white/65">
                {f}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="mt-8">
        <ReferencesPanel references={report.references} />
      </section>
    </main>
  );
}
