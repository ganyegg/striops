import AppPage from "@/components/AppPage";
import AskPanel from "@/components/AskPanel";

export const dynamic = "force-dynamic";

export default function AskPage() {
  return (
    <AppPage
      crumb="Ask"
      eyebrow="Natural language"
      title="Ask Striops"
      lead="Ask a question or generate a short report. Answers are grounded in the current brief, pulse, health breakdown, comparatives, and metric facts — not invented."
    >
      <AskPanel />

      <section className="mt-8 border-t border-white/10 pt-6">
        <h2 className="font-display text-lg font-semibold text-white">How Striops uses AI</h2>
        <ul className="mt-3 space-y-2 text-sm text-white/60">
          <li>
            <strong className="text-white/80">Engines</strong> — scores, forecasts, risk ranks,
            valuation, health formula. Deterministic and auditable.
          </li>
          <li>
            <strong className="text-white/80">Gemini narration</strong> — strategic summary and health
            one-liner on the morning brief.
          </li>
          <li>
            <strong className="text-white/80">Ask Striops</strong> — retrieves those facts, then asks
            the model to answer or write a note. Citations link back to reports.
          </li>
        </ul>
      </section>
    </AppPage>
  );
}
