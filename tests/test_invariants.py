import pytest
from engine.math_engine import build_investment_plan

def get_base_answers():
    return {
        "target_sector": "Financial Services",
        "S1_SILO": 5.0,
        "S1_ARCH": "Siloed On-Premises",
        "S1_API_GATEWAY": "Batch",
        "S5_DATA_OWNERSHIP": 50.0,
        "S5_LINEAGE": 50.0,
        "S5_DQ_SLA": 50.0,
        "S5_REGULATORY_TRACE": 50.0,
        "S5_CHANGE_MGMT": 50.0,
        "S5_MAINTENANCE_COST": 6.5,
        "S5_BIZ_VALUE": 20.0
    }

def test_determinism():
    """G2: Same inputs = exact same output"""
    ans = get_base_answers()
    plan1 = build_investment_plan(ans, 100.0, ["Revenue Growth"])
    plan2 = build_investment_plan(ans, 100.0, ["Revenue Growth"])
    assert plan1 == plan2

def test_budget_constraint():
    """Ensure we do not approve more budget than available."""
    ans = get_base_answers()
    budget = 5.0  # tiny budget
    plan = build_investment_plan(ans, budget, ["Revenue Growth"])
    
    approved = [p for p in plan if p.get("budget_approved", False)]
    total_cost = sum(p.get("impl_cost", 0) for p in approved) / 1e6
    assert total_cost <= budget

def test_quadrant_labels_present():
    ans = get_base_answers()
    plan = build_investment_plan(ans, 100.0, ["Revenue Growth"])
    for uc in plan:
        assert "quadrant" in uc
        assert uc["quadrant"] in ["Strategic Bets", "Quick Wins / Fill-ins", "Park (Data-Blocked)", "De-prioritize"]

def test_scenario_haircuts():
    """Ensure the aggressive scenario produces higher ANV than the conservative scenario for the same lever."""
    ans = get_base_answers()
    plan_base = build_investment_plan(ans, 100.0, ["Revenue Growth"], scenario="base")
    plan_cons = build_investment_plan(ans, 100.0, ["Revenue Growth"], scenario="conservative")
    plan_aggr = build_investment_plan(ans, 100.0, ["Revenue Growth"], scenario="aggressive")
    
    # Check first lever
    base_anv = plan_base[0]["anv"]
    cons_anv = plan_cons[0]["anv"]
    aggr_anv = plan_aggr[0]["anv"]
    
    assert cons_anv < base_anv
    assert base_anv < aggr_anv

def test_sector_filtering():
    """Ensure insurance levers do not appear for pure banking/markets."""
    ans = get_base_answers()
    ans["target_sector"] = "Asset Management"
    plan = build_investment_plan(ans, 100.0, ["Revenue Growth"])
    
    # Lever 11 is "Next-Gen Underwriting (Life/Health)"
    names = [p["name"] for p in plan]
    assert not any("Underwriting" in n for n in names)
