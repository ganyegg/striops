import Link from "next/link";
import type { CriticalSector, SectorsReport } from "@/lib/api";

function statusClass(status: string): string {
  switch (status) {
    case "worsening":
      return "text-striops-bad border-striops-bad/30 bg-striops-bad/10";
    case "improving":
      return "text-striops-good border-striops-good/30 bg-striops-good/10";
    case "mixed":
      return "text-striops-warn border-striops-warn/30 bg-striops-warn/10";
    case "flat":
      return "text-white/55 border-white/15 bg-white/5";
    default:
      return "text-white/40 border-white/10 bg-white/[0.03]";
  }
}

function SectorCard({ s }: { s: CriticalSector }) {
  const estimate = s.affected?.population_estimate;
  return (
    <Link
      href={s.href}
      className={`card block p-4 transition hover:border-striops-accent/40 ${
        s.priority === "P3" ? "opacity-80" : ""
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-[10px] uppercase tracking-[0.18em] text-white/35">
            {s.priority}
            {s.priority === "P3" ? " · secondary" : ""}
          </p>
          <h3 className="mt-0.5 font-display text-lg font-semibold text-white">{s.name}</h3>
        </div>
        <span className={`pill border text-[10px] capitalize ${statusClass(s.status)}`}>{s.status}</span>
      </div>
      <p className="mt-2 text-xs leading-relaxed text-white/50">{s.mayor_question}</p>
      {s.headline ? (
        <p className="mt-2 line-clamp-2 text-sm text-white/70">{s.headline}</p>
      ) : null}
      {estimate != null ? (
        <p className="mt-3 font-display text-xl font-semibold text-striops-sand">
          ~{estimate.toLocaleString("en-ZA")}
          <span className="ml-1.5 font-sans text-xs font-normal text-white/40">{s.affected?.unit}</span>
        </p>
      ) : s.blocker ? (
        <p className="mt-3 rounded-lg border border-white/10 bg-white/[0.03] px-2.5 py-2 text-[11px] text-white/45">
          No data yet: {s.blocker}
        </p>
      ) : null}
      {s.ownership_note ? (
        <p className="mt-2 text-[10px] leading-relaxed text-white/35">{s.ownership_note}</p>
      ) : null}
      {s.top_risk_title ? (
        <p className="mt-2 text-[11px] text-striops-bad/80">Risk: {s.top_risk_title}</p>
      ) : null}
    </Link>
  );
}

export default function CriticalSectors({ report }: { report: SectorsReport }) {
  const primary = report.sectors.filter((s) => s.priority === "P0" || s.priority === "P1");
  const secondary = report.sectors.filter((s) => s.priority === "P2" || s.priority === "P3");

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <p className="text-xs text-white/45">
          P0 ready {report.p0_ready_count}/{report.p0_total} · Empty cells are data requests, not silence
        </p>
        <Link href="/ask" className="text-xs text-striops-accent hover:underline">
          Ask about a sector →
        </Link>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {primary.map((s) => (
          <SectorCard key={s.id} s={s} />
        ))}
      </div>
      {secondary.length > 0 ? (
        <div className="mt-4">
          <p className="mb-2 text-[10px] uppercase tracking-[0.2em] text-white/30">Secondary signals</p>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {secondary.map((s) => (
              <SectorCard key={s.id} s={s} />
            ))}
          </div>
        </div>
      ) : null}
      <p className="mt-3 text-xs text-white/35">{report.note}</p>
    </div>
  );
}
