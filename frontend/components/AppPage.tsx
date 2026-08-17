import Link from "next/link";
import PageChrome from "@/components/PageChrome";

/** Shared chrome for secondary app pages (title + breadcrumbs). */
export default function AppPage({
  crumb,
  eyebrow,
  title,
  lead,
  children,
  wide = false,
}: {
  crumb: string;
  eyebrow?: string;
  title: string;
  lead?: string;
  children: React.ReactNode;
  wide?: boolean;
}) {
  return (
    <main className={`mx-auto px-6 py-10 pb-24 ${wide ? "max-w-6xl" : "max-w-5xl"}`}>
      <PageChrome
        crumbs={
          <>
            <Link href="/" className="font-display font-semibold text-white/80 hover:text-white">
              Striops
            </Link>
            <span className="text-white/25">/</span>
            <span className="text-white/80">{crumb}</span>
          </>
        }
        backLabel="← Command"
      />

      <div className="mt-6 mb-8">
        {eyebrow ? (
          <p className="text-xs uppercase tracking-[0.22em] text-white/35">{eyebrow}</p>
        ) : null}
        <h1 className="mt-1 font-display text-3xl font-semibold text-white">{title}</h1>
        {lead ? <p className="mt-2 max-w-2xl text-sm text-white/55">{lead}</p> : null}
      </div>

      {children}
    </main>
  );
}

export function BackendDown({ message }: { message: string }) {
  return (
    <main className="mx-auto max-w-3xl px-6 py-24">
      <Link href="/" className="text-sm text-striops-accent hover:underline">
        ← Command
      </Link>
      <h1 className="mt-6 font-display text-2xl font-semibold text-white">Striops is waking up</h1>
      <p className="mt-3 text-white/60">
        The reasoning core did not answer in time. On the free tier the API sleeps
        after inactivity and takes about a minute to wake — wait a moment and
        refresh. Running locally, start the backend first.
      </p>
      <pre className="mt-4 rounded-lg bg-white/5 p-4 text-xs text-white/50">{message}</pre>
    </main>
  );
}
