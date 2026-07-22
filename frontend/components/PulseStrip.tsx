import Link from "next/link";
import type { CityPulse } from "@/lib/api";

const DIRECTION_META: Record<
  string,
  { badge: string; dot: string; label: string }
> = {
  worsening: {
    badge: "bg-striops-bad/15 text-striops-bad border border-striops-bad/30",
    dot: "bg-striops-bad",
    label: "Worsening",
  },
  improving: {
    badge: "bg-striops-good/15 text-striops-good border border-striops-good/30",
    dot: "bg-striops-good",
    label: "Improving",
  },
  flat: {
    badge: "bg-white/5 text-white/50 border border-white/10",
    dot: "bg-white/30",
    label: "Flat",
  },
};

export default function PulseStrip({
  pulse,
  compact = false,
}: {
  pulse: CityPulse;
  /** Show live feeds first (already sorted server-side); hide demonstration rows until expand. */
  compact?: boolean;
}) {
  const comparison =
    pulse.data_through && pulse.previous_period
      ? `${pulse.data_through} vs ${pulse.previous_period}`
      : "latest vs previous month";

  const live = pulse.items.filter((i) => i.provenance === "live");
  const demo = pulse.items.filter((i) => i.provenance !== "live");
  const shown = compact && live.length > 0 ? live : pulse.items;

  return (
    <div className="card overflow-hidden p-0">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/10 bg-white/[0.03] px-5 py-3">
        <div className="flex flex-col gap-0.5 sm:flex-row sm:items-center sm:gap-2.5">
          <span className="flex items-center gap-2.5">
            <span className="relative flex h-2.5 w-2.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-striops-accent opacity-60" />
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-striops-accent" />
            </span>
            <span className="text-sm font-semibold text-white/85">City Pulse</span>
          </span>
          <span className="text-xs text-white/40">
            {comparison} · {pulse.cadence || "monthly"} series
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-xs">
          {live.length > 0 ? (
            <span className="rounded-full border border-striops-accent/30 bg-striops-accent/10 px-2 py-0.5 text-striops-accent">
              {live.length} live
            </span>
          ) : null}
          <span className="text-striops-bad">{pulse.worsening_count} worsening</span>
          <span className="text-white/25">·</span>
          <span className="text-striops-good">{pulse.improving_count} improving</span>
        </div>
      </div>
      <ul className="divide-y divide-white/[0.06]">
        {shown.map((item) => {
          const meta = DIRECTION_META[item.direction] ?? DIRECTION_META.flat;
          const isLive = item.provenance === "live";
          return (
            <li key={`${item.entity_id}-${item.metric}`}>
              <Link
                href={item.href}
                className="group flex items-start gap-3 px-5 py-3 transition-colors hover:bg-white/[0.04]"
              >
                <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${meta.dot}`} />
                <span className="min-w-0 flex-1">
                  <span className="flex flex-wrap items-center gap-2">
                    <span className="text-sm text-white/80 group-hover:text-white">
                      {item.sentence}
                    </span>
                    <span
                      className={`rounded-full px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide ${
                        isLive
                          ? "border border-striops-accent/30 bg-striops-accent/10 text-striops-accent"
                          : "border border-white/10 bg-white/[0.03] text-white/35"
                      }`}
                    >
                      {isLive ? "Live" : "Demo"}
                    </span>
                  </span>
                  {item.plain_language ? (
                    <span className="mt-0.5 block text-xs text-white/40">
                      {item.plain_language}
                    </span>
                  ) : null}
                </span>
                <span
                  className={`shrink-0 rounded-full px-2 py-0.5 text-[11px] font-medium ${meta.badge}`}
                >
                  {meta.label}
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
      {compact && demo.length > 0 ? (
        <p className="border-t border-white/10 px-5 py-2.5 text-[11px] text-white/35">
          Showing {live.length} live Open Data feeds first.{" "}
          <a href="#pulse-all" className="text-striops-accent hover:underline">
            +{demo.length} demonstration series further down
          </a>
          .
        </p>
      ) : (
        <p className="border-t border-white/10 px-5 py-2.5 text-[11px] text-white/35">
          {pulse.period_note} · Live = City Open Data · Demo = awaiting departmental extract · every
          line opens the full metric report.
        </p>
      )}
    </div>
  );
}
