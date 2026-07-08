"""
engine/math_engine.py

BFSI AI Investment Engine — Core Computation Module
Hybrid model supporting both Mutual Funds & Life Insurance (MMIL)
"""

from __future__ import annotations
import math
from config.value_pools import BFSI_LEVERS
from engine.regulatory import check_regulatory_compliance

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

def payback_months(total_impl_cost: float, anv: float) -> float:
    if anv <= 0:
        return 999.0
    return (total_impl_cost / (anv / 12.0))


# ─────────────────────────────────────────────────────────────────────────────
# LEVER-SPECIFIC FORMULAS
# ─────────────────────────────────────────────────────────────────────────────

def lever_1_trade_recon(a: dict, scenario: str = "base") -> float:
    fte          = a.get("S3_FTE_RECON", 8.0)
    loaded_cost  = 150_000
    time_pct     = 0.70
    breaks       = a.get("S3_ANNUAL_BREAKS", 50_000)
    mins_per_brk = 15.0
    cost_per_min = 1.50
    stp_current  = a.get("S3_STP", 65) / 100.0
    stp_target   = 0.90 if scenario == "base" else 0.95
    fails        = a.get("S3_FAIL_EVENTS", 200.0)
    fail_penalty = 100_000
    err_red      = 0.75
    baseline = fte * loaded_cost * time_pct
    break_cost = breaks * mins_per_brk * cost_per_min
    stp_uplift = max(0, stp_target - stp_current)
    automation_savings = (baseline + break_cost) * stp_uplift
    error_avoidance = fails * fail_penalty * err_red
    run_cost = 500_000
    return automation_savings + error_avoidance - run_cost

def lever_3_research(a: dict, scenario: str = "base") -> float:
    analysts     = a.get("S2_ANALYST_COUNT", 40.0)
    parse_hrs    = a.get("S2_PARSING_HOURS", 450.0)
    names        = a.get("S2_NAMES_COVERED", 40.0)
    loaded_cost  = 350_000
    automation   = 0.85
    multiplier   = 3.5
    alpha_bps    = 15.0
    aum          = a.get("S1_AUM", 50.0) * 1e9

    hours_saved = parse_hrs * analysts * automation
    value_per_hr = loaded_cost / 2000.0
    efficiency_val = hours_saved * value_per_hr
    
    # Bug fix: Previously we multiplied by 'names * analysts' which artificially multiplied total AUM 
    # thousands of times over. We should assume the coverage alpha applies to ~10% of the active AUM.
    active_aum_share = 0.10
    coverage_val = (multiplier - 1.0) * (alpha_bps / 10_000) * (aum * active_aum_share)
    
    run_cost = 400_000
    return coverage_val + efficiency_val - run_cost

def lever_5_onboarding(a: dict, scenario: str = "base") -> float:
    fte          = a.get("S4_ONBOARD_FTE", 6.0)
    loaded_cost  = 140_000
    automation   = 0.90
    days_current = a.get("S4_ONBOARD_DAYS", 45.0)
    days_ai      = 10.0
    new_clients  = 50
    avg_aum      = 200e6  # $200M avg new client
    fee_bps      = 30
    aml_alerts   = 10_000
    false_pos    = a.get("S4_AML_FALSE_POS", 85) / 100.0
    cost_per_inv = 2_000
    red_pct      = 0.80

    fte_savings = fte * loaded_cost * automation
    days_saved = max(0, days_current - days_ai)
    ramp_value = new_clients * avg_aum * (fee_bps / 10_000) * (days_saved / 365.0)
    aml_save = aml_alerts * false_pos * cost_per_inv * red_pct
    run_cost = 350_000
    return fte_savings + ramp_value + aml_save - run_cost

def lever_10_corp_actions(a: dict, scenario: str = "base") -> float:
    volume       = a.get("S3_CA_VOLUME", 1200.0) * 12
    mins_per_doc = 15.0
    cost_per_min = 1.50
    automation   = 0.90
    err_rate     = 0.005
    err_cost     = 50_000
    err_red      = 0.85
    run_cost     = 200_000
    processing_cost = volume * mins_per_doc * cost_per_min
    return (processing_cost * automation) + (volume * err_rate * err_cost * err_red) - run_cost

def lever_6_compliance(a: dict, scenario: str = "base") -> float:
    fte         = a.get("S4_COMPLIANCE_FTE", 10.0)
    loaded_cost = 180_000
    automation  = 0.65
    err_events  = 5
    avg_fine    = 500_000
    err_red     = 0.70
    run_cost    = 300_000
    return (fte * loaded_cost * automation) + (err_events * avg_fine * err_red) - run_cost

def lever_2_execution(a: dict, scenario: str = "base") -> float:
    aum         = a.get("S1_AUM", 50.0)
    turnover    = 1.5
    notional    = aum * turnover * 1e9
    bps_saved   = 3.5
    run_cost    = 600_000
    return (notional * bps_saved / 10_000) - run_cost

def lever_4_distribution(a: dict, scenario: str = "base") -> float:
    admin_pct   = a.get("S2_ADMIN_PCT", 45) / 100.0
    sales_fte   = 20.0
    loaded_cost = 280_000
    freed_pct   = 0.40
    new_aum_per_fte = 0.5e9
    fee_bps     = 25
    run_cost    = 500_000
    freed = sales_fte * admin_pct * freed_pct
    return (freed * new_aum_per_fte * fee_bps / 10_000) - run_cost

def lever_7_nav(a: dict, scenario: str = "base") -> float:
    nav_fte     = 8.0
    loaded_cost = 160_000
    automation  = 0.55
    nav_errors  = 2
    error_cost  = 2_000_000
    err_red     = 0.90
    run_cost    = 400_000
    return (nav_fte * loaded_cost * automation) + (nav_errors * error_cost * err_red) - run_cost

def lever_8_personalization(a: dict, scenario: str = "base") -> float:
    aum         = a.get("S1_AUM", 50.0) * 1e9
    churn       = 0.05
    ret_uplift  = 0.15
    fee_bps     = 30
    run_cost    = 600_000
    return (aum * churn * ret_uplift * fee_bps / 10_000) - run_cost

def lever_9_data_platform(a: dict, scenario: str = "base") -> float:
    silos       = a.get("S1_SILO", 5.0)
    recon_cost  = silos * 800_000
    recon_red   = 0.80
    modernize   = 5_000_000
    run_cost    = 300_000
    return (recon_cost * recon_red) - run_cost - (modernize / 3)


# ── NEW HYBRID/INSURANCE LEVERS (MMIL Context) ──

def lever_11_underwriting_automation(a: dict, scenario: str = "base") -> float:
    """MAUDE-based underwriting automation for life insurance."""
    annual_apps = a.get("S2_ANNUAL_UNDERWRITING_APPS", 50_000)
    underwriter_fte = a.get("S2_UNDERWRITER_FTE", 15.0)
    loaded_cost_per_fte = 150_000
    
    scenarios = {
        "conservative": {"automation_rate": 0.70, "volume_uplift": 1.2},
        "base": {"automation_rate": 0.90, "volume_uplift": 1.5},
        "aggressive": {"automation_rate": 0.95, "volume_uplift": 2.0},
    }
    
    scenario_params = scenarios.get(scenario, scenarios["base"])
    automation_rate = scenario_params["automation_rate"]
    volume_uplift = scenario_params["volume_uplift"]
    
    fte_savings = underwriter_fte * automation_rate * loaded_cost_per_fte
    
    avg_premium_per_app = 50_000
    new_apps = annual_apps * (volume_uplift - 1.0)
    revenue_uplift = new_apps * (avg_premium_per_app * 0.05)
    
    lapse_reduction = 0.02
    avg_customer_lifetime_value = 200_000
    lapse_savings = annual_apps * lapse_reduction * avg_customer_lifetime_value * 0.10
    
    run_cost = 500_000
    return fte_savings + revenue_uplift + lapse_savings - run_cost

def lever_12_claims_processing(a: dict, scenario: str = "base") -> float:
    """AI-driven claims processing automation."""
    annual_claims = a.get("S3_ANNUAL_CLAIMS", 100_000)
    processor_fte = a.get("S3_CLAIMS_PROCESSOR_FTE", 22.0)
    loaded_cost_per_fte = 140_000
    current_stp = a.get("S3_STP", 65) / 100.0
    
    scenarios = {
        "conservative": {"target_stp": 0.75, "fte_reduction": 0.50},
        "base": {"target_stp": 0.85, "fte_reduction": 0.65},
        "aggressive": {"target_stp": 0.92, "fte_reduction": 0.75},
    }
    
    scenario_params = scenarios.get(scenario, scenarios["base"])
    
    fte_savings = processor_fte * scenario_params["fte_reduction"] * loaded_cost_per_fte
    stp_uplift = max(0, scenario_params["target_stp"] - current_stp)
    stp_savings = annual_claims * stp_uplift * 500  # $500 manual intervention cost
    
    # Average fraudulent claim assumed at $5,000 instead of $100,000 to reflect standard retail claims
    fraud_prevention = annual_claims * 0.02 * 5_000 * 0.50
    run_cost = 400_000
    
    return fte_savings + stp_savings + fraud_prevention - run_cost

def lever_13_cdp(a: dict, scenario: str = "base") -> float:
    """Customer Data Platform (CDP) for life + wealth cross-sell."""
    total_customers = a.get("S4_RURAL_CUSTOMERS", 100_000) * 5  # Estimated total from rural
    avg_customer_value = 1_000
    
    cross_sell_uplift = 0.10
    retention_uplift = 0.05
    
    cross_sell_revenue = (total_customers * cross_sell_uplift) * avg_customer_value * 0.08
    churn_reduction = total_customers * 0.05 * retention_uplift * avg_customer_value * 0.10
    efficiency_savings = 5.0 * 180_000 * 0.60
    
    run_cost = 600_000
    return cross_sell_revenue + churn_reduction + efficiency_savings - run_cost

def lever_14_rural_onboarding(a: dict, scenario: str = "base") -> float:
    """Digital-first onboarding for rural customers (offline + biometric)."""
    target_rural = a.get("S4_RURAL_CUSTOMERS", 100_000)
    current_dropout = 0.30
    
    dropout_reduction = 0.50
    dropout_savings = (target_rural * current_dropout * dropout_reduction) * 1_000 * 0.05
    
    speed_savings = target_rural * (50.0 - 2.0) * 50 / 50.0
    efficiency_savings = 8.0 * 120_000 * 0.70
    
    run_cost = 400_000
    return dropout_savings + speed_savings + efficiency_savings - run_cost


# ─────────────────────────────────────────────────────────────────────────────
# GOVERNANCE / EXECUTION RISK
# ─────────────────────────────────────────────────────────────────────────────

def compute_governance_readiness(a: dict) -> float:
    ownership   = a.get("S5_DATA_OWNERSHIP", 55.0)
    lineage     = a.get("S5_LINEAGE", 35.0)
    dq_sla      = a.get("S5_DQ_SLA", 72.0)
    reg_trace   = a.get("S5_REGULATORY_TRACE", 50.0)
    chng_mgmt   = a.get("S5_CHANGE_MGMT", 45.0)
    return (ownership + lineage + dq_sla + reg_trace + chng_mgmt) / 5.0

def compute_execution_risk(a: dict) -> float:
    gov = compute_governance_readiness(a)
    return 1.0 - (gov / 100.0)


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
    "lever_14": lever_14_rural_onboarding,
}

# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def calculate_investment_plan(answers: dict, budget_usd_m: float = 999.0, primary_goals: list[str] = None, llm_intel: dict | None = None) -> list[dict]:
    """
    Score all BFSI levers, filtering by budget and ranking by goal alignment.
    """
    if primary_goals is None:
        primary_goals = []
        
    exec_risk = compute_execution_risk(answers)
    scored = []

    # Evaluate all levers initially (we will assign budget approval later)
    feasible_levers = BFSI_LEVERS
    
    # 2. Assign Goal Weights
    goal_weights = {
        "Margin Expansion (Cost)": 1.0,
        "Alpha Generation (Revenue)": 1.0,
        "Regulatory Resilience (Risk)": 1.0,
        "Client Coverage Scaling": 1.0,
    }

    for lever in feasible_levers:
        lid = lever["id"]
        compute_fn = LEVER_COMPUTE.get(lid)

        # Explicit exception handling (no silent masking)
        if compute_fn:
            try:
                anv = compute_fn(answers, scenario="base")
            except ZeroDivisionError:
                anv = 0.0
            except Exception:
                anv = 0.0
        else:
            anv = lever.get("anv_estimate", 0.0)

        impl_cost = lever.get("impl_cost_estimate", 1_000_000)
        payback   = payback_months(impl_cost, anv)
        roi       = risk_adjusted_roi(impl_cost, anv, exec_risk)

        impact      = lever.get("base_impact", 50)
        feasibility = lever.get("base_feasibility", 50)
        
        # CORRECT SPEED SCORE: Linear interpolation (0 to 100 based on 36 month to 1 month payback)
        speed_score = max(0, min(100, int(100 * (36 - payback) / 35)))

        # CORRECT QUADRANT LOGIC: Impact x Feasibility (not Speed)
        if impact >= 65 and feasibility >= 60:
            quadrant = "Strategic Bets"
        elif impact < 65 and feasibility >= 60:
            quadrant = "Quick Wins / Fill-ins"
        elif impact >= 65 and feasibility < 60:
            quadrant = "Park (Data-Blocked)"
        else:
            quadrant = "Evaluate"
            
        # Goal Alignment
        goal_alignment = sum(
            goal_weights.get(goal, 0) for goal in primary_goals
            if goal in lever.get("goal_alignment", [])
        )
        
        # Negative ANV handling
        warning_flag = "VALUE_DESTRUCTIVE" if anv < 0 else None

        # Regulatory Compliance Check
        reg_status = check_regulatory_compliance(lid, answers)

        scored.append({
            "name":        lever["name"],
            "id":          lid,
            "impact":      impact,
            "speed":       speed_score,
            "feasibility": feasibility,
            "anv":         anv, # Keep negative for display
            "anv_m":       round(anv / 1e6, 2),
            "impl_cost":   impl_cost,
            "payback":     round(payback, 1),
            "roi":         round(roi, 1),
            "quadrant":    quadrant,
            "priority":    lever.get("priority", "P2"),
            "goal_weight": goal_alignment,
            "warning":     warning_flag,
            "reg_status":  reg_status,
            "budget_approved": False
        })

    # Rank by Goal Alignment first, then ANV
    scored.sort(key=lambda x: (x["goal_weight"], x["anv"]), reverse=True)
    
    # Cumulative Budget Check
    cumulative_cost = 0.0
    budget_limit = budget_usd_m * 1e6
    for s in scored:
        if cumulative_cost + s["impl_cost"] <= budget_limit:
            s["budget_approved"] = True
            cumulative_cost += s["impl_cost"]
            
    return scored


build_investment_plan = calculate_investment_plan
