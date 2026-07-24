import Link from "next/link";
import MetricTrendChart from "@/components/MetricTrendChart";
import PageChrome from "@/components/PageChrome";
import ReferencesPanel from "@/components/ReferencesPanel";
import { getWinReport, priorityColor, type InitiativeReport } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function WinReportPage({ params }: { params: { winId: string } }) {
  const winId = decodeURIComponent(params.winId);
  let report: InitiativeReport;
  try {
    report = await getWinReport(winId);
  } catch (e) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-24">
        <Link href="/wins" className="text-sm text-striops-accent hover:underline">
          ← Back to briefing
        </Link>
        <h1 className="mt-6 font-display text-2xl font-semibold">Win report unavailable</h1>
        <p className="mt-3 text-white/60">{e instanceof Error ? e.message : String(e)}</p>
      </main>
    );
  }

  const w = report.initiative;

  return (
    <main className="pb-16">
      {w.image_url ? (
        <div className="relative h-64 w-full md:h-80">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={w.image_url} alt="" className="h-full w-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-t from-ink-950 via-ink-950/60 to-ink-950/20" />
          <div className="absolute inset-x-0 bottom-0 mx-auto max-w-5xl px-6 pb-8">
            <p className="text-xs uppercase tracking-[0.25em] text-striops-sand/80">Win report</p>
            <h1 className="mt-1 font-display text-3xl font-semibold text-white md:text-4xl">
              {w.title}
            </h1>
          </div>
        </div>
      ) : null}

      <div className="mx-auto max-w-5xl px-6 py-10">
        <PageChrome
          crumbs={
            <>
              <Link href="/" className="font-display font-semibold text-white/80 hover:text-white">
                Striops
              </Link>
              <span className="text-white/25">/</span>
              <Link href="/wins" className="text-white/50 hover:text-white/80">
                Wins
              </Link>
            </>
          }
        />

        {!w.image_url ? (
          <>
            <p className="text-xs uppercase tracking-[0.25em] text-white/35">Win report</p>
            <h1 className="mt-1 font-display text-3xl font-semibold text-white">{w.title}</h1>
          </>
        ) : null}

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className="pill bg-striops-ocean/20 text-striops-accent">{w.category}</span>
          <span className={`pill ${priorityColor(w.priority)}`}>{w.status}</span>
          <span className="text-xs text-white/40">
            Confidence {Math.round(w.confidence * 100)}% · {w.owner}
          </span>
        </div>

        <p className="mt-4 font-display text-xl text-striops-sand">{w.headline}</p>

        <div className="mt-6 rounded-2xl border border-striops-sky/20 bg-striops-sky/10 p-5">
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-striops-sky">
            In plain language
          </p>
          <p className="mt-2 text-[15px] leading-relaxed text-white/85">{w.plain_language}</p>
        </div>

        <p className="mt-5 text-sm leading-relaxed text-white/65">
          <span className="font-semibold text-white/80">Why it matters: </span>
          {w.why_it_matters}
        </p>

        <section className="mt-8 grid gap-3 sm:grid-cols-3">
          {w.metrics.map((m, i) => (
            <div key={i} className="card-win p-4">
              <p className="text-[11px] uppercase tracking-wide text-white/40">{m.label}</p>
              <p className="mt-1 font-display text-2xl font-semibold text-striops-good">{m.value}</p>
              <p className="mt-1 text-xs text-white/35">as of {m.as_of}</p>
            </div>
          ))}
        </section>

        {w.evidence?.length ? (
          <section className="mt-8">
            <h2 className="mb-3 font-display text-lg font-semibold">Evidence</h2>
            <div className="card divide-y divide-white/5">
              {w.evidence.map((e, i) => (
                <div key={i} className="flex justify-between gap-4 px-4 py-3 text-sm">
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

        <section className="mt-8 rounded-2xl border border-striops-gold/25 bg-striops-gold/10 p-5">
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-striops-gold">
            Recommended next step
          </p>
          <p className="mt-2 text-sm text-white/85">{w.next_step}</p>
        </section>

        {report.metric_report ? (
          <section className="mt-8 space-y-3">
            <div className="flex items-end justify-between">
              <h2 className="font-display text-lg font-semibold">Related trend</h2>
              <Link
                href={`/metrics/${report.metric_report.entity_id}/${report.metric_report.metric}`}
                className="text-xs text-striops-accent hover:underline"
              >
                Full metric report ↗
              </Link>
            </div>
            <MetricTrendChart
              series={report.metric_report.series}
              projected={report.metric_report.projected}
              unit={report.metric_report.unit}
              label={report.metric_report.metric_label}
            />
          </section>
        ) : null}

        {w.related_risk_ids?.length ? (
          <section className="mt-8">
            <h2 className="mb-3 font-display text-lg font-semibold">Related risks to watch</h2>
            <div className="flex flex-wrap gap-2">
              {w.related_risk_ids.map((id) => (
                <Link
                  key={id}
                  href={`/risks/${id}`}
                  className="pill border border-striops-bad/30 bg-striops-bad/10 text-striops-bad hover:underline"
                >
                  Open risk report ↗
                </Link>
              ))}
            </div>
          </section>
        ) : null}

        {w.image_credit ? (
          <p className="mt-8 text-[11px] text-white/30">Image: {w.image_credit}</p>
        ) : null}

        <section className="mt-8">
          <ReferencesPanel references={report.references} />
        </section>
      </div>
    </main>
  );
}
