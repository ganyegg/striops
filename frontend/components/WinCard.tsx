import Link from "next/link";
import type { Initiative } from "@/lib/api";
import { priorityColor } from "@/lib/api";

export default function WinCard({ win }: { win: Initiative }) {
  return (
    <Link
      href={`/wins/${encodeURIComponent(win.id)}`}
      className="card-win group block overflow-hidden transition hover:border-striops-ocean/50 hover:shadow-glow"
    >
      {win.image_url ? (
        <div className="relative h-36 overflow-hidden">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={win.image_url}
            alt=""
            className="h-full w-full object-cover transition duration-500 group-hover:scale-105"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-ink-950 via-ink-950/40 to-transparent" />
          <span className="absolute bottom-3 left-4 pill bg-striops-ocean/90 text-white">
            {win.category}
          </span>
        </div>
      ) : null}
      <div className="p-5">
        <div className="flex items-start justify-between gap-3">
          <h3 className="font-display text-lg font-semibold text-white">{win.title}</h3>
          <span className={`pill ${priorityColor(win.priority)}`}>{win.status}</span>
        </div>
        <p className="mt-2 text-sm font-medium text-striops-sand/90">{win.headline}</p>
        <p className="mt-2 text-sm leading-relaxed text-white/60">{win.plain_language}</p>
        {win.metrics?.[0] ? (
          <div className="mt-4 flex items-end justify-between border-t border-white/10 pt-3">
            <div>
              <p className="text-[11px] uppercase tracking-wide text-white/40">{win.metrics[0].label}</p>
              <p className="font-display text-xl font-semibold text-striops-good">{win.metrics[0].value}</p>
            </div>
            <span className="text-[11px] text-striops-accent">Open report →</span>
          </div>
        ) : null}
      </div>
    </Link>
  );
}
