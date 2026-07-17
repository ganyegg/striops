import HealthGauge from "@/components/HealthGauge";
import OpportunityCard from "@/components/OpportunityCard";
import RecommendationCard from "@/components/RecommendationCard";
import RiskCard from "@/components/RiskCard";
import Section from "@/components/Section";
import SimulationPanel from "@/components/SimulationPanel";
import {
  getBrief,
  getScenarios,
  type ExecutiveBrief,
  type ScenarioOption,
} from "@/lib/api";

// The brief is generated live; never cache.
export const dynamic = "force-dynamic";

function BackendDown({ message }: { message: string }) {
  return (
    <main className="mx-auto max-w-3xl px-6 py-24">
      <h1 className="text-2xl font-semibold text-white/90">Helm AI is waking up</h1>
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
  try {
    [brief, scenarios] = await Promise.all([getBrief(), getScenarios()]);
  } catch (e) {
    return <BackendDown message={e instanceof Error ? e.message : String(e)} />;
  }

  return (
    <main className="mx-auto max-w-6xl px-6 py-12">
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-2.5 w-2.5 rounded-full bg-helm-accent" />
          <span className="text-sm font-semibold tracking-wide text-white/80">HELM AI</span>
          <span className="text-sm text-white/30">· Think Ahead</span>
        </div>
        <span className="text-xs text-white/40">
          Overall confidence {Math.round(brief.confidence * 100)}%
        </span>
      </header>

      <div className="mt-10 grid items-center gap-8 md:grid-cols-[1fr_320px]">
        <div>
          <h1 className="text-4xl font-semibold tracking-tight text-white md:text-5xl">
            {brief.greeting}
          </h1>
          <p className="mt-4 max-w-2xl text-lg leading-relaxed text-white/70">
            {brief.strategic_summary}
          </p>
          <p className="mt-3 max-w-2xl text-sm text-white/45">{brief.health_narrative}</p>
        </div>
        <div className="card p-4">
          <HealthGauge score={brief.health_score} />
        </div>
      </div>

      {brief.emerging_trends.length ? (
        <div className="mt-8 flex flex-wrap gap-2">
          {brief.emerging_trends.map((t, i) => (
            <span key={i} className="pill bg-white/5 text-white/60">
              {t}
            </span>
          ))}
        </div>
      ) : null}

      <Section eyebrow="Act before it happens" title="Today's Top Risks">
        <div className="grid gap-4 md:grid-cols-2">
          {brief.top_risks.map((r) => (
            <RiskCard key={r.id} risk={r} />
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

      <Section eyebrow="The highest-leverage moves" title="Recommended Decisions">
        <div className="grid gap-4">
          {brief.recommended_decisions.map((rec, i) => (
            <RecommendationCard key={rec.id} rec={rec} index={i} />
          ))}
        </div>
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

      <footer className="mt-16 border-t border-white/5 pt-6 text-xs text-white/30">
        Helm AI · Strategic Intelligence Operating System · Serving {brief.generated_for}
      </footer>
    </main>
  );
}
