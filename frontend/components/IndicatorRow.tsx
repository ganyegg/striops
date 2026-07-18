import Link from "next/link";
import type { Indicator, Source } from "@/lib/api";
import VerificationBadge from "./VerificationBadge";

function TrendGlyph({ trend }: { trend: Indicator["trend"] }) {
  if (trend === "na") return null;
  const map = { up: "↑", down: "↓", flat: "→" } as const;
  const color =
    trend === "up" ? "text-striops-bad" : trend === "down" ? "text-striops-good" : "text-white/40";
  return (
    <span className={`text-xs ${color}`} title={`Trend: ${trend}`}>
      {map[trend]}
    </span>
  );
}

export default function IndicatorRow({
  indicator,
  source,
  href,
}: {
  indicator: Indicator;
  source?: Source;
  href?: string;
}) {
  const body = (
    <>
      <div className="flex items-start justify-between gap-3">
        <span className="text-sm text-white/55">{indicator.label}</span>
        <VerificationBadge status={indicator.verification} />
      </div>
      <div className="mt-1 flex items-baseline gap-2">
        <span className="text-xl font-semibold text-white/95">{indicator.value}</span>
        <TrendGlyph trend={indicator.trend} />
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-white/40">
        <span className="pill bg-white/5 text-white/50">as of {indicator.as_of}</span>
        <span>Confidence {Math.round(indicator.confidence * 100)}%</span>
        {indicator.trend_note ? <span>· {indicator.trend_note}</span> : null}
      </div>
      {indicator.method ? (
        <p className="mt-2 text-xs italic text-white/35">{indicator.method}</p>
      ) : null}
      <div className="mt-3 flex items-center justify-between border-t border-white/5 pt-2 text-[11px]">
        <span className="text-white/35">{source?.publisher ?? "Source"}</span>
        {href ? (
          <span className="text-striops-accent">Open report →</span>
        ) : source ? (
          <span className="text-striops-accent">Verify ↗</span>
        ) : null}
      </div>
    </>
  );

  if (href) {
    return (
      <Link
        href={href}
        className="card block p-4 transition hover:border-striops-accent/30 hover:bg-white/[0.05]"
      >
        {body}
      </Link>
    );
  }

  if (source) {
    return (
      <a
        href={source.url}
        target="_blank"
        rel="noopener noreferrer"
        className="card block p-4 transition hover:border-striops-accent/30"
      >
        {body}
      </a>
    );
  }

  return <div className="card p-4">{body}</div>;
}
