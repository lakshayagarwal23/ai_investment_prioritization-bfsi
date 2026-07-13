/**
 * Typed client for the engine API. One source of truth for the contract —
 * these types mirror api/schemas.py exactly.
 */

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Scenario = "conservative" | "base" | "aggressive";
export type AiStack = "Frontier" | "Balanced" | "Cost-optimized";

export interface Question {
  id: string;
  section: string;
  question: string;
  help?: string;
  type: "numeric" | "percentage" | "categorical";
  options?: string[];
  default?: number | string;
  visible_when?: { sector?: string[] };
}

export interface Config {
  sectors: string[];
  goals: string[];
  scenarios: Scenario[];
  ai_stacks: Record<string, { run_x: number; capability_x: number; desc: string }>;
  questions: Question[];
  engine_version: string;
}

export interface Lever {
  id: string;
  name: string;
  short_name: string;
  quadrant: string;
  quadrant_label: string;
  anv_m: number;
  impl_cost_m: number;
  payback_months: number | null;
  impact: number;
  feasibility: number;
  priority: string;
  budget_approved: boolean;
  warning: string | null;
  reg_risk: "green" | "yellow" | "red";
  reg_mitigations: string[];
  cost_basis: string;
}

export interface Summary {
  company_name: string;
  budget_m: number;
  committed_m: number;
  uncommitted_m: number;
  total_anv_m: number;
  risk_adjusted_anv_m: number;
  exec_risk_pct: number;
  confidence_pct: number;
  payback_months: number | null;
  funded_count: number;
  blocked_anv_m: number;
}

export interface Diagnostic {
  verdict: string;
  verdict_action: string;
  deprecation_score: number;
  score_math: string;
  pillars: Record<string, number>;
  pillar_explain: Record<string, string>;
  tco: {
    annual_maintenance_m: number;
    business_value_m: number;
    ratio_pct: number | null;
    band: string;
    verdict: string;
    security_flag: boolean;
  };
  self_funding: {
    legacy_annual_savings_m: number;
    unlocked_anv_m: number;
    total_annual_value_m: number;
    rebuild_cost_m: number;
    payback_months: number | null;
  };
  rebuild_breakdown: { component: string; amount_m: number; basis: string }[];
  guardrails: string[];
  recommend_funding: boolean;
}

export interface Report {
  run_id: string;
  engine_version: string;
  assumptions_hash: string;
  summary: Summary;
  levers: Lever[];
  diagnostic: Diagnostic;
  scenario: Scenario;
  ai_stack: AiStack;
  foundation_decision: boolean;
}

export interface ReportRequest {
  answers: Record<string, number | string>;
  company_name: string;
  target_sector: string;
  budget_usd_m: number;
  primary_goals: string[];
  scenario: Scenario;
  ai_stack: AiStack;
  foundation_decision: boolean;
}

export async function fetchConfig(): Promise<Config> {
  const r = await fetch(`${API_URL}/api/config`);
  if (!r.ok) throw new Error(`config failed: ${r.status}`);
  return r.json();
}

export async function computeReport(req: ReportRequest): Promise<Report> {
  const r = await fetch(`${API_URL}/api/report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!r.ok) throw new Error(`report failed: ${r.status} ${await r.text()}`);
  return r.json();
}
