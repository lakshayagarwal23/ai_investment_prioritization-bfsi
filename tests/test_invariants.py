"""
Engine invariants. Each test encodes a defect class that has actually
shipped in a previous build — if one fails, a client-facing lie is back.
"""
import pytest

from config.questions import QUESTIONS, OBJECTIVE_INPUTS
from config.value_pools import BFSI_LEVERS, GOALS, SECTOR_MF, SECTOR_INS
from engine.math_engine import build_investment_plan, LEVER_COMPUTE, compute_execution_risk
from engine.regulatory import check_regulatory_compliance

QUESTION_IDS = {q["id"] for q in QUESTIONS}


def mf_answers(**overrides):
    """Realistic asset-manager answers (every asked question present)."""
    a = {q["id"]: q.get("default") for q in QUESTIONS}
    a["target_sector"] = SECTOR_MF
    a.update(overrides)
    return a


def ins_answers(**overrides):
    a = {q["id"]: q.get("default") for q in QUESTIONS}
    a["target_sector"] = SECTOR_INS
    a.update(overrides)
    return a


# ── Config integrity: the bugs that broke the default path ──────────────────

def test_goal_taxonomy_is_unified():
    """Lever goal_alignment strings MUST match the questionnaire's goal options.
    A mismatch silently dampens every lever to 25% impact (shipped bug)."""
    assert list(OBJECTIVE_INPUTS) == list(GOALS)
    for lever in BFSI_LEVERS:
        for goal in lever["goal_alignment"]:
            assert goal in GOALS, f"{lever['id']} aligns to unknown goal '{goal}'"


def test_value_drivers_reference_asked_questions():
    """Every lever's impact driver must be a question we actually ask."""
    for lever in BFSI_LEVERS:
        driver = lever.get("value_driver")
        if driver:
            assert driver["answer_key"] in QUESTION_IDS, (
                f"{lever['id']} is driven by phantom question {driver['answer_key']}")


def test_every_lever_has_a_compute_function():
    for lever in BFSI_LEVERS:
        assert lever["id"] in LEVER_COMPUTE


# ── Recommendation quality in the DEFAULT path ───────────────────────────────

def test_default_goals_produce_strategic_bets():
    """With the app's default goal selection, the matrix must not collapse."""
    plan = build_investment_plan(mf_answers(), 100.0, [GOALS[0]])
    bets = [p for p in plan if p["quadrant"] == "Strategic Bets"]
    assert len(bets) >= 2, "default goal selection produced no Strategic Bets"


def test_selected_goal_boosts_matching_lever_impact():
    ans = mf_answers()
    with_goal = {p["id"]: p["impact"] for p in build_investment_plan(ans, 100.0, [GOALS[0]])}
    # lever_1 aligns to Margin Expansion; lever_2 (revenue-only) does not
    assert with_goal["lever_1"] > with_goal["lever_2"] * 1.5


# ── Economics sanity: numbers a CFO will not laugh at ────────────────────────

@pytest.mark.parametrize("answers", [mf_answers(), ins_answers()])
def test_portfolio_economics_are_defensible(answers):
    plan = build_investment_plan(answers, 100.0, [])
    funded = [p for p in plan if p["budget_approved"]]
    assert funded, "no levers funded on a $100M budget"
    total_anv = sum(p["anv"] for p in funded)
    total_cost = sum(p["impl_cost"] for p in funded)
    simple_roi = total_anv / total_cost
    assert 0.3 <= simple_roi <= 2.5, f"portfolio ROI {simple_roi:.0%} outside credible band"
    # No single lever may dominate the story
    assert max(p["anv"] for p in funded) <= 0.45 * total_anv, "one lever dominates the portfolio"
    # No funded lever pays back implausibly fast or never
    for p in funded:
        assert 4.0 <= p["payback"] <= 120.0, f"{p['id']} payback {p['payback']}mo"


def test_negative_anv_levers_never_consume_budget():
    plan = build_investment_plan(mf_answers(), 100.0, [])
    for p in plan:
        if p["anv"] <= 0:
            assert not p["budget_approved"]


def test_budget_constraint_respected():
    plan = build_investment_plan(mf_answers(), 5.0, [])
    approved = [p for p in plan if p["budget_approved"]]
    assert sum(p["impl_cost"] for p in approved) <= 5.0 * 1e6


def test_determinism():
    ans = mf_answers()
    assert build_investment_plan(ans, 100.0, [GOALS[0]]) == \
           build_investment_plan(ans, 100.0, [GOALS[0]])


def test_scenario_ordering():
    ans = mf_answers()
    by_id = lambda plan: {p["id"]: p["anv"] for p in plan}
    cons = by_id(build_investment_plan(ans, 100.0, [], scenario="conservative"))
    base = by_id(build_investment_plan(ans, 100.0, [], scenario="base"))
    aggr = by_id(build_investment_plan(ans, 100.0, [], scenario="aggressive"))
    for lid in base:
        if base[lid] > 0:
            assert cons[lid] < base[lid] < aggr[lid]


# ── Sector gating ─────────────────────────────────────────────────────────────

def test_insurers_do_not_get_capital_markets_levers():
    names = [p["name"] for p in build_investment_plan(ins_answers(), 100.0, [])]
    assert not any("Trade Reconciliation" in n for n in names)
    assert not any("Order Routing" in n for n in names)
    assert not any("NAV" in n for n in names)


def test_asset_managers_do_not_get_insurance_levers():
    names = [p["name"] for p in build_investment_plan(mf_answers(), 100.0, [])]
    assert not any("Underwriting" in n for n in names)
    assert not any("Claims" in n for n in names)


# ── Answers must matter: the diagnostic has to diagnose ──────────────────────

def test_answers_move_the_numbers():
    small = build_investment_plan(mf_answers(S1_AUM=10.0, S3_TOTAL_OPS_FTE=100.0), 100.0, [])
    large = build_investment_plan(mf_answers(S1_AUM=200.0, S3_TOTAL_OPS_FTE=1500.0), 100.0, [])
    assert sum(p["anv"] for p in large) > 2 * sum(p["anv"] for p in small)


def test_architecture_moves_feasibility():
    legacy = build_investment_plan(
        mf_answers(S1_ERP="Legacy monolith (>10 years old)",
                   S1_ARCH="Siloed On-Premises (Batch)", S1_SILO=9.0,
                   S5_GOVERNANCE_SCORE=30, S1_KTLO=90), 100.0, [])
    modern = build_investment_plan(
        mf_answers(S1_ERP="Modern cloud-native",
                   S1_ARCH="Cloud-Native (AWS/Azure/GCP)", S1_SILO=2.0,
                   S5_GOVERNANCE_SCORE=85, S1_KTLO=45), 100.0, [])
    leg = {p["id"]: p["feasibility"] for p in legacy}
    mod = {p["id"]: p["feasibility"] for p in modern}
    for lid in leg:
        assert mod[lid] > leg[lid]


# ── Regulatory layer must be dynamic and must bite ───────────────────────────

def test_regulatory_risk_responds_to_governance():
    weak = check_regulatory_compliance("lever_11", {"S5_GOVERNANCE_SCORE": 20})
    strong = check_regulatory_compliance("lever_11", {"S5_GOVERNANCE_SCORE": 85})
    assert weak["risk_level"] == "red"
    assert strong["risk_level"] == "green"


def test_red_regulatory_status_caps_lever_anv():
    ok = build_investment_plan(ins_answers(S5_GOVERNANCE_SCORE=85), 100.0, [])
    capped = build_investment_plan(ins_answers(S5_GOVERNANCE_SCORE=20), 100.0, [])
    uw_ok = next(p for p in ok if p["id"] == "lever_11")
    uw_capped = next(p for p in capped if p["id"] == "lever_11")
    assert uw_capped["anv"] < uw_ok["anv"]
    assert uw_capped["warning"] == "REG_CAPPED"


# ── Risk model bounds ─────────────────────────────────────────────────────────

def test_execution_risk_is_clamped():
    assert compute_execution_risk({"S5_GOVERNANCE_SCORE": -50}) <= 0.45
    assert compute_execution_risk({"S5_GOVERNANCE_SCORE": 5000}) >= 0.05
    assert 0.05 <= compute_execution_risk({}) <= 0.45


# ── Legacy diagnostic: explainable, TCO-grounded, no black box ───────────────

def _legacy_inputs(**over):
    from engine.legacy_diagnostic import LegacyInputs
    base = dict(maintenance_cost_m=6.5, biz_value_m=20.0, silo_count=5.0,
                architecture="Hybrid — partial cloud", api_maturity="On-prem with API layer",
                data_ownership=0, lineage=0, dq_sla=0, reg_trace=0, change_mgmt=0,
                unlocked_anv_m=2.0, governance_score=50.0)
    base.update(over)
    return LegacyInputs(**base)


def test_diagnostic_is_fully_explained():
    """Every score must ship with its inputs and arithmetic — client-facing contract."""
    from engine.legacy_diagnostic import run_diagnostic
    res = run_diagnostic(_legacy_inputs())
    assert res["score_math"].endswith(f"= {res['deprecation_score']} / 100")
    for pillar in ("tech_debt", "fragmentation", "governance"):
        assert res["pillar_explain"][pillar]
    assert res["verdict_action"] and res["guardrails"]
    assert res["tco"]["ratio_pct"] == 32  # 6.5 / 20 = 32.5, banker's rounding
    assert res["tco"]["band"] == "watch"


def test_diagnostic_tco_bands():
    from engine.legacy_diagnostic import run_diagnostic
    assert run_diagnostic(_legacy_inputs(maintenance_cost_m=2.0))["tco"]["band"] == "healthy"
    assert run_diagnostic(_legacy_inputs(maintenance_cost_m=15.0))["tco"]["band"] == "critical"
    assert run_diagnostic(_legacy_inputs(maintenance_cost_m=25.0))["tco"]["band"] == "value-negative"


def test_diagnostic_verdicts_move_with_inputs():
    from engine.legacy_diagnostic import run_diagnostic
    healthy = run_diagnostic(_legacy_inputs(
        maintenance_cost_m=1.0, silo_count=2, governance_score=90,
        architecture="Cloud-Native (AWS/Azure/GCP)", api_maturity="Modern cloud-native"))
    rotten = run_diagnostic(_legacy_inputs(
        maintenance_cost_m=18.0, silo_count=9, governance_score=60,
        architecture="Siloed On-Premises (Batch)", api_maturity="Legacy monolith (>10 years old)"))
    blocked = run_diagnostic(_legacy_inputs(
        maintenance_cost_m=18.0, silo_count=9, governance_score=30,
        architecture="Siloed On-Premises (Batch)", api_maturity="Legacy monolith (>10 years old)"))
    assert healthy["verdict"] == "KEEP AND OPTIMIZE"
    assert rotten["verdict"] == "REPLACE THE CORE"
    assert blocked["verdict"] == "FIX GOVERNANCE FIRST"
    assert rotten["tco"]["security_flag"] is True
    assert healthy["tco"]["security_flag"] is False
    # Client-facing language: verdicts and playbooks must be jargon-free
    for res in (healthy, rotten, blocked):
        text = res["verdict_action"] + " ".join(res["guardrails"])
        assert "strangler" not in text.lower()
        assert "—" not in text, "em dashes are banned from report copy"


# ── Bottom-up rebuild cost model ──────────────────────────────────────────────

def test_rebuild_estimate_is_bottom_up_and_sums():
    from engine.legacy_diagnostic import estimate_rebuild_cost
    est = estimate_rebuild_cost(6.5, 5, "Hybrid — partial cloud",
                                "On-prem with API layer", 50)
    assert abs(sum(c["amount_m"] for c in est["breakdown"]) - est["total_m"]) < 0.5
    assert est["low_m"] < est["total_m"] < est["high_m"]
    assert len(est["breakdown"]) == 6
    for c in est["breakdown"]:
        assert c["basis"], "every cost line must state its driver"


def test_rebuild_estimate_responds_to_complexity():
    from engine.legacy_diagnostic import estimate_rebuild_cost
    easy = estimate_rebuild_cost(10, 3, "Cloud-Native (AWS/Azure/GCP)",
                                 "Modern cloud-native", 85)
    hard = estimate_rebuild_cost(10, 9, "Siloed On-Premises (Batch)",
                                 "Legacy monolith (>10 years old)", 25)
    assert hard["total_m"] > easy["total_m"] * 1.5, \
        "a monolithic, siloed, ungoverned estate must cost far more to replace"


def test_diagnostic_carries_rebuild_breakdown():
    from engine.legacy_diagnostic import run_diagnostic
    res = run_diagnostic(_legacy_inputs())
    assert res["rebuild_estimate"] is not None
    assert res["self_funding"]["rebuild_cost_m"] == res["rebuild_estimate"]["total_m"]
    # a client-provided figure overrides the model and disables the breakdown
    res2 = run_diagnostic(_legacy_inputs(rebuild_cost_m=30.0))
    assert res2["self_funding"]["rebuild_cost_m"] == 30.0
    assert res2["rebuild_estimate"] is None


# ── Foundation decision ───────────────────────────────────────────────────────

def test_foundation_lever_is_coherent():
    plan = build_investment_plan(mf_answers(), 100.0, [], foundation_decision=True)
    fnd = next(p for p in plan if p["id"] == "lever_0_foundation")
    assert fnd["anv"] > 0, "foundation lever must carry its legacy-savings ANV"
    assert fnd["payback"] > 0
    assert fnd["budget_approved"], "foundation must be funded first on a $100M budget"
