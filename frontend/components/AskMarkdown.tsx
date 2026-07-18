"use client";

type BriefSection = {
  heading: string;
  paragraphs: string[];
  bullets: string[];
};

/** Repair Gemini answers that omit newlines between headings/bullets. */
export function normalizeAskMarkdown(text: string): string {
  let t = (text || "").replace(/\r\n/g, "\n").replace(/\r/g, "\n").trim();
  if (!t) return t;

  t = t.replace(/\s*(###\s+)/g, "\n\n$1");
  t = t.replace(/\s+([*•]\s+\*\*)/g, "\n- **");
  t = t.replace(/\s+(-\s+\*\*)/g, "\n- **");
  t = t.replace(/([^\n])\s+([*•]\s+)/g, "$1\n- ");
  t = t.replace(/([^\n])\s+(-\s+)(?!\*)/g, "$1\n- ");
  t = t.replace(/^\s+/, "");

  for (const name of ["Snapshot", "Evidence(?:\\s*\\([^)]*\\))?", "Watch(?:\\s*\\([^)]*\\))?", "Gaps"]) {
    t = t.replace(new RegExp(`(###\\s+${name})\\s+(?=[A-Za-z0-9*•\\-])`, "i"), "$1\n\n");
  }

  t = t.replace(/^[*•]\s+/gm, "- ");
  t = t.replace(/\n{3,}/g, "\n\n");
  return t.trim();
}

function stripInlineMd(s: string): string {
  return s.replace(/\*\*/g, "").trim();
}

function parseSections(raw: string): BriefSection[] {
  const md = normalizeAskMarkdown(raw);
  if (!md.includes("###")) {
    const lines = md
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean);
    const bullets = lines.filter((l) => /^[-*•]\s+/.test(l)).map((l) => l.replace(/^[-*•]\s+/, ""));
    const paragraphs = lines.filter((l) => !/^[-*•]\s+/.test(l));
    return [{ heading: "Answer", paragraphs, bullets }];
  }

  const chunks = md.split(/^###\s+/m).filter(Boolean);
  return chunks.map((chunk) => {
    const lines = chunk.split("\n").map((l) => l.trimEnd());
    const heading = stripInlineMd(lines[0] || "Section");
    const paragraphs: string[] = [];
    const bullets: string[] = [];
    for (const line of lines.slice(1)) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      if (/^[-*•]\s+/.test(trimmed)) {
        bullets.push(trimmed.replace(/^[-*•]\s+/, ""));
      } else {
        paragraphs.push(trimmed);
      }
    }
    return { heading, paragraphs, bullets };
  });
}

function RichLine({ text }: { text: string }) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith("**") && part.endsWith("**")) {
          return (
            <strong key={i} className="font-semibold text-white">
              {part.slice(2, -2)}
            </strong>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </>
  );
}

/** Sectioned Ask brief — survives smashed single-line Gemini markdown. */
export default function AskMarkdown({ content }: { content: string }) {
  const sections = parseSections(content);

  return (
    <div className="ask-brief space-y-3">
      {sections.map((section) => (
        <section
          key={section.heading}
          className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3"
        >
          <h3 className="font-display text-[12px] font-semibold uppercase tracking-[0.16em] text-striops-sand">
            {section.heading}
          </h3>
          {section.paragraphs.length > 0 ? (
            <div className="mt-2 space-y-2">
              {section.paragraphs.map((p, i) => (
                <p key={i} className="text-sm leading-relaxed text-white/75">
                  <RichLine text={p} />
                </p>
              ))}
            </div>
          ) : null}
          {section.bullets.length > 0 ? (
            <ul className="mt-2.5 space-y-2">
              {section.bullets.map((b, i) => (
                <li
                  key={i}
                  className="relative pl-3.5 text-sm leading-relaxed text-white/75 before:absolute before:left-0 before:top-[0.55em] before:h-1.5 before:w-1.5 before:rounded-full before:bg-striops-accent"
                >
                  <RichLine text={b} />
                </li>
              ))}
            </ul>
          ) : null}
        </section>
      ))}
    </div>
  );
}
