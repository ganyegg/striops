export default function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div className="flex items-center gap-2" title={`Confidence ${pct}%`}>
      <span className="text-[11px] uppercase tracking-wide text-white/40">Confidence</span>
      <div className="h-1.5 w-20 overflow-hidden rounded-full bg-white/10">
        <div className="h-full rounded-full bg-striops-accent" style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[11px] tabular-nums text-white/60">{pct}%</span>
    </div>
  );
}
