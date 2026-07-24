import AppPage, { BackendDown } from "@/components/AppPage";
import PulseStrip from "@/components/PulseStrip";
import { getPulse } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function PulsePage() {
  try {
    const pulse = await getPulse();
    return (
      <AppPage
        crumb="Pulse"
        eyebrow="What moved"
        title="City pulse"
        lead={`${pulse.data_through} vs ${pulse.previous_period} — live Open Data and national feeds first; demonstration series are labelled.`}
        wide
      >
        <PulseStrip pulse={pulse} />
        {pulse.period_note ? (
          <p className="mt-6 text-xs text-white/40">{pulse.period_note}</p>
        ) : null}
      </AppPage>
    );
  } catch (e) {
    return <BackendDown message={e instanceof Error ? e.message : String(e)} />;
  }
}
