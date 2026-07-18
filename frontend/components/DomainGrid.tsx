import Link from "next/link";
import type { DomainSummary } from "@/lib/api";

function VerifiedBar({ share }: { share: number }) {
  const pct = Math.round(share * 100);
  return (
    <div className="mt-3 flex items-center gap-2">
      <div className="h-1 w-16 overflow-hidden rounded-full bg-white/10">
        <div className="h-full rounded-full bg-striops-good" style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[10px] text-white/40">{pct}% verified</span>
    </div>
  );
}

export default function DomainGrid({
  code,
  domains,
}: {
  code: string;
  domains: DomainSummary[];
}) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {domains.map((d) => {
        const inner = (
          <>
            <div className="flex items-start justify-between gap-2">
              <h3 className="text-[15px] font-semibold text-white/90">{d.name}</h3>
              {!d.available ? (
                <span className="pill bg-white/5 text-white/30">soon</span>
              ) : (
                <span className="text-white/25">↗</span>
              )}
            </div>
            <p className="mt-1 text-xs leading-relaxed text-white/45">
              {d.summary ?? d.description}
            </p>
            {d.available ? (
              <>
                <p className="mt-2 text-[11px] text-white/35">{d.indicator_count} indicators</p>
                <VerifiedBar share={d.verified_share} />
              </>
            ) : null}
          </>
        );
        return d.available ? (
          <Link
            key={d.id}
            href={`/${code}/domains/${d.id}`}
            className="card p-4 transition hover:border-striops-accent/30 hover:bg-white/[0.05]"
          >
            {inner}
          </Link>
        ) : (
          <div key={d.id} className="card p-4 opacity-60">
            {inner}
          </div>
        );
      })}
    </div>
  );
}
