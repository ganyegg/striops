import AppPage, { BackendDown } from "@/components/AppPage";
import ActionTracker from "@/components/ActionTracker";
import DecisionLog from "@/components/DecisionLog";
import RecommendationCard from "@/components/RecommendationCard";
import ValueLedgerPanel from "@/components/ValueLedgerPanel";
import { formatZAR, getActions, getBrief, getDecisions, getValueLedger } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ActPage() {
  try {
    const [actions, ledger, brief, decisionRegister] = await Promise.all([
      getActions(),
      getValueLedger(),
      getBrief(),
      getDecisions(),
    ]);
    return (
      <AppPage
        crumb="Actions"
        eyebrow="Assign, decide, prove"
        title="Actions & decisions"
        lead={`${actions.open_count} open · ${actions.overdue_count} overdue · ${formatZAR(actions.total_expected_impact_zar)} expected on open actions`}
        wide
      >
        <div className="grid gap-10 lg:grid-cols-2 lg:gap-8">
          <section>
            <h2 className="font-display text-xl font-semibold text-white">Action tracker</h2>
            <p className="mt-1 text-sm text-white/45">Assign & track</p>
            <div className="mt-4">
              <ActionTracker register={actions} />
            </div>
          </section>
          <section>
            <h2 className="font-display text-xl font-semibold text-white">Value delivered</h2>
            <p className="mt-1 text-sm text-white/45">What Striops surfaced → what happened → worth</p>
            <div className="mt-4">
              <ValueLedgerPanel ledger={ledger} />
            </div>
          </section>
        </div>

        <section className="mt-12">
          <h2 className="font-display text-xl font-semibold text-white">Recommended decisions</h2>
          <p className="mt-1 text-sm text-white/45">Highest-leverage moves — each links to a risk or opportunity</p>
          <div className="mt-4 grid gap-4">
            {brief.recommended_decisions.map((rec, i) => (
              <RecommendationCard key={rec.id} rec={rec} index={i} />
            ))}
          </div>
        </section>

        <section className="mt-12">
          <h2 className="font-display text-xl font-semibold text-white">Decision register</h2>
          <p className="mt-1 text-sm text-white/45">What was decided, by whom, and when it comes up for review</p>
          <div className="mt-4">
            <DecisionLog register={decisionRegister} />
          </div>
        </section>
      </AppPage>
    );
  } catch (e) {
    return <BackendDown message={e instanceof Error ? e.message : String(e)} />;
  }
}
