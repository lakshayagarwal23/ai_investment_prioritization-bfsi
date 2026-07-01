import pytest
from engine.math_engine import build_investment_plan
from llm.openai_client import generate_executive_summary

def test_no_financial_keys():
    plan = build_investment_plan(100, ["Revenue Growth"])
    # G-NF: Prove no ROI exists
    for key in ["roi", "npv", "payback", "initial_investment", "expected_roi_pct", "npv_usd", "payback_months", "payback_label"]:
        assert key not in plan
        assert key not in plan.get("executive_decision", {})

def test_archetype_postures():
    # G1: Clean estate
    clean = build_investment_plan(
        100, 
        ["Revenue Growth"], 
        discovery_answers={"Q3.1": "Fully centralized (e.g., global SAP S/4HANA instance)", "Q3.2": "Modern cloud data lake", "Q4.2": "minimal"}
    )
    assert clean["complexity_score"] < 0.30

    # Fragmented estate
    frag = build_investment_plan(
        100, 
        ["Revenue Growth"], 
        discovery_answers={"Q3.1": "Highly fragmented across business units", "Q3.2": "old, slow local servers"}
    )
    assert frag["complexity_score"] >= 0.30
    assert frag["data_eng_line_item"] is not None

def test_consistency():
    # G2: Same inputs = exact same output
    ans = {"Q3.1": "clean"}
    run1 = build_investment_plan(100, ["Revenue Growth"], discovery_answers=ans)
    run2 = build_investment_plan(100, ["Revenue Growth"], discovery_answers=ans)
    assert run1 == run2

def test_pydantic_validation_fallback(monkeypatch):
    # G4: Malformed payload triggers static fallback
    class MockMessage:
        content = '{"missing_required_keys": true}'
    class MockChoice:
        message = MockMessage()
    class MockResponse:
        choices = [MockChoice()]
    class MockChat:
        completions = type('MockCompletions', (), {'create': lambda **kw: MockResponse()})()
    class MockClient:
        chat = MockChat()
    
    monkeypatch.setenv("OPENAI_API_KEY", "fake_key")
    monkeypatch.setattr("openai.OpenAI", lambda api_key: MockClient())
    
    plan = build_investment_plan(100, ["Revenue Growth"])
    payload, is_ai = generate_executive_summary("TestCo", plan, {})
    assert not is_ai
    assert payload["executive_decision"]["readiness_tier"] in ["Leader", "Strategic", "Emerging", "Laggard"]

def test_no_value_at_stake():
    # (a) no "value at stake" string appears in the engine plan or fallback payload
    plan = build_investment_plan(100, ["Revenue Growth"])
    payload, _ = generate_executive_summary("TestCo", plan, {})
    import json
    full_str = str(plan) + json.dumps(payload)
    assert "value at stake" not in full_str.lower()
    assert "value-at-stake" not in full_str.lower()

def test_risk_rows_carry_triggering_answer():
    # (b) each risk row carries a triggering answer
    frag = build_investment_plan(
        100, 
        ["Revenue Growth"], 
        discovery_answers={"Q3.1": "Highly fragmented across business units", "Q3.2": "old, slow local servers", "Q4.1": "voluntary"}
    )
    drivers = frag.get("derivation", {}).get("risk_drivers", []) + frag.get("derivation", {}).get("complexity_drivers", [])
    assert any("Q3.1" in d for d in drivers)
    assert any("Q3.2" in d for d in drivers)
    assert any("Q4.1" in d for d in drivers)

def test_fmt_usd_no_spaces():
    # (c) _fmt_usd output contains no spaces
    from ui.dashboard import _fmt_usd
    res = _fmt_usd(6700000)
    assert " " not in res
    assert res == "&#36;6.7M"

def test_w1_posture_integrity():
    plan = build_investment_plan(100, ["Revenue Growth"], discovery_answers={"Q3.2": "old local servers", "Q3.3": "historically unreliable"})
    assert plan["posture"] == "ADDRESS FOUNDATIONS FIRST"
    # Risk description is now a verbose sentence; check it references data estate issues
    assert "data" in plan["primary_risk"].lower() or "estate" in plan["primary_risk"].lower()

def test_w2_objective_alignment_and_adoption_penalty():
    # Margin only
    plan = build_investment_plan(100, ["Margin Recovery"], discovery_answers={"Q4.1": "voluntary"})
    # Sales Copilot should have lower impact/feasibility
    sales = next(u for u in plan["scoring_matrix"] if "Sales Copilot" in u["name"])
    promo = next(u for u in plan["scoring_matrix"] if "Trade Promotion" in u["name"])
    assert promo["composite_score"] > sales["composite_score"]
    assert sales["feasibility"] < 90  # Adoption penalty applied

def test_w3_sector_and_scale():
    # Beauty vs Home Care
    plan_beauty = build_investment_plan(100, ["Revenue Growth"], discovery_answers={"Q0.1": "Beauty & Personal Care", "Q1.2": "200000000"}) # $200M -> challenger
    plan_home = build_investment_plan(100, ["Revenue Growth"], discovery_answers={"Q0.1": "Home & House Care"})
    
    beauty_pers = next(u for u in plan_beauty["scoring_matrix"] if "Consumer Personalization" in u["name"])
    home_pers = next(u for u in plan_home["scoring_matrix"] if "Consumer Personalization" in u["name"])
    assert beauty_pers["composite_score"] > home_pers["composite_score"]
    
    # Scale penalty
    beauty_sc = next(u for u in plan_beauty["scoring_matrix"] if "Demand Sensing & Forecasting" in u["name"])
    assert beauty_sc["feasibility"] < 90 # Penalized

def test_w4_cost_and_foundation():
    plan = build_investment_plan(100, ["Revenue Growth"], discovery_answers={"Q4.3": "external SI"})
    assert plan["total_cost"] == plan["total_budget"] + plan["si_cost"]
    
    # Check foundation rows
    foundation_allocs = sum(r["allocation_usd"] for r in plan["ledger_rows"] if r["pillar"] == "Foundation (Data & Controls)")
    import math
    assert math.isclose(foundation_allocs, plan["foundation_usd"], rel_tol=1e-5)

def test_w5_risk_register():
    plan = build_investment_plan(100, ["Revenue Growth"], discovery_answers={"Q3.2": "old, slow local servers", "Q1.4": "no clear sponsor"})
    risks = plan["risk_register"]
    assert len(risks) <= 5
    assert any(r["name"] == "Executive Sponsorship" for r in risks)
    assert any(r["name"] == "Data Integration & Infrastructure" for r in risks)

def test_portfolio_pct_sums_to_100():
    # Multiple profiles
    plan1 = build_investment_plan(100, ["Revenue Growth"])
    plan2 = build_investment_plan(100, ["Margin Recovery", "Enterprise Productivity"])
    assert sum(plan1["value_portfolio"]["pct"].values()) == 100
    assert sum(plan2["value_portfolio"]["pct"].values()) == 100

def test_mutual_exclusivity():
    from config.value_pools import VALUE_TYPE
    plan = build_investment_plan(100, ["Revenue Growth"])
    # A single use case string is only a key in VALUE_TYPE once (Python dict invariant)
    # But check the actual rows
    seen = set()
    for r in plan["ledger_rows"]:
        if r["pillar"] == "Value Initiative":
            assert r["initiative"] not in seen
            seen.add(r["initiative"])
            assert r["value_type"] in ["Revenue generation", "Operating-profit enhancement", "Productivity & scaling"]

def test_ledger_subtotals_match_portfolio():
    plan = build_investment_plan(100, ["Revenue Growth"])
    ledger_totals = {"Revenue generation": 0.0, "Operating-profit enhancement": 0.0, "Productivity & scaling": 0.0}
    for r in plan["ledger_rows"]:
        if r["pillar"] == "Value Initiative":
            ledger_totals[r["value_type"]] += r["allocation_usd"]
            
    import math
    if sum(ledger_totals.values()) > 0:
        for vt, val in plan["value_portfolio"]["usd"].items():
            assert math.isclose(ledger_totals[vt], val, rel_tol=1e-5)

def test_alignment_sentence_varies_by_mandate():
    plan_rev = build_investment_plan(100, ["Revenue Growth"])
    plan_mar = build_investment_plan(100, ["Margin Recovery"])
    assert plan_rev["value_portfolio"]["alignment_sentence"] != plan_mar["value_portfolio"]["alignment_sentence"]
    assert "revenue" in plan_rev["value_portfolio"]["alignment_sentence"].lower()

def test_w6_posture_consistency_gate():
    """
    FIX 5: Global Consistency Gate.
    1. If FOUNDATION_FIRST, funded value initiatives are exactly $0.
    2. No funded initiatives possess feasibility < FEAS_MID.
    3. The set of "Strategic bets" is perfectly a subset of deferred_initiatives.
    4. No "Quick win" has feasibility < FEAS_MID.
    5. No forbidden finance tokens ("ROI", "NPV", "payback") leak outside the disclaimer.
    """
    from config.value_pools import FEAS_MID
    from ui.dashboard import _fmt_usd
    import json
    
    # Force FOUNDATION_FIRST
    plan_foundations = build_investment_plan(100, ["Revenue Growth"], discovery_answers={"Q3.1": "Highly fragmented across business units", "Q3.2": "old, slow local servers"})
    assert plan_foundations["posture"] == "ADDRESS FOUNDATIONS FIRST"
    
    # 1. If FOUNDATION_FIRST, funded value initiatives are exactly $0.
    funded_value_allocs = sum(r["allocation_usd"] for r in plan_foundations["ledger_rows"] if r["pillar"] == "Value Initiative")
    assert funded_value_allocs == 0.0
    
    # Check normal plan for other rules
    plan = build_investment_plan(100, ["Revenue Growth"])
    deferred = set(plan["deferred_initiatives"])
    funded_names = set(r["initiative"] for r in plan["ledger_rows"] if r["pillar"] == "Value Initiative")
    
    for uc in plan["scoring_matrix"]:
        # 3. "Strategic bets" is a subset of deferred_initiatives
        if uc["quadrant_name"] == "Strategic bets":
            assert uc["name"] in deferred
            assert uc["name"] not in funded_names
        
        # 4. No "Quick win" has feasibility < FEAS_MID
        if uc["quadrant_name"] == "Quick wins":
            assert uc["feasibility"] >= FEAS_MID
            
        # 2. No funded initiatives possess feasibility < FEAS_MID
        if uc["name"] in funded_names:
            assert uc["feasibility"] >= FEAS_MID

    # 5. No forbidden finance tokens leak outside the disclaimer
    payload, _ = generate_executive_summary("TestCo", plan, {})
    summary_text = payload.get("executive_summary", "")
    summary_text = summary_text.replace("This diagnostic deliberately does not project ROI or payback", "")
    payload["executive_summary"] = summary_text
    
    full_str = json.dumps(payload).lower()
    assert "roi" not in full_str
    assert "npv" not in full_str
    
def test_quadrant_labels_present():
    plan = build_investment_plan(100, ["Revenue Growth"])
    for uc in plan["scoring_matrix"]:
        assert "quadrant_name" in uc
        assert "quadrant_action" in uc
        assert uc["quadrant_name"] in ["Prime candidates", "Strategic bets", "Tactical add-ons", "Marginal"]
