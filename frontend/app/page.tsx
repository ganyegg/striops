import ActionTracker from "@/components/ActionTracker";
import AskPanel from "@/components/AskPanel";
import BriefingBento from "@/components/BriefingBento";
import BudgetSpendChart from "@/components/BudgetSpendChart";
import CriticalSectors from "@/components/CriticalSectors";
import DecisionLog from "@/components/DecisionLog";
import DomainGrid from "@/components/DomainGrid";
import FeedStatusPanel from "@/components/FeedStatusPanel";
import OpportunityCard from "@/components/OpportunityCard";
import PulseStrip from "@/components/PulseStrip";
import RecommendationCard from "@/components/RecommendationCard";
import RiskCard from "@/components/RiskCard";
import SimulationPanel from "@/components/SimulationPanel";
import SiteHeader from "@/components/SiteHeader";
import StorySection from "@/components/StorySection";
import StrategicRead from "@/components/StrategicRead";
import ValueLedgerPanel from "@/components/ValueLedgerPanel";
import WinCard from "@/components/WinCard";
import Link from "next/link";
import {
  formatRefreshSAST,
  formatZAR,
  getActions,
  getBrief,
  getComparatives,
  getDecisions,
  getFeeds,
  getGlossary,
  getMunicipalityDomains,
  getPulse,
  getScenarios,
  getSectors,
  getSnapshot,
  getValueLedger,
  getWins,
  glossaryForRisk,
  type ActionRegister,
  type CityPulse,
  type ComparativesReport,
  type DecisionRegister,
  type DomainSummary,
  type ExecutiveBrief,
  type FeedsReport,
  type GlossaryEntry,
  type Initiative,
  type ScenarioOption,
  type SectorsReport,
  type CitySnapshot,
  type ValueLedger,
} from "@/lib/api";

const MUNICIPALITY = "CPT";

export const dynamic = "force-dynamic";

function BackendDown({ message }: { message: string }) {
  return (
    <main className="mx-auto max-w-3xl px-6 py-24">
      <h1 className="font-display text-2xl font-semibold text-white">Striops is waking up</h1>
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
  let comparatives: ComparativesReport;
  let sectors: SectorsReport;
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
      comparatives,
      sectors,
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
      getComparatives(),
      getSectors(),
    ]);
  } catch (e) {
    return <BackendDown message={e instanceof Error ? e.message : String(e)} />;
  }

  const dataThrough = snapshot.data_through || pulse.data_through || "—";
  const briefRefreshed = formatRefreshSAST(snapshot.brief_refreshed_at || snapshot.generated_at);

  return (
    <main className="pb-24">
      {/* ── Hero (brand + orientation only) ── */}
      <div className="hero-band">
        <div className="hero-band-overlay px-6 pb-10 pt-6">
          <div className="mx-auto max-w-6xl">
            <SiteHeader dataThrough={dataThrough} briefRefreshed={briefRefreshed} />
            <div className="mt-8 max-w-2xl">
              <p className="text-xs font-medium uppercase tracking-[0.28em] text-striops-sand/80">
                {snapshot.greeting}
              </p>
              <p className="mt-2 text-sm text-white/55">
                Cape Town · Health {brief.health_score}/100 · Data through {dataThrough}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-6xl space-y-12 px-6 pt-8">
        {/* ── Command + Simulator (side) ── */}
        <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
          <StorySection
            step="01"
            eyebrow="Start here"
            title="Command centre"
            lead="Strategic health and headline KPIs — each tile opens evidence or a breakdown."
          >
            <BriefingBento
              kpis={snapshot.kpis}
              healthScore={brief.health_score}
              healthNarrative={snapshot.health_narrative || brief.health_narrative}
            />
            <p className="mt-4 text-xs leading-relaxed text-white/38">{snapshot.confidence_note}</p>
          </StorySection>

          <aside className="space-y-4 lg:sticky lg:top-20">
            <SimulationPanel scenarios={scenarios} compact />
            <BudgetSpendChart scenarios={scenarios} compact />
          </aside>
        </div>

        {/* ── Strategic read ── */}
        <StorySection
          step="02"
          eyebrow="Briefing"
          title="Today's strategic read"
          lead="Snapshot, pressure, redeploy, and watch — scannable like Ask Striops."
        >
          <StrategicRead brief={brief} />
        </StorySection>

        {/* ── Critical sectors ── */}
        <StorySection
          id="sectors"
          step="03"
          eyebrow="Mayor spine"
          title="Critical sectors"
          lead="Health, water, safety, housing, energy first — libraries stay secondary. Empty means the data request, not silence."
        >
          <CriticalSectors report={sectors} />
        </StorySection>

        {/* ── City pulse ── */}
        <StorySection
          id="pulse"
          step="04"
          eyebrow="What moved"
          title="City pulse"
          lead={`${pulse.data_through} vs ${pulse.previous_period} — every line opens a metric report.`}
        >
          <PulseStrip pulse={pulse} />
        </StorySection>

        {/* ── Compare ── */}
        <StorySection
          id="compare"
          step="05"
          eyebrow="Contrast to decide"
          title="Headline contrasts"
          lead="Only complementary pairs — dams vs losses, clinics vs EMS. Each opens the full chart."
        >
          <div className="grid gap-4 md:grid-cols-2">
            {comparatives.packs.map((pack) => (
              <Link
                key={pack.id}
                href={`/compare#${pack.id}`}
                className="card group block p-5 transition hover:border-striops-accent/40 hover:shadow-glow"
              >
                <p className="text-[11px] uppercase tracking-[0.16em] text-striops-accent/80">
                  {pack.eyebrow}
                </p>
                <h3 className="mt-1 font-display text-lg font-semibold text-white">{pack.title}</h3>
                <p className="mt-2 line-clamp-2 text-sm text-white/55">{pack.why_it_matters}</p>
                {pack.ratio ? (
                  <p className="mt-3 font-display text-2xl font-semibold text-striops-sand">
                    {pack.ratio.value}
                    <span className="ml-2 font-sans text-xs font-normal text-white/40">
                      {pack.ratio.label}
                    </span>
                  </p>
                ) : (
                  <p className="mt-3 text-xs text-white/40">
                    {pack.series.map((s) => s.label).join(" · ")}
                  </p>
                )}
                <p className="mt-2 text-[11px] text-striops-accent opacity-80 group-hover:opacity-100">
                  Open chart →
                </p>
              </Link>
            ))}
          </div>
          <p className="mt-3 text-xs text-white/35">
            Striops is dynamic — new metrics show up after ingest. Use{" "}
            <strong className="text-white/50">Refresh now</strong> in the header when you need data
            immediately.
          </p>
        </StorySection>

        {/* ── Ask ── */}
        <StorySection
          id="ask"
          step="06"
          eyebrow="Interrogate the twin"
          title="Ask Striops"
          lead="Natural language over retrieved facts. Engines own the numbers; AI writes the answer."
        >
          <AskPanel />
        </StorySection>

        {/* ── Wins ── */}
        <StorySection
          id="wins"
          step="07"
          eyebrow="Momentum first"
          title="What's working"
          lead="Lead with delivery the City can stand on — before the room only hears problems."
          variant="accent"
        >
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {wins.map((w) => (
              <WinCard key={w.id} win={w} />
            ))}
          </div>
        </StorySection>

        {/* ── Risks ── */}
        <StorySection
          id="risks"
          step="08"
          eyebrow="Act before it happens"
          title="Top risks"
          lead="Ranked by score, priced where we can, each with a full drill-down report."
        >
          <div className="grid gap-4 md:grid-cols-2">
            {brief.top_risks.map((r) => (
              <RiskCard key={r.id} risk={r} glossary={glossaryForRisk(r.id, glossary)} />
            ))}
          </div>
        </StorySection>

        {/* ── Opportunities ── */}
        <StorySection
          id="opportunities"
          step="09"
          eyebrow="Value in plain sight"
          title="Opportunities"
          lead="Underspend and efficiency gains you can redeploy this cycle."
        >
          <div className="grid gap-4 md:grid-cols-2">
            {brief.top_opportunities.map((o) => (
              <OpportunityCard key={o.id} opp={o} />
            ))}
          </div>
        </StorySection>

        {/* ── Accountability ── */}
        <div id="act" className="grid scroll-mt-24 gap-14 lg:grid-cols-2 lg:gap-8">
          <StorySection
            step="10"
            eyebrow="Assign & track"
            title="Action tracker"
            lead={`${actions.open_count} open · ${actions.overdue_count} overdue · ${formatZAR(actions.total_expected_impact_zar)} expected on open actions`}
          >
            <ActionTracker register={actions} />
          </StorySection>

          <StorySection
            step="11"
            eyebrow="Prove the ROI"
            title="Value delivered"
            lead="What Striops surfaced → what happened → what it was worth."
          >
            <ValueLedgerPanel ledger={ledger} />
          </StorySection>
        </div>

        {/* ── Decisions ── */}
        <StorySection
          step="12"
          eyebrow="Highest-leverage moves"
          title="Recommended decisions"
          lead="The engine's synthesis — each links to the underlying risk or opportunity."
        >
          <div className="grid gap-4">
            {brief.recommended_decisions.map((rec, i) => (
              <RecommendationCard key={rec.id} rec={rec} index={i} />
            ))}
          </div>
        </StorySection>

        <StorySection
          step="13"
          eyebrow="Institutional memory"
          title="Decision register"
          lead="What was decided, by whom, and when it comes up for review."
          variant="muted"
        >
          <DecisionLog register={decisionRegister} />
        </StorySection>

        {/* ── Domains (simulator moved up) ── */}
        <div id="explore" className="scroll-mt-24">
          <StorySection
            step="14"
            eyebrow="Go deeper"
            title="Domain intelligence"
            lead="Source-linked profiles by directorate — use the simulator above for what-if runs."
          >
            <DomainGrid code={MUNICIPALITY} domains={domains} />
          </StorySection>
        </div>

        {/* ── Trust layer ── */}
        <StorySection
          step="15"
          eyebrow="Nothing to hide"
          title="Sources & reasoning"
          lead="Where every feed stands today — and the agents that merged today's brief."
        >
          <FeedStatusPanel report={feeds} />
          <div className="mt-6 grid gap-3 md:grid-cols-2">
            {brief.agent_contributions
              .filter((c) => c.confidence > 0)
              .map((c) => (
                <div key={c.agent} className="card p-4 transition hover:border-white/20">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold text-white/85">{c.agent}</span>
                    <span className="text-xs text-white/40">{Math.round(c.confidence * 100)}%</span>
                  </div>
                  <p className="mt-1.5 text-sm text-white/60">{c.summary}</p>
                </div>
              ))}
          </div>
        </StorySection>

        <footer className="border-t border-white/10 pt-8 text-xs text-white/35">
          Striops · Strategic Intelligence Operating System · {brief.generated_for} · Data through{" "}
          {dataThrough} · Brief {briefRefreshed}
        </footer>
      </div>
    </main>
  );
}
