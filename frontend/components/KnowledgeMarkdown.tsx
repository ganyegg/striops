"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Link from "next/link";

export default function KnowledgeMarkdown({ content }: { content: string }) {
  return (
    <article className="knowledge-prose">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h1 className="mb-6 font-display text-4xl font-semibold text-white">{children}</h1>
          ),
          h2: ({ children }) => {
            const text = String(children);
            const id = text
              .toLowerCase()
              .replace(/[^\w\s-]/g, "")
              .replace(/\s+/g, "-")
              .replace(/^(\d)-/, "$1-");
            return (
              <h2
                id={id}
                className="mb-4 mt-12 scroll-mt-24 border-t border-white/10 pt-10 font-display text-2xl font-semibold text-white first:mt-0 first:border-0 first:pt-0"
              >
                {children}
              </h2>
            );
          },
          h3: ({ children }) => (
            <h3 className="mb-3 mt-8 font-display text-xl font-semibold text-helm-sand">{children}</h3>
          ),
          p: ({ children }) => (
            <p className="mb-4 text-[15px] leading-relaxed text-white/70">{children}</p>
          ),
          ul: ({ children }) => (
            <ul className="mb-4 list-none space-y-2 pl-0 text-white/70">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="mb-4 list-decimal space-y-2 pl-6 text-white/70">{children}</ol>
          ),
          li: ({ children }) => (
            <li className="relative pl-4 text-[15px] leading-relaxed before:absolute before:left-0 before:text-helm-accent before:content-['—']">
              {children}
            </li>
          ),
          strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
          a: ({ href, children }) => {
            const external = href?.startsWith("http");
            if (external) {
              return (
                <a
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-helm-accent underline decoration-helm-accent/40 underline-offset-2 hover:decoration-helm-accent"
                >
                  {children}
                </a>
              );
            }
            return (
              <Link href={href || "#"} className="text-helm-accent hover:underline">
                {children}
              </Link>
            );
          },
          code: ({ className, children }) => {
            const isBlock = className?.includes("language-");
            if (isBlock) {
              const lang = className?.replace("language-", "") || "";
              if (lang === "mermaid") {
                return (
                  <pre className="mb-4 overflow-x-auto rounded-xl border border-helm-accent/20 bg-ink-950/80 p-4 text-xs leading-relaxed text-helm-sand/80">
                    <span className="mb-2 block text-[10px] uppercase tracking-widest text-helm-accent/70">
                      Diagram (open in GitHub or Mermaid Live for render)
                    </span>
                    {children}
                  </pre>
                );
              }
              return (
                <pre className="mb-4 overflow-x-auto rounded-xl border border-white/10 bg-ink-950/80 p-4 text-sm text-helm-sand/90">
                  <code>{children}</code>
                </pre>
              );
            }
            return (
              <code className="rounded bg-white/10 px-1.5 py-0.5 text-sm text-helm-sand">{children}</code>
            );
          },
          pre: ({ children }) => <>{children}</>,
          table: ({ children }) => (
            <div className="mb-6 overflow-x-auto rounded-xl border border-white/10">
              <table className="w-full min-w-[480px] text-left text-sm">{children}</table>
            </div>
          ),
          thead: ({ children }) => <thead className="border-b border-white/10 bg-white/5">{children}</thead>,
          th: ({ children }) => (
            <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-white/50">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="border-t border-white/[0.06] px-4 py-3 text-white/70">{children}</td>
          ),
          blockquote: ({ children }) => (
            <blockquote className="mb-4 border-l-2 border-helm-accent pl-4 text-white/65 italic">
              {children}
            </blockquote>
          ),
          hr: () => <hr className="my-10 border-white/10" />,
        }}
      >
        {content}
      </ReactMarkdown>
    </article>
  );
}
