import AppPage, { BackendDown } from "@/components/AppPage";
import CriticalSectors from "@/components/CriticalSectors";
import { getSectors } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function SectorsPage() {
  try {
    const sectors = await getSectors();
    return (
      <AppPage
        crumb="Sectors"
        eyebrow="Operating spine"
        title="Critical sectors"
        lead="Health, water, safety, housing, energy first — libraries stay secondary. Empty means the data request, not silence."
        wide
      >
        <CriticalSectors report={sectors} />
      </AppPage>
    );
  } catch (e) {
    return <BackendDown message={e instanceof Error ? e.message : String(e)} />;
  }
}
