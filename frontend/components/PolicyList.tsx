import type { Policy, Source } from "@/lib/api";

export default function PolicyList({
  policies,
  sources,
}: {
  policies: Policy[];
  sources: Source[];
}) {
  if (!policies?.length) return null;
  const byId = new Map(sources.map((s) => [s.id, s]));
  return (
    <div className="space-y-3">
      {policies.map((p, i) => {
        const src = byId.get(p.source_id);
        return (
          <div key={i} className="card p-4">
            <div className="flex items-start justify-between gap-3">
              <h4 className="text-[15px] font-semibold text-white/90">{p.title}</h4>
              <span className="pill bg-white/5 text-white/60">{p.status}</span>
            </div>
            <p className="mt-1 text-xs text-white/40">as of {p.as_of}</p>
            <p className="mt-2 text-sm text-white/60">{p.detail}</p>
            {src ? (
              <a
                href={src.url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 inline-block text-[11px] text-striops-accent hover:underline"
              >
                Verify ↗ {src.publisher}
              </a>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
