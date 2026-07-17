import Link from "next/link";
import MetricTrendChart from "@/components/MetricTrendChart";
import PageChrome from "@/components/PageChrome";
import ReferencesPanel from "@/components/ReferencesPanel";
import VerificationBadge from "@/components/VerificationBadge";
import {
  getIndicatorReport,
  getMetricReport,
  type IndicatorReport,
  type MetricReport,
} from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function IndicatorReportPage({
  params,
}: {
  params: { municipality: string; domain: string; key: string };
}) {
  const code = params.municipality.toUpperCase();
  const domainId = params.domain;
  const key = decodeURIComponent(params.key);

  let report: IndicatorReport;
  try {
    report = await getIndicatorReport(code, domainId, key);
  } catch (e) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-24">
        <Link href={`/${code}/domains/${domainId}`} className="text-sm text-helm-accent hover:underline">
          ← Back to domain
        </Link>
        <h1 className="mt-6 text-2xl font-semibold text-white/90">Indicator unavailable</h1>
        <p className="mt-3 text-white/60">{e instanceof Error ? e.message : String(e)}</p>
      </main>
    );
  }

  let metricReport: MetricReport | null = null;
  if (report.related_metric) {
    try {
      metricReport = await getMetricReport(
        report.related_metric.entity_id,
        report.related_metric.metric,
      );
    } catch {
      metricReport = null;
    }
  }

  const ind = report.indicator;

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <PageChrome
        backHref={`/${code}/domains/${domainId}`}
        backLabel="← Domain"
        crumbs={
          <>
            <Link href="/" className="font-semibold text-white/80 hover:text-white">
              Helm
            </Link>
            <span className="text-white/25">/</span>
            <Link href={`/${code}/domains/${domainId}`} className="text-white/50 hover:text-white/80">
              {report.domain_name}
            </Link>
            <span className="text-white/25">/</span>
            <span className="text-white/80">{ind.label}</span>
          </>
        }
      />

      <div className="mt-8">
        <p className="text-xs uppercase tracking-[0.25em] text-white/35">Indicator report</p>
        <div className="mt-1 flex flex-wrap items-center gap-3">
          <h1 className="text-3xl font-semibold tracking-tight text-white">{ind.label}</h1>
          <VerificationBadge status={ind.verification} />
        </div>
        <p className="mt-4 text-4xl font-semibold tabular-nums text-white">{ind.value}</p>
        <p className="mt-2 text-xs text-white/40">
          as of {ind.as_of} · confidence {Math.round(ind.confidence * 100)}%
          {ind.trend !== "na" ? ` · trend ${ind.trend}` : ""}
        </p>
        <p className="mt-4 max-w-3xl text-[15px] leading-relaxed text-white/65">{report.narrative}</p>
        {ind.method ? (
          <p className="mt-2 text-sm italic text-white/40">{ind.method}</p>
        ) : null}
        {report.source ? (
          <a
            href={report.source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-3 inline-block text-sm text-helm-accent hover:underline"
          >
            Verify primary source ↗ · {report.source.publisher}
          </a>
        ) : null}
      </div>

      <section className="mt-8 card p-5">
        <p className="text-xs uppercase tracking-[0.2em] text-white/40">Domain context</p>
        <p className="mt-2 text-sm text-white/65">{report.domain_summary}</p>
      </section>

      {metricReport ? (
        <section className="mt-8 space-y-3">
          <div className="flex items-end justify-between">
            <h2 className="text-lg font-semibold text-white/90">Related time series</h2>
            <Link
              href={`/metrics/${metricReport.entity_id}/${metricReport.metric}`}
              className="text-xs text-helm-accent hover:underline"
            >
              Full metric report ↗
            </Link>
          </div>
          <MetricTrendChart
            series={metricReport.series}
            projected={metricReport.projected}
            unit={metricReport.unit}
            label={metricReport.metric_label}
          />
        </section>
      ) : null}

      {report.related_risk_ids.length ? (
        <section className="mt-8">
          <h2 className="mb-3 text-lg font-semibold text-white/90">Related risks</h2>
          <div className="flex flex-wrap gap-2">
            {report.related_risk_ids.map((id) => (
              <Link
                key={id}
                href={`/risks/${id}`}
                className="pill border border-helm-bad/30 bg-helm-bad/10 text-helm-bad hover:underline"
              >
                {id.replace(/^risk-/, "").replace(/-/g, " ")} ↗
              </Link>
            ))}
          </div>
        </section>
      ) : null}

      {report.related_indicators.length ? (
        <section className="mt-8">
          <h2 className="mb-3 text-lg font-semibold text-white/90">Related indicators</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {report.related_indicators.map((ri) => (
              <Link
                key={ri.key}
                href={`/${code}/domains/${domainId}/indicators/${ri.key}`}
                className="card p-4 transition hover:border-helm-accent/30"
              >
                <p className="text-sm text-white/50">{ri.label}</p>
                <p className="mt-1 text-lg font-semibold text-white/90">{ri.value}</p>
              </Link>
            ))}
          </div>
        </section>
      ) : null}

      {report.watchpoints.length ? (
        <section className="mt-8">
          <h2 className="mb-3 text-lg font-semibold text-white/90">Watchpoints</h2>
          <ul className="space-y-2">
            {report.watchpoints.map((w, i) => (
              <li key={i} className="flex gap-2 text-sm text-white/65">
                <span className="text-helm-warn">•</span>
                {w}
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
