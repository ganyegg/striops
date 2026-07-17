import type { ExecutiveBrief } from "@/lib/api";
import { formatZAR } from "@/lib/api";

function firstSentences(text: string, n = 2): string {
  const parts = text
    .replace(/\s+/g, " ")
    .trim()
    .split(/(?<=[.!?])\s+/)
    .filter(Boolean);
  return parts.slice(0, n).join(" ");
}

type Block = {
  title: string;
  tone: "accent" | "warn" | "good" | "neutral";
  lines: string[];
};

export default function StrategicRead({ brief }: { brief: ExecutiveBrief }) {
  const snapshot = firstSentences(brief.strategic_summary || brief.health_narrative || "", 2);
  const blocks: Block[] = (
    [
      {
        title: "Snapshot",
        tone: "accent" as const,
        lines: [
          snapshot || `Strategic health ${brief.health_score}/100 for ${brief.generated_for}.`,
          brief.health_narrative ? firstSentences(brief.health_narrative, 1) : "",
        ].filter(Boolean),
      },
      {
        title: "Pressure",
        tone: "warn" as const,
        lines: brief.top_risks.slice(0, 3).map((r) => {
          const cost = r.cost_estimate?.amount_zar
            ? ` · ${formatZAR(r.cost_estimate.amount_zar)}`
            : "";
          return `${r.title} (score ${r.score}${cost})`;
        }),
      },
      {
        title: "Redeploy",
        tone: "good" as const,
        lines: brief.top_opportunities.slice(0, 3).map((o) => {
          const val = o.value_estimate != null ? ` · ${formatZAR(o.value_estimate)}` : "";
          return `${o.title}${val}`;
        }),
      },
      {
        title: "Watch",
        tone: "neutral" as const,
        lines: (brief.emerging_trends || []).slice(0, 3),
      },
    ] satisfies Block[]
  ).filter((b) => b.lines.length > 0);

  const toneBorder: Record<Block["tone"], string> = {
    accent: "border-helm-accent/30",
    warn: "border-helm-warn/25",
    good: "border-helm-good/25",
    neutral: "border-white/10",
  };
  const toneLabel: Record<Block["tone"], string> = {
    accent: "text-helm-accent/85",
    warn: "text-helm-warn/90",
    good: "text-helm-good/90",
    neutral: "text-helm-sand/80",
  };

  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <p className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-[11px] text-white/45">
          Confidence {Math.round((brief.confidence || 0) * 100)}%
        </p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        {blocks.map((b) => (
          <section
            key={b.title}
            className={`rounded-xl border bg-white/[0.03] px-4 py-3 ${toneBorder[b.tone]}`}
          >
            <h3
              className={`font-display text-[12px] font-semibold uppercase tracking-[0.16em] ${toneLabel[b.tone]}`}
            >
              {b.title}
            </h3>
            <ul className="mt-2.5 space-y-2">
              {b.lines.map((line, i) => (
                <li
                  key={i}
                  className="relative pl-3.5 text-sm leading-relaxed text-white/75 before:absolute before:left-0 before:top-[0.55em] before:h-1.5 before:w-1.5 before:rounded-full before:bg-helm-accent/80"
                >
                  {line}
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </div>
  );
}
