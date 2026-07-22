"use client";

import Link from "next/link";
import { useState } from "react";
import AskMarkdown from "@/components/AskMarkdown";
import { askStriops, type AskResponse } from "@/lib/api";

const SUGGESTIONS = [
  "Khayelitsha — what do we know and what’s missing?",
  "How is clinic access trending versus EMS?",
  "Compare dam storage and non-revenue water — what should we do?",
  "What are the top risks driving the penalty?",
];

export default function AskPanel({ compact = false }: { compact?: boolean }) {
  const [question, setQuestion] = useState("");
  const [mode, setMode] = useState<"answer" | "report">("answer");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit(q?: string) {
    const text = (q ?? question).trim();
    if (text.length < 3) return;
    setQuestion(text);
    setBusy(true);
    setError(null);
    try {
      const res = await askStriops(text, mode);
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ask failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={compact ? "" : "card p-5"}>
      {!compact ? (
        <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-[11px] uppercase tracking-[0.2em] text-striops-accent/80">Ask Striops</p>
            <h3 className="mt-1 font-display text-xl font-semibold text-white">
              Natural language → grounded answer
            </h3>
            <p className="mt-1 text-sm text-white/50">
              AI narrates over retrieved facts. Engines own the numbers.
            </p>
          </div>
          <Link href="/ask" className="text-xs text-striops-accent hover:underline">
            Open full ask →
          </Link>
        </div>
      ) : null}

      <div className="flex flex-wrap gap-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => submit(s)}
            className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-left text-[11px] text-white/55 transition hover:border-striops-accent/40 hover:text-white/80"
          >
            {s}
          </button>
        ))}
      </div>

      <div className="mt-4 flex flex-col gap-3 sm:flex-row">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          rows={compact ? 2 : 3}
          placeholder="Ask about risks, water, health access, the score…"
          className="min-h-[3rem] flex-1 rounded-xl border border-white/10 bg-ink-950/60 px-3 py-2 text-sm text-white placeholder:text-white/30 focus:border-striops-accent/50 focus:outline-none"
        />
        <div className="flex shrink-0 flex-col gap-2">
          <div className="flex rounded-full border border-white/10 p-0.5 text-[11px]">
            {(["answer", "report"] as const).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => setMode(m)}
                className={`rounded-full px-3 py-1 capitalize ${
                  mode === m ? "bg-striops-accent/20 text-striops-accent" : "text-white/45"
                }`}
              >
                {m}
              </button>
            ))}
          </div>
          <button
            type="button"
            disabled={busy}
            onClick={() => submit()}
            className="rounded-xl bg-striops-accent px-4 py-2 text-sm font-semibold text-ink-950 disabled:opacity-50"
          >
            {busy ? "Thinking…" : "Ask"}
          </button>
        </div>
      </div>

      {error ? <p className="mt-3 text-sm text-striops-bad">{error}</p> : null}

      {result ? (
        <div className="mt-5 space-y-3 border-t border-white/10 pt-4">
          <AskMarkdown content={result.answer} />
          {result.report_markdown ? (
            <div className="max-h-80 overflow-auto rounded-xl border border-white/10 bg-white/[0.03] p-4">
              <AskMarkdown content={result.report_markdown} />
            </div>
          ) : null}
          {result.data_gaps &&
          result.data_gaps.length > 0 &&
          !/###\s*Gaps/i.test(result.answer) ? (
            <div className="rounded-xl border border-striops-warn/25 bg-striops-warn/5 p-3">
              <p className="text-[11px] uppercase tracking-wide text-striops-warn">Data gaps (not invented)</p>
              <ul className="mt-2 space-y-1.5 text-xs text-white/60">
                {result.data_gaps.map((g) => (
                  <li key={g.sector_id}>
                    <span className="text-white/80">{g.sector_name}:</span> {g.blocker}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          <div className="flex flex-wrap gap-2">
            {result.citations.slice(0, 8).map((c) => (
              <Link
                key={c.href + c.label}
                href={c.href}
                className="rounded-full border border-white/10 px-2.5 py-0.5 text-[11px] text-striops-sky hover:border-striops-sky/40"
              >
                {c.label}
              </Link>
            ))}
          </div>
          <p className="text-[11px] text-white/35">
            {result.ai_role} ·{" "}
            {result.narrator === "deterministic" ? (
              <span className="text-striops-sand/80">
                grounded deterministic brief (Gemini unavailable) · {result.model}
              </span>
            ) : (
              <span>model {result.model}</span>
            )}
          </p>
        </div>
      ) : null}
    </div>
  );
}
