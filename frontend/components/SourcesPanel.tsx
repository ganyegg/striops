import type { Source } from "@/lib/api";

export default function SourcesPanel({ sources }: { sources: Source[] }) {
  if (!sources?.length) return null;
  return (
    <div className="card p-5">
      <p className="text-xs uppercase tracking-[0.2em] text-white/40">Data Sources</p>
      <dl className="mt-4 space-y-3">
        {sources.map((s) => (
          <div key={s.id} className="border-b border-dashed border-white/10 pb-3 last:border-0">
            <div className="flex items-start justify-between gap-3">
              <div>
                <dt className="text-sm text-white/80">{s.title}</dt>
                <dd className="mt-0.5 text-xs text-white/45">
                  {s.publisher}
                  {s.coverage ? ` · ${s.coverage}` : ""}
                  {s.retrieved_at ? ` · retrieved ${s.retrieved_at}` : ""}
                </dd>
              </div>
              <a
                href={s.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-none text-xs text-striops-accent hover:underline"
              >
                Open ↗
              </a>
            </div>
          </div>
        ))}
      </dl>
    </div>
  );
}
