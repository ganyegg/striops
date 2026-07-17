// Typed client for the Helm AI backend.

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
