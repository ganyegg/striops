import Link from "next/link";
import type { CityPulse } from "@/lib/api";

const DIRECTION_META: Record<
  string,
  { badge: string; dot: string; label: string }
> = {
  worsening: {
    badge: "bg-helm-bad/15 text-helm-bad border border-helm-bad/30",
    dot: "bg-helm-bad",
    label: "Worsening",
  },
  improving: {
    badge: "bg-helm-good/15 text-helm-good border border-helm-good/30",
    dot: "bg-helm-good",
    label: "Improving",
  },
  flat: {
    badge: "bg-white/5 text-white/50 border border-white/10",
    dot: "bg-white/30",
    label: "Flat",
  },
};

export default function PulseStrip({ pulse }: { pulse: CityPulse }) {
  const comparison =
    pulse.data_through && pulse.previous_period
      ? `${pulse.data_through} vs ${pulse.previous_period}`
      : "latest vs previous month";

  return (
    <div className="card overflow-hidden p-0">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/10 bg-white/[0.03] px-5 py-3">
        <div className="flex flex-col gap-0.5 sm:flex-row sm:items-center sm:gap-2.5">
          <span className="flex items-center gap-2.5">
            <span className="relative flex h-2.5 w-2.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-helm-accent opacity-60" />
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-helm-accent" />
            </span>
            <span className="text-sm font-semibold text-white/85">City Pulse</span>
          </span>
          <span className="text-xs text-white/40">
            {comparison} · {pulse.cadence || "monthly"} series
          </span>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <span className="text-helm-bad">{pulse.worsening_count} worsening</span>
          <span className="text-white/25">·</span>
          <span className="text-helm-good">{pulse.improving_count} improving</span>
        </div>
      </div>
      <ul className="divide-y divide-white/[0.06]">
        {pulse.items.map((item) => {
          const meta = DIRECTION_META[item.direction] ?? DIRECTION_META.flat;
          return (
            <li key={`${item.entity_id}-${item.metric}`}>
              <Link
                href={item.href}
                className="group flex items-start gap-3 px-5 py-3 transition-colors hover:bg-white/[0.04]"
              >
                <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${meta.dot}`} />
                <span className="min-w-0 flex-1">
                  <span className="text-sm text-white/80 group-hover:text-white">
                    {item.sentence}
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
      <p className="border-t border-white/10 px-5 py-2.5 text-[11px] text-white/35">
        {pulse.period_note} · every line opens the full metric report.
      </p>
    </div>
  );
}
