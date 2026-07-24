import AppPage, { BackendDown } from "@/components/AppPage";
import SimulationPanel from "@/components/SimulationPanel";
import { getScenarios } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function SimulatePage() {
  try {
    const scenarios = await getScenarios();
    return (
      <AppPage
        crumb="Simulate"
        eyebrow="What-if"
        title="Scenario simulator"
        lead="Run budget and service scenarios against the current twin — engines own the arithmetic."
      >
        <SimulationPanel scenarios={scenarios} />
      </AppPage>
    );
  } catch (e) {
    return <BackendDown message={e instanceof Error ? e.message : String(e)} />;
  }
}
