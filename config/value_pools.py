"""
config/value_pools.py

14 BFSI AI value levers — declarative specs consumed by engine/math_engine.py.

DESIGN CONTRACT
---------------
1. Every `value_driver.answer_key` MUST be a question that exists in
   config/questions.py (enforced by tests/test_invariants.py). The engine
   sizes each lever's impact from the firm's OWN answers; `base_impact` /
   `base_feasibility` are only (a) the fallback when an answer is missing
   and (b) the seed the dynamic model modulates.
2. Every `goal_alignment` entry MUST be drawn from GOALS below, which is
   the single source of truth shared with the questionnaire (enforced by
   tests). A string mismatch here silently zeroes goal-fit — never again.
3. `sectors` gates which levers a firm is scored on. "all" = every sector.

`value_driver` fields:
  - "answer_key":  the questionnaire field whose magnitude proxies the raw
                   size of this lever's value pool for THIS firm.
  - "typical":     the peer-median value of that field (denominator used to
                   normalise the firm's answer to ~1.0 at median).
  - "kind":        "scale" (bigger answer = bigger pool, e.g. AUM, claims) or
                   "gap"  (bigger answer = SMALLER pool, e.g. a high STP rate
                           means little automation headroom left).

Benchmarks sourced: BCG 2026, PwC 2025, IVP, Jersey Finance, Coalition
Greenwich 2026, Manulife MAUDE (as an industry benchmark, not a client).
"""

# ── Canonical goal taxonomy (single source of truth) ─────────────────────────
# config/questions.py imports this; levers below reference ONLY these strings.
GOALS = [
    "Margin Expansion (Cost Reduction)",
    "Alpha Generation (Revenue Growth)",
    "Regulatory Resilience (Risk Management)",
    "Client Coverage Scaling",
]
GOAL_COST, GOAL_REVENUE, GOAL_RISK, GOAL_COVERAGE = GOALS

# Levers that cannot ship until the data foundation is modernized.
# Single definition — imported by the engine and both UI modules.
# lever_9 (Golden Source) IS foundation work, so funding the foundation
# unblocks it by definition.
PLATFORM_GATED_LEVERS = {"lever_2", "lever_7", "lever_8", "lever_9", "lever_11", "lever_13"}

# What each build cost covers — shown wherever a cost is itemized so no
# dollar figure appears without a stated basis. Delivery-benchmark scopes
# for a mid-size BFSI firm; replaced by scoped vendor quotes in engagement.
COST_BASIS = {
    "lever_1":  "Recon platform licence, custodian-feed integration, ~6-month build and tuning team",
    "lever_2":  "Order-routing engine licence, broker connectivity, SEBI algo registration and testing",
    "lever_3":  "Document-AI pipeline, research data licences, analyst workflow integration",
    "lever_4":  "CRM intelligence layer, admin-task automation, sales enablement rollout",
    "lever_5":  "KYC/AML decisioning platform, registry integrations, model validation",
    "lever_6":  "Reg-reporting automation suite, rule library setup, parallel-run validation",
    "lever_7":  "NAV oversight tooling, fund-accounting system integration",
    "lever_8":  "Personalisation engine, statement generation, channel integration",
    "lever_9":  "Golden-source data layer build, entity resolution, source-system onboarding",
    "lever_10": "Document-extraction models, corporate-actions workflow integration",
    "lever_11": "Underwriting decision engine, medical-data integrations, actuarial validation",
    "lever_12": "Claims triage and fraud models, core-system integration, adjuster workflow",
    "lever_13": "Customer data platform licence, identity resolution, campaign integration",
    "lever_14": "Digital onboarding journeys, biometric KYC integration, distributor rollout",
    "lever_0_foundation": "Bottom-up modernization estimate; six-component breakdown on The Foundation tab",
}

SECTOR_MF = "Mutual Funds / Asset Management"
SECTOR_INS = "Life & General Insurance"
SECTOR_DIV = "Diversified Financial Services"

BFSI_LEVERS = [
    {
        "id": "lever_1",
        "short_name": "Trade Reconciliation",
        "name": "Agentic Trade Reconciliation",
        "priority": "P0",
        "base_impact": 90,
        "base_feasibility": 75,
        "anv_estimate": 5_000_000,
        "impl_cost_estimate": 1_000_000,
        "goal_alignment": [GOAL_COST, GOAL_RISK],
        "value_driver": {"answer_key": "S3_TOTAL_OPS_FTE", "typical": 400.0, "kind": "scale"},
        "benchmark": "50% cost reduction; 90-95% STP achievable (IVP / Jersey Finance 2025-26)",
        "defensibility": "medium",
        "sectors": [SECTOR_MF, SECTOR_DIV],
    },
    {
        "id": "lever_2",
        "short_name": "Smart Execution",
        "name": "Agentic Execution & Smart Order Routing",
        "priority": "P1",
        "base_impact": 65,
        "base_feasibility": 62,
        "anv_estimate": 4_000_000,
        "impl_cost_estimate": 1_200_000,
        "goal_alignment": [GOAL_REVENUE],
        "value_driver": {"answer_key": "S2_ELECTRONIC_FLOW", "typical": 60.0, "kind": "gap"},
        "benchmark": "1-2 bps IS savings on non-electronic flow; 70-80% manual workflow automated (BCG 2026)",
        "defensibility": "low",
        "sectors": [SECTOR_MF, SECTOR_DIV],
    },
    {
        "id": "lever_3",
        "short_name": "Research Coverage",
        "name": "Research Coverage Amplification",
        "priority": "P0",
        "base_impact": 88,
        "base_feasibility": 90,
        "anv_estimate": 1_500_000,
        "impl_cost_estimate": 800_000,
        "goal_alignment": [GOAL_REVENUE, GOAL_COST],
        "value_driver": {"answer_key": "S1_AUM", "typical": 50.0, "kind": "scale"},
        "benchmark": "3-5x coverage expansion; >90% parsing automation (BCG / Oliver Wyman 2026)",
        "defensibility": "medium",
        "sectors": [SECTOR_MF, SECTOR_DIV],
    },
    {
        "id": "lever_4",
        "short_name": "Sales Coverage",
        "name": "Distribution & Sales Coverage Scaling",
        "priority": "P1",
        "base_impact": 78,
        "base_feasibility": 68,
        "anv_estimate": 2_000_000,
        "impl_cost_estimate": 1_500_000,
        "goal_alignment": [GOAL_REVENUE, GOAL_COVERAGE],
        "value_driver": {"answer_key": "S2_ELECTRONIC_FLOW", "typical": 60.0, "kind": "gap"},
        "benchmark": "2-3x coverage; 15-25% win-rate uplift (BCG 2026, PwC 2025)",
        "defensibility": "medium",
        "sectors": ["all"],
    },
    {
        "id": "lever_5",
        "short_name": "Onboarding & KYC",
        "name": "Client Onboarding & KYC/AML Automation",
        "priority": "P0",
        "base_impact": 85,
        "base_feasibility": 78,
        "anv_estimate": 5_000_000,
        "impl_cost_estimate": 900_000,
        "goal_alignment": [GOAL_COST, GOAL_COVERAGE, GOAL_RISK],
        "value_driver": {"answer_key": "S4_AML_FALSE_POS", "typical": 85.0, "kind": "scale"},
        "benchmark": "~90% of structured steps automated; AML false-positives -80% (Jersey Finance 2025)",
        "defensibility": "medium",
        "sectors": ["all"],
    },
    {
        "id": "lever_6",
        "short_name": "Reg Reporting",
        "name": "Regulatory & Compliance Automation",
        "priority": "P2",
        "base_impact": 60,
        "base_feasibility": 68,
        "anv_estimate": 5_000_000,
        "impl_cost_estimate": 1_100_000,
        "goal_alignment": [GOAL_RISK, GOAL_COST],
        "value_driver": {"answer_key": "S4_REG_MONTHS", "typical": 6.0, "kind": "scale"},
        "benchmark": "60-80% reporting automation; 70-90% error reduction (EY 2026, Deloitte 2026)",
        "defensibility": "low",
        "sectors": ["all"],
    },
    {
        "id": "lever_7",
        "short_name": "NAV Oversight",
        "name": "Fund Accounting & NAV Oversight",
        "priority": "P3",
        "base_impact": 58,
        "base_feasibility": 40,
        "anv_estimate": 700_000,
        "impl_cost_estimate": 800_000,
        "goal_alignment": [GOAL_COST, GOAL_RISK],
        "value_driver": {"answer_key": "S1_AUM", "typical": 50.0, "kind": "scale"},
        "benchmark": "50-75% automation; high data-readiness dependency (Alpha FMC 2026)",
        "defensibility": "low",
        "sectors": [SECTOR_MF, SECTOR_DIV],
    },
    {
        "id": "lever_8",
        "short_name": "Personalization",
        "name": "Hyper-Personalized Client Servicing",
        "priority": "P2",
        "base_impact": 68,
        "base_feasibility": 45,
        "anv_estimate": 500_000,
        "impl_cost_estimate": 1_800_000,
        "goal_alignment": [GOAL_REVENUE, GOAL_COVERAGE],
        "value_driver": {"answer_key": "S1_AUM", "typical": 50.0, "kind": "scale"},
        "benchmark": "10-20% retention uplift; reporting cost -20-35% (BCG 2026, PwC 2025)",
        "defensibility": "high",
        "sectors": ["all"],
    },
    {
        "id": "lever_9",
        "short_name": "Golden Source",
        "name": "Data Platform Consolidation (Golden Source)",
        "priority": "P0",
        "base_impact": 100,
        "base_feasibility": 42,
        "anv_estimate": 1_300_000,
        "impl_cost_estimate": 2_500_000,
        "goal_alignment": [GOAL_COST, GOAL_RISK],
        "value_driver": {"answer_key": "S1_SILO", "typical": 5.0, "kind": "scale"},
        "benchmark": "Prerequisite multiplier (1.2-1.5x) on all other levers; 70-90% recon cost cut (Coalition Greenwich 2026)",
        "defensibility": "high",
        "sectors": ["all"],
    },
    {
        "id": "lever_10",
        "short_name": "Corporate Actions",
        "name": "Corporate Actions & Document Processing",
        "priority": "P0",
        "base_impact": 80,
        "base_feasibility": 88,
        "anv_estimate": 500_000,
        "impl_cost_estimate": 600_000,
        "goal_alignment": [GOAL_COST, GOAL_RISK],
        "value_driver": {"answer_key": "S3_STP", "typical": 65.0, "kind": "gap"},
        "benchmark": "90% extraction automation; CA golden-copy from unstructured PDFs (Arcesium / Magic FinServ 2025-26)",
        "defensibility": "low",
        "sectors": [SECTOR_MF, SECTOR_DIV],
    },
    # ── Insurance levers ──
    {
        "id": "lever_11",
        "short_name": "Underwriting",
        "name": "Life Underwriting Automation",
        "priority": "P0",
        "base_impact": 95,
        "base_feasibility": 70,
        "anv_estimate": 8_000_000,
        "impl_cost_estimate": 2_500_000,
        "goal_alignment": [GOAL_COST, GOAL_REVENUE, GOAL_COVERAGE],
        "value_driver": {"answer_key": "S2_ANNUAL_UNDERWRITING_APPS", "typical": 250_000.0, "kind": "scale"},
        "benchmark": "90% STP; 2-minute decision vs 5-7 days manual (Manulife MAUDE benchmark)",
        "defensibility": "medium",
        "sectors": [SECTOR_INS, SECTOR_DIV],
    },
    {
        "id": "lever_12",
        "short_name": "Claims & Fraud",
        "name": "Claims Processing & Fraud Detection",
        "priority": "P0",
        "base_impact": 85,
        "base_feasibility": 65,
        "anv_estimate": 8_500_000,
        "impl_cost_estimate": 1_800_000,
        "goal_alignment": [GOAL_COST, GOAL_RISK],
        "value_driver": {"answer_key": "S3_ANNUAL_CLAIMS", "typical": 500_000.0, "kind": "scale"},
        "benchmark": "85-90% STP target; 50% fraud detection rate uplift; 2-3 day processing",
        "defensibility": "medium",
        "sectors": [SECTOR_INS, SECTOR_DIV],
    },
    {
        "id": "lever_13",
        "short_name": "Customer 360",
        "name": "Customer Data Platform (CDP) & Cross-Sell",
        "priority": "P1",
        "base_impact": 75,
        "base_feasibility": 55,
        "anv_estimate": 2_500_000,
        "impl_cost_estimate": 2_500_000,
        "goal_alignment": [GOAL_REVENUE, GOAL_COVERAGE],
        "value_driver": {"answer_key": "S1_AUM", "typical": 50.0, "kind": "scale"},
        "benchmark": "Unified 360-degree customer view; 10-15% cross-sell uplift",
        "defensibility": "high",
        "sectors": ["all"],
    },
    {
        "id": "lever_14",
        "short_name": "Digital Onboarding",
        "name": "Digital Onboarding Expansion",
        "priority": "P0",
        "base_impact": 88,
        "base_feasibility": 82,
        "anv_estimate": 3_500_000,
        "impl_cost_estimate": 1_200_000,
        "goal_alignment": [GOAL_REVENUE, GOAL_COVERAGE],
        "value_driver": {"answer_key": "S2_QUOTE_TO_BIND_DAYS", "typical": 7.0, "kind": "scale"},
        "benchmark": "40-50% application-dropout reduction; 1-2 day turnaround (industry digital-onboarding benchmarks)",
        "defensibility": "high",
        "sectors": [SECTOR_INS, SECTOR_DIV],
    },
]

# ── Auditable model constants (surfaced in the Assumptions Appendix) ─────────
# Loaded FTE costs are India-blended, fully loaded (salary + benefits +
# overhead + vendor allocation), in USD/year.
CONSTANTS = {
    # Loaded workforce costs (USD/yr, India blended, fully loaded)
    "Ops_FTE_Loaded_Cost_USD": 55_000,
    "Underwriter_Loaded_Cost_USD": 75_000,
    "Analyst_Loaded_Cost_USD": 120_000,
    "Compliance_FTE_Loaded_Cost_USD": 70_000,
    "NAV_Ops_Loaded_Cost_USD": 65_000,
    "Onboarding_FTE_Loaded_Cost_USD": 45_000,
    # Derivation multipliers (used when an internal metric is inferred from
    # an asked question — every derivation is listed here, none is hidden)
    "Recon_Breaks_per_OpsFTE_x_ManualShare": 800,
    "Settlement_Fails_per_OpsFTE_x_ManualShare": 1.5,
    "Underwriters_per_Annual_Apps": 1 / 2500,
    "InForce_Policies_per_Annual_App": 7,
    "MF_Folios_per_AUM_Billion": 12_000,
    "AML_Alerts_per_Ops_FTE": 120,
    "Ops_Pool_Attribution_Recon_Pct": 20,
    "Ops_Pool_Attribution_Claims_Pct": 40,
    "Ops_Pool_Attribution_Onboarding_Pct": 15,
    "Ops_Pool_Attribution_Compliance_Pct": 25,
    # Revenue economics
    "Avg_Annual_Premium_USD": 700,
    "New_Business_Margin_Pct": 25,
    "Insurance_Customer_Margin_USD_Yr": 45,
    "MF_Folio_Margin_USD_Yr": 30,
    # Legacy / foundation: bottom-up rebuild model (engine/legacy_diagnostic.py)
    "Rebuild_Core_Complexity_Monolith_x": 2.2,
    "Rebuild_Core_Complexity_OnPrem_x": 1.7,
    "Rebuild_Core_Complexity_Modern_x": 1.2,
    "Rebuild_Migration_Cost_per_Silo_USD_M": 0.35,
    "Rebuild_Integration_Cost_per_Silo_USD_M": 0.15,
    "Rebuild_Testing_ParallelRun_Pct": 15,
    "Rebuild_Training_Change_Pct": 8,
    "Rebuild_Contingency_Pct": 15,
    "Rebuild_Estimate_Range_Pct": 20,
    "Legacy_Savings_Retention_Rate": 0.65,
    # Realization
    "Year_1_Ramp_Curve_Pct": 25,
    "Year_2_Ramp_Curve_Pct": 60,
    "Year_3_Ramp_Curve_Pct": 100,
    "Conservative_Haircut_Pct": 50,
    "Base_Haircut_Pct": 60,
    "Aggressive_Haircut_Pct": 75,
    # Execution-risk model: risk = (1 - governance/100) * dampener, clamped
    "Exec_Risk_Governance_Dampener": 0.5,
    "Exec_Risk_Floor_Pct": 5,
    "Exec_Risk_Cap_Pct": 45,
    # Dynamic-impact model weights (Impact = value-pool x goal-fit x urgency)
    "Impact_Weight_ValuePool_Pct": 55,
    "Impact_Weight_Urgency_Pct": 45,
    "Impact_OffGoal_Floor": 0.25,   # off-goal levers dampened, not zeroed (GE-McKinsey style)
    "Impact_ValuePool_Cap": 1.6,    # a firm 60%+ above peer-median saturates the pool score
    # Regulatory: a red (non-compliant) lever has its automation benefit capped
    "Reg_NonCompliant_Automation_Cap_Pct": 50,
}
