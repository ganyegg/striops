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
    <header className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <CoctLogo height={40} href="/" />
        <div className="flex flex-wrap items-center gap-3">
          <p className="text-[11px] uppercase tracking-[0.2em] text-white/40">
            Prepared for the City of Cape Town
          </p>
          <RefreshButton />
        </div>
      </div>

      <div className="flex flex-wrap items-end justify-between gap-6">
        <Link href="/" className="group flex items-start gap-3.5 transition hover:opacity-95">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/brand/striops-logo.svg"
            alt=""
            className="mt-0.5 h-14 w-14 shrink-0 drop-shadow-[0_0_18px_rgba(20,184,166,0.35)] md:h-16 md:w-16"
          />
          <span className="min-w-0">
            <span className="block font-display text-3xl font-semibold tracking-tight text-white md:text-4xl">
              Striops
            </span>
            <span className="mt-1 block text-base font-medium tracking-wide text-striops-sand/90 md:text-lg">
              Trusted with foresight
            </span>
            <span className="mt-1.5 block text-[11px] uppercase tracking-[0.18em] text-white/35">
              Strategic Intelligence Operating System
            </span>
          </span>
        </Link>

        <div className="flex flex-col items-end gap-3">
          <nav className="hidden items-center gap-1 text-xs md:flex">
            {[
              ["#command", "Brief"],
              ["#ask", "Ask"],
              ["#sectors", "Sectors"],
              ["#pulse", "Pulse"],
              ["#compare", "Compare"],
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
          <div className="flex flex-wrap items-center justify-end gap-2 text-xs">
            <span className="rounded-full border border-striops-accent/30 bg-striops-accent/10 px-3 py-1 text-striops-accent">
              Through {dataThrough}
            </span>
            <span className="hidden rounded-full border border-white/15 bg-white/5 px-3 py-1 text-white/45 sm:inline">
              {briefRefreshed}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
