import type { Recommendation } from "@/lib/api";
import { priorityColor } from "@/lib/api";
import ConfidenceBar from "./ConfidenceBar";

export default function RecommendationCard({
  rec,
  index,
}: {
  rec: Recommendation;
  index: number;
}) {
  return (
    <div className="card flex gap-4 p-5">
      <div className="flex h-8 w-8 flex-none items-center justify-center rounded-full bg-helm-gold/15 text-sm font-bold text-helm-gold">
        {index + 1}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-3">
          <h3 className="text-[15px] font-semibold text-white/90">{rec.title}</h3>
          <span className={`pill ${priorityColor(rec.priority)}`}>{rec.priority}</span>
        </div>
        <p className="mt-2 text-sm leading-relaxed text-white/60">{rec.rationale}</p>
        <p className="mt-2 text-sm text-white/50">
          <span className="text-helm-gold">Expected impact: </span>
          {rec.expected_impact}
        </p>
        <div className="mt-3">
          <ConfidenceBar value={rec.confidence} />
        </div>
      </div>
    </div>
  );
}
