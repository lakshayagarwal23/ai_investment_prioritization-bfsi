"""
config/peer_corpus.py

Peer intelligence data for FMCG / CPG AI investment benchmarking.
All companies listed are distinct, independently-traded public entities.

IMPORTANT: Hindustan Unilever Limited (HUL, NSE: HINDUNILVR) is the Indian
subsidiary of Unilever PLC (LSE: ULVR). They operate under a unified global
strategy and are treated as a single peer entity (Unilever) in this corpus
to avoid benchmark double-counting.

Data sources:
  Annual Reports 2023-2024
  McKinsey Global Survey on AI Adoption in Consumer Goods, 2024
  Gartner FMCG AI Market Report Q3-2024
  Company Capital Markets Day investor presentations
"""

PEER_INTELLIGENCE = {
    "PnG": {
        "company": "Procter & Gamble",
        "ticker": "PG",
        "exchange": "NYSE",
        "geography": "Global",
        "ai_investment_usd_m": 1200,
        "supply_chain_savings_usd_m": 1500,
        "driver": "AI-powered demand sensing and end-to-end supply chain optimization",
        "payback_months": 18,
        "margin_uplift": "250bps gross margin expansion",
        "inventory_reduction": "22% inventory reduction",
        "nps_uplift_pts": 0,
        "revenue_uplift_pct": 8,
        "headline_stat": "$1.5B supply chain savings via end-to-end AI",
    },
    "Nestle": {
        "company": "Nestle S.A.",
        "ticker": "NESN",
        "exchange": "SWX",
        "geography": "Global",
        "ai_investment_usd_m": 800,
        "tpo_savings_usd_m": 340,
        "nps_uplift_pts": 12,
        "driver": "Trade Promotion Optimization and AI-driven demand forecasting",
        "payback_months": 20,
        "margin_uplift": "180bps gross margin expansion",
        "inventory_reduction": "18% inventory reduction",
        "revenue_uplift_pct": 6,
        "headline_stat": "12-pt NPS uplift via Trade Promotion AI",
    },
    "Unilever": {
        "company": "Unilever PLC",
        "ticker": "ULVR",
        "exchange": "LSE",
        "geography": "Global",
        "ai_investment_usd_m": 1100,
        "driver": "AI-powered demand sensing and personalized digital marketing at scale",
        "payback_months": 21,
        "inventory_reduction": "15% inventory reduction",
        "nps_uplift_pts": 8,
        "margin_uplift": "120bps gross margin expansion",
        "revenue_uplift_pct": 10,
        "headline_stat": "15% inventory reduction via AI demand sensing",
    },
    "CocaCola": {
        "company": "The Coca-Cola Company",
        "ticker": "KO",
        "exchange": "NYSE",
        "geography": "Global",
        "ai_investment_usd_m": 600,
        "driver": "AI-powered manufacturing yield optimization and dynamic pricing intelligence",
        "payback_months": 19,
        "cost_savings_usd_m": 500,
        "margin_uplift": "200bps gross margin expansion",
        "inventory_reduction": "12% inventory reduction",
        "nps_uplift_pts": 5,
        "revenue_uplift_pct": 7,
        "headline_stat": "$500M cost reduction via AI manufacturing optimization",
    },
    "Mondelez": {
        "company": "Mondelez International",
        "ticker": "MDLZ",
        "exchange": "NASDAQ",
        "geography": "Global",
        "ai_investment_usd_m": 450,
        "driver": "AI-driven trade promotion optimization and e-commerce personalization",
        "payback_months": 22,
        "revenue_uplift_pct": 18,
        "nps_uplift_pts": 10,
        "margin_uplift": "140bps gross margin expansion",
        "inventory_reduction": "14% inventory reduction",
        "headline_stat": "18% revenue growth in e-commerce via AI personalization",
    },
    "Reckitt": {
        "company": "Reckitt Benckiser Group",
        "ticker": "RKT",
        "exchange": "LSE",
        "geography": "Global",
        "ai_investment_usd_m": 380,
        "driver": "AI-powered digital shelf analytics and consumer insight platforms",
        "payback_months": 24,
        "nps_uplift_pts": 14,
        "margin_uplift": "160bps gross margin expansion",
        "revenue_uplift_pct": 9,
        "inventory_reduction": "10% inventory reduction",
        "headline_stat": "14-pt NPS improvement via AI digital shelf analytics",
    },
    "Colgate": {
        "company": "Colgate-Palmolive",
        "ticker": "CL",
        "exchange": "NYSE",
        "geography": "Global",
        "ai_investment_usd_m": 320,
        "driver": "AI-powered pricing intelligence and supply chain automation",
        "payback_months": 20,
        "margin_uplift": "230bps gross margin expansion",
        "inventory_reduction": "16% inventory reduction",
        "nps_uplift_pts": 6,
        "revenue_uplift_pct": 5,
        "headline_stat": "230bps margin expansion via AI pricing intelligence",
    },
    "Danone": {
        "company": "Danone S.A.",
        "ticker": "BN",
        "exchange": "EPA",
        "geography": "Global",
        "ai_investment_usd_m": 290,
        "driver": "AI-powered demand forecasting and sustainability-linked waste reduction",
        "payback_months": 22,
        "waste_reduction_pct": 30,
        "margin_uplift": "110bps gross margin expansion",
        "inventory_reduction": "19% inventory reduction",
        "nps_uplift_pts": 7,
        "revenue_uplift_pct": 6,
        "headline_stat": "30% food waste reduction via AI demand forecasting",
    },
    "Marico": {
        "company": "Marico Limited",
        "ticker": "MARICO",
        "exchange": "NSE",
        "geography": "India & South Asia",
        "ai_investment_usd_m": 45,
        "driver": "AI-powered rural distribution intelligence and secondary sales demand sensing",
        "payback_months": 18,
        "revenue_uplift_pct": 12,
        "margin_uplift": "150bps gross margin expansion",
        "inventory_reduction": "11% inventory reduction",
        "nps_uplift_pts": 4,
        "headline_stat": "12% revenue growth via AI distribution intelligence",
    },
    "ITC": {
        "company": "ITC Limited",
        "ticker": "ITC",
        "exchange": "NSE",
        "geography": "India & South Asia",
        "ai_investment_usd_m": 120,
        "driver": "AI-powered agribusiness optimization and FMCG go-to-market intelligence",
        "payback_months": 24,
        "margin_uplift": "200bps gross margin expansion",
        "inventory_reduction": "20% inventory reduction",
        "revenue_uplift_pct": 8,
        "nps_uplift_pts": 5,
        "headline_stat": "200bps margin expansion via AI agribusiness platform",
    },
}

# Industry-level benchmark aggregates (McKinsey + Gartner 2024)
INDUSTRY_BENCHMARKS = {
    # ── Aggregate statistics ────────────────────────────────────────────────
    "avg_payback_months": 21,
    "median_payback_months": 22,
    "avg_roi_pct": 185,
    "top_quartile_roi_pct": 280,
    "avg_margin_uplift_bps": 175,
    "ai_programme_failure_rate_pct": 58,
    "data_fragmentation_avg_delay_months": 4.5,
    "change_mgmt_cost_multiplier": 1.75,
    "peer_count": 10,
    "use_cases_modeled": 30,

    # ── Data engineering cost model (complexity modifier) ───────────────────
    "typical_data_eng_fte": 4,            # FTEs needed for pre-AI data remediation
    "typical_data_eng_months": 8,         # months duration
    "fte_monthly_rate_usd": 15_000,       # fully-loaded monthly cost per FTE (USD)

    # ── Change management overhead (risk modifier) ──────────────────────────
    "change_mgmt_overhead_pct": 0.08,     # 8% of total budget for structured OCM

    # ── Primary goal allocation sub-configurations ──────────────────────────
    # Used by math_engine.py to set pillar labels and break down use cases.
    "primary_goal_allocation": {
        "Revenue Growth": {
            "label": "Revenue & Growth AI",
            "sub_initiatives": [
                "Trade Promotion Optimization",
                "Sales Copilot / Next-Best-Action",
                "Consumer Personalization Engine",
                "Demand Sensing & Forecasting",
            ],
        },
        "Margin Recovery": {
            "label": "Margin Defense & Supply Chain AI",
            "sub_initiatives": [
                "Procurement AI & Supplier Intelligence",
                "Manufacturing Yield Optimization",
                "Logistics Route & Cost Optimization",
                "Waste Reduction via Predictive Maintenance",
            ],
        },
        "Enterprise Productivity": {
            "label": "Enterprise Productivity AI",
            "sub_initiatives": [
                "Enterprise Knowledge Search Copilot",
                "Invoice & PO Extraction Automation",
                "Field Sales Productivity Platform",
                "Meeting & Document Intelligence",
            ],
        },
    },
}
