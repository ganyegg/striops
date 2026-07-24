import AppPage, { BackendDown } from "@/components/AppPage";
import RiskCard from "@/components/RiskCard";
import { getBrief, getGlossary, glossaryForRisk } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function RisksPage() {
  try {
    const [brief, glossary] = await Promise.all([getBrief(), getGlossary()]);
    return (
      <AppPage
        crumb="Risks"
        eyebrow="Act before it happens"
        title="Top risks"
        lead="Ranked by score, priced where we can, each with a full drill-down report."
        wide
      >
        <div className="grid gap-4 md:grid-cols-2">
          {brief.top_risks.map((r) => (
            <RiskCard key={r.id} risk={r} glossary={glossaryForRisk(r.id, glossary)} />
          ))}
        </div>
      </AppPage>
    );
  } catch (e) {
    return <BackendDown message={e instanceof Error ? e.message : String(e)} />;
  }
}
