export default function Section({
  title,
  eyebrow,
  children,
}: {
  title: string;
  eyebrow?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mt-12">
      <div className="mb-4">
        {eyebrow ? (
          <p className="text-xs uppercase tracking-[0.25em] text-white/35">{eyebrow}</p>
        ) : null}
        <h2 className="mt-1 text-xl font-semibold text-white/90">{title}</h2>
      </div>
      {children}
    </section>
  );
}
