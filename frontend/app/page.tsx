import ActionTracker from "@/components/ActionTracker";
import DecisionLog from "@/components/DecisionLog";
import DomainGrid from "@/components/DomainGrid";
import FeedStatusPanel from "@/components/FeedStatusPanel";
import HeroKPIStrip from "@/components/HeroKPIStrip";
import OpportunityCard from "@/components/OpportunityCard";
import PulseStrip from "@/components/PulseStrip";
import RecommendationCard from "@/components/RecommendationCard";
import RiskCard from "@/components/RiskCard";
import Section from "@/components/Section";
import SimulationPanel from "@/components/SimulationPanel";
import ValueLedgerPanel from "@/components/ValueLedgerPanel";
import WinCard from "@/components/WinCard";
import {
  formatRefreshSAST,
  getActions,
  getBrief,
  getDecisions,
  getFeeds,
  getGlossary,
  getMunicipalityDomains,
  getPulse,
  getScenarios,
  getSnapshot,
  getValueLedger,
  getWins,
  glossaryForRisk,
  type ActionRegister,
  type CityPulse,
  type DecisionRegister,
  type DomainSummary,
  type ExecutiveBrief,
  type FeedsReport,
  type GlossaryEntry,
  type Initiative,
  type ScenarioOption,
  type CitySnapshot,
  type ValueLedger,
} from "@/lib/api";

const MUNICIPALITY = "CPT";

export const dynamic = "force-dynamic";

function BackendDown({ message }: { message: string }) {
  return (
    <main className="mx-auto max-w-3xl px-6 py-24">
      <h1 className="font-display text-2xl font-semibold text-white">Helm is waking up</h1>
      <p className="mt-3 text-white/60">
        The reasoning core is not reachable yet. Start the backend and refresh.
      </p>
      <pre className="mt-4 rounded-lg bg-white/5 p-4 text-xs text-white/50">{message}</pre>
    </main>
  );
}

export default async function Home() {
  let brief: ExecutiveBrief;
  let scenarios: ScenarioOption[];
  let domains: DomainSummary[];
  let snapshot: CitySnapshot;
  let wins: Initiative[];
  let glossary: Record<string, GlossaryEntry>;
  let pulse: CityPulse;
  let decisionRegister: DecisionRegister;
  let feeds: FeedsReport;
  let actions: ActionRegister;
  let ledger: ValueLedger;
  try {
    [
      brief,
      scenarios,
      domains,
      snapshot,
      wins,
      glossary,
      pulse,
      decisionRegister,
      feeds,
      actions,
      ledger,
    ] = await Promise.all([
      getBrief(),
      getScenarios(),
      getMunicipalityDomains(MUNICIPALITY),
      getSnapshot(),
      getWins(),
      getGlossary(),
      getPulse(),
      getDecisions(),
      getFeeds(),
      getActions(),
      getValueLedger(),
    ]);
  } catch (e) {
    return <BackendDown message={e instanceof Error ? e.message : String(e)} />;
  }

  const dataThrough = snapshot.data_through || pulse.data_through || "—";
  const briefRefreshed = formatRefreshSAST(snapshot.brief_refreshed_at || snapshot.generated_at);

  return (
    <main className="pb-16">
      <div className="hero-band">
        <div className="hero-band-overlay px-6 pb-12 pt-8">
          <div className="mx-auto max-w-6xl">
            <header className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <div className="h-3 w-3 rounded-full bg-helm-accent shadow-[0_0_12px_rgba(20,184,166,0.8)]" />
                <span className="font-display text-lg font-semibold tracking-wide text-white">
                  Helm
                </span>
                <span className="hidden text-sm text-white/45 sm:inline">· Think Ahead</span>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-full border border-white/15 bg-white/5 px-3 py-1 text-xs text-white/60">
                  City of Cape Town · live briefing
                </span>
                <span className="rounded-full border border-helm-accent/30 bg-helm-accent/10 px-3 py-1 text-xs text-helm-accent">
                  Data through {dataThrough}
                </span>
                <span className="rounded-full border border-white/15 bg-white/5 px-3 py-1 text-xs text-white/50">
                  Brief refreshed {briefRefreshed}
                </span>
              </div>
            </header>

            <div className="mt-12 max-w-3xl">
              <p className="text-xs font-medium uppercase tracking-[0.28em] text-helm-sand/80">
                Executive briefing
              </p>
              <h1 className="mt-2 font-display text-4xl font-semibold tracking-tight text-white md:text-5xl lg:text-6xl">
                {snapshot.greeting}
              </h1>
              <p className="mt-3 max-w-xl text-lg text-helm-sand/90">{snapshot.tagline}</p>
              <p className="mt-4 max-w-2xl text-[15px] leading-relaxed text-white/75">
                {brief.strategic_summary}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-6xl px-6">
        <section className="-mt-6">
          <p className="mb-3 text-xs font-medium uppercase tracking-[0.22em] text-white/40">
            City health at a glance
          </p>
          <HeroKPIStrip
            kpis={snapshot.kpis}
            healthScore={brief.health_score}
            healthNarrative={snapshot.health_narrative || brief.health_narrative}
          />
          <p className="mt-4 text-xs leading-relaxed text-white/40">{snapshot.confidence_note}</p>
        </section>

        <section className="mt-10">
          <PulseStrip pulse={pulse} />
        </section>

        <Section eyebrow="What is working" title="Today's Wins & Initiatives">
          <p className="-mt-2 mb-5 max-w-2xl text-sm text-white/55">
            Delivery the City can stand on — with plain language, source links, and open reports.
            Celebrate these before the room only hears problems.
          </p>
          <div id="wins" className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {wins.map((w) => (
              <WinCard key={w.id} win={w} />
            ))}
          </div>
        </Section>

        <Section eyebrow="Act before it happens" title="Today's Top Risks">
          <p className="-mt-2 mb-5 max-w-2xl text-sm text-white/55">
            Each risk opens a full report: trend chart, score breakdown, estimated annual cost, and
            references you can defend in the room.
          </p>
          <div id="risks" className="grid gap-4 md:grid-cols-2">
            {brief.top_risks.map((r) => (
              <RiskCard key={r.id} risk={r} glossary={glossaryForRisk(r.id, glossary)} />
            ))}
          </div>
        </Section>

        <Section eyebrow="Value hiding in plain sight" title="Today's Top Opportunities">
          <div className="grid gap-4 md:grid-cols-2">
            {brief.top_opportunities.map((o) => (
              <OpportunityCard key={o.id} opp={o} />
            ))}
          </div>
        </Section>

        <Section eyebrow="Who does what, by when" title="Action Tracker">
          <ActionTracker register={actions} />
        </Section>

        <Section eyebrow="The highest-leverage moves" title="Recommended Decisions">
          <div className="grid gap-4">
            {brief.recommended_decisions.map((rec, i) => (
              <RecommendationCard key={rec.id} rec={rec} index={i} />
            ))}
          </div>
        </Section>

        <Section eyebrow="What Helm surfaced → what ensued" title="Value Delivered">
          <p className="-mt-2 mb-5 max-w-2xl text-sm text-white/55">
            The renewal artifact: every insight Helm raised, the action that followed, and the rand
            value — labelled projected, realised, or avoided cost so the claim survives scrutiny.
          </p>
          <ValueLedgerPanel ledger={ledger} />
        </Section>

        <Section eyebrow="Institutional memory" title="Decision Register">
          <p className="-mt-2 mb-5 max-w-2xl text-sm text-white/55">
            What was decided, by whom, and when it comes up for review — linked to the risk or win
            it addresses. This is the memory that survives elections and staff turnover.
          </p>
          <DecisionLog register={decisionRegister} />
        </Section>

        <Section eyebrow="Verifiable, source-linked intelligence" title="Deep Dive by Domain">
          <DomainGrid code={MUNICIPALITY} domains={domains} />
        </Section>

        <Section eyebrow="What happens if…" title="Decision Simulator">
          <SimulationPanel scenarios={scenarios} />
        </Section>

        <Section eyebrow="Independent reasoning, merged" title="Agent Briefing">
          <div className="grid gap-3 md:grid-cols-2">
            {brief.agent_contributions
              .filter((c) => c.confidence > 0)
              .map((c) => (
                <div key={c.agent} className="card p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold text-white/85">{c.agent}</span>
                    <span className="text-xs text-white/40">
                      {Math.round(c.confidence * 100)}%
                    </span>
                  </div>
                  <p className="mt-1.5 text-sm text-white/60">{c.summary}</p>
                </div>
              ))}
          </div>
        </Section>

        <Section eyebrow="Nothing to hide" title="Where the Numbers Come From">
          <FeedStatusPanel report={feeds} />
        </Section>

        <footer className="mt-16 border-t border-white/10 pt-6 text-xs text-white/35">
          Helm · Strategic Intelligence Operating System · Serving {brief.generated_for}. Data
          through {dataThrough}. Brief refreshed {briefRefreshed}. Images on win cards are
          illustrative (Unsplash); every number links to a public City / Treasury / SAPS / DWS
          source in its report.
        </footer>
      </div>
    </main>
  );
}
