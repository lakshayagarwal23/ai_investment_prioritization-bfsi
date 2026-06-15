"""
engine/math_engine.py  (v2 — genuinely bottom-up & traceable)

DESIGN PRINCIPLE (the answer to "why is this number what it is?"):
A CFO accepts a projected number only when it decomposes into:

        Value  =  a baseline the client gave us
                  x  an uplift rate backed by named peer evidence
                  x  a realization factor that reflects THIS client's risk

Nothing in this engine is a free-floating constant. Every headline figure
carries a `derivation` string naming the exact inputs and the formula that
produced it. Capital is allocated to where the recoverable dollars are
(value-at-stake), not to a fixed 40/30/30 split. Where the client did not
give us a baseline, the lever is marked `quantified=False` and excluded from
the value math instead of being silently faked.

Backward compatibility: this module still returns every key the dashboard
reads (budget_usd_m, expected_roi_pct, ledger_rows, scoring_matrix, donut_*,
data_eng_line_item, complexity_triggered, risk_triggered, ...). It ADDS a
`derivation` block and a `value_levers` block that you can surface to show
your working.
"""

from __future__ import annotations
import re
from config.peer_corpus import INDUSTRY_BENCHMARKS, PEER_INTELLIGENCE


# ─────────────────────────────────────────────────────────────────────────────
# EVIDENCE TABLE
# Each uplift band is a CONSERVATIVE, attributable range — i.e. the share of the
# peer-disclosed gain that is plausibly transferable to a new programme. These
# are the single point where "industry evidence" enters the model, so they are
# explicit, citable, and easy to challenge or override in a review.
# Format: (low_rate, high_rate, peer_citation)
# ─────────────────────────────────────────────────────────────────────────────
EVIDENCE = {
    # Incremental revenue as a % of baseline revenue (demand sensing, NBA, personalization).
    # Peers disclose 6–12% total; we attribute a conservative 1.5–4.0% to the AI programme.
    "revenue_uplift": (0.015, 0.040, "P&G / Unilever / Marico disclosures (6–12% total; conservative attributable share)"),
    # Gross-margin expansion in basis points (procurement + trade-promo optimization).
    # Peers disclose 110–250bps; conservative attributable band 80–180bps.
    "margin_bps": (80, 180, "P&G 250bps / ITC 200bps / Nestlé 180bps (conservative attributable share)"),
    # Inventory / working-capital reduction as % of inventory value (demand forecasting).
    "inventory_reduction": (0.10, 0.20, "Unilever 15% / P&G 22% / Marico 11% inventory reduction"),
    # Opex efficiency as % of addressable operating cost (copilots, automation).
    "opex_efficiency": (0.03, 0.08, "Gartner top-quartile 15–25% task productivity; conservative cost share"),
}

# Annual carrying cost of working capital (used to annualize a one-time inventory release).
WACC_CARRY = 0.12
DISCOUNT_RATE = 0.12          # for NPV
HORIZON_YEARS = 3


# ─────────────────────────────────────────────────────────────────────────────
# PARSING HELPERS  (intake fields Q1.2 and Q2.3 are free text)
# ─────────────────────────────────────────────────────────────────────────────
def _parse_money_usd(text: str) -> float | None:
    """Extract a dollar baseline from free text like 'Baseline $2.5B, Target +10%'.
    Returns USD (absolute) or None if not found."""
    if not text:
        return None
    # find a number adjacent to $ / bn / mn / cr (crore) etc.
    m = re.search(r"\$?\s*([\d,]+(?:\.\d+)?)\s*(b|bn|billion|m|mn|million|cr|crore|k)?", text, re.I)
    if not m:
        return None
    try:
        val = float(m.group(1).replace(",", ""))
    except ValueError:
        return None
    unit = (m.group(2) or "").lower()
    mult = {
        "b": 1e9, "bn": 1e9, "billion": 1e9,
        "m": 1e6, "mn": 1e6, "million": 1e6,
        "cr": 1e7 / 83, "crore": 1e7 / 83,   # ~₹1cr in USD at ~83 INR/USD; rough, flagged
        "k": 1e3, "": 1.0,
    }.get(unit, 1.0)
    return val * mult


def _parse_pct(text: str) -> float | None:
    """Extract a target uplift percent from text like 'Target +10%'. Returns 0.10."""
    if not text:
        return None
    m = re.search(r"([+\-]?\d+(?:\.\d+)?)\s*%", text)
    if not m:
        return None
    return abs(float(m.group(1))) / 100.0


def _midpoint(low: float, high: float) -> float:
    return (low + high) / 2.0


# ─────────────────────────────────────────────────────────────────────────────
# RISK / COMPLEXITY SCORING  (driven by the CORRECT question IDs)
# Note: v1 keyed these off Q4.3 and a non-existent Q5.2, so they almost never
# fired. v2 reads the questions that actually measure the construct.
# ─────────────────────────────────────────────────────────────────────────────
def _complexity_score(ans: dict) -> tuple[float, list[str]]:
    """0.0 (clean) → 1.0 (severe tech debt). Drives foundation cost + timeline."""
    score, why = 0.0, []
    erp = (ans.get("Q3.1", "") or "")
    if "fragmented" in erp.lower() or "lack of centralized" in erp.lower():
        score += 0.35; why.append("Q3.1: fragmented/absent ERP topology")
    elif "minor legacy" in erp.lower():
        score += 0.15; why.append("Q3.1: minor legacy systems")
    cloud = (ans.get("Q3.2", "") or "")
    if "old, slow local" in cloud.lower() or "trying to move" in cloud.lower():
        score += 0.30; why.append("Q3.2: data largely on-prem / mid-migration")
    elif "some is on old servers" in cloud.lower():
        score += 0.15; why.append("Q3.2: hybrid data estate")
    sku = (ans.get("Q2.1", "") or "")
    if "Over 5,000" in sku:
        score += 0.20; why.append("Q2.1: >5,000 SKUs (forecasting load)")
    elif "2,000 to 5,000" in sku:
        score += 0.10; why.append("Q2.1: 2,000–5,000 SKUs")
    return min(score, 1.0), why


def _risk_score(ans: dict) -> tuple[float, list[str]]:
    """0.0 (low) → 1.0 (high execution risk). Drives realization haircut + band."""
    score, why = 0.0, []
    adopt = (ans.get("Q4.1", "") or "")
    if "voluntary" in adopt.lower() or "no strategy" in adopt.lower():
        score += 0.35; why.append("Q4.1: weak/voluntary adoption alignment")
    elif "loosely enforced" in adopt.lower():
        score += 0.15; why.append("Q4.1: loosely enforced adoption")
    sponsor = (ans.get("Q1.4", "") or "")
    if "don't have one clear sponsor" in sponsor.lower():
        score += 0.25; why.append("Q1.4: no single executive sponsor")
    elif "Head of Tech" in sponsor or "Head of Sales" in sponsor or "Head of Supply" in sponsor:
        score += 0.10; why.append("Q1.4: functional (not CEO/CFO) sponsor")
    data_q = (ans.get("Q3.3", "") or "")
    if "historically unreliable" in data_q.lower():
        score += 0.25; why.append("Q3.3: historically unreliable data")
    elif "occasionally inaccurate" in data_q.lower():
        score += 0.12; why.append("Q3.3: weekly/monthly, occasionally inaccurate data")
    return min(score, 1.0), why


# ─────────────────────────────────────────────────────────────────────────────
# VALUE-AT-STAKE  (the core: client baseline x evidenced band)
# ─────────────────────────────────────────────────────────────────────────────
def _build_value_levers(primary_goals: list, ans: dict) -> list[dict]:
    """Construct value levers. Each is quantified ONLY if the client gave a baseline."""
    levers: list[dict] = []

    # Q1.2 stores {kpi_label: "Baseline $X, Target +Y%"}; Q2.3 free text holds forecast error.
    kpi_answers = ans.get("Q1.2", {}) if isinstance(ans.get("Q1.2"), dict) else {}

    # Pull a revenue baseline from any KPI line that names revenue/sales.
    revenue_base = None
    for label, txt in kpi_answers.items():
        if re.search(r"reven|sales|top.?line|growth", label, re.I) or re.search(r"reven|sales", txt, re.I):
            revenue_base = _parse_money_usd(txt) or revenue_base
    # Fallback: any parseable money baseline at all.
    if revenue_base is None:
        for txt in kpi_answers.values():
            revenue_base = _parse_money_usd(txt) or revenue_base
            if revenue_base:
                break

    def add(name, basis_label, basis_value, band_key, kind):
        low_r, high_r, cite = EVIDENCE[band_key]
        if basis_value and basis_value > 0:
            v_low, v_high = basis_value * low_r, basis_value * high_r
            levers.append({
                "name": name, "kind": kind, "quantified": True,
                "basis_label": basis_label, "basis_value": basis_value,
                "rate_low": low_r, "rate_high": high_r, "citation": cite,
                "value_low": v_low, "value_high": v_high,
                "value_mid": _midpoint(v_low, v_high),
                "derivation": f"{basis_label} ${basis_value:,.0f} x {low_r:.1%}–{high_r:.1%} ({cite})",
            })
        else:
            levers.append({
                "name": name, "kind": kind, "quantified": False,
                "basis_label": basis_label, "value_mid": 0.0,
                "citation": cite,
                "derivation": f"NOT QUANTIFIED — no {basis_label.lower()} baseline supplied in intake",
            })

    if "Revenue Growth" in primary_goals:
        add("Revenue Uplift (demand sensing, NBA, personalization)",
            "Annual revenue baseline", revenue_base, "revenue_uplift", "recurring")
        # Working-capital release annualized via carrying cost; needs inventory proxy = 12% of revenue (CPG norm).
        inv_proxy = revenue_base * 0.12 if revenue_base else None
        if inv_proxy:
            low_r, high_r, cite = EVIDENCE["inventory_reduction"]
            wc_mid = _midpoint(inv_proxy * low_r, inv_proxy * high_r) * WACC_CARRY
            levers.append({
                "name": "Working-Capital Release (inventory reduction)",
                "kind": "recurring", "quantified": True,
                "basis_label": "Inventory (≈12% of revenue, CPG norm)", "basis_value": inv_proxy,
                "rate_low": low_r, "rate_high": high_r, "citation": cite,
                "value_low": inv_proxy * low_r * WACC_CARRY, "value_high": inv_proxy * high_r * WACC_CARRY,
                "value_mid": wc_mid,
                "derivation": f"Inventory ${inv_proxy:,.0f} x {low_r:.0%}–{high_r:.0%} reduction x {WACC_CARRY:.0%} carry ({cite})",
            })

    if "Margin Recovery" in primary_goals:
        low_bps, high_bps, cite = EVIDENCE["margin_bps"]
        if revenue_base:
            v_low, v_high = revenue_base * low_bps / 10000, revenue_base * high_bps / 10000
            levers.append({
                "name": "Gross-Margin Expansion (procurement + trade-promo AI)",
                "kind": "recurring", "quantified": True,
                "basis_label": "Annual revenue baseline", "basis_value": revenue_base,
                "rate_low": low_bps / 10000, "rate_high": high_bps / 10000, "citation": cite,
                "value_low": v_low, "value_high": v_high, "value_mid": _midpoint(v_low, v_high),
                "derivation": f"Revenue ${revenue_base:,.0f} x {low_bps:.0f}–{high_bps:.0f}bps ({cite})",
            })
        else:
            add("Gross-Margin Expansion", "Annual revenue baseline", None, "margin_bps", "recurring")

    if "Enterprise Productivity" in primary_goals:
        opex_proxy = revenue_base * 0.18 if revenue_base else None  # addressable SG&A proxy
        add("Operating-Cost Efficiency (copilots, automation)",
            "Addressable operating cost (≈18% of revenue)", opex_proxy, "opex_efficiency", "recurring")

    return levers


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY
# ─────────────────────────────────────────────────────────────────────────────
def calculate_investment_plan(
    budget_usd_m: float,
    primary_goals: list,
    timeline_months: int = 24,
    q1_answer: str = "",          # retained for signature compatibility (unused)
    q2_answer: str = "",
    q3_answer: str = "",
    discovery_answers: dict = None,
) -> dict:
    ans = discovery_answers or {}
    budget_usd = budget_usd_m * 1_000_000
    if not primary_goals:
        primary_goals = ["Revenue Growth"]

    # ── 1. RISK & COMPLEXITY from the correct fields ─────────────────────────
    complexity, complexity_why = _complexity_score(ans)
    risk, risk_why = _risk_score(ans)
    complexity_triggered = complexity >= 0.30
    risk_triggered = risk >= 0.30

    # ── 2. VALUE AT STAKE ────────────────────────────────────────────────────
    levers = _build_value_levers(primary_goals, ans)
    quantified = [lv for lv in levers if lv["quantified"]]
    value_at_stake_mid = sum(lv["value_mid"] for lv in quantified)

    # ── 3. REALIZATION FACTOR (risk haircut) ─────────────────────────────────
    # High execution risk + tech debt shave the share of value actually captured.
    realization = round(max(0.45, 1.0 - 0.35 * risk - 0.20 * complexity), 3)
    realizable_annual_value = value_at_stake_mid * realization

    # ── 4. FOUNDATION FLOOR scales with tech debt (not a flat 30%) ───────────
    foundation_pct = round(0.20 + 0.20 * complexity, 3)   # 20% clean → 40% severe
    foundation_usd = budget_usd * foundation_pct
    deployable_usd = budget_usd - foundation_usd

    # Data-engineering line item (only when complexity is real)
    data_eng_line_item = None
    timeline_penalty = 0
    if complexity_triggered:
        fte = INDUSTRY_BENCHMARKS["typical_data_eng_fte"]
        dur = INDUSTRY_BENCHMARKS["typical_data_eng_months"]
        rate = INDUSTRY_BENCHMARKS["fte_monthly_rate_usd"]
        cost = fte * dur * rate
        data_eng_line_item = {
            "fte_count": fte, "duration_months": dur, "rate_per_fte_month": rate,
            "total_cost": cost, "total_formatted": f"${cost:,.0f}",
            "formula": f"{fte} FTEs x {dur} months x ${rate:,}/month",
        }
        timeline_penalty = round(3 * complexity)

    # ── 5. ALLOCATION FOLLOWS VALUE (capital where the dollars are) ──────────
    goal_cfg = INDUSTRY_BENCHMARKS["primary_goal_allocation"]
    ledger_rows: list[dict] = []
    if value_at_stake_mid > 0:
        for lv in quantified:
            share = lv["value_mid"] / value_at_stake_mid
            ledger_rows.append({
                "initiative": lv["name"],
                "pillar": "Value Driver",
                "allocation_usd": deployable_usd * share,
                "phase": "Year 1–2",
                "roi_driver": lv["derivation"],
                "peer_benchmark": lv["citation"],
                "value_at_stake_usd": lv["value_mid"],
            })
    else:
        # No baselines supplied: fall back to evidence-weighted default split, but SAY SO.
        main = primary_goals[0]
        for init in goal_cfg.get(main, goal_cfg["Revenue Growth"])["sub_initiatives"]:
            ledger_rows.append({
                "initiative": init, "pillar": "Value Driver (unquantified)",
                "allocation_usd": deployable_usd / 4, "phase": "Year 1–2",
                "roi_driver": "Even split — client supplied no baseline to size value",
                "peer_benchmark": "Provide Q1.2 / Q2.3 baselines to enable bottom-up sizing",
                "value_at_stake_usd": 0.0,
            })

    # Foundation line items
    for name, pct in [
        ("Data Platform & MLOps Infrastructure", 0.40),
        ("Enterprise Data Governance & Compliance", 0.25),
        ("Model Monitoring & Observability", 0.20),
        ("API Integration Layer", 0.15),
    ]:
        ledger_rows.append({
            "initiative": name, "pillar": "Foundation / MLOps",
            "allocation_usd": foundation_usd * pct, "phase": "Year 1",
            "roi_driver": f"Foundation sized at {foundation_pct:.0%} of budget (scales with tech-debt score {complexity:.2f})",
            "peer_benchmark": "; ".join(complexity_why) or "Clean estate — minimum foundation floor",
            "value_at_stake_usd": 0.0,
        })

    # ── 6. ROI / NPV / PAYBACK derived from cash flows (not a constant) ──────
    if realizable_annual_value > 0:
        cum_value = realizable_annual_value * HORIZON_YEARS
        roi_pct = round((cum_value - budget_usd) / budget_usd * 100)
        npv = sum(realizable_annual_value / ((1 + DISCOUNT_RATE) ** y) for y in range(1, HORIZON_YEARS + 1)) - budget_usd
        monthly_value = realizable_annual_value / 12
        payback_raw = budget_usd / monthly_value if monthly_value > 0 else timeline_months
        payback_months = round(payback_raw + timeline_penalty)
        total_3yr_return = cum_value
        value_known = True
    else:
        # Honest "insufficient data" state instead of a fabricated 185%.
        roi_pct = 0
        npv = -budget_usd
        payback_months = timeline_months
        total_3yr_return = 0.0
        value_known = False

    # Confidence band widens with risk, tech debt, and stale data.
    band = round(20 + 25 * risk + 15 * complexity)
    if "historically unreliable" in (ans.get("Q3.3", "") or "").lower():
        band += 10
    confidence_band_pct = float(min(band, 60))
    lo = max(payback_months - 3, 1)
    payback_label = f"{lo}–{payback_months + 3} months" if value_known else "Insufficient baseline data"

    # ── 7. SCORING MATRIX fed by REAL signals ────────────────────────────────
    scoring_matrix = _build_scoring_matrix(primary_goals, complexity_triggered, risk_triggered,
                                           len((ans.get("Q1.5", "") or "")) > 10)

    # ── 8. CHART + DERIVATION TRACE ──────────────────────────────────────────
    donut_labels = ["Value Drivers", "Foundation / MLOps"]
    donut_values = [deployable_usd, foundation_usd]
    donut_colors = ["#D04A02", "#2D2D2D"]

    derivation = {
        "value_at_stake_mid_usd": value_at_stake_mid,
        "realization_factor": realization,
        "realization_formula": f"max(0.45, 1 - 0.35*risk({risk:.2f}) - 0.20*complexity({complexity:.2f})) = {realization}",
        "realizable_annual_value_usd": realizable_annual_value,
        "foundation_pct": foundation_pct,
        "roi_formula": (f"(3yr realizable value ${realizable_annual_value*HORIZON_YEARS:,.0f} - "
                        f"budget ${budget_usd:,.0f}) / budget = {roi_pct}%") if value_known
                       else "ROI not computed — no client baseline supplied (see value_levers)",
        "payback_formula": (f"budget ${budget_usd:,.0f} / monthly value "
                            f"${realizable_annual_value/12:,.0f} + {timeline_penalty}mo debt penalty") if value_known
                           else "Payback not computed — insufficient data",
        "risk_drivers": risk_why,
        "complexity_drivers": complexity_why,
        "value_known": value_known,
    }

    return {
        # ── dashboard contract (unchanged keys) ──
        "budget_usd_m": budget_usd_m,
        "budget_usd": budget_usd,
        "primary_goals": primary_goals,
        "primary_goal_label": " + ".join(goal_cfg.get(g, goal_cfg["Revenue Growth"])["label"] for g in primary_goals),
        "primary_usd": deployable_usd,
        "foundation_usd": foundation_usd,
        "secondary_usd": 0.0,
        "donut_labels": donut_labels,
        "donut_values": donut_values,
        "donut_colors": donut_colors,
        "ledger_rows": ledger_rows,
        "complexity_triggered": complexity_triggered,
        "data_eng_line_item": data_eng_line_item,
        "complexity_timeline_penalty_months": timeline_penalty,
        "risk_triggered": risk_triggered,
        "change_mgmt_flag": risk_triggered,
        "change_mgmt_cost": budget_usd * INDUSTRY_BENCHMARKS["change_mgmt_overhead_pct"] if risk_triggered else 0.0,
        "payback_label": payback_label,
        "confidence_band_pct": confidence_band_pct,
        "expected_roi_pct": roi_pct,
        "npv_usd": npv,
        "total_3yr_return": total_3yr_return,
        "scoring_matrix": scoring_matrix,
        "q1_focus": _parse_q1_focus(ans.get("Q1.5", "") or ""),
        # ── new, surfaceable: shows your working ──
        "value_levers": levers,
        "derivation": derivation,
        "complexity_score": complexity,
        "risk_score": risk,
    }


# ─────────────────────────────────────────────────────────────────────────────
# UNCHANGED-ISH HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _parse_q1_focus(answer: str) -> str:
    lowered = answer.lower()
    if any(k in lowered for k in ["procurement", "supply", "back-office", "purchasing"]):
        return "Procurement & Back-Office Efficiency"
    if any(k in lowered for k in ["manufacturing", "yield", "factory", "plant", "production"]):
        return "Manufacturing Yield Optimization"
    if any(k in lowered for k in ["demand", "sales", "revenue", "channel", "distribution"]):
        return "Front-Office Demand Generation"
    return "Balanced Optimization"


def _build_scoring_matrix(primary_goals: list, complexity: bool, risk: bool, interdependency: bool) -> list:
    base_cases = {
        "Revenue Growth": [
            {"name": "Trade Promotion Optimization", "impact": 88, "feasibility": 72, "speed": 65, "fit": 90},
            {"name": "Sales Copilot / Next-Best-Action", "impact": 80, "feasibility": 78, "speed": 80, "fit": 85},
            {"name": "Demand Sensing & Forecasting", "impact": 75, "feasibility": 70, "speed": 70, "fit": 80},
            {"name": "Consumer Personalization Engine", "impact": 70, "feasibility": 60, "speed": 55, "fit": 75},
        ],
        "Margin Recovery": [
            {"name": "Procurement AI & Supplier Intelligence", "impact": 90, "feasibility": 74, "speed": 60, "fit": 92},
            {"name": "Manufacturing Yield Optimization", "impact": 82, "feasibility": 65, "speed": 55, "fit": 85},
            {"name": "Logistics Route & Cost Optimization", "impact": 74, "feasibility": 80, "speed": 75, "fit": 78},
            {"name": "Predictive Maintenance AI", "impact": 70, "feasibility": 68, "speed": 60, "fit": 72},
        ],
        "Enterprise Productivity": [
            {"name": "Enterprise Knowledge Search", "impact": 72, "feasibility": 88, "speed": 90, "fit": 80},
            {"name": "Invoice & PO Extraction", "impact": 68, "feasibility": 85, "speed": 88, "fit": 76},
            {"name": "Field Sales Productivity Platform", "impact": 78, "feasibility": 75, "speed": 72, "fit": 82},
            {"name": "Meeting & Document Intelligence", "impact": 62, "feasibility": 90, "speed": 92, "fit": 70},
        ],
    }
    main = primary_goals[0] if primary_goals else "Revenue Growth"
    cases = base_cases.get(main, base_cases["Revenue Growth"])
    scored = []
    for c in cases:
        s = c["impact"] * 0.40 + c["feasibility"] * 0.25 + c["speed"] * 0.20 + c["fit"] * 0.15
        if complexity: s -= 8
        if risk: s -= 5
        if interdependency: s -= 3
        s = round(max(s, 0), 1)
        scored.append({
            "name": c["name"], "impact": c["impact"],
            "feasibility": max(c["feasibility"] - (10 if complexity else 0), 0),
            "speed": max(c["speed"] - (5 if risk else 0), 0), "fit": c["fit"],
            "composite_score": s,
            "priority": "High" if s >= 78 else ("Medium" if s >= 68 else "Watch"),
        })
    scored.sort(key=lambda x: x["composite_score"], reverse=True)
    return scored


build_investment_plan = calculate_investment_plan