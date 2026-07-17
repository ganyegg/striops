import type { Evidence } from "@/lib/api";

export default function EvidenceList({ items }: { items: Evidence[] }) {
  if (!items?.length) return null;
  return (
    <div className="mt-3 space-y-1 border-t border-white/5 pt-3">
      {items.map((e, i) => (
        <div key={i} className="flex items-baseline justify-between gap-3 text-xs">
          <span className="text-white/45">{e.label}</span>
          <span className="text-right text-white/70">
            {e.value}
            {e.source ? <span className="ml-1 text-white/30">· {e.source}</span> : null}
          </span>
        </div>
      ))}
    </div>
  );
}
