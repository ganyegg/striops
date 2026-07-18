import type { FeedsReport } from "@/lib/api";

const STATUS_META: Record<string, { className: string }> = {
  live: { className: "bg-striops-good/15 text-striops-good border border-striops-good/30" },
  cached: { className: "bg-striops-accent/15 text-striops-accent border border-striops-accent/30" },
  curated: { className: "bg-striops-sky/15 text-striops-sky border border-striops-sky/30" },
  seed: { className: "bg-striops-warn/15 text-striops-warn border border-striops-warn/30" },
};

export default function FeedStatusPanel({ report }: { report: FeedsReport }) {
  return (
    <div>
      <p className="mb-4 max-w-2xl text-sm text-white/55">{report.honesty_note}</p>
      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        {report.feeds.map((feed) => {
          const meta = STATUS_META[feed.status] ?? STATUS_META.seed;
          return (
            <div key={feed.id} className="card flex flex-col p-4">
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-semibold leading-snug text-white/90">{feed.name}</p>
                <span className={`shrink-0 rounded-full px-2.5 py-0.5 text-[11px] font-medium ${meta.className}`}>
                  {feed.status_label}
                </span>
              </div>
              <p className="mt-1 text-xs text-white/45">
                {feed.publisher} · {feed.cadence}
              </p>
              <p className="mt-1 text-[11px] text-white/35">
                Last refreshed: {feed.last_refreshed_label || "unknown"}
              </p>
              <p className="mt-2 flex-1 text-sm leading-relaxed text-white/60">{feed.description}</p>
              <p className="mt-3 border-t border-white/10 pt-2.5 text-xs text-white/45">
                <span className="font-medium text-striops-accent/90">Live unlocks:</span> {feed.unlocks}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
