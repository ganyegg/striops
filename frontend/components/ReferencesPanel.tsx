import type { ReferenceLink } from "@/lib/api";

export default function ReferencesPanel({ references }: { references: ReferenceLink[] }) {
  if (!references?.length) return null;
  return (
    <div className="card p-5">
      <p className="text-xs uppercase tracking-[0.2em] text-white/40">References</p>
      <p className="mt-1 text-xs text-white/40">
        Every figure is verifiable against a public source. Open the link to confirm.
      </p>
      <ul className="mt-4 space-y-3">
        {references.map((r, i) => (
          <li key={i} className="border-b border-dashed border-white/10 pb-3 last:border-0">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm text-white/85">{r.label}</p>
                <p className="mt-0.5 text-xs text-white/40">
                  {r.publisher}
                  {r.as_of ? ` · ${r.as_of}` : ""}
                </p>
                {r.note ? <p className="mt-1 text-xs text-white/35">{r.note}</p> : null}
              </div>
              <a
                href={r.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-none text-xs text-striops-accent hover:underline"
              >
                Open ↗
              </a>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
