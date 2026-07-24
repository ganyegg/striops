import AppPage, { BackendDown } from "@/components/AppPage";
import WinCard from "@/components/WinCard";
import { getWins } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function WinsPage() {
  try {
    const wins = await getWins();
    return (
      <AppPage
        crumb="Wins"
        eyebrow="Momentum first"
        title="What's working"
        lead="Lead with delivery the City can stand on — before the room only hears problems."
        wide
      >
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {wins.map((w) => (
            <WinCard key={w.id} win={w} />
          ))}
        </div>
      </AppPage>
    );
  } catch (e) {
    return <BackendDown message={e instanceof Error ? e.message : String(e)} />;
  }
}
