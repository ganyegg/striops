import Link from "next/link";
import DomainTabs from "@/components/DomainTabs";
import IndicatorRow from "@/components/IndicatorRow";
import PageChrome from "@/components/PageChrome";
import PolicyList from "@/components/PolicyList";
import SourcesPanel from "@/components/SourcesPanel";
import {
  getDomainProfile,
  getMunicipality,
  getMunicipalityDomains,
  type DomainProfile,
  type DomainSummary,
  type Municipality,
} from "@/lib/api";

export const dynamic = "force-dynamic";

function ErrorState({ code, message }: { code: string; message: string }) {
  return (
    <main className="mx-auto max-w-3xl px-6 py-24">
      <Link href="/" className="text-sm text-helm-accent hover:underline">
        ← Back to briefing
      </Link>
      <h1 className="mt-6 text-2xl font-semibold text-white/90">Domain unavailable</h1>
      <p className="mt-3 text-white/60">
        This deep-dive isn&apos;t available for {code} yet, or the reasoning core is unreachable.
      </p>
      <pre className="mt-4 rounded-lg bg-white/5 p-4 text-xs text-white/50">{message}</pre>
    </main>
  );
}

export default async function DomainPage({
  params,
}: {
  params: { municipality: string; domain: string };
}) {
  const code = params.municipality.toUpperCase();
  let profile: DomainProfile;
  let domains: DomainSummary[];
  let muni: Municipality;
  try {
    [profile, domains, muni] = await Promise.all([
      getDomainProfile(code, params.domain),
      getMunicipalityDomains(code),
      getMunicipality(code),
    ]);
  } catch (e) {
    return <ErrorState code={code} message={e instanceof Error ? e.message : String(e)} />;
  }

  const sourceById = new Map(profile.sources.map((s) => [s.id, s]));
  const verifiedCount = profile.indicators.filter((i) => i.verification === "verified").length;

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <PageChrome
        crumbs={
          <>
            <Link href="/" className="font-semibold text-white/80 hover:text-white">
              Helm
            </Link>
            <span className="text-white/25">/</span>
            <span className="text-white/50">{muni.name}</span>
            <span className="text-white/25">/</span>
            <span className="text-white/80">{profile.name}</span>
          </>
        }
      />

      <div className="mt-8">
        <p className="text-xs uppercase tracking-[0.25em] text-white/35">Deep Dive</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight text-white">{profile.name}</h1>
        <p className="mt-3 max-w-3xl text-[15px] leading-relaxed text-white/65">{profile.summary}</p>
        <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-white/40">
          {profile.last_updated ? <span>Updated {profile.last_updated}</span> : null}
          <span className="pill bg-helm-good/10 text-helm-good">
            {verifiedCount}/{profile.indicators.length} indicators verified
          </span>
        </div>
      </div>

      <div className="mt-6">
        <DomainTabs code={code} domains={domains} active={profile.id} />
      </div>

      {profile.coverage_note ? (
        <p className="mt-6 rounded-lg border border-white/5 bg-white/[0.02] p-3 text-xs leading-relaxed text-white/45">
          {profile.coverage_note}
        </p>
      ) : null}

      <section className="mt-8">
        <h2 className="mb-4 text-lg font-semibold text-white/90">Indicators</h2>
        <div className="grid gap-3 md:grid-cols-2">
          {profile.indicators.map((ind) => (
            <IndicatorRow
              key={ind.key}
              indicator={ind}
              source={sourceById.get(ind.source_id)}
              href={`/${code}/domains/${profile.id}/indicators/${ind.key}`}
            />
          ))}
        </div>
      </section>

      {profile.policies.length ? (
        <section className="mt-10">
          <h2 className="mb-4 text-lg font-semibold text-white/90">Policies</h2>
          <PolicyList policies={profile.policies} sources={profile.sources} />
        </section>
      ) : null}

      {profile.watchpoints.length ? (
        <section className="mt-10">
          <h2 className="mb-4 text-lg font-semibold text-white/90">Watchpoints</h2>
          <ul className="space-y-2">
            {profile.watchpoints.map((w, i) => (
              <li key={i} className="flex gap-2 text-sm text-white/65">
                <span className="text-helm-warn">•</span>
                {w}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="mt-10">
        <SourcesPanel sources={profile.sources} />
      </section>

      <footer className="mt-16 border-t border-white/5 pt-6 text-xs text-white/30">
        Every figure links to its public source. Items marked &ldquo;Needs verification&rdquo; are sourced
        but should be confirmed before publication.
      </footer>
    </main>
  );
}
