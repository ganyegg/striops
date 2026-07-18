import Link from "next/link";
import CompareChart from "@/components/CompareChart";
import PageChrome from "@/components/PageChrome";
import { getComparatives } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ComparePage() {
  let report;
  try {
    report = await getComparatives();
  } catch (e) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-24">
        <Link href="/" className="text-sm text-striops-accent hover:underline">
          ← Back to briefing
        </Link>
        <h1 className="mt-6 font-display text-2xl font-semibold text-white">Comparatives unavailable</h1>
        <p className="mt-3 text-white/60">{e instanceof Error ? e.message : String(e)}</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-5xl px-6 py-10 pb-24">
      <PageChrome
        crumbs={
          <>
            <Link href="/" className="font-display font-semibold text-white/80 hover:text-white">
              Striops
            </Link>
            <span className="text-white/25">/</span>
            <span className="text-white/80">Compare</span>
          </>
        }
      />

      <div className="mt-6">
        <p className="text-xs uppercase tracking-[0.22em] text-white/35">Headline contrasts</p>
        <h1 className="mt-1 font-display text-3xl font-semibold text-white">Compare & decide</h1>
        <p className="mt-2 max-w-2xl text-sm text-white/55">
          Related metrics side-by-side — dams vs NRW, clinics vs EMS, and other packs that earn a
          strategic ratio. {report.data_through ? `Data through ${report.data_through}.` : null}
        </p>
        <p className="mt-2 text-xs text-white/35">{report.note}</p>
      </div>

      <div className="mt-10 space-y-10">
        {report.packs.map((pack) => (
          <section key={pack.id} id={pack.id} className="card scroll-mt-24 p-6">
            <p className="text-[11px] uppercase tracking-[0.18em] text-striops-accent/80">{pack.eyebrow}</p>
            <h2 className="mt-1 font-display text-2xl font-semibold text-white">{pack.title}</h2>
            <p className="mt-2 text-sm text-white/55">{pack.why_it_matters}</p>
            <p className="mt-2 text-sm text-striops-sand/80">
              <span className="text-white/40">Decision: </span>
              {pack.decision_anchor}
            </p>

            <div className="mt-5">
              <CompareChart series={pack.series} />
            </div>

            <div className="mt-4 flex flex-wrap gap-3">
              {pack.series.map((s) => (
                <Link
                  key={`${s.entity_id}-${s.metric}`}
                  href={s.href}
                  className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-xs transition hover:border-striops-accent/40"
                >
                  <span className="block text-white/45">{s.label}</span>
                  <span className="font-display text-lg text-white">
                    {s.latest ?? "—"}
                    {s.unit ? <span className="ml-1 text-xs text-white/40">{s.unit}</span> : null}
                  </span>
                  {s.change_pct != null ? (
                    <span className="block text-white/40">
                      {s.change_pct > 0 ? "+" : ""}
                      {s.change_pct}% MoM
                    </span>
                  ) : null}
                </Link>
              ))}
            </div>

            {pack.ratio ? (
              <div className="mt-5 rounded-xl border border-striops-accent/25 bg-striops-accent/5 p-4">
                <p className="text-[11px] uppercase tracking-wide text-striops-accent/90">
                  Strategic ratio · {pack.ratio.label}
                </p>
                <p className="mt-1 font-display text-3xl font-semibold text-white">
                  {pack.ratio.value}
                  <span className="ml-2 font-sans text-sm font-normal text-white/45">{pack.ratio.unit}</span>
                </p>
                <p className="mt-2 text-sm text-white/70">{pack.ratio.interpretation}</p>
                <p className="mt-1 text-xs text-white/40">{pack.ratio.why_it_matters}</p>
              </div>
            ) : null}
          </section>
        ))}
      </div>
    </main>
  );
}
