"""
config/value_pools.py

14 BFSI AI value levers with base scoring, implementation cost estimates, and goal alignments.
Supports a Hybrid Business Model (Mutual Funds + Life Insurance / Wealth Management).
Benchmarks sourced: BCG 2026, PwC 2025, IVP, Jersey Finance, Coalition Greenwich 2026, Manulife MAUDE Data.
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
        "benchmark": "50% cost reduction; 90–95% STP achievable (IVP / Jersey Finance 2025–26)",
        "sectors": ["all"]
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
        "benchmark": "2–5 bps IS savings; 70–80% manual workflow automated (BCG 2026)",
        "sectors": ["Mutual Funds / Asset Management", "Diversified Financial Services"]
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
        "benchmark": "3–5x coverage expansion; >90% parsing automation (BCG / Oliver Wyman 2026)",
        "sectors": ["Mutual Funds / Asset Management", "Diversified Financial Services"]
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
        "benchmark": "2–3x coverage; 15–25% win-rate uplift (BCG 2026, PwC 2025)",
        "sectors": ["all"]
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
        "benchmark": "~90% of structured steps automated; AML false-positives –80% (Jersey Finance 2025)",
        "sectors": ["all"]
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
        "benchmark": "60–80% reporting automation; 70–90% error reduction (EY 2026, Deloitte 2026)",
        "sectors": ["all"]
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
        "benchmark": "50–75% automation; high data-readiness dependency (Alpha FMC 2026)",
        "sectors": ["Mutual Funds / Asset Management", "Diversified Financial Services"]
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
        "benchmark": "10–20% retention uplift; reporting cost –20–35% (BCG 2026, PwC 2025)",
        "sectors": ["all"]
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
        "benchmark": "Prerequisite multiplier (1.2–1.5x) on all other levers; 70–90% recon cost cut (Coalition Greenwich 2026)",
        "sectors": ["all"]
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
        "benchmark": "90% extraction automation; CA golden-copy from unstructured PDFs (Arcesium / Magic FinServ 2025–26)",
        "sectors": ["Mutual Funds / Asset Management", "Diversified Financial Services"]
    },
    # ── NEW INSURANCE / WEALTH (MMIL) LEVERS ──
    {
        "id": "lever_11",
        "name": "Life Underwriting Automation (MAUDE)",
        "priority": "P0",
        "base_impact": 95,
        "base_feasibility": 70,
        "anv_estimate": 10_500_000,
        "impl_cost_estimate": 2_500_000,
        "goal_alignment": ["Margin Expansion (Cost)", "Alpha Generation (Revenue)", "Client Coverage Scaling"],
        "benchmark": "90% STP; 2-minute decision vs 5-7 days manual (Manulife MAUDE scale)",
        "sectors": ["Life & General Insurance", "Diversified Financial Services"]
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
        "benchmark": "85-90% STP target; 50% fraud detection rate uplift; 2-3 day processing",
        "sectors": ["Life & General Insurance", "Diversified Financial Services"]
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
        "benchmark": "Unified 360-degree view (Life+MF); 10-15% cross-sell uplift",
        "sectors": ["all"]
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
        "benchmark": "50% dropout reduction; 1-2 day turnaround (Mahindra SamurAI ecosystem advantage)",
        "sectors": ["Life & General Insurance", "Diversified Financial Services"]
    }
]
