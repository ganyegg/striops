import AppPage, { BackendDown } from "@/components/AppPage";
import OpportunityCard from "@/components/OpportunityCard";
import { getBrief } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function OpportunitiesPage() {
  try {
    const brief = await getBrief();
    return (
      <AppPage
        crumb="Opportunities"
        eyebrow="Value in plain sight"
        title="Opportunities"
        lead="Underspend and efficiency gains you can redeploy this cycle."
        wide
      >
        <div className="grid gap-4 md:grid-cols-2">
          {brief.top_opportunities.map((o) => (
            <OpportunityCard key={o.id} opp={o} />
          ))}
        </div>
      </AppPage>
    );
  } catch (e) {
    return <BackendDown message={e instanceof Error ? e.message : String(e)} />;
  }
}
