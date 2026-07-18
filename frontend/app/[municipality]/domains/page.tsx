import Link from "next/link";
import DomainGrid from "@/components/DomainGrid";
import PageChrome from "@/components/PageChrome";
import {
  getMunicipality,
  getMunicipalityDomains,
  type DomainSummary,
  type Municipality,
} from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DomainsIndex({
  params,
}: {
  params: { municipality: string };
}) {
  const code = params.municipality.toUpperCase();
  let domains: DomainSummary[];
  let muni: Municipality;
  try {
    [domains, muni] = await Promise.all([
      getMunicipalityDomains(code),
      getMunicipality(code),
    ]);
  } catch (e) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-24">
        <Link href="/" className="text-sm text-striops-accent hover:underline">
          ← Back to briefing
        </Link>
        <p className="mt-6 text-white/60">
          Couldn&apos;t load domains: {e instanceof Error ? e.message : String(e)}
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <PageChrome
        crumbs={
          <>
            <Link href="/" className="font-semibold text-white/80 hover:text-white">
              Striops
            </Link>
            <span className="text-white/25">/</span>
            <span className="text-white/50">{muni.name}</span>
            <span className="text-white/25">/</span>
            <span className="text-white/80">Deep Dive</span>
          </>
        }
      />

      <div className="mt-8">
        <p className="text-xs uppercase tracking-[0.25em] text-white/35">Deep Dive</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight text-white">
          {muni.name}
        </h1>
        <p className="mt-3 max-w-2xl text-[15px] text-white/60">
          Verifiable intelligence by domain. Every indicator links to its public source.
        </p>
      </div>

      <div className="mt-8">
        <DomainGrid code={code} domains={domains} />
      </div>
    </main>
  );
}
