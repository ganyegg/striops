// Typed client for the Helm backend.

export type Priority = "critical" | "high" | "medium" | "low";

export interface Evidence {
  label: string;
  value: string;
  source?: string | null;
}

export interface Forecast {
  entity_id: string;
  metric: string;
  direction: "improving" | "stable" | "worsening";
  slope: number;
  projected_next: number;
  confidence: number;
  contributing_factors: string[];
}

export interface Risk {
  id: string;
  title: string;
  reason: string;
  likelihood: number;
  impact: number;
  trend: number;
  confidence: number;
  priority: Priority;
  owner: string;
  mitigation: string;
  evidence: Evidence[];
  forecast?: Forecast | null;
  score: number;
}

export interface Opportunity {
  id: string;
  title: string;
  reason: string;
  value_estimate: number;
  unit: string;
  confidence: number;
  priority: Priority;
  owner: string;
  action: string;
  evidence: Evidence[];
}

export interface Recommendation {
  id: string;
  title: string;
  rationale: string;
  confidence: number;
  priority: Priority;
  expected_impact: string;
  evidence: Evidence[];
  linked_risk_ids: string[];
  linked_opportunity_ids: string[];
}

export interface AgentContribution {
  agent: string;
  summary: string;
  confidence: number;
}

export interface ExecutiveBrief {
  greeting: string;
  generated_for: string;
  health_score: number;
  health_narrative: string;
  strategic_summary: string;
  top_risks: Risk[];
  top_opportunities: Opportunity[];
  recommended_decisions: Recommendation[];
  emerging_trends: string[];
  confidence: number;
  agent_contributions: AgentContribution[];
}

export interface ScenarioImpact {
  dimension: string;
  delta: string;
  detail: string;
  confidence: number;
}

export interface Scenario {
  name: string;
  description: string;
  impacts: ScenarioImpact[];
}

export interface SimulationResult {
  question: string;
  baseline: Scenario;
  scenario: Scenario;
  recommended: string;
  recommendation_detail: string;
  confidence: number;
  evidence: Evidence[];
  alternatives: string[];
}

export interface ScenarioOption {
  function_name: string;
  current_budget: number;
  current_actual: number;
  modelled: boolean;
}

// Server components use the in-cluster URL; the browser uses the public URL.
const SERVER_BASE = process.env.API_BASE_URL || "http://localhost:8000";
export const CLIENT_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function getBrief(): Promise<ExecutiveBrief> {
  const res = await fetch(`${SERVER_BASE}/brief`, { cache: "no-store" });
  if (!res.ok) throw new Error(`brief failed: ${res.status}`);
  return res.json();
}

export async function getScenarios(): Promise<ScenarioOption[]> {
  const res = await fetch(`${SERVER_BASE}/simulate/scenarios`, { cache: "no-store" });
  if (!res.ok) throw new Error(`scenarios failed: ${res.status}`);
  return res.json();
}

export async function runSimulation(
  functionName: string,
  pctChange: number,
): Promise<SimulationResult> {
  const res = await fetch(`${CLIENT_BASE}/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ function_name: functionName, pct_change: pctChange }),
  });
  if (!res.ok) throw new Error(`simulation failed: ${res.status}`);
  return res.json();
}

export function formatZAR(value: number): string {
  if (Math.abs(value) >= 1e9) return `R${(value / 1e9).toFixed(2)}bn`;
  if (Math.abs(value) >= 1e6) return `R${(value / 1e6).toFixed(1)}m`;
  return `R${value.toLocaleString()}`;
}

export function priorityColor(p: Priority): string {
  switch (p) {
    case "critical":
      return "bg-helm-bad/15 text-helm-bad border border-helm-bad/30";
    case "high":
      return "bg-orange-400/15 text-orange-300 border border-orange-400/30";
    case "medium":
      return "bg-helm-warn/15 text-helm-warn border border-helm-warn/30";
    default:
      return "bg-white/5 text-white/60 border border-white/10";
  }
}

// -------------------------------------------------------------------------
// Municipalities + deep-dive domain profiles (provenance-first)
// -------------------------------------------------------------------------

export type VerificationStatus = "verified" | "needs_verification" | "estimate";
export type IndicatorTrend = "up" | "down" | "flat" | "na";

export interface Municipality {
  code: string;
  name: string;
  province: string;
  category: string;
  seat?: string | null;
  population?: string | null;
  wards?: number | null;
  status: "live" | "in_progress" | "planned";
  data_sources: Record<string, string>;
  domains_available: string[];
}

export interface DomainSummary {
  id: string;
  name: string;
  description: string;
  icon: string;
  order: number;
  available: boolean;
  summary: string | null;
  indicator_count: number;
  verified_share: number;
}

export interface Source {
  id: string;
  publisher: string;
  title: string;
  url: string;
  retrieved_at?: string | null;
  license?: string | null;
  coverage?: string | null;
}

export interface Indicator {
  key: string;
  label: string;
  value: string;
  numeric?: number | null;
  unit?: string | null;
  as_of: string;
  trend: IndicatorTrend;
  trend_note?: string | null;
  verification: VerificationStatus;
  method?: string | null;
  source_id: string;
  confidence: number;
}

export interface Policy {
  title: string;
  status: string;
  as_of: string;
  detail: string;
  source_id: string;
}

export interface DomainProfile {
  id: string;
  name: string;
  municipality: string;
  summary: string;
  indicators: Indicator[];
  policies: Policy[];
  watchpoints: string[];
  sources: Source[];
  last_updated?: string | null;
  coverage_note?: string | null;
}

export async function getMunicipalities(): Promise<Municipality[]> {
  const res = await fetch(`${SERVER_BASE}/municipalities`, { cache: "no-store" });
  if (!res.ok) throw new Error(`municipalities failed: ${res.status}`);
  return res.json();
}

export async function getMunicipality(code: string): Promise<Municipality> {
  const res = await fetch(`${SERVER_BASE}/municipalities/${code}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`municipality failed: ${res.status}`);
  return res.json();
}

export async function getMunicipalityDomains(code: string): Promise<DomainSummary[]> {
  const res = await fetch(`${SERVER_BASE}/municipalities/${code}/domains`, { cache: "no-store" });
  if (!res.ok) throw new Error(`domains failed: ${res.status}`);
  return res.json();
}

export async function getDomainProfile(
  code: string,
  domainId: string,
): Promise<DomainProfile> {
  const res = await fetch(`${SERVER_BASE}/municipalities/${code}/domains/${domainId}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`domain profile failed: ${res.status}`);
  return res.json();
}

export function verificationMeta(v: VerificationStatus): { label: string; className: string } {
  switch (v) {
    case "verified":
      return { label: "Verified", className: "bg-helm-good/15 text-helm-good border border-helm-good/30" };
    case "estimate":
      return { label: "Estimate", className: "bg-helm-accent/15 text-helm-accent border border-helm-accent/30" };
    default:
      return { label: "Needs verification", className: "bg-helm-warn/15 text-helm-warn border border-helm-warn/30" };
  }
}

// -------------------------------------------------------------------------
// Drill-down reports (risks / metrics / indicators)
// -------------------------------------------------------------------------

export interface ChartPoint {
  period: string;
  value: number;
  kind: "actual" | "projected" | string;
}

export interface MetricStats {
  latest: number;
  previous?: number | null;
  change?: number | null;
  change_pct?: number | null;
  period_start?: string | null;
  period_end?: string | null;
  n_points: number;
  min_value?: number | null;
  max_value?: number | null;
  mean?: number | null;
}

export interface ReferenceLink {
  label: string;
  publisher: string;
  url: string;
  as_of?: string | null;
  note?: string | null;
}

export interface ScoreBreakdown {
  likelihood: number;
  impact: number;
  trend: number;
  confidence: number;
  score: number;
  formula: string;
}

export interface MetricReport {
  entity_id: string;
  entity_name: string;
  metric: string;
  metric_label: string;
  unit?: string | null;
  series: ChartPoint[];
  projected: ChartPoint[];
  forecast?: Forecast | null;
  stats: MetricStats;
  owner?: string | null;
  department?: string | null;
  related_domain_id?: string | null;
  related_risk_id?: string | null;
  narrative: string;
  references: ReferenceLink[];
}

export interface RiskReport {
  risk: Risk;
  score_breakdown: ScoreBreakdown;
  metric_report?: MetricReport | null;
  related_domain_id?: string | null;
  related_budget_function?: string | null;
  narrative: string;
  what_changed: string[];
  recommended_actions: string[];
  references: ReferenceLink[];
  plain_language?: string | null;
  term?: string | null;
  in_one_line?: string | null;
}

export interface IndicatorReport {
  municipality_code: string;
  municipality_name: string;
  domain_id: string;
  domain_name: string;
  indicator: Indicator;
  source?: Source | null;
  domain_summary: string;
  watchpoints: string[];
  related_indicators: Indicator[];
  related_risk_ids: string[];
  related_metric?: { entity_id: string; metric: string } | null;
  narrative: string;
  references: ReferenceLink[];
}

export async function getRiskReport(riskId: string): Promise<RiskReport> {
  const res = await fetch(`${SERVER_BASE}/risks/${encodeURIComponent(riskId)}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`risk report failed: ${res.status}`);
  return res.json();
}

export async function getMetricReport(entityId: string, metric: string): Promise<MetricReport> {
  const res = await fetch(
    `${SERVER_BASE}/metrics/${encodeURIComponent(entityId)}/${encodeURIComponent(metric)}`,
    { cache: "no-store" },
  );
  if (!res.ok) throw new Error(`metric report failed: ${res.status}`);
  return res.json();
}

export async function getIndicatorReport(
  code: string,
  domainId: string,
  indicatorKey: string,
): Promise<IndicatorReport> {
  const res = await fetch(
    `${SERVER_BASE}/municipalities/${code}/domains/${domainId}/indicators/${indicatorKey}`,
    { cache: "no-store" },
  );
  if (!res.ok) throw new Error(`indicator report failed: ${res.status}`);
  return res.json();
}

/** Map opportunity ids to a report href. */
export function opportunityHref(oppId: string): string {
  if (oppId.startsWith("opp-efficiency-")) {
    const rest = oppId.slice("opp-efficiency-".length);
    const metrics = [
      "refuse_service_requests",
      "non_revenue_water_pct",
      "road_maintenance_backlog_km",
      "public_lighting_outages",
      "library_visits",
    ];
    for (const m of metrics) {
      if (rest.endsWith(`-${m}`)) {
        const entity = rest.slice(0, -(m.length + 1));
        return `/metrics/${entity}/${m}`;
      }
    }
  }
  if (oppId.startsWith("opp-underspend-")) {
    return "/CPT/domains/budget";
  }
  return `/opportunities/${encodeURIComponent(oppId)}`;
}

export function recommendationHref(rec: Recommendation): string {
  if (rec.linked_risk_ids?.[0]) return `/risks/${encodeURIComponent(rec.linked_risk_ids[0])}`;
  if (rec.linked_opportunity_ids?.[0]) return opportunityHref(rec.linked_opportunity_ids[0]);
  return "/";
}

// -------------------------------------------------------------------------
// Snapshot + Wins / Initiatives
// -------------------------------------------------------------------------

export interface HeroKPI {
  key: string;
  label: string;
  value: string;
  hint: string;
  tone: "good" | "warn" | "bad" | "neutral" | string;
  href?: string | null;
  plain_language?: string | null;
}

export interface CitySnapshot {
  municipality: string;
  greeting: string;
  tagline: string;
  health_score: number;
  kpis: HeroKPI[];
  confidence_note: string;
}

export interface WinMetric {
  label: string;
  value: string;
  as_of: string;
  source_id: string;
}

export interface Initiative {
  id: string;
  title: string;
  headline: string;
  plain_language: string;
  why_it_matters: string;
  category: string;
  status: string;
  priority: Priority;
  confidence: number;
  owner: string;
  image_url?: string | null;
  image_credit?: string | null;
  metrics: WinMetric[];
  evidence: Evidence[];
  next_step: string;
  related_domain_id?: string | null;
  related_risk_ids: string[];
  related_metric?: { entity_id: string; metric: string } | null;
  source_ids: string[];
}

export interface InitiativeReport {
  initiative: Initiative;
  sources: Source[];
  references: ReferenceLink[];
  narrative: string;
  metric_report?: MetricReport | null;
}

export interface GlossaryEntry {
  term: string;
  definition: string;
  in_one_line: string;
}

export async function getSnapshot(): Promise<CitySnapshot> {
  const res = await fetch(`${SERVER_BASE}/snapshot`, { cache: "no-store" });
  if (!res.ok) throw new Error(`snapshot failed: ${res.status}`);
  return res.json();
}

export async function getWins(): Promise<Initiative[]> {
  const res = await fetch(`${SERVER_BASE}/wins`, { cache: "no-store" });
  if (!res.ok) throw new Error(`wins failed: ${res.status}`);
  return res.json();
}

export async function getWinReport(id: string): Promise<InitiativeReport> {
  const res = await fetch(`${SERVER_BASE}/wins/${encodeURIComponent(id)}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`win report failed: ${res.status}`);
  return res.json();
}

export async function getGlossary(): Promise<Record<string, GlossaryEntry>> {
  const res = await fetch(`${SERVER_BASE}/glossary`, { cache: "no-store" });
  if (!res.ok) throw new Error(`glossary failed: ${res.status}`);
  return res.json();
}

// -------------------------------------------------------------------------
// Pulse (what changed), feed transparency, decision register
// -------------------------------------------------------------------------

export interface PulseItem {
  entity_id: string;
  metric: string;
  label: string;
  unit?: string | null;
  latest: number;
  previous: number;
  change: number;
  change_pct: number;
  direction: "improving" | "worsening" | "flat";
  sentence: string;
  plain_language?: string | null;
  href: string;
}

export interface CityPulse {
  generated_at: string;
  period_note: string;
  items: PulseItem[];
  worsening_count: number;
  improving_count: number;
}

export interface FeedStatus {
  id: string;
  name: string;
  publisher: string;
  status: "live" | "cached" | "curated" | "seed";
  status_label: string;
  cadence: string;
  description: string;
  unlocks: string;
}

export interface FeedsReport {
  generated_at: string;
  honesty_note: string;
  feeds: FeedStatus[];
  live_count: number;
  total_count: number;
}

export interface Decision {
  id: string;
  date?: string | null;
  title: string;
  status: "decided" | "in_progress" | "pending" | "overdue";
  owner: string;
  context: string;
  outcome?: string | null;
  linked_risk_id?: string | null;
  linked_win_id?: string | null;
  review_by?: string | null;
}

export interface DecisionRegister {
  municipality: string;
  decisions: Decision[];
  open_count: number;
  overdue_count: number;
  note: string;
}

export async function getPulse(): Promise<CityPulse> {
  const res = await fetch(`${SERVER_BASE}/pulse`, { cache: "no-store" });
  if (!res.ok) throw new Error(`pulse failed: ${res.status}`);
  return res.json();
}

export async function getFeeds(): Promise<FeedsReport> {
  const res = await fetch(`${SERVER_BASE}/feeds`, { cache: "no-store" });
  if (!res.ok) throw new Error(`feeds failed: ${res.status}`);
  return res.json();
}

export async function getDecisions(): Promise<DecisionRegister> {
  const res = await fetch(`${SERVER_BASE}/decisions`, { cache: "no-store" });
  if (!res.ok) throw new Error(`decisions failed: ${res.status}`);
  return res.json();
}

export function glossaryForRisk(riskId: string, glossary: Record<string, GlossaryEntry>): GlossaryEntry | null {
  for (const [key, entry] of Object.entries(glossary)) {
    if (riskId.includes(key)) return entry;
  }
  return null;
}

export function toneClass(tone: string): string {
  switch (tone) {
    case "good":
      return "text-helm-good";
    case "warn":
      return "text-helm-warn";
    case "bad":
      return "text-helm-bad";
    default:
      return "text-helm-sky";
  }
}
