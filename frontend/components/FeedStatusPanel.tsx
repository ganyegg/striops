import type { FeedsReport } from "@/lib/api";

const STATUS_META: Record<string, { className: string }> = {
  live: { className: "bg-helm-good/15 text-helm-good border border-helm-good/30" },
  cached: { className: "bg-helm-accent/15 text-helm-accent border border-helm-accent/30" },
  curated: { className: "bg-helm-sky/15 text-helm-sky border border-helm-sky/30" },
  seed: { className: "bg-helm-warn/15 text-helm-warn border border-helm-warn/30" },
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
              <p className="mt-2 flex-1 text-sm leading-relaxed text-white/60">{feed.description}</p>
              <p className="mt-3 border-t border-white/10 pt-2.5 text-xs text-white/45">
                <span className="font-medium text-helm-accent/90">Live unlocks:</span> {feed.unlocks}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
