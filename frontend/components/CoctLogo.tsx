import Link from "next/link";

/** Official City of Cape Town wordmark + crest (SVG), on a light plate for contrast. */
export default function CoctLogo({
  height = 36,
  href,
  className = "",
}: {
  height?: number;
  href?: string;
  className?: string;
}) {
  const plate = (
    <span
      className={`inline-flex shrink-0 items-center rounded-lg bg-white px-3 py-1.5 shadow-sm ring-1 ring-black/5 ${className}`}
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/brand/coct-logo.svg"
        alt="City of Cape Town"
        height={height}
        style={{ height, width: "auto" }}
        className="block"
      />
    </span>
  );

  if (!href) return plate;

  return (
    <Link href={href} className="transition hover:opacity-90" aria-label="City of Cape Town — home">
      {plate}
    </Link>
  );
}
