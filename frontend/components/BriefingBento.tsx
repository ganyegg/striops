import Link from "next/link";
import type { HeroKPI } from "@/lib/api";
import { toneClass } from "@/lib/api";
import HealthGauge from "./HealthGauge";

function HealthTile({
  score,
  narrative,
}: {
  score: number;
  narrative?: string | null;
}) {
  return (
    <Link
      href="/health"
      className="kpi-tile kpi-health-tile group flex flex-col border-helm-accent/35 bg-gradient-to-br from-helm-accent/10 via-ink-950/80 to-ink-900/90 hover:border-helm-accent/55 hover:shadow-glow md:h-full"
      aria-label={`Strategic health score ${score} out of 100 — open breakdown`}
    >
      <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-helm-accent/90">
        Strategic health
      </p>
      <div className="my-auto">
        <HealthGauge score={score} compact />
      </div>
      <p className="line-clamp-3 text-center text-xs leading-relaxed text-white/55">
        {narrative || "Active risks weighed against redeployable opportunities."}
      </p>
      <p className="mt-2 text-center text-[11px] text-helm-accent/80 group-hover:text-helm-accent">
        Open breakdown →
      </p>
    </Link>
  );
}

function KpiTile({ k }: { k: HeroKPI }) {
  const border =
    k.tone === "good"
      ? "border-helm-good/25 hover:border-helm-good/45"
      : k.tone === "warn"
        ? "border-helm-warn/25 hover:border-helm-warn/45"
        : k.tone === "bad"
          ? "border-helm-bad/25 hover:border-helm-bad/45"
          : "border-white/10 hover:border-helm-sky/35";

  const inner = (
    <>
      <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-white/45">{k.label}</p>
      <p className={`mt-1.5 font-display text-2xl font-semibold tabular-nums leading-none md:text-[1.75rem] ${toneClass(k.tone)}`}>
        {k.value}
        {k.hint ? (
          <span className="ml-1.5 font-sans text-xs font-normal text-white/40">{k.hint}</span>
        ) : null}
      </p>
      {k.plain_language ? (
        <p className="mt-2 text-xs leading-snug text-white/45">{k.plain_language}</p>
      ) : null}
    </>
  );

  const className = `kpi-tile ${border}`;

  return k.href && k.href !== "/" ? (
    <Link href={k.href} className={`${className} block`}>
      {inner}
    </Link>
  ) : (
    <div className={className}>{inner}</div>
  );
}

export default function BriefingBento({
  kpis,
  healthScore,
  healthNarrative,
}: {
  kpis: HeroKPI[];
  healthScore: number;
  healthNarrative?: string | null;
}) {
  return (
    <div id="command" className="kpi-command-grid scroll-mt-24">
      <HealthTile score={healthScore} narrative={healthNarrative} />
      {kpis.map((k) => (
        <KpiTile key={k.key} k={k} />
      ))}
    </div>
  );
}
