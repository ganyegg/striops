import Link from "next/link";
import type { CityPulse } from "@/lib/api";

const DOT: Record<string, string> = {
  worsening: "bg-helm-bad",
  improving: "bg-helm-good",
  flat: "bg-white/30",
};

export default function PulseCompact({ pulse }: { pulse: CityPulse }) {
  const top = pulse.items.slice(0, 4);
  const comparison =
    pulse.data_through && pulse.previous_period
      ? `${pulse.data_through} vs ${pulse.previous_period}`
      : "month over month";

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-2xl border border-white/10 bg-ink-900/70 shadow-card backdrop-blur-md">
      <div className="flex items-center justify-between border-b border-white/10 bg-white/[0.03] px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-helm-accent opacity-60" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-helm-accent" />
          </span>
          <span className="text-sm font-semibold text-white/85">City Pulse</span>
        </div>
        <a href="#pulse" className="text-[11px] text-helm-accent hover:underline">
          Full pulse →
        </a>
      </div>
      <p className="border-b border-white/[0.06] px-4 py-2 text-[11px] text-white/40">
        {comparison} · {pulse.worsening_count} worsening · {pulse.improving_count} improving
      </p>
      <ul className="flex flex-1 flex-col divide-y divide-white/[0.06]">
        {top.map((item) => (
          <li key={`${item.entity_id}-${item.metric}`}>
            <Link
              href={item.href}
              className="group flex items-start gap-2.5 px-4 py-3 transition hover:bg-white/[0.04]"
            >
              <span className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${DOT[item.direction] ?? DOT.flat}`} />
              <span className="min-w-0 flex-1 text-sm leading-snug text-white/75 group-hover:text-white">
                {item.label}{" "}
                <span className="text-white/45">
                  {item.change_pct > 0 ? "+" : ""}
                  {item.change_pct}%
                </span>
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
