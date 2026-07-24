import AppPage, { BackendDown } from "@/components/AppPage";
import FeedStatusPanel from "@/components/FeedStatusPanel";
import { getBrief, getFeeds } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function SourcesPage() {
  try {
    const [feeds, brief] = await Promise.all([getFeeds(), getBrief()]);
    return (
      <AppPage
        crumb="Sources"
        eyebrow="Nothing to hide"
        title="Sources & reasoning"
        lead="Where every feed stands today — and the agents that merged today's brief."
        wide
      >
        <FeedStatusPanel report={feeds} />
        <div className="mt-8">
          <h2 className="font-display text-xl font-semibold text-white">Agent contributions</h2>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
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
        </div>
      </AppPage>
    );
  } catch (e) {
    return <BackendDown message={e instanceof Error ? e.message : String(e)} />;
  }
}
