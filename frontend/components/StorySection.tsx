export default function StorySection({
  id,
  step,
  eyebrow,
  title,
  lead,
  children,
  variant = "default",
}: {
  id?: string;
  step?: string;
  eyebrow?: string;
  title: string;
  lead?: string;
  children: React.ReactNode;
  variant?: "default" | "accent" | "muted";
}) {
  const border =
    variant === "accent"
      ? "border-l-2 border-helm-accent pl-5"
      : variant === "muted"
        ? "border-l-2 border-white/10 pl-5"
        : "";

  return (
    <section id={id} className={`scroll-mt-24 ${border}`}>
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          {step ? (
            <p className="mb-1 font-mono text-[11px] uppercase tracking-[0.3em] text-helm-accent/80">
              {step}
            </p>
          ) : null}
          {eyebrow ? (
            <p className="text-xs uppercase tracking-[0.22em] text-white/35">{eyebrow}</p>
          ) : null}
          <h2 className="mt-1 font-display text-2xl font-semibold text-white md:text-3xl">{title}</h2>
          {lead ? <p className="mt-2 max-w-2xl text-sm leading-relaxed text-white/55">{lead}</p> : null}
        </div>
      </div>
      {children}
    </section>
  );
}
