import Link from "next/link";
import type { DomainSummary } from "@/lib/api";

export default function DomainTabs({
  code,
  domains,
  active,
}: {
  code: string;
  domains: DomainSummary[];
  active: string;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {domains.map((d) =>
        d.available ? (
          <Link
            key={d.id}
            href={`/${code}/domains/${d.id}`}
            className={`pill border transition ${
              d.id === active
                ? "border-helm-accent/50 bg-helm-accent/10 text-helm-accent"
                : "border-white/10 bg-white/5 text-white/60 hover:text-white/90"
            }`}
          >
            {d.name}
          </Link>
        ) : (
          <span
            key={d.id}
            className="pill border border-white/5 bg-white/[0.02] text-white/25"
            title="On the roadmap"
          >
            {d.name} · soon
          </span>
        ),
      )}
    </div>
  );
}
