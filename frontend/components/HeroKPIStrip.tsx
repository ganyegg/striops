import Link from "next/link";
import type { HeroKPI } from "@/lib/api";
import { toneClass } from "@/lib/api";
import HealthGauge from "./HealthGauge";

const TONE_ORDER = ["good", "neutral", "warn", "bad"] as const;

function groupByTone(kpis: HeroKPI[]): Record<string, HeroKPI[]> {
  const groups: Record<string, HeroKPI[]> = { good: [], neutral: [], warn: [], bad: [] };
  for (const k of kpis) {
    const tone = TONE_ORDER.includes(k.tone as (typeof TONE_ORDER)[number]) ? k.tone : "neutral";
    groups[tone].push(k);
  }
  return groups;
}

function KPITile({ k }: { k: HeroKPI }) {
  const border =
    k.tone === "good"
      ? "border-helm-good/25 hover:border-helm-good/50"
      : k.tone === "warn"
        ? "border-helm-warn/25 hover:border-helm-warn/50"
        : k.tone === "bad"
          ? "border-helm-bad/25 hover:border-helm-bad/50"
          : "border-white/10 hover:border-helm-sky/40";
  const inner = (
    <>
      <p className="text-[11px] font-medium uppercase tracking-[0.16em] text-white/45">{k.label}</p>
      <p className={`mt-1 font-display text-2xl font-semibold tabular-nums md:text-3xl ${toneClass(k.tone)}`}>
        {k.value}
        {k.hint ? (
          <span className="ml-1 font-sans text-sm font-normal text-white/40">{k.hint}</span>
        ) : null}
      </p>
      {k.plain_language ? (
        <p className="mt-2 text-xs leading-relaxed text-white/50">{k.plain_language}</p>
      ) : null}
    </>
  );
  return k.href && k.href !== "/" ? (
    <Link href={k.href} className={`kpi-tile block ${border}`}>
      {inner}
    </Link>
  ) : (
    <div className={`kpi-tile ${border}`}>{inner}</div>
  );
}

export default function HeroKPIStrip({
  kpis,
  healthScore,
  healthNarrative,
}: {
  kpis: HeroKPI[];
  healthScore: number;
  healthNarrative?: string | null;
}) {
  const groups = groupByTone(kpis.filter((k) => k.key !== "health"));
  const left = [...groups.good, ...groups.neutral];
  const right = [...groups.warn, ...groups.bad];

  return (
    <div className="kpi-constellation">
      <div className="kpi-constellation-side">
        {left.map((k) => (
          <KPITile key={k.key} k={k} />
        ))}
      </div>

      <div className="kpi-constellation-centre card border-helm-accent/30 bg-ink-950/60 p-4 shadow-glow">
        <HealthGauge score={healthScore} />
        {healthNarrative ? (
          <p className="mt-1 px-2 pb-2 text-center text-xs leading-relaxed text-white/55">
            {healthNarrative}
          </p>
        ) : (
          <p className="mt-1 px-2 pb-2 text-center text-xs text-white/40">
            Composite of active risks vs redeployable opportunities.
          </p>
        )}
      </div>

      <div className="kpi-constellation-side">
        {right.map((k) => (
          <KPITile key={k.key} k={k} />
        ))}
      </div>
    </div>
  );
}
