"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Link from "next/link";

/** Compact markdown renderer for Ask Helm answers. */
export default function AskMarkdown({ content }: { content: string }) {
  return (
    <div className="ask-prose text-sm leading-relaxed text-white/80">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h2: ({ children }) => (
            <h2 className="mb-2 mt-4 font-display text-base font-semibold text-white first:mt-0">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="mb-1.5 mt-3 text-[13px] font-semibold uppercase tracking-wide text-helm-sand">
              {children}
            </h3>
          ),
          p: ({ children }) => <p className="mb-2.5 text-white/75">{children}</p>,
          ul: ({ children }) => (
            <ul className="mb-2.5 list-none space-y-1.5 pl-0">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="mb-2.5 list-decimal space-y-1.5 pl-5 text-white/75">{children}</ol>
          ),
          li: ({ children }) => (
            <li className="relative pl-3.5 text-white/75 before:absolute before:left-0 before:text-helm-accent before:content-['•']">
              {children}
            </li>
          ),
          strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
          a: ({ href, children }) =>
            href?.startsWith("/") ? (
              <Link href={href} className="text-helm-sky underline-offset-2 hover:underline">
                {children}
              </Link>
            ) : (
              <a
                href={href}
                target="_blank"
                rel="noreferrer"
                className="text-helm-sky underline-offset-2 hover:underline"
              >
                {children}
              </a>
            ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
