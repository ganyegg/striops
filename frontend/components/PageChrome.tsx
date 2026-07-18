import Link from "next/link";
import CoctLogo from "./CoctLogo";

export default function PageChrome({
  crumbs,
  backHref = "/",
  backLabel = "← Briefing",
}: {
  crumbs?: React.ReactNode;
  backHref?: string;
  backLabel?: string;
}) {
  return (
    <header className="mb-6 flex flex-wrap items-center justify-between gap-4 text-sm">
      <div className="flex min-w-0 flex-wrap items-center gap-3">
        <CoctLogo height={32} href="/" />
        {crumbs ? (
          <div className="flex min-w-0 flex-wrap items-center gap-2 text-white/50">{crumbs}</div>
        ) : null}
      </div>
      <Link href={backHref} className="text-xs text-striops-accent hover:underline">
        {backLabel}
      </Link>
    </header>
  );
}
