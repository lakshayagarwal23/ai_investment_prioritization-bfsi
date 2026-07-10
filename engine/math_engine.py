"""
engine/math_engine.py

BFSI AI Investment Engine — Core Computation Module.

DESIGN CONTRACT
---------------
1. Every lever formula reads ONLY (a) questions that are actually asked in
   config/questions.py, or (b) parameters derived from asked questions via
   multipliers declared in config/value_pools.py CONSTANTS. No lever is
   priced from a phantom input.
2. All numbers are deterministic: same answers -> same plan (tested).
3. Benefit attribution: the shared ops-FTE pool is split across levers
   (recon 20%, claims 40%, onboarding 15%, compliance 25% — sums to 100%)
   so FTE savings are never double-counted across the portfolio.
4. Scenario haircuts (50/60/75%) are the benefits-realisation discount;
   execution risk (governance-driven) is applied ONCE, at portfolio level,
   and labelled wherever it is shown.
"""

from __future__ import annotations
from config.value_pools import BFSI_LEVERS, CONSTANTS, GOALS, PLATFORM_GATED_LEVERS
from engine.regulatory import check_regulatory_compliance

# ── Loaded costs and derivation multipliers (auditable in the Appendix) ──────
_OPS_COST = CONSTANTS["Ops_FTE_Loaded_Cost_USD"]
_UW_COST = CONSTANTS["Underwriter_Loaded_Cost_USD"]
_ANALYST_COST = CONSTANTS["Analyst_Loaded_Cost_USD"]
_COMPLIANCE_COST = CONSTANTS["Compliance_FTE_Loaded_Cost_USD"]
_NAV_COST = CONSTANTS["NAV_Ops_Loaded_Cost_USD"]
_ONBOARD_COST = CONSTANTS["Onboarding_FTE_Loaded_Cost_USD"]
_PREMIUM = CONSTANTS["Avg_Annual_Premium_USD"]
_NB_MARGIN = CONSTANTS["New_Business_Margin_Pct"] / 100.0
_POLICY_MARGIN = _PREMIUM * _NB_MARGIN          # margin per policy-year
_INS_CUST_MARGIN = CONSTANTS["Insurance_Customer_Margin_USD_Yr"]
_MF_FOLIO_MARGIN = CONSTANTS["MF_Folio_Margin_USD_Yr"]


def _f(a: dict, key: str, default: float) -> float:
    """Answer as float with a safe fallback (prefill may store strings)."""
    try:
        return float(a.get(key, default))
    except (TypeError, ValueError):
        return default


# ─────────────────────────────────────────────────────────────────────────────
# SHARED BACKBONE
# ─────────────────────────────────────────────────────────────────────────────

def anv_backbone(baseline_cost: float, post_ai_cost: float,
                 incremental_revenue: float, run_cost_ai: float) -> float:
    savings = baseline_cost - post_ai_cost
    return savings + incremental_revenue - run_cost_ai


def risk_adjusted_roi(total_impl_cost: float, anv: float, execution_risk: float) -> float:
    if total_impl_cost <= 0:
        return 0.0
    raw_roi = (anv / total_impl_cost) * 100.0
    return raw_roi * (1.0 - execution_risk)


def payback_months(total_impl_cost: float, steady_anv: float) -> float:
    """Ramped payback: Year 1 = 25%, Year 2 = 60%, Year 3+ = 100% of steady ANV."""
    if steady_anv <= 0:
        return 999.0

    y1_cf = steady_anv * 0.25
    if y1_cf >= total_impl_cost:
        return (total_impl_cost / y1_cf) * 12.0

    y2_cf = steady_anv * 0.60
    if y1_cf + y2_cf >= total_impl_cost:
        rem = total_impl_cost - y1_cf
        return 12.0 + (rem / y2_cf) * 12.0

    y3_cf = steady_anv * 1.0
    if y1_cf + y2_cf + y3_cf >= total_impl_cost:
        rem = total_impl_cost - y1_cf - y2_cf
        return 24.0 + (rem / y3_cf) * 12.0

    rem = total_impl_cost - y1_cf - y2_cf - y3_cf
    return 36.0 + (rem / y3_cf) * 12.0


def compute_dynamic_feasibility(base_feasibility: int, answers: dict) -> int:
    """Per-firm feasibility from architecture, core-system age, silos,
    keep-the-lights-on burden, and governance — all asked questions."""
    score = float(base_feasibility)

    erp = str(answers.get("S1_ERP", "")).lower()
    if "monolith" in erp:
        score -= 15
    elif "cloud-native" in erp:
        score += 10

    arch = str(answers.get("S1_ARCH", "")).lower()
    if "siloed" in arch:
        score -= 10
    elif "cloud-native" in arch:
        score += 5

    silos = _f(answers, "S1_SILO", 5.0)
    if silos >= 7:
        score -= 10
    elif silos <= 3:
        score += 5

    ktlo = _f(answers, "S1_KTLO", 72.0)
    if ktlo >= 80:
        score -= 10
    elif ktlo <= 50:
        score += 5

    gov = _f(answers, "S5_GOVERNANCE_SCORE", 50.0)
    if gov > 75:
        score += 10
    elif gov < 40:
        score -= 15

    return max(0, min(100, int(score)))


# ─────────────────────────────────────────────────────────────────────────────
# LEVER-SPECIFIC FORMULAS  (raw steady-state ANV, before scenario haircut)
# ─────────────────────────────────────────────────────────────────────────────

def lever_1_trade_recon(a: dict, scenario: str = "base") -> float:
    """Recon pool = 20% of ops FTE; breaks & fails derived from ops size and
    the manual share of flow (1 - STP)."""
    ops_fte = _f(a, "S3_TOTAL_OPS_FTE", 400.0)
    stp = _f(a, "S3_STP", 65) / 100.0
    manual_share = max(0.0, 1.0 - stp)

    recon_fte = ops_fte * (CONSTANTS["Ops_Pool_Attribution_Recon_Pct"] / 100.0)
    stp_target = 0.90 if scenario != "aggressive" else 0.95
    stp_uplift = max(0.0, stp_target - stp)
    # share of today's manual recon work that the uplift removes
    captured = stp_uplift / manual_share if manual_share > 0 else 0.0

    fte_baseline = recon_fte * _OPS_COST * 0.70          # 70% of their time is break-fixing
    breaks = ops_fte * CONSTANTS["Recon_Breaks_per_OpsFTE_x_ManualShare"] * manual_share
    break_cost = breaks * 15.0 * 1.20                    # 15 min/break @ $1.20/min loaded
    automation_savings = (fte_baseline + break_cost) * captured

    fails = ops_fte * CONSTANTS["Settlement_Fails_per_OpsFTE_x_ManualShare"] * manual_share
    error_avoidance = fails * 15_000 * 0.60              # $15K avg fail penalty, 60% avoided

    run_cost = 250_000
    return automation_savings + error_avoidance - run_cost


def lever_2_execution(a: dict, scenario: str = "base") -> float:
    """Implementation-shortfall savings on the NON-electronic share of flow only."""
    aum = _f(a, "S1_AUM", 50.0) * 1e9
    electronic = _f(a, "S2_ELECTRONIC_FLOW", 60) / 100.0
    notional = aum * 1.5                                  # annual turnover
    addressable = notional * max(0.0, 1.0 - electronic)
    bps_saved = 1.5
    run_cost = 600_000
    return (addressable * bps_saved / 10_000) - run_cost


def lever_3_research(a: dict, scenario: str = "base") -> float:
    aum_b = _f(a, "S1_AUM", 50.0)
    analysts = max(10.0, min(80.0, aum_b * 0.8))          # derived: ~0.8 analysts per $B
    parse_hrs = 450.0
    automation = 0.85
    hours_saved = parse_hrs * analysts * automation
    efficiency_val = hours_saved * (_ANALYST_COST / 2000.0)

    # Broader coverage: +2bps incremental alpha on ~10% of active AUM
    coverage_val = (2.0 / 10_000) * (aum_b * 1e9 * 0.10)

    run_cost = 400_000
    return coverage_val + efficiency_val - run_cost


def lever_4_distribution(a: dict, scenario: str = "base") -> float:
    """Freed sales capacity redeployed to coverage. Admin burden proxied by
    the non-digital share of applications (asked), sales bench derived from ops size."""
    ops_fte = _f(a, "S3_TOTAL_OPS_FTE", 400.0)
    admin_share = max(0.0, 1.0 - _f(a, "S2_ELECTRONIC_FLOW", 60) / 100.0)
    sales_fte = ops_fte * 0.15
    freed = sales_fte * admin_share * 0.40                # 40% of admin time automatable
    new_aum_per_freed_fte = 100e6                         # $100M new AUM per redeployed FTE
    fee_bps = 25
    run_cost = 500_000
    return (freed * new_aum_per_freed_fte * fee_bps / 10_000) - run_cost


def lever_5_onboarding(a: dict, scenario: str = "base") -> float:
    ops_fte = _f(a, "S3_TOTAL_OPS_FTE", 400.0)
    onboarding_fte = ops_fte * (CONSTANTS["Ops_Pool_Attribution_Onboarding_Pct"] / 100.0)
    fte_savings = onboarding_fte * _ONBOARD_COST * 0.75

    false_pos = _f(a, "S4_AML_FALSE_POS", 85) / 100.0
    alerts = ops_fte * CONSTANTS["AML_Alerts_per_Ops_FTE"]
    aml_save = alerts * false_pos * 60.0 * 0.80           # $60/false-positive investigation, 80% cut

    # Faster ramp: 35 days of fees earned earlier on new-client AUM
    ramp_value = 50 * 200e6 * (30 / 10_000) * (35.0 / 365.0)

    run_cost = 350_000
    return fte_savings + aml_save + ramp_value - run_cost


def lever_6_compliance(a: dict, scenario: str = "base") -> float:
    ops_fte = _f(a, "S3_TOTAL_OPS_FTE", 400.0)
    compliance_fte = ops_fte * (CONSTANTS["Ops_Pool_Attribution_Compliance_Pct"] / 100.0)
    fte_savings = compliance_fte * _COMPLIANCE_COST * 0.55

    # Reg-change effort: months-to-implement (asked) x team cost, halved by AI
    reg_months = _f(a, "S4_REG_MONTHS", 6.0)
    changes_per_year = 2.0
    team_cost_per_month = 120_000
    reg_change_save = reg_months * team_cost_per_month * changes_per_year * 0.50

    run_cost = 300_000
    return fte_savings + reg_change_save - run_cost


def lever_7_nav(a: dict, scenario: str = "base") -> float:
    aum_b = _f(a, "S1_AUM", 50.0)
    nav_fte = max(4.0, min(20.0, aum_b * 0.16))           # derived: ~0.16 NAV ops per $B
    fte_savings = nav_fte * _NAV_COST * 0.55
    error_avoidance = 1 * 500_000 * 0.80                  # one material NAV error/yr avoided
    run_cost = 400_000
    return fte_savings + error_avoidance - run_cost


def lever_8_personalization(a: dict, scenario: str = "base") -> float:
    aum = _f(a, "S1_AUM", 50.0) * 1e9
    churn, ret_uplift, fee_bps = 0.05, 0.15, 30
    run_cost = 600_000
    return (aum * churn * ret_uplift * fee_bps / 10_000) - run_cost


def lever_9_data_platform(a: dict, scenario: str = "base") -> float:
    """Recon-spend elimination from a golden-source layer. Scoped as a focused
    consolidation program — the full core rebuild is the Foundation decision,
    priced separately. Build capex lives in impl_cost_estimate, NOT amortized
    here as well (that double-counted the investment)."""
    silos = _f(a, "S1_SILO", 5.0)
    recon_cost = silos * 400_000                          # $400K/yr duplicated-data ops per silo
    run_cost = 300_000
    return (recon_cost * 0.80) - run_cost


def lever_10_corp_actions(a: dict, scenario: str = "base") -> float:
    volume = 1200.0 * 12                                  # CA events/yr, peer-median book
    processing_cost = volume * 15.0 * 1.20 * 0.90
    error_avoidance = volume * 0.005 * 8_000 * 0.85
    run_cost = 200_000
    return processing_cost + error_avoidance - run_cost


def lever_11_underwriting_automation(a: dict, scenario: str = "base") -> float:
    """Underwriting bench derived from application volume (asked)."""
    apps = _f(a, "S2_ANNUAL_UNDERWRITING_APPS", 250_000)
    underwriters = max(4.0, apps * CONSTANTS["Underwriters_per_Annual_Apps"])

    redeploy = {"conservative": 0.45, "base": 0.60, "aggressive": 0.70}.get(scenario, 0.60)
    fte_savings = underwriters * _UW_COST * redeploy

    # Faster decisions lift conversion a few points — not the old 50% fantasy
    conversion_uplift = 0.04
    revenue_uplift = apps * conversion_uplift * _POLICY_MARGIN

    # Better-fit policies lapse less: 0.8pp improvement on the in-force book
    in_force = apps * CONSTANTS["InForce_Policies_per_Annual_App"]
    lapse_savings = in_force * 0.008 * _POLICY_MARGIN

    run_cost = 400_000
    return fte_savings + revenue_uplift + lapse_savings - run_cost


def lever_12_claims_processing(a: dict, scenario: str = "base") -> float:
    claims = _f(a, "S3_ANNUAL_CLAIMS", 500_000)
    ops_fte = _f(a, "S3_TOTAL_OPS_FTE", 400.0)
    processor_fte = ops_fte * (CONSTANTS["Ops_Pool_Attribution_Claims_Pct"] / 100.0)
    current_stp = _f(a, "S3_STP", 65) / 100.0

    params = {
        "conservative": {"target_stp": 0.75, "fte_reduction": 0.45},
        "base": {"target_stp": 0.85, "fte_reduction": 0.60},
        "aggressive": {"target_stp": 0.92, "fte_reduction": 0.70},
    }.get(scenario, {"target_stp": 0.85, "fte_reduction": 0.60})

    fte_savings = processor_fte * params["fte_reduction"] * _OPS_COST
    stp_uplift = max(0.0, params["target_stp"] - current_stp)
    stp_savings = claims * stp_uplift * 25.0              # $25 manual-handling cost per claim

    fraud_prevention = claims * 0.005 * 1_200 * 0.30      # 0.5% of claims, $1.2K avg, 30% caught
    run_cost = 400_000
    return fte_savings + stp_savings + fraud_prevention - run_cost


def _customer_base(a: dict) -> float:
    """In-force policies for insurers; folios for asset managers. Derived
    from asked volumes via multipliers declared in CONSTANTS."""
    sector = str(a.get("target_sector", ""))
    if "Insurance" in sector:
        apps = _f(a, "S2_ANNUAL_UNDERWRITING_APPS", 250_000)
        return apps * CONSTANTS["InForce_Policies_per_Annual_App"]
    aum_b = _f(a, "S1_AUM", 50.0)
    return aum_b * CONSTANTS["MF_Folios_per_AUM_Billion"]


def lever_13_cdp(a: dict, scenario: str = "base") -> float:
    customers = _customer_base(a)
    sector = str(a.get("target_sector", ""))
    margin = _INS_CUST_MARGIN if "Insurance" in sector else _MF_FOLIO_MARGIN

    cross_sell = customers * 0.03 * margin                # 3% of base adopts one more product
    retention = customers * 0.05 * 0.10 * margin          # 10% cut of a 5% churn pool
    efficiency = 5.0 * _OPS_COST * 0.60                   # small campaign-ops team automated
    run_cost = 600_000
    return cross_sell + retention + efficiency - run_cost


def lever_14_digital_onboarding(a: dict, scenario: str = "base") -> float:
    """Application-dropout recovery priced from asked volumes and onboarding days."""
    apps = _f(a, "S2_ANNUAL_UNDERWRITING_APPS", 250_000)
    days = _f(a, "S2_QUOTE_TO_BIND_DAYS", 7.0)

    dropout = min(0.50, days * 0.03)                      # each onboarding day ~3pp dropout
    recovered = apps * dropout * 0.40                     # 40% of dropouts recoverable
    dropout_value = recovered * _POLICY_MARGIN

    onboarding_staff = 12.0
    efficiency = onboarding_staff * _ONBOARD_COST * 0.70
    run_cost = 400_000
    return dropout_value + efficiency - run_cost


# ─────────────────────────────────────────────────────────────────────────────
# GOVERNANCE / EXECUTION RISK
# ─────────────────────────────────────────────────────────────────────────────

def compute_governance_readiness(a: dict) -> float:
    return max(0.0, min(100.0, _f(a, "S5_GOVERNANCE_SCORE", 50.0)))


def compute_execution_risk(a: dict) -> float:
    """Governance-driven execution discount, dampened and clamped so it is a
    haircut, not a coin-flip: gov 50 -> 25% risk, gov 0 -> 45%, gov 100 -> 5%."""
    gov = compute_governance_readiness(a)
    raw = (1.0 - gov / 100.0) * CONSTANTS["Exec_Risk_Governance_Dampener"]
    floor = CONSTANTS["Exec_Risk_Floor_Pct"] / 100.0
    cap = CONSTANTS["Exec_Risk_Cap_Pct"] / 100.0
    return max(floor, min(cap, raw))


# ─────────────────────────────────────────────────────────────────────────────
# LEVER CATALOGUE
# ─────────────────────────────────────────────────────────────────────────────

LEVER_COMPUTE = {
    "lever_1":  lever_1_trade_recon,
    "lever_2":  lever_2_execution,
    "lever_3":  lever_3_research,
    "lever_4":  lever_4_distribution,
    "lever_5":  lever_5_onboarding,
    "lever_6":  lever_6_compliance,
    "lever_7":  lever_7_nav,
    "lever_8":  lever_8_personalization,
    "lever_9":  lever_9_data_platform,
    "lever_10": lever_10_corp_actions,
    "lever_11": lever_11_underwriting_automation,
    "lever_12": lever_12_claims_processing,
    "lever_13": lever_13_cdp,
    "lever_14": lever_14_digital_onboarding,
}

IMPACT_THRESHOLD = 65
FEASIBILITY_THRESHOLD = 60


def compute_dynamic_impact(lever: dict, answers: dict, primary_goals: list[str]) -> int:
    base_impact = float(lever.get("base_impact", 50.0))

    val_driver = lever.get("value_driver")
    if not val_driver or val_driver["answer_key"] not in answers:
        value_pool_score = base_impact
    else:
        answer_val = _f(answers, val_driver["answer_key"], float(val_driver["typical"]))
        typical_val = float(val_driver["typical"])
        if val_driver["kind"] == "scale":
            ratio = answer_val / typical_val if typical_val else 1.0
        else:  # gap: a high answer means little headroom left
            ratio = (100.0 - answer_val) / (100.0 - typical_val) if typical_val != 100.0 else 1.0
        ratio = max(0.0, min(ratio, CONSTANTS["Impact_ValuePool_Cap"]))
        value_pool_score = base_impact * ratio

    priority_map = {"P0": 100, "P1": 75, "P2": 50, "P3": 25}
    urgency = priority_map.get(lever.get("priority", "P2"), 50)

    wt_val_pool = CONSTANTS["Impact_Weight_ValuePool_Pct"] / 100.0
    wt_urgency = CONSTANTS["Impact_Weight_Urgency_Pct"] / 100.0
    raw_impact = (value_pool_score * wt_val_pool) + (urgency * wt_urgency)

    if primary_goals:
        matched = any(goal in primary_goals for goal in lever.get("goal_alignment", []))
        goal_multiplier = 1.0 if matched else CONSTANTS["Impact_OffGoal_Floor"]
    else:
        goal_multiplier = 1.0

    return max(0, min(100, int(raw_impact * goal_multiplier)))


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def calculate_investment_plan(answers: dict, budget_usd_m: float = 999.0,
                              primary_goals: list[str] = None,
                              llm_intel: dict | None = None,
                              scenario: str = "base",
                              foundation_decision: bool = False) -> list[dict]:
    """Score all sector-applicable levers, rank by goal alignment then value,
    and allocate the budget greedily to positive-value levers."""
    if primary_goals is None:
        primary_goals = []

    exec_risk = compute_execution_risk(answers)
    sector = answers.get("target_sector", "all")
    feasible_levers = [l for l in BFSI_LEVERS
                       if "all" in l.get("sectors", ["all"]) or sector in l.get("sectors", ["all"])]

    haircuts = {"conservative": 0.50, "base": 0.60, "aggressive": 0.75}
    haircut = haircuts.get(scenario, 0.60)

    scored = []
    for lever in feasible_levers:
        lid = lever["id"]
        compute_fn = LEVER_COMPUTE.get(lid)

        warning_flag = None
        if compute_fn:
            try:
                anv = compute_fn(answers, scenario=scenario) * haircut
            except Exception:
                # Surface the failure — never rank a broken lever as a $0 result
                anv = 0.0
                warning_flag = "COMPUTE_ERROR"
        else:
            anv = lever.get("anv_estimate", 0.0) * haircut

        # Regulatory check BEFORE final economics: a non-compliant lever has
        # its automation benefit capped until mitigations land.
        reg_status = check_regulatory_compliance(lid, answers)
        if anv > 0 and reg_status.get("risk_level") == "red":
            cap = CONSTANTS["Reg_NonCompliant_Automation_Cap_Pct"] / 100.0
            anv *= cap
            warning_flag = warning_flag or "REG_CAPPED"

        if anv < 0 and warning_flag is None:
            warning_flag = "VALUE_DESTRUCTIVE"

        impl_cost = lever.get("impl_cost_estimate", 1_000_000)
        payback = payback_months(impl_cost, anv)
        roi = risk_adjusted_roi(impl_cost, anv, exec_risk)

        impact = compute_dynamic_impact(lever, answers, primary_goals)
        feasibility = compute_dynamic_feasibility(lever.get("base_feasibility", 50), answers)
        # A funded foundation removes the data-platform constraint, so gated
        # levers become deliverable: their readiness rises above the threshold
        # (and the quadrant follows naturally, keeping the matrix consistent).
        if foundation_decision and lid in PLATFORM_GATED_LEVERS:
            feasibility = max(feasibility, FEASIBILITY_THRESHOLD + 5)
        speed_score = max(0, min(100, int(100 * (36 - payback) / 35)))

        if impact >= IMPACT_THRESHOLD and feasibility >= FEASIBILITY_THRESHOLD:
            quadrant = "Strategic Bets"
        elif impact < IMPACT_THRESHOLD and feasibility >= FEASIBILITY_THRESHOLD:
            quadrant = "Quick Wins / Fill-ins"
        elif impact >= IMPACT_THRESHOLD and feasibility < FEASIBILITY_THRESHOLD:
            quadrant = "Park (Data-Blocked)"
        else:
            quadrant = "De-prioritize"

        goal_alignment = sum(1.0 for goal in primary_goals
                             if goal in lever.get("goal_alignment", []))

        scored.append({
            "name":        lever["name"],
            "short_name":  lever.get("short_name", lever["name"]),
            "id":          lid,
            "impact":      impact,
            "speed":       speed_score,
            "feasibility": feasibility,
            "anv":         anv,
            "anv_m":       round(anv / 1e6, 2),
            "impl_cost":   impl_cost,
            "payback":     round(payback, 1),
            "roi":         round(roi, 1),
            "quadrant":    quadrant,
            "priority":    lever.get("priority", "P2"),
            "goal_weight": goal_alignment,
            "warning":     warning_flag,
            "reg_status":  reg_status,
            "budget_approved": False,
        })

    if foundation_decision:
        scored.append(_foundation_lever(answers))

    # Rank by goal alignment first, then ANV
    scored.sort(key=lambda x: (x["goal_weight"], x["anv"]), reverse=True)

    # Greedy budget allocation. Capital discipline: only positive-value levers
    # the engine actually recommends executing (Strategic Bets / Quick Wins)
    # consume budget — parked and de-prioritized levers never do.
    cumulative_cost = 0.0
    budget_limit = budget_usd_m * 1e6
    for s in scored:
        if s["anv"] <= 0 or s["warning"] == "COMPUTE_ERROR":
            continue
        if s["quadrant"] not in ("Strategic Bets", "Quick Wins / Fill-ins"):
            continue
        if cumulative_cost + s["impl_cost"] <= budget_limit:
            s["budget_approved"] = True
            cumulative_cost += s["impl_cost"]

    return scored


def _foundation_lever(answers: dict) -> dict:
    """Foundation modernization as a first-class portfolio line: its ANV is the
    retained legacy-maintenance savings, its cost the estimated rebuild capex."""
    from engine.legacy_diagnostic import run_diagnostic, LegacyInputs
    inputs = LegacyInputs(
        maintenance_cost_m=_f(answers, "S5_MAINTENANCE_COST", 6.5),
        biz_value_m=_f(answers, "S5_BIZ_VALUE", 20.0),
        silo_count=_f(answers, "S1_SILO", 5.0),
        architecture=answers.get("S1_ARCH", "Hybrid — partial cloud"),
        api_maturity=answers.get("S1_ERP", "On-prem with API layer"),
        data_ownership=0, lineage=0, dq_sla=0, reg_trace=0, change_mgmt=0,
        unlocked_anv_m=0,
        governance_score=compute_governance_readiness(answers),
    )
    res = run_diagnostic(inputs)
    rebuild_capex = res["self_funding"]["rebuild_cost_m"] * 1e6
    legacy_savings = res["self_funding"]["legacy_annual_savings_m"] * 1e6
    return {
        "name":        "Foundation Modernization",
        "short_name":  "Modernization",
        "id":          "lever_0_foundation",
        "impact":      90,
        "speed":       20,
        "feasibility": 80,
        "anv":         legacy_savings,
        "anv_m":       round(legacy_savings / 1e6, 2),
        "impl_cost":   rebuild_capex,
        "payback":     round(payback_months(rebuild_capex, legacy_savings), 1),
        "roi":         round(risk_adjusted_roi(rebuild_capex, legacy_savings, 0.2), 1),
        "quadrant":    "Strategic Bets",
        "priority":    "P0",
        "goal_weight": 5,
        "warning":     None,
        "reg_status":  check_regulatory_compliance("lever_9", answers),
        "budget_approved": False,
    }


build_investment_plan = calculate_investment_plan
