"""
config/value_pools.py

14 BFSI AI value levers.

REBUILD NOTE (dynamic impact):
Each lever now carries `value_driver` metadata so the engine can size its
business impact FROM THE FIRM'S OWN ANSWERS instead of a frozen `base_impact`
constant. `base_impact` / `base_feasibility` are retained only as (a) a fallback
when an answer is missing and (b) the seed the dynamic model modulates.

`value_driver` fields:
  - "answer_key":  the questionnaire field whose magnitude proxies the raw
                   size of this lever's value pool for THIS firm.
  - "typical":     the peer-median value of that field (denominator used to
                   normalise the firm's answer to ~1.0 at median).
  - "kind":        "scale" (bigger answer = bigger pool, e.g. AUM, claims) or
                   "gap"  (bigger answer = SMALLER pool, e.g. a high STP rate
                           means little automation headroom left).

Benchmarks sourced: BCG 2026, PwC 2025, IVP, Jersey Finance, Coalition
Greenwich 2026, Manulife MAUDE.
"""

BFSI_LEVERS = [
    {
        "id": "lever_1",
        "name": "Agentic Trade Reconciliation",
        "priority": "P0",
        "base_impact": 90,
        "base_feasibility": 75,
        "anv_estimate": 14_500_000,
        "impl_cost_estimate": 1_000_000,
        "goal_alignment": ["Margin Expansion (Cost)", "Regulatory Resilience (Risk)"],
        "value_driver": {"answer_key": "S3_TOTAL_OPS_FTE", "typical": 50.0, "kind": "scale"},
        "benchmark": "50% cost reduction; 90-95% STP achievable (IVP / Jersey Finance 2025-26)",
        "sectors": ["all"],
    },
    {
        "id": "lever_2",
        "name": "Agentic Execution & Smart Order Routing",
        "priority": "P1",
        "base_impact": 65,
        "base_feasibility": 62,
        "anv_estimate": 2_000_000,
        "impl_cost_estimate": 1_200_000,
        "goal_alignment": ["Alpha Generation (Revenue)"],
        "value_driver": {"answer_key": "S1_AUM", "typical": 50.0, "kind": "scale"},
        "benchmark": "2-5 bps IS savings; 70-80% manual workflow automated (BCG 2026)",
        "sectors": ["Mutual Funds / Asset Management", "Diversified Financial Services"],
    },
    {
        "id": "lever_3",
        "name": "Research Coverage Amplification",
        "priority": "P0",
        "base_impact": 88,
        "base_feasibility": 90,
        "anv_estimate": 8_000_000,
        "impl_cost_estimate": 800_000,
        "goal_alignment": ["Alpha Generation (Revenue)", "Margin Expansion (Cost)"],
        "value_driver": {"answer_key": "S1_AUM", "typical": 50.0, "kind": "scale"},
        "benchmark": "3-5x coverage expansion; >90% parsing automation (BCG / Oliver Wyman 2026)",
        "sectors": ["Mutual Funds / Asset Management", "Diversified Financial Services"],
    },
    {
        "id": "lever_4",
        "name": "Distribution & Sales Coverage Scaling",
        "priority": "P1",
        "base_impact": 78,
        "base_feasibility": 68,
        "anv_estimate": 4_000_000,
        "impl_cost_estimate": 1_500_000,
        "goal_alignment": ["Alpha Generation (Revenue)", "Client Coverage Scaling"],
        "value_driver": {"answer_key": "S2_ADMIN_PCT", "typical": 45.0, "kind": "scale"},
        "benchmark": "2-3x coverage; 15-25% win-rate uplift (BCG 2026, PwC 2025)",
        "sectors": ["all"],
    },
    {
        "id": "lever_5",
        "name": "Client Onboarding & KYC/AML Automation",
        "priority": "P0",
        "base_impact": 85,
        "base_feasibility": 78,
        "anv_estimate": 5_500_000,
        "impl_cost_estimate": 900_000,
        "goal_alignment": ["Margin Expansion (Cost)", "Client Coverage Scaling", "Regulatory Resilience (Risk)"],
        "value_driver": {"answer_key": "S4_AML_FALSE_POS", "typical": 85.0, "kind": "scale"},
        "benchmark": "~90% of structured steps automated; AML false-positives -80% (Jersey Finance 2025)",
        "sectors": ["all"],
    },
    {
        "id": "lever_6",
        "name": "Regulatory & Compliance Automation",
        "priority": "P2",
        "base_impact": 60,
        "base_feasibility": 68,
        "anv_estimate": 2_800_000,
        "impl_cost_estimate": 1_100_000,
        "goal_alignment": ["Regulatory Resilience (Risk)", "Margin Expansion (Cost)"],
        "value_driver": {"answer_key": "S4_REG_MONTHS", "typical": 6.0, "kind": "scale"},
        "benchmark": "60-80% reporting automation; 70-90% error reduction (EY 2026, Deloitte 2026)",
        "sectors": ["all"],
    },
    {
        "id": "lever_7",
        "name": "Fund Accounting & NAV Oversight",
        "priority": "P3",
        "base_impact": 58,
        "base_feasibility": 40,
        "anv_estimate": 3_900_000,
        "impl_cost_estimate": 2_000_000,
        "goal_alignment": ["Margin Expansion (Cost)", "Regulatory Resilience (Risk)"],
        "value_driver": {"answer_key": "S1_AUM", "typical": 50.0, "kind": "scale"},
        "benchmark": "50-75% automation; high data-readiness dependency (Alpha FMC 2026)",
        "sectors": ["Mutual Funds / Asset Management", "Diversified Financial Services"],
    },
    {
        "id": "lever_8",
        "name": "Hyper-Personalized Client Servicing",
        "priority": "P2",
        "base_impact": 68,
        "base_feasibility": 45,
        "anv_estimate": 2_500_000,
        "impl_cost_estimate": 1_800_000,
        "goal_alignment": ["Alpha Generation (Revenue)", "Client Coverage Scaling"],
        "value_driver": {"answer_key": "S1_AUM", "typical": 50.0, "kind": "scale"},
        "benchmark": "10-20% retention uplift; reporting cost -20-35% (BCG 2026, PwC 2025)",
        "sectors": ["all"],
    },
    {
        "id": "lever_9",
        "name": "Data Platform Consolidation (Golden Source)",
        "priority": "P0",
        "base_impact": 100,
        "base_feasibility": 42,
        "anv_estimate": 3_200_000,
        "impl_cost_estimate": 5_000_000,
        "goal_alignment": ["Margin Expansion (Cost)", "Regulatory Resilience (Risk)"],
        "value_driver": {"answer_key": "S1_SILO", "typical": 5.0, "kind": "scale"},
        "benchmark": "Prerequisite multiplier (1.2-1.5x) on all other levers; 70-90% recon cost cut (Coalition Greenwich 2026)",
        "sectors": ["all"],
    },
    {
        "id": "lever_10",
        "name": "Corporate Actions & Document Processing",
        "priority": "P0",
        "base_impact": 80,
        "base_feasibility": 88,
        "anv_estimate": 3_000_000,
        "impl_cost_estimate": 600_000,
        "goal_alignment": ["Margin Expansion (Cost)", "Regulatory Resilience (Risk)"],
        "value_driver": {"answer_key": "S3_STP", "typical": 65.0, "kind": "gap"},
        "benchmark": "90% extraction automation; CA golden-copy from unstructured PDFs (Arcesium / Magic FinServ 2025-26)",
        "sectors": ["Mutual Funds / Asset Management", "Diversified Financial Services"],
    },
    # -- INSURANCE / WEALTH (MMIL) LEVERS --
    {
        "id": "lever_11",
        "name": "Life Underwriting Automation (MAUDE)",
        "priority": "P0",
        "base_impact": 95,
        "base_feasibility": 70,
        "anv_estimate": 10_500_000,
        "impl_cost_estimate": 2_500_000,
        "goal_alignment": ["Margin Expansion (Cost)", "Alpha Generation (Revenue)", "Client Coverage Scaling"],
        "value_driver": {"answer_key": "S2_ANNUAL_UNDERWRITING_APPS", "typical": 50_000.0, "kind": "scale"},
        "benchmark": "90% STP; 2-minute decision vs 5-7 days manual (Manulife MAUDE scale)",
        "sectors": ["Life & General Insurance", "Diversified Financial Services"],
    },
    {
        "id": "lever_12",
        "name": "Claims Processing & Fraud Detection",
        "priority": "P0",
        "base_impact": 85,
        "base_feasibility": 65,
        "anv_estimate": 6_500_000,
        "impl_cost_estimate": 1_800_000,
        "goal_alignment": ["Margin Expansion (Cost)", "Regulatory Resilience (Risk)"],
        "value_driver": {"answer_key": "S3_ANNUAL_CLAIMS", "typical": 100_000.0, "kind": "scale"},
        "benchmark": "85-90% STP target; 50% fraud detection rate uplift; 2-3 day processing",
        "sectors": ["Life & General Insurance", "Diversified Financial Services"],
    },
    {
        "id": "lever_13",
        "name": "Customer Data Platform (CDP) & Cross-Sell",
        "priority": "P1",
        "base_impact": 75,
        "base_feasibility": 55,
        "anv_estimate": 8_500_000,
        "impl_cost_estimate": 2_500_000,
        "goal_alignment": ["Alpha Generation (Revenue)", "Client Coverage Scaling"],
        "value_driver": {"answer_key": "S1_AUM", "typical": 50.0, "kind": "scale"},
        "benchmark": "Unified 360-degree view (Life+MF); 10-15% cross-sell uplift",
        "sectors": ["all"],
    },
    {
        "id": "lever_14",
        "name": "Rural Digital Onboarding (Offline+Biometric)",
        "priority": "P0",
        "base_impact": 88,
        "base_feasibility": 82,
        "anv_estimate": 3_500_000,
        "impl_cost_estimate": 1_200_000,
        "goal_alignment": ["Alpha Generation (Revenue)", "Client Coverage Scaling"],
        "value_driver": {"answer_key": "S2_QUOTE_TO_BIND_DAYS", "typical": 7.0, "kind": "scale"},
        "benchmark": "50% dropout reduction; 1-2 day turnaround (Mahindra SamurAI ecosystem advantage)",
        "sectors": ["Life & General Insurance", "Diversified Financial Services"],
    },
]

# ── Auditable model constants (surfaced in the Assumptions Appendix) ──
CONSTANTS = {
    "FTE_Cost_USD_Year": 65000,
    "Rebuild_Capex_Multiplier": 3.5,
    "Legacy_Savings_Retention_Rate": 0.65,
    "Year_1_Ramp_Curve_Pct": 25,
    "Year_2_Ramp_Curve_Pct": 60,
    "Year_3_Ramp_Curve_Pct": 100,
    "Conservative_Haircut_Pct": 50,
    "Base_Haircut_Pct": 60,
    "Aggressive_Haircut_Pct": 75,
    # Dynamic-impact model weights (Impact = value-pool x goal-fit x urgency)
    "Impact_Weight_ValuePool_Pct": 55,
    "Impact_Weight_Urgency_Pct": 45,
    "Impact_OffGoal_Floor": 0.25,   # off-goal levers dampened, not zeroed (GE-McKinsey style)
    "Impact_ValuePool_Cap": 1.6,    # a firm 60%+ above peer-median saturates the pool score
}
