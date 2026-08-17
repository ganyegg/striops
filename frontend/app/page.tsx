import AskPanel from "@/components/AskPanel";
import BriefingBento from "@/components/BriefingBento";
import BudgetSpendChart from "@/components/BudgetSpendChart";
import PulseStrip from "@/components/PulseStrip";
import SimulationPanel from "@/components/SimulationPanel";
import SiteHeader from "@/components/SiteHeader";
import StorySection from "@/components/StorySection";
import Link from "next/link";
import { PRIMARY_NAV } from "@/lib/nav";
import {
  formatRefreshSAST,
  getBrief,
  getPulse,
  getScenarios,
  getSnapshot,
  type CityPulse,
  type CitySnapshot,
  type ExecutiveBrief,
  type ScenarioOption,
} from "@/lib/api";

export const dynamic = "force-dynamic";

function BackendDown({ message }: { message: string }) {
  return (
    <main className="mx-auto max-w-3xl px-6 py-24">
      <h1 className="font-display text-2xl font-semibold text-white">Striops is waking up</h1>
      <p className="mt-3 text-white/60">
        The reasoning core did not answer in time. On the free tier the API sleeps
        after inactivity and takes about a minute to wake — wait a moment and
        refresh. Running locally, start the backend first.
      </p>
      <pre className="mt-4 rounded-lg bg-white/5 p-4 text-xs text-white/50">{message}</pre>
    </main>
  );
}

export default async function Home() {
  let brief: ExecutiveBrief;
  let scenarios: ScenarioOption[];
  let snapshot: CitySnapshot;
  let pulse: CityPulse;
  try {
    [brief, scenarios, snapshot, pulse] = await Promise.all([
      getBrief(),
      getScenarios(),
      getSnapshot(),
      getPulse(),
    ]);
  } catch (e) {
    return <BackendDown message={e instanceof Error ? e.message : String(e)} />;
  }

  const dataThrough = snapshot.data_through || pulse.data_through || "—";
  const briefRefreshed = formatRefreshSAST(snapshot.brief_refreshed_at || snapshot.generated_at);
  // Pulse + Ask stay on the home page — don't duplicate them in the portal grid.
  const portal = PRIMARY_NAV.filter(
    (item) => item.href !== "/" && item.href !== "/pulse" && item.href !== "/ask",
  );

  return (
    <main className="pb-24">
      <div className="hero-band">
        <div className="hero-band-overlay px-6 pb-8 pt-6">
          <div className="mx-auto max-w-6xl">
            <SiteHeader dataThrough={dataThrough} briefRefreshed={briefRefreshed} activeHref="/" />
            <div className="mt-6 max-w-2xl">
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

      <div className="mx-auto max-w-6xl space-y-10 px-6 pt-8">
        <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_380px]">
          <div className="space-y-6">
            <StorySection
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

            <BudgetSpendChart scenarios={scenarios} />
          </div>

          <aside className="lg:sticky lg:top-20 lg:h-[calc(100vh-7rem)]">
            <SimulationPanel scenarios={scenarios} compact />
            <p className="mt-3 text-center text-xs text-white/35">
              <Link href="/simulate" className="text-striops-accent hover:underline">
                Open full simulator →
              </Link>
            </p>
          </aside>
        </div>

        <StorySection
          id="pulse"
          eyebrow="What moved"
          title="City pulse"
          lead={`${pulse.data_through} vs ${pulse.previous_period} — live feeds first; demonstration series are labelled.`}
        >
          <PulseStrip pulse={pulse} />
        </StorySection>

        <StorySection
          id="ask"
          eyebrow="Interrogate the twin"
          title="Ask Striops"
          lead="Natural language over retrieved facts. Engines own the numbers; AI narrates — or a deterministic brief if the narrator is unavailable."
        >
          <AskPanel />
        </StorySection>

        <StorySection
          eyebrow="Navigate"
          title="Open a workspace"
          lead="Themes, risks, sectors, and the rest each have their own page."
        >
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {portal.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="group block border-b border-white/10 py-4 transition hover:border-striops-accent/40"
              >
                <span className="font-display text-lg font-semibold text-white group-hover:text-striops-sand">
                  {item.label}
                </span>
                <span className="mt-1 block text-sm text-white/45">{item.blurb}</span>
              </Link>
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
