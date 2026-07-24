import Link from "next/link";
import type { ThemesReport } from "@/lib/api";

const STATUS_STYLE: Record<string, string> = {
  worsening: "text-striops-bad border-striops-bad/30 bg-striops-bad/10",
  improving: "text-striops-good border-striops-good/30 bg-striops-good/10",
  mixed: "text-striops-sand border-striops-sand/30 bg-striops-sand/10",
  watching: "text-striops-accent border-striops-accent/30 bg-striops-accent/10",
  gap: "text-white/45 border-white/15 bg-white/[0.03]",
};

const READY_STYLE: Record<string, string> = {
  live: "text-striops-accent border-striops-accent/30",
  partial: "text-striops-sand border-striops-sand/30",
  awaiting_extract: "text-white/40 border-white/15",
};

export default function CityThemes({ report }: { report: ThemesReport }) {
  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="rounded-full border border-striops-accent/30 bg-striops-accent/10 px-2.5 py-1 text-striops-accent">
          {report.live_theme_count} themes with live feeds
        </span>
        <span className="rounded-full border border-white/15 px-2.5 py-1 text-white/45">
          {report.gap_theme_count} awaiting extract
        </span>
        <span className="text-white/35">{report.official_anchor}</span>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {report.themes.map((t) => (
          <article key={t.id} className="card flex flex-col p-5">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <h3 className="font-display text-lg font-semibold text-white">{t.name}</h3>
              <div className="flex flex-wrap gap-1.5">
                <span
                  className={`rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide ${
                    STATUS_STYLE[t.status] ?? STATUS_STYLE.gap
                  }`}
                >
                  {t.status}
                </span>
                <span
                  className={`rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide ${
                    READY_STYLE[t.readiness] ?? READY_STYLE.awaiting_extract
                  }`}
                >
                  {t.readiness.replace("_", " ")}
                </span>
              </div>
            </div>
            <p className="mt-2 text-sm text-white/70">{t.mayor_question}</p>

            <div className="mt-3 space-y-2 text-xs leading-relaxed">
              <p>
                <span className="text-white/40">City reports: </span>
                <span className="text-white/55">{t.city_says}</span>
              </p>
              <p>
                <span className="text-striops-accent/80">Striops adds: </span>
                <span className="text-white/70">{t.striops_adds}</span>
              </p>
            </div>

            {t.evidence.length > 0 ? (
              <ul className="mt-3 space-y-1.5 border-t border-white/10 pt-3">
                {t.evidence.map((e) => (
                  <li key={e.label + e.value} className="flex flex-wrap items-baseline justify-between gap-2 text-xs">
                    <span className="text-white/50">{e.label}</span>
                    <span className="text-right">
                      {e.href ? (
                        <Link href={e.href} className="font-medium text-white hover:text-striops-accent">
                          {e.value}
                        </Link>
                      ) : (
                        <span className="font-medium text-white">{e.value}</span>
                      )}
                      {e.period ? <span className="ml-1.5 text-white/35">{e.period}</span> : null}
                      <span
                        className={`ml-1.5 rounded-full px-1.5 py-0.5 text-[10px] uppercase ${
                          e.provenance === "live"
                            ? "bg-striops-accent/15 text-striops-accent"
                            : "bg-white/5 text-white/35"
                        }`}
                      >
                        {e.provenance}
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            ) : null}

            {t.gap ? (
              <p className="mt-3 rounded-lg border border-striops-warn/25 bg-striops-warn/5 px-3 py-2 text-[11px] text-striops-warn/90">
                Gap: {t.gap}
              </p>
            ) : null}

            <Link
              href="/ask"
              className="mt-auto pt-3 text-[11px] text-striops-accent hover:underline"
            >
              Ask: {t.ask_prompt.slice(0, 64)}
              {t.ask_prompt.length > 64 ? "…" : ""} →
            </Link>
          </article>
        ))}
      </div>

      <div className="card p-5">
        <p className="text-[11px] uppercase tracking-[0.18em] text-striops-accent/80">
          Why this beats a PDF
        </p>
        <h3 className="mt-1 font-display text-lg font-semibold text-white">
          Continuous OS vs quarterly reports
        </h3>
        <div className="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {report.value_over_reports.map((v) => (
            <div key={v.title} className="rounded-xl border border-white/10 bg-white/[0.02] p-3">
              <p className="text-sm font-semibold text-white">{v.title}</p>
              <p className="mt-2 text-[11px] leading-relaxed text-white/40">
                <span className="text-white/35">Report: </span>
                {v.report_does}
              </p>
              <p className="mt-1.5 text-[11px] leading-relaxed text-white/70">
                <span className="text-striops-accent/80">Striops: </span>
                {v.striops_does}
              </p>
            </div>
          ))}
        </div>
        <p className="mt-4 text-[11px] leading-relaxed text-white/35">{report.source_note}</p>
        <p className="mt-2 text-[11px] leading-relaxed text-striops-sand/70">{report.fiscal_period_note}</p>
      </div>
    </div>
  );
}
