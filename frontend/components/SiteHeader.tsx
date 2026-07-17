import Link from "next/link";
import CoctLogo from "./CoctLogo";
import RefreshButton from "./RefreshButton";

export default function SiteHeader({
  dataThrough,
  briefRefreshed,
}: {
  dataThrough: string;
  briefRefreshed: string;
}) {
  return (
    <header className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <CoctLogo height={40} href="/" />
        <div className="flex flex-wrap items-center gap-3">
          <p className="text-[11px] uppercase tracking-[0.2em] text-white/40">
            Prepared for the City of Cape Town
          </p>
          <RefreshButton />
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link href="/" className="flex items-center gap-2.5 transition hover:opacity-90">
            <div className="h-3 w-3 rounded-full bg-helm-accent shadow-[0_0_12px_rgba(20,184,166,0.8)]" />
            <span className="font-display text-lg font-semibold tracking-wide text-white">Helm</span>
          </Link>
          <span className="hidden text-sm text-white/40 sm:inline">· Think Ahead</span>
        </div>

        <nav className="hidden items-center gap-1 text-xs md:flex">
          {[
            ["#command", "Brief"],
            ["#sectors", "Sectors"],
            ["#pulse", "Pulse"],
            ["#compare", "Compare"],
            ["#ask", "Ask"],
            ["#wins", "Wins"],
            ["#risks", "Risks"],
            ["#act", "Actions"],
            ["#explore", "Explore"],
          ].map(([href, label]) => (
            <a
              key={href}
              href={href}
              className="rounded-full px-3 py-1.5 text-white/50 transition hover:bg-white/5 hover:text-white/80"
            >
              {label}
            </a>
          ))}
        </nav>

        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="rounded-full border border-helm-accent/30 bg-helm-accent/10 px-3 py-1 text-helm-accent">
            Through {dataThrough}
          </span>
          <span className="hidden rounded-full border border-white/15 bg-white/5 px-3 py-1 text-white/45 sm:inline">
            {briefRefreshed}
          </span>
        </div>
      </div>
    </header>
  );
}
