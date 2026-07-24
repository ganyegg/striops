import AppPage, { BackendDown } from "@/components/AppPage";
import StrategicRead from "@/components/StrategicRead";
import { getBrief } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function BriefingPage() {
  try {
    const brief = await getBrief();
    return (
      <AppPage
        crumb="Briefing"
        eyebrow="Strategic read"
        title="Today's strategic read"
        lead="Snapshot, pressure, redeploy, and watch — scannable like Ask Striops."
      >
        <StrategicRead brief={brief} />
      </AppPage>
    );
  } catch (e) {
    return <BackendDown message={e instanceof Error ? e.message : String(e)} />;
  }
}
