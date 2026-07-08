"""
config/peer_corpus.py

Industry benchmarks and peer intelligence for the BFSI / Mutual Funds AI Investment Engine.
Targeted at Mid-Tier / Emerging Mutual Funds navigating the "Valley of Death".
Contains data from BCG, PwC, Oliver Wyman, EY, Alpha FMC, and Coalition Greenwich.
"""

INDUSTRY_BENCHMARKS = {
    "global_aum": 147e12, # 147 trillion
    "industry_profit_margin_flat_since": 2010,
    "industry_profit_margin": 0.30,
    "cost_to_income_ratio": 0.68,
    "ai_adoption": {
        "using_or_planning": 0.91,
        "scaled_beyond_pilots": 0.07,
    },
    "value_potential": {
        "cost_reduction_min": 0.25,
        "cost_reduction_max": 0.35,
        "coverage_expansion_min": 3,
        "coverage_expansion_max": 5,
    },
    "deprecation_scoring": {
        "tech_debt_weight": 0.40,
        "fragmentation_weight": 0.35,
        "governance_inverse_weight": 0.25,
    },
}

PEER_INTELLIGENCE = [
    {
        "name": "Mid-Tier Alpha Partners",
        "segment": "Mid-tier",
        "aum": 120e9,
        "notes": "Struggling with 26% margin; high fragmentation across 14 point solutions. Prime candidate for legacy kill."
    },
    {
        "name": "Emerging Market Fund A",
        "segment": "Emerging",
        "aum": 45e9,
        "notes": "Deployed Agentic Recon in 2025; reduced trade break resolution cycle by 80%."
    },
    {
        "name": "Regional Wealth Managers",
        "segment": "Mid-tier",
        "aum": 250e9,
        "notes": "Currently scaling Research Amplification; covering 4x names per analyst."
    },
    {
        "name": "Boutique Quant Capital",
        "segment": "Emerging",
        "aum": 15e9,
        "notes": "Cloud-native from day one. Using GenAI for 10-K extractions."
    },
    {
        "name": "Legacy Mutual Corp",
        "segment": "Mid-tier",
        "aum": 310e9,
        "notes": "Valley of Death: Maintenance costs eating 78% of IT budget. Planning Data Mesh migration."
    }
]
