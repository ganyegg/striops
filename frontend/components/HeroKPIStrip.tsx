import Link from "next/link";
import type { HeroKPI } from "@/lib/api";
import { toneClass } from "@/lib/api";

export default function HeroKPIStrip({ kpis }: { kpis: HeroKPI[] }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {kpis.map((k) => {
        const inner = (
          <>
            <p className="text-[11px] font-medium uppercase tracking-[0.16em] text-white/45">
              {k.label}
            </p>
            <p className={`mt-1 font-display text-3xl font-semibold tabular-nums ${toneClass(k.tone)}`}>
              {k.value}
              {k.hint ? (
                <span className="ml-1 text-sm font-sans font-normal text-white/40">{k.hint}</span>
              ) : null}
            </p>
            {k.plain_language ? (
              <p className="mt-2 text-xs leading-relaxed text-white/50">{k.plain_language}</p>
            ) : null}
          </>
        );
        return k.href && k.href !== "/" ? (
          <Link key={k.key} href={k.href} className="kpi-tile block">
            {inner}
          </Link>
        ) : (
          <div key={k.key} className="kpi-tile">
            {inner}
          </div>
        );
      })}
    </div>
  );
}
