import Link from "next/link";
import AskPanel from "@/components/AskPanel";
import PageChrome from "@/components/PageChrome";

export const dynamic = "force-dynamic";

export default function AskPage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-10 pb-24">
      <PageChrome
        crumbs={
          <>
            <Link href="/" className="font-display font-semibold text-white/80 hover:text-white">
              Helm
            </Link>
            <span className="text-white/25">/</span>
            <span className="text-white/80">Ask</span>
          </>
        }
      />

      <div className="mt-6 mb-8">
        <p className="text-xs uppercase tracking-[0.22em] text-white/35">Natural language</p>
        <h1 className="mt-1 font-display text-3xl font-semibold text-white">Ask Helm</h1>
        <p className="mt-2 text-sm text-white/55">
          Ask a question or generate a short report. Answers are grounded in the current brief,
          pulse, health breakdown, comparatives, and metric facts — not invented.
        </p>
      </div>

      <AskPanel />

      <section className="card mt-8 p-5">
        <h2 className="font-display text-lg font-semibold text-white">How Helm uses AI</h2>
        <ul className="mt-3 space-y-2 text-sm text-white/60">
          <li>
            <strong className="text-white/80">Engines</strong> — scores, forecasts, risk ranks,
            valuation, health formula. Deterministic and auditable.
          </li>
          <li>
            <strong className="text-white/80">Gemini narration</strong> — strategic summary and
            health one-liner on the morning brief.
          </li>
          <li>
            <strong className="text-white/80">Ask Helm</strong> — retrieves those facts, then asks
            the model to answer or write a note. Citations link back to reports.
          </li>
        </ul>
        <p className="mt-4 text-xs text-white/40">
          The system is dynamic: new series and domains appear after ingest. Use{" "}
          <strong className="text-white/55">Refresh now</strong> in the header when you need data
          immediately.
        </p>
      </section>
    </main>
  );
}
