import fs from "fs";
import path from "path";
import Link from "next/link";
import CoctLogo from "@/components/CoctLogo";
import KnowledgeMarkdown from "@/components/KnowledgeMarkdown";

export const dynamic = "force-dynamic";

const SECTIONS = [
  { id: "1-product-definition", label: "Product" },
  { id: "2-how-the-reasoning-works", label: "Reasoning" },
  { id: "3-data-current-state-and-connection-map", label: "Data" },
  { id: "4-architecture-hosting-security-popia", label: "Architecture" },
  { id: "5-accountability-layer-v03", label: "Accountability" },
  { id: "6-the-90-day-pilot-playbook", label: "Pilot" },
  { id: "7-why-r180000-is-justified--the-real-case", label: "R180k case" },
  { id: "8-pricing-and-commercial-model", label: "Pricing" },
  { id: "10-objection-handling--faq", label: "FAQ" },
];

function loadHelmDoc(): string {
  const docPath = path.join(process.cwd(), "..", "docs", "HELM.md");
  return fs.readFileSync(docPath, "utf-8");
}

export default function KnowledgePage() {
  const content = loadHelmDoc();

  return (
    <main className="min-h-screen pb-20">
      <div className="border-b border-white/10 bg-ink-950/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-4">
          <div className="flex min-w-0 flex-wrap items-start gap-4">
            <CoctLogo height={40} href="/" />
            <div>
              <Link href="/" className="text-xs text-helm-accent hover:underline">
                ← Back to briefing
              </Link>
              <h1 className="mt-1 font-display text-2xl font-semibold text-white">Helm Knowledge Base</h1>
              <p className="text-sm text-white/45">
                Product, data, pilot, security — City of Cape Town reference.
              </p>
            </div>
          </div>
          <a
            href="https://github.com/ganyegg/helm/blob/main/docs/HELM.md"
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-full border border-white/15 px-4 py-2 text-xs text-white/55 hover:border-helm-accent/40 hover:text-helm-accent"
          >
            View on GitHub
          </a>
        </div>
      </div>

      <div className="mx-auto grid max-w-6xl gap-10 px-6 pt-8 lg:grid-cols-[220px_1fr]">
        <aside className="hidden lg:block">
          <nav className="sticky top-8 space-y-1 text-sm">
            <p className="mb-3 text-[10px] uppercase tracking-[0.2em] text-white/35">Jump to</p>
            {SECTIONS.map((s) => (
              <a
                key={s.id}
                href={`#${s.id}`}
                className="block rounded-lg px-3 py-2 text-white/50 transition hover:bg-white/5 hover:text-white/85"
              >
                {s.label}
              </a>
            ))}
          </nav>
        </aside>
        <KnowledgeMarkdown content={content} />
      </div>
    </main>
  );
}
