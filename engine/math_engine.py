"""
engine/math_engine.py  (v4 — CFO-ready diagnostic; no financial projections)

DESIGN PRINCIPLE:
This engine is a *prioritisation and readiness diagnostic*, not a financial
forecast. The only dollar figures it produces are allocations of the client's
own stated budget — not projected returns.

Invariant 1: No ROI, NPV, payback, or ramped-return computation exists here.
Invariant 2: Ledger allocation follows the scoring matrix (composite × feasibility).
Invariant 3: Unknown answers default to conservative (fragmented/high-risk).
Invariant 4: Identical inputs → identical output (pure function, no randomness).
"""

from __future__ import annotations
import re
from config.peer_corpus import INDUSTRY_BENCHMARKS, PEER_INTELLIGENCE
from config.value_pools import (
    VALUE_TYPE, REVENUE, OPPROFIT, PRODUCTIVITY,
    MANDATE_VALUE_TYPES, COLORS as VT_COLORS, DISPLAY_NAME as VT_DISPLAY,
    SHORT_LABEL as VT_SHORT, classify_quadrant, IMPACT_MID, FEAS_MID,
)

_BUCKET_RULES = {
  "Q3.1": [
    (["lack of centralized","complete lack","highly fragmented","fragmented","decentralized","regional instances","multiple erp","no centralized"], "fragmented"),
    (["mostly centralized","minor legacy","some legacy"], "medium"),
    (["centralized","centralised","s/4hana","s4hana","single instance","global sap","unified"], "clean"),
  ],
  "Q3.2": [
    (["old","on-prem","on prem","local server","slow local","no, almost"], "fragmented"),
    (["some of it","partial","migrating","moving","currently trying"], "medium"),
    (["modern cloud","all of it is in","fully cloud","cloud-native","yes, all"], "clean"),
  ],
  "Q2.1": [
    (["over 5","5,000","5000",">5"], "fragmented"),
    (["2,000","2000","500 to 2","1,000","1000"], "medium"),
    (["under 500","<500","fewer than 500"], "clean"),
  ],
  "Q3.3": [
    (["weekly","monthly","inaccurate","unreliable","historically unreliable","stale","less frequent"], "fragmented"),
    (["daily","generally accurate"], "medium"),
    (["real-time","real time","near real","highly accurate"], "clean"),
  ],
}

def _canonical(qid: str, answer: str, mapping: dict | None = None) -> str:
    """Return the canonical bucket for a given answer option."""
    if mapping and answer in mapping:
        return mapping[answer]
    a = (answer or "").lower()
    for kws, bucket in _BUCKET_RULES.get(qid, []):
        if any(k in a for k in kws):
            return bucket
    return "medium"   # genuinely unrecognised → moderate, not worst-case

ASSUMPTIONS = INDUSTRY_BENCHMARKS["model_assumptions"]


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
# Match a number that carries a MONETARY signal: either a currency marker
# ($, USD, INR, Rs, ₹) in front, or a magnitude unit (bn/mn/cr/lakh/k) behind.
# The trailing "(?!\s*%)" guard means "10%" can never be read as money.
_MONEY_RE = re.compile(
    r"(?P<cur>\$|usd|inr|rs\.?|₹)?\s*"
    r"(?P<num>\d+(?:\.\d+)?)\s*"
    r"(?P<unit>bn|billion|b|mn|million|m|crore|cr|lakh|lac|k)?\b(?!\s*%)",
    re.I,
)


def _parse_money_usd(text: str) -> float | None:
    """Extract a dollar baseline from free text like 'Baseline $2.5B, Target +10%'.

    Only figures with a currency marker OR a magnitude unit are accepted, so a
    bare '10%' target is never mistaken for a '$10' baseline. When several
    monetary figures appear, the LARGEST is returned (the revenue baseline is
    almost always the big number). Returns USD (absolute) or None.
    """
    if not text:
        return None
    cleaned = text.replace(",", "")
    inr_per_usd = ASSUMPTIONS["inr_per_usd"]
    unit_mult = {
        "b": 1e9, "bn": 1e9, "billion": 1e9,
        "m": 1e6, "mn": 1e6, "million": 1e6,
        "cr": 1e7 / inr_per_usd, "crore": 1e7 / inr_per_usd,    # ₹1cr  = 10^7 INR
        "lakh": 1e5 / inr_per_usd, "lac": 1e5 / inr_per_usd,    # ₹1lakh= 10^5 INR
        "k": 1e3, "": 1.0,
    }
    best: float | None = None
    for m in _MONEY_RE.finditer(cleaned):
        cur = m.group("cur")
        unit = (m.group("unit") or "").lower()
        # Require a monetary signal; skip ambiguous bare integers.
        if not cur and not unit:
            continue
        try:
            val = float(m.group("num")) * unit_mult.get(unit, 1.0)
        except ValueError:
            continue
        if best is None or val > best:
            best = val
    return best


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


def _parse_payback_limit_months(answer: str) -> int | None:
    """Q1.3 -> the board's maximum acceptable payback, as an UPPER bound in months.
    Returns None when there is no strict timeline."""
    a = (answer or "").lower()
    if "no strict" in a:
        return None
    if "under 12" in a:
        return 12
    if "12 to 18" in a:
        return 18
    if "18 to 24" in a:
        return 24
    if "24 to 36" in a:
        return 36
    return None


# ─────────────────────────────────────────────────────────────────────────────
# RISK / COMPLEXITY SCORING  (driven by the CORRECT question IDs)
# Note: v1 keyed these off Q4.3 and a non-existent Q5.2, so they almost never
# fired. v2/v3 read the questions that actually measure the construct.
# ─────────────────────────────────────────────────────────────────────────────
def _complexity_score(ans: dict, mapping: dict | None = None) -> tuple[float, list[str]]:
    """0.0 (clean) → 1.0 (severe tech debt). Drives foundation cost + timeline.

    mapping: optional option_buckets dict from LLM intel (D1 — threads through
    tailored answers so fragmented estates don't silently score as clean).
    """
    score, why = 0.0, []
    erp = ans.get("Q3.1", "") or ""
    erp_bucket = _canonical("Q3.1", erp, mapping)
    if erp_bucket == "fragmented":
        score += 0.35; why.append("Q3.1: fragmented ERP topology")
    elif erp_bucket == "medium":
        score += 0.15; why.append("Q3.1: minor legacy systems")

    cloud = ans.get("Q3.2", "") or ""
    if "old, slow local" in cloud.lower() or "trying to move" in cloud.lower():
        score += 0.30; why.append("Q3.2: data largely on-prem / mid-migration")
    elif "some is on old servers" in cloud.lower():
        score += 0.15; why.append("Q3.2: hybrid data estate")

    sku = ans.get("Q2.1", "") or ""
    sku_bucket = _canonical("Q2.1", sku, mapping)
    if sku_bucket == "fragmented":
        score += 0.20; why.append("Q2.1: >5,000 SKUs (forecasting load)")
    elif sku_bucket == "medium":
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


def _si_cost_inflation(ans: dict) -> tuple[float, str]:
    """Q4.3 -> programme-cost inflation from delivery model. External SI is the
    most expensive; a fully internal build adds nothing."""
    a = (ans.get("Q4.3", "") or "").lower()
    cfg = ASSUMPTIONS["si_cost_inflation"]
    if "external" in a:
        return cfg["external"], "Q4.3: external Systems Integrator (+{:.0%} programme cost)".format(cfg["external"])
    if "hybrid" in a:
        return cfg["hybrid"], "Q4.3: hybrid internal + SI (+{:.0%} programme cost)".format(cfg["hybrid"])
    if "internal" in a:
        return cfg["internal"], "Q4.3: fully internal build (no SI premium)"
    return cfg["hybrid"], "Q4.3: delivery model not specified — modelled as hybrid (+15%)"


def _compliance_foundation_uplift(ans: dict) -> tuple[float, str]:
    """Q4.2 -> extra foundation spend for data residency / privacy controls."""
    a = (ans.get("Q4.2", "") or "").lower()
    cfg = ASSUMPTIONS["compliance_foundation_uplift"]
    if "strict" in a:
        return cfg["strict"], "Q4.2: strict multiregional compliance (+{:.0%} foundation)".format(cfg["strict"])
    if "moderate" in a:
        return cfg["moderate"], "Q4.2: moderate compliance (+{:.0%} foundation)".format(cfg["moderate"])
    if "minimal" in a:
        return cfg["minimal"], "Q4.2: minimal regulatory constraints"
    if "unknown" in a:
        return cfg["unknown"], "Q4.2: compliance unknown — treated as moderate (+{:.0%})".format(cfg["unknown"])
    return 0.0, ""


def _oos_recovery_rate(ans: dict) -> tuple[float, str]:
    """Q2.4 -> recoverable lost sales (as % of revenue) that demand sensing wins back."""
    a = (ans.get("Q2.4", "") or "").lower()
    cfg = ASSUMPTIONS["oos_revenue_recovery"]
    for key in ("constantly", "frequently", "occasionally", "rarely"):
        if key in a:
            return cfg[key], key
    return 0.0, ""


# ─────────────────────────────────────────────────────────────────────────────
# PRIORITY LEVERS  (the core: client baseline x evidenced band)
# ─────────────────────────────────────────────────────────────────────────────
def _build_value_levers(primary_goals: list, ans: dict) -> list[dict]:
    """Construct value levers. Each is quantified ONLY if the client gave a baseline."""
    levers: list[dict] = []

    # Q1.2 stores {kpi_label: "Baseline $X, Target +Y%"}; Q2.3 free text holds forecast error.
    kpi_answers = ans.get("Q1.2", {}) if isinstance(ans.get("Q1.2"), dict) else {}

    # Pull a revenue baseline from any KPI line that names revenue/sales.
    revenue_base = None
    for label, val in kpi_answers.items():
        if isinstance(val, dict):
            if val.get("engine") == "revenue" or re.search(r"reven|sales|top.?line|growth", label, re.I):
                if val.get("amount_is_money", True):
                    revenue_base = float(val.get("amount_usd_m", 0)) or revenue_base
        else:
            txt = str(val)
            if re.search(r"reven|sales|top.?line|growth", label, re.I) or re.search(r"reven|sales", txt, re.I):
                revenue_base = _parse_money_usd(txt) or revenue_base

    # Fallback: any parseable money baseline at all.
    if revenue_base is None:
        for val in kpi_answers.values():
            if isinstance(val, dict):
                if val.get("amount_is_money", True):
                    revenue_base = float(val.get("amount_usd_m", 0)) or revenue_base
            else:
                revenue_base = _parse_money_usd(str(val)) or revenue_base
            if revenue_base:
                break

    inv_ratio = ASSUMPTIONS["inventory_pct_of_revenue"]
    opex_ratio = ASSUMPTIONS["addressable_opex_pct_of_revenue"]

    def add(name, basis_label, basis_value, band_key, kind, lever_key="opex"):
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
                "lever_key": lever_key,
            })
        else:
            levers.append({
                "name": name, "kind": kind, "quantified": False,
                "basis_label": basis_label, "value_mid": 0.0,
                "citation": cite,
                "derivation": f"NOT QUANTIFIED — no {basis_label.lower()} baseline supplied in intake",
                "lever_key": lever_key,
            })

    if "Revenue Growth" in primary_goals:
        add("Revenue Uplift (demand sensing, NBA, personalization)",
            "Annual revenue baseline", revenue_base, "revenue_uplift", "recurring", "revenue")

        # Q2.4: recoverable lost sales from fewer out-of-stocks.
        oos_rate, oos_freq = _oos_recovery_rate(ans)
        if revenue_base and oos_rate > 0:
            oos_value = revenue_base * oos_rate
            levers.append({
                "name": "Lost-Sales Recovery (out-of-stock reduction)",
                "kind": "recurring", "quantified": True,
                "basis_label": "Annual revenue baseline", "basis_value": revenue_base,
                "rate_low": oos_rate, "rate_high": oos_rate,
                "citation": f"Q2.4: OOS impact '{oos_freq}' → recoverable demand-sensing share",
                "value_low": oos_value, "value_high": oos_value, "value_mid": oos_value,
                "derivation": f"Revenue ${revenue_base:,.0f} x {oos_rate:.1%} recoverable lost sales (Q2.4: '{oos_freq}')",
                "lever_key": "oos"
            })

        # Working-capital release annualized via carrying cost; inventory proxy = % of revenue (CPG norm).
        inv_proxy = revenue_base * inv_ratio if revenue_base else None
        if inv_proxy:
            low_r, high_r, cite = EVIDENCE["inventory_reduction"]
            wc_mid = _midpoint(inv_proxy * low_r, inv_proxy * high_r) * WACC_CARRY
            levers.append({
                "name": "Working-Capital Release (inventory reduction)",
                "kind": "recurring", "quantified": True,
                "basis_label": f"Inventory (≈{inv_ratio:.0%} of revenue, CPG norm)", "basis_value": inv_proxy,
                "rate_low": low_r, "rate_high": high_r, "citation": cite,
                "value_low": inv_proxy * low_r * WACC_CARRY, "value_high": inv_proxy * high_r * WACC_CARRY,
                "value_mid": wc_mid,
                "derivation": f"Inventory ${inv_proxy:,.0f} x {low_r:.0%}–{high_r:.0%} reduction x {WACC_CARRY:.0%} carry ({cite})",
                "lever_key": "inventory"
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
                "lever_key": "margin"
            })
        else:
            add("Gross-Margin Expansion", "Annual revenue baseline", None, "margin_bps", "recurring", "margin")

    if "Enterprise Productivity" in primary_goals:
        opex_proxy = revenue_base * opex_ratio if revenue_base else None  # addressable SG&A proxy
        add("Operating-Cost Efficiency (copilots, automation)",
            f"Addressable operating cost (≈{opex_ratio:.0%} of revenue)", opex_proxy, "opex_efficiency", "recurring", "opex")

    return levers


# ─────────────────────────────────────────────────────────────────────────────
# VALUE PORTFOLIO (Framework 2 — pure function, no side effects)
# ─────────────────────────────────────────────────────────────────────────────
def compute_value_portfolio(funded_value_rows: list[dict], primary_goals: list[str]) -> dict:
    """Compute the value-type portfolio breakdown from funded ledger rows.
    
    Returns a dict with:
      usd:  {type: amount} — absolute USD by value type
      pct:  {type: int}    — percentage by value type (sums to exactly 100)
      aligned_pct: int     — share of funded capital in mandate-aligned types
      mandate_types: set   — which value types the mandate maps to
      alignment_sentence: str — deterministic template sentence
    """
    total = sum(r["allocation_usd"] for r in funded_value_rows) or 1.0
    by_type: dict[str, float] = {REVENUE: 0.0, OPPROFIT: 0.0, PRODUCTIVITY: 0.0}
    for r in funded_value_rows:
        vt = r.get("value_type", VALUE_TYPE.get(r["initiative"], PRODUCTIVITY))
        by_type[vt] += r["allocation_usd"]

    pct = {k: round(100 * v / total) for k, v in by_type.items()}
    # Fix rounding so the three sum to exactly 100.
    drift = 100 - sum(pct.values())
    if drift:
        pct[max(pct, key=pct.get)] += drift

    # Mandate alignment.
    mandate_types: set[str] = set()
    for g in primary_goals:
        mandate_types |= MANDATE_VALUE_TYPES.get(g, set())
    if not mandate_types:
        mandate_types = {REVENUE}
    aligned_pct = sum(pct[t] for t in by_type if t in mandate_types)

    # Deterministic alignment sentence.
    types_list = sorted(VT_DISPLAY[t].lower() for t in mandate_types)
    if len(types_list) == 1:
        type_names = types_list[0]
    elif len(types_list) == 2:
        type_names = f"{types_list[0]} and {types_list[1]}"
    else:
        type_names = ", ".join(types_list[:-1]) + f", and {types_list[-1]}"

    if aligned_pct >= 80:
        alignment_sentence = f"Strong goal alignment: {aligned_pct}% of deployed capital is directed toward {type_names}, directly supporting your primary objectives."
    elif aligned_pct >= 60:
        alignment_sentence = f"Moderate goal alignment: {aligned_pct}% of deployed capital is directed toward {type_names}. Further optimisation may improve alignment with your goals."
    else:
        alignment_sentence = f"Weak goal alignment: Only {aligned_pct}% of deployed capital targets {type_names}. A review of the underlying investment ranking is advised."

    return {
        "usd": by_type,
        "pct": pct,
        "aligned_pct": aligned_pct,
        "mandate_types": mandate_types,
        "alignment_sentence": alignment_sentence,
    }


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY
# ─────────────────────────────────────────────────────────────────────────────
def calculate_investment_plan(
    budget_usd_m: float,
    primary_goals: list[str],
    timeline_months: int = 24,
    q1_answer: str = "",          # retained for signature compatibility (unused)
    q2_answer: str = "",
    q3_answer: str = "",
    discovery_answers: dict = None,
    skip_cf: bool = False,
) -> dict:
    ans = discovery_answers or {}
    budget_usd = budget_usd_m * 1_000_000
    if not primary_goals:
        primary_goals = ["Revenue Growth"]

    # ── 1. RISK & COMPLEXITY from the correct fields ─────────────────────────
    mapping = None   # option_buckets from LLM intel (wired by sidebar, D1)
    try:
        import streamlit as st
        mapping = st.session_state.get("option_buckets")
    except Exception:
        pass

    complexity, complexity_why = _complexity_score(ans, mapping)
    risk, risk_why = _risk_score(ans)
    complexity_triggered = complexity >= 0.30
    risk_triggered = risk >= 0.30

    # Deterministic AI-maturity score — spec formula: 90 - 35c - 30r - 20d
    # Varies genuinely per client; never an LLM guess (R2, Invariant 4).
    data_badness = _data_quality_badness(ans)
    
    # ── 1b. POSTURE AND PRIMARY RISK (W1) ────────────────────────────────────
    cloud_ans = (ans.get("Q3.2", "") or "").lower()
    infra_score = 1.0 if "old, slow local" in cloud_ans or "trying to move" in cloud_ans else 0.5 if "some is on old servers" in cloud_ans else 0.0
    dq_ans = (ans.get("Q3.3", "") or "").lower()
    dq_score = 0.90 if "historically unreliable" in dq_ans else 0.50 if "occasionally inaccurate" in dq_ans else 0.20 if "daily" in dq_ans else 0.05 if "real-time" in dq_ans or "near real" in dq_ans else 0.40
    
    drivers = sorted([
        ("data estate not ready", max(dq_score, infra_score)),
        ("execution / adoption risk", risk),
        ("estate complexity", complexity)
    ], key=lambda x: x[1], reverse=True)
    
    primary_risk_label = drivers[0][0]
    primary_risk_score = drivers[0][1]

    # Fix 6: Verbose risk descriptions for client-facing output
    RISK_DESCRIPTIONS = {
        "data estate not ready": (
            "Data estate readiness — your current data infrastructure and quality "
            "scores indicate significant gaps that must be remediated before AI "
            "models can operate reliably."
        ),
        "estate complexity": (
            "Technology estate complexity — the combination of legacy system density, "
            "SKU breadth, and integration surface area creates execution risk that "
            "must be managed through a structured foundation phase."
        ),
        "execution / adoption risk": (
            "Execution & adoption risk — organisational change readiness and internal "
            "capability gaps represent the primary barrier to realising value from "
            "AI investments."
        ),
    }
    primary_risk_verbose = RISK_DESCRIPTIONS.get(primary_risk_label, primary_risk_label)
    
    # Foundations First if the primary risk is data or complexity and it crosses the threshold.
    if primary_risk_label in ("data estate not ready", "estate complexity") and primary_risk_score >= 0.40:
        posture = "ADDRESS FOUNDATIONS FIRST"
    else:
        posture = "INVEST NOW — PHASED"
    
    data_risk = max(complexity, data_badness)
    maturity_score = int(max(20, min(95, round(90 - 35 * complexity - 30 * risk - 20 * data_badness))))
    
    if posture == "ADDRESS FOUNDATIONS FIRST":
        maturity_score = min(maturity_score, 49) # Cap at Emerging
        
    maturity_class = ("Leader"    if maturity_score >= 75 else
                      "Strategic" if maturity_score >= 50 else
                      "Emerging"  if maturity_score >= 25 else "Laggard")

    # Delivery model (Q4.3) and compliance (Q4.2) cost overlays.
    si_inflation, si_why = _si_cost_inflation(ans)
    compliance_uplift, compliance_why = _compliance_foundation_uplift(ans)

    # Value levers are built for evidence text only; their value_mid figures
    # are NOT used in allocation (which follows the scoring matrix — G0.4).
    levers = _build_value_levers(primary_goals, ans)
    revenue_base = next((l["basis_value"] for l in levers if l["lever_key"] == "revenue" and l.get("basis_value")), None)


    # ── 4. FOUNDATION FLOOR scales with tech debt AND compliance ─────────────
    foundation_pct = round(min(0.55, 0.20 + 0.20 * complexity + compliance_uplift), 3)  # 20% clean → up to 55%
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

    # ── 4b. TOTAL PROGRAMME COST (client budget + SI delivery premium) ───────
    si_cost = budget_usd * si_inflation
    total_program_cost = budget_usd + si_cost

    phase1_usd = foundation_usd

    # ── 5. BUILD SCORING MATRIX (before ledger; ledger derives from it — G0.4) ──
    # Must be built here so both ledger and return dict share the same object.
    scale = "enterprise"
    if revenue_base:
        if revenue_base < 1e9: scale = "challenger"
        elif revenue_base < 10e9: scale = "mid"
    
    scoring_matrix = _build_scoring_matrix(
        primary_goals, complexity_triggered, risk_triggered,
        len((ans.get("Q1.5", "") or "")) > 10, ans=ans, levers=levers, data_risk=data_risk, revenue_base=revenue_base
    )

    # ── 5b. ALLOCATION FOLLOWS MATRIX  (Invariant 2: matrix and ledger share one spine) ──
    from config.evidence import get_evidence
    from config.value_pools import IMPACT_MID, FEAS_MID
    
    # Read company name for company-aware evidence (Fix 1: avoid self-citations)
    _company_name = ""
    try:
        import streamlit as _st
        _company_name = _st.session_state.get("company_name", "")
    except Exception:
        pass
    
    ledger_rows: list[dict] = []
    deferred_initiatives = []
    
    FOUNDATION_FIRST = (posture == "ADDRESS FOUNDATIONS FIRST")
    
    if scoring_matrix:
        planned_deployable_usd = budget_usd - foundation_usd
        if FOUNDATION_FIRST:
            funded = []
            deferred = scoring_matrix
            for uc in deferred:
                uc["priority"] = "Watch"
            deployable_usd = 0.0
        else:
            for uc in scoring_matrix:
                if uc["impact"] >= IMPACT_MID and uc["feasibility"] < FEAS_MID:
                    # Strategic bets must be deferred.
                    uc["priority"] = "Watch"
            
            funded = [uc for uc in scoring_matrix if uc["priority"] in {"High", "Medium"}]
            deferred = [uc for uc in scoring_matrix if uc["priority"] == "Watch"]
            
        # Construct phases AFTER deployable_usd is finalized (Fix 3)
        phases = [
            {"name": "Phase 1 — Foundations", "window": "Months 0–6",
             "usd": foundation_usd,
             "gate": "Phase 1 Validation — data-readiness & baseline review",
             "focus": "Build the data platform, governance and controls before any AI scales."},
            {"name": "Phase 2 — Scale", "window": "Months 6–18",
             "usd": planned_deployable_usd * 0.6,
             "gate": "Phase 2 Validation — value realization before further funding",
             "focus": "Deploy the highest-value AI initiatives against your baselines."},
            {"name": "Phase 3 — Expand", "window": "Months 18+",
             "usd": planned_deployable_usd * 0.4,
             "gate": "—",
             "focus": "Extend proven AI across the enterprise."},
        ]

        if not funded:
            base_feas = 50.0
            overall_feas = 50.0
        else:
            w_feas = sum(uc["feasibility"] * uc["composite_score"] for uc in funded)
            w_tot = sum(uc["composite_score"] for uc in funded)
            base_feas = w_feas / w_tot if w_tot else 0.0
            
            # Apply complexity penalty and cap deliverability to avoid 94% fallacy (Fix 5)
            penalty = (complexity * 15) + (data_badness * 10)
            overall_feas = max(0.0, min(82.0, base_feas - penalty))
            
        deferred_initiatives = [uc["name"] for uc in deferred]
        total_w = sum(uc["composite_score"] * (uc["feasibility"] / 100.0) for uc in funded) or 1.0

        # Fix 1: Assign each funded initiative to Phase 2 or Phase 3.
        # Highest-scoring initiatives fill Phase 2 (60% of capital), remainder → Phase 3.
        funded_sorted = sorted(funded, key=lambda x: x["composite_score"], reverse=True)
        phase2_cap = planned_deployable_usd * 0.6
        phase2_running = 0.0

        for uc in funded_sorted:
            w = uc["composite_score"] * (uc["feasibility"] / 100.0)
            alloc = deployable_usd * w / total_w
            if phase2_running + alloc <= phase2_cap * 1.10:  # 10% tolerance
                phase_label = "Phase 2"
                phase2_running += alloc
            else:
                phase_label = "Phase 3"
            ledger_rows.append({
                "initiative": uc["name"],
                "pillar": "Value Initiative",
                "allocation_usd": alloc,
                "phase": phase_label,
                "evidence": get_evidence(uc["name"], _company_name),
                "deliverability_pct": uc["feasibility"],
                "rationale": uc.get("rationale", ""),
                "value_type": VALUE_TYPE.get(uc["name"], PRODUCTIVITY),
            })

        # Fix 2: Reconcile phase USD with actual initiative sums so roadmap
        # cards and ledger rows are perfectly consistent.
        phase2_actual = sum(r["allocation_usd"] for r in ledger_rows
                            if r.get("phase") == "Phase 2" and r.get("pillar") == "Value Initiative")
        phase3_actual = sum(r["allocation_usd"] for r in ledger_rows
                            if r.get("phase") == "Phase 3" and r.get("pillar") == "Value Initiative")
        if len(phases) >= 3 and not FOUNDATION_FIRST:
            phases[1]["usd"] = phase2_actual
            phases[2]["usd"] = phase3_actual
    else:
        # No scoring matrix (no objectives selected) — park whole deployable as pending.
        ledger_rows.append({
            "initiative": "Value initiatives (select objectives above to see ranked use cases)",
            "pillar": "Value Initiative (pending objective selection)",
            "allocation_usd": deployable_usd, "phase": "Phase 2–3",
            "evidence": "", "deliverability_pct": None, "rationale": "",
        })
        phases = [
            {"name": "Phase 1 — Foundations", "window": "Months 0–6", "usd": foundation_usd, "gate": "Phase 1 Validation — data-readiness", "focus": ""},
            {"name": "Phase 2 — Scale", "window": "Months 6–18", "usd": deployable_usd * 0.6, "gate": "Phase 2 Validation — value validation", "focus": ""},
            {"name": "Phase 3 — Expand", "window": "Months 18+", "usd": deployable_usd * 0.4, "gate": "—", "focus": ""},
        ]

    # Foundation line items — cost/allocation lines only (not value forecasts)
    FOUNDATION_PURPOSE = {
      "Data Platform & Infrastructure": "Consolidates your ERP/source data into a single governed data lake — the prerequisite for every downstream use case.",
      "Data Governance & Compliance": "Stands up the access controls, lineage and audit trail required by your compliance profile.",
      "Model Monitoring & Observability": "Ongoing drift, accuracy and performance monitoring so models stay reliable after launch.",
      "System Integration Layer": "Connects the new AI services back into your existing ERP and operational systems.",
    }

    foundation_rationale = ("; ".join(filter(None, complexity_why + [compliance_why]))
                            or "Clean data estate — minimum foundation only.")
    c = complexity
    p_platform = 0.34 + 0.12 * c
    p_integration = 0.13 + 0.10 * c
    p_governance = 0.30 - 0.10 * c
    p_monitoring = 0.23 - 0.12 * c
    p_total = p_platform + p_integration + p_governance + p_monitoring

    for name, pct in [
        ("Data Platform & Infrastructure", p_platform / p_total),
        ("System Integration Layer", p_integration / p_total),
        ("Data Governance & Compliance", p_governance / p_total),
        ("Model Monitoring & Observability", p_monitoring / p_total),
    ]:
        ledger_rows.append({
            "initiative": name, "pillar": "Foundation (Data & Controls)",
            "allocation_usd": foundation_usd * pct, "phase": "Phase 1",
            "evidence": FOUNDATION_PURPOSE[name],
            "deliverability_pct": None,
            "rationale": foundation_rationale,
        })

    # SI delivery premium — explicit, visible cost line (not a value forecast)
    if si_cost > 0:
        ledger_rows.append({
            "initiative": "Systems Integrator Delivery Premium",
            "pillar": "Delivery / SI",
            "allocation_usd": si_cost, "phase": "Phase 1–2",
            "evidence": f"Programme cost inflated +{si_inflation:.0%} by delivery model ({si_why})",
            "deliverability_pct": None,
            "rationale": si_why,
        })

    # ── 6. CONFIDENCE BAND (widens with risk + tech debt — no payback reference) ──
    band = 20 + 25 * risk + 15 * complexity
    if "historically unreliable" in (ans.get("Q3.3", "") or "").lower():
        band += 10
    if "unknown" in (ans.get("Q4.2", "") or "").lower():
        band += 5
    confidence_band_pct = float(min(round(band), 60))

    # ── W5. RISK REGISTER ────────────────────────────────────────────────────
    c_risks = []
    
    sev1 = "High" if infra_score >= 0.8 else "Med" if infra_score >= 0.4 else "Low"
    if infra_score > 0:
        c_risks.append({"name": "Data Integration & Infrastructure", "trigger": "Legacy servers / mixed cloud", "severity": sev1, "mitigation": "Ring-fence legacy; phase scaling on data-readiness.", "score": infra_score})
        
    adoption_penalty = 20 if "voluntary" in (ans.get("Q4.1", "") or "").lower() else 0
    sev2 = "High" if adoption_penalty >= 20 else "Med" if adoption_penalty >= 10 else "Low"
    if adoption_penalty > 0:
        c_risks.append({"name": "Change Management & Adoption", "trigger": "Voluntary/Loose adoption strategy", "severity": sev2, "mitigation": "Tie field KPIs to tooling adoption; exec mandate.", "score": (adoption_penalty / 20.0) * 1.2})
        
    q14 = (ans.get("Q1.4", "") or "").lower()
    sev3 = "High" if "no clear" in q14 else "Med" if "cfo" not in q14 and "ceo" not in q14 else "Low"
    score3 = 1.0 if sev3 == "High" else 0.5 if sev3 == "Med" else 0.0
    if score3 > 0:
        c_risks.append({"name": "Executive Sponsorship", "trigger": "Lacking strong C-suite mandate", "severity": sev3, "mitigation": "Elevate steering committee to CEO/CFO level.", "score": score3})
        
    sev4 = "High" if compliance_uplift >= 0.08 else "Med" if compliance_uplift >= 0.04 else "Low"
    if compliance_uplift > 0:
        c_risks.append({"name": "Compliance & Governance", "trigger": "Strict/Unknown regulatory profile", "severity": sev4, "mitigation": "Front-load Data Governance foundation spend.", "score": compliance_uplift * 5.0})
        
    sev5 = "High" if si_inflation >= 0.3 else "Med" if si_inflation >= 0.1 else "Low"
    if si_inflation > 0:
        c_risks.append({"name": "SI Dependency & Premium", "trigger": "External SI delivery model", "severity": sev5, "mitigation": "Cap SI margins; require internal capability build.", "score": si_inflation * 2.5})
        
    sev6 = "High" if data_badness >= 0.6 else "Med" if data_badness >= 0.3 else "Low"
    if data_badness > 0:
        c_risks.append({"name": "Benefit Realization", "trigger": "Poor data accuracy/freshness", "severity": sev6, "mitigation": "Delay ROI forecasts until Phase 1 data-readiness validates.", "score": data_badness})
        
    q21 = (ans.get("Q2.1", "") or "").lower()
    score7 = 0.8 if "2,000" in q21 or "5,000" in q21 else 0.4 if "500" in q21 else 0.0
    sev7 = "High" if score7 >= 0.8 else "Med" if score7 >= 0.4 else "Low"
    if score7 > 0:
        c_risks.append({"name": "SKU Complexity / Compute", "trigger": "High/massive SKU count", "severity": sev7, "mitigation": "Pilot ML on top 20% SKUs before enterprise rollout.", "score": score7})
        
    c_risks.sort(key=lambda x: x["score"], reverse=True)
    risk_register = c_risks[:5]

    # ── 7. CHART + DERIVATION TRACE ──────────────────────────────────────────
    donut_labels = ["Value Initiatives", "Enabling Investment (Data & Controls)"]
    donut_values = [deployable_usd, foundation_usd]
    donut_colors = ["#D04A02", "#2D2D2D"]

    derivation = {
        "foundation_pct": foundation_pct,
        "total_program_cost_usd": total_program_cost,
        "si_inflation": si_inflation,
        "compliance_foundation_uplift": compliance_uplift,
        "risk_drivers": risk_why,
        "complexity_drivers": complexity_why,
        "cost_overlays": list(filter(None, [si_why, compliance_why])),
    }

    # ── W6. BIGGEST UNLOCK (SENSITIVITY ANALYSIS) ─────────────────────────────
    biggest_unlocks = []
    if not skip_cf:
        base_funded = len(funded)
        
        # Test 1: Cloud Migration
        if infra_score > 0:
            ans_cf = dict(ans)
            ans_cf["Q3.2"] = "modern cloud"
            cf_res = calculate_investment_plan(budget_usd_m, primary_goals, timeline_months, discovery_answers=ans_cf, skip_cf=True)
            cf_funded = len([r for r in cf_res["scoring_matrix"] if r["priority"] in {"High", "Medium"}])
            posture_flip = cf_res["posture"] != posture
            if cf_funded > base_funded or posture_flip:
                biggest_unlocks.append({
                    "lever": "Migrate remaining infrastructure to modern cloud",
                    "delta_funded": cf_funded - base_funded,
                    "posture_flip": cf_res["posture"] if posture_flip else None
                })
                
        # Test 2: Executive Mandate (Adoption)
        if adoption_penalty > 0:
            ans_cf = dict(ans)
            ans_cf["Q4.1"] = "mandatory"
            cf_res = calculate_investment_plan(budget_usd_m, primary_goals, timeline_months, discovery_answers=ans_cf, skip_cf=True)
            cf_funded = len([r for r in cf_res["scoring_matrix"] if r["priority"] in {"High", "Medium"}])
            posture_flip = cf_res["posture"] != posture
            if cf_funded > base_funded or posture_flip:
                biggest_unlocks.append({
                    "lever": "Enforce mandatory field adoption via executive KPIs",
                    "delta_funded": cf_funded - base_funded,
                    "posture_flip": cf_res["posture"] if posture_flip else None
                })
                
        # Test 3: Data Cleansing
        if dq_score > 0.20:
            ans_cf = dict(ans)
            ans_cf["Q3.3"] = "real-time"
            cf_res = calculate_investment_plan(budget_usd_m, primary_goals, timeline_months, discovery_answers=ans_cf, skip_cf=True)
            cf_funded = len([r for r in cf_res["scoring_matrix"] if r["priority"] in {"High", "Medium"}])
            posture_flip = cf_res["posture"] != posture
            if cf_funded > base_funded or posture_flip:
                biggest_unlocks.append({
                    "lever": "Cleanse and unify core master data to real-time accuracy",
                    "delta_funded": cf_funded - base_funded,
                    "posture_flip": cf_res["posture"] if posture_flip else None
                })

    # ── W-NEW. QUADRANT CLASSIFICATION ─────────────────────────────────────
    for uc in scoring_matrix:
        qname, qaction = classify_quadrant(uc["impact"], uc["feasibility"])
        uc["quadrant_name"] = qname
        uc["quadrant_action"] = qaction
        uc["value_type"] = VALUE_TYPE.get(uc["name"], PRODUCTIVITY)

    # ── W-NEW. VALUE PORTFOLIO ────────────────────────────────────────────
    value_ledger_rows = [r for r in ledger_rows if r.get("pillar") == "Value Initiative"]
    
    # Fix: If foundations_first, the client still wants to see the projected portfolio mix.
    # We must calculate what the ledger rows *would* be if they were funded.
    if not value_ledger_rows and scoring_matrix:
        # Determine what would be funded (High/Medium impact + decent feasibility)
        # We can use the quadrant classification (Prime candidates, Tactical add-ons, Strategic bets, Marginal)
        # Strategic bets and Marginal are deferred. Prime candidates and Tactical add-ons would be funded.
        hypothetical_funded = [uc for uc in scoring_matrix if uc["quadrant_name"] in {"Prime candidates", "Tactical add-ons"}]
        
        # In case none fit, just fallback to top 2 by composite score
        if not hypothetical_funded:
            hypothetical_funded = sorted(scoring_matrix, key=lambda x: x["composite_score"], reverse=True)[:2]
            
        total_w = sum(uc["composite_score"] * (uc["feasibility"] / 100.0) for uc in hypothetical_funded) or 1.0
        
        planned_deployable = budget_usd - foundation_usd
        
        for uc in hypothetical_funded:
            w = uc["composite_score"] * (uc["feasibility"] / 100.0)
            alloc = planned_deployable * w / total_w
            value_ledger_rows.append({
                "initiative": uc["name"],
                "allocation_usd": alloc,
                "value_type": uc["value_type"]
            })

    value_portfolio = compute_value_portfolio(
        value_ledger_rows,
        primary_goals,
    )

    goal_cfg = INDUSTRY_BENCHMARKS["primary_goal_allocation"]
    return {
        # ── Cost / allocation (client's own money — not forecasts) ────────────
        "budget_usd_m": budget_usd_m,
        "budget_usd": budget_usd,
        "primary_goals": primary_goals,
        "primary_goal_label": " + ".join(goal_cfg.get(g, goal_cfg["Revenue Growth"])["label"] for g in primary_goals),
        "primary_usd": deployable_usd,
        "foundation_usd": foundation_usd,
        "secondary_usd": 0.0,
        "deployable_usd": deployable_usd,
        "phases": phases,
        "total_cost": total_program_cost,
        "total_budget": budget_usd,
        "si_cost": si_cost,
        "si_inflation": si_inflation,
        "foundation_usd": foundation_usd,
        "compliance_foundation_uplift_pct": compliance_uplift,
        # ── Chart data ────────────────────────────────────────────────────────
        "donut_labels": donut_labels,
        "donut_values": donut_values,
        "donut_colors": donut_colors,
        "risk_register": risk_register,
        # ── Core outputs (matrix drives ledger) ───────────────────────────────
        "scoring_matrix": scoring_matrix,
        "phases": phases,
        "ledger_rows": ledger_rows,
        "value_portfolio": value_portfolio,
        # ── Risk / complexity signals ─────────────────────────────────────────
        "complexity_triggered": complexity_triggered,
        "risk_triggered": risk_triggered,
        "complexity_score": complexity,
        "risk_score": risk,
        "change_mgmt_flag": risk_triggered,
        "change_mgmt_cost": budget_usd * INDUSTRY_BENCHMARKS["change_mgmt_overhead_pct"] if risk_triggered else 0.0,
        "data_eng_line_item": data_eng_line_item,
        "complexity_timeline_penalty_months": timeline_penalty,
        "confidence_band_pct": confidence_band_pct,
        # ── Deterministic maturity (R2) ────────────────────────────────────────
        "data_badness": data_badness,
        "maturity_score": maturity_score,
        "maturity_class": maturity_class,
        "deferred_initiatives": deferred_initiatives,
        "posture": posture,
        "primary_risk": primary_risk_verbose,
        "build_vs_buy_flag": scale == "challenger" and "internal" not in (ans.get("Q4.3", "") or "").lower(),
        # ── Derivation trace ──────────────────────────────────────────────────
        "derivation": derivation,
        "q1_focus": _parse_q1_focus(ans.get("Q1.5", "") or ""),
        "biggest_unlocks": biggest_unlocks,
    }

build_investment_plan = calculate_investment_plan
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


def _data_quality_badness(ans: dict) -> float:
    """Q3.3 -> freshness/accuracy, Q3.2 -> infrastructure. Blends both."""
    a = (ans.get("Q3.3", "") or "").lower()
    if "historically unreliable" in a:        dq = 0.90
    elif "occasionally inaccurate" in a:      dq = 0.50
    elif "daily" in a:                        dq = 0.20
    elif "real-time" in a or "near real" in a: dq = 0.05
    else:                                     dq = 0.40

    cloud = (ans.get("Q3.2", "") or "").lower()
    if "old, slow local" in cloud or "trying to move" in cloud:
        infra = 1.0
    elif "some is on old servers" in cloud:
        infra = 0.5
    else:
        infra = 0.0

    return min(1.0, 0.6 * dq + 0.4 * infra)

def _feasibility(base, data_dependency, data_risk) -> int:
    """Data-hungry use cases lose more feasibility when data is messy."""
    f = base - data_dependency * 55.0 * data_risk
    return int(round(min(max(f, 10), 98)))

def _speed_score(base, build_effort, complexity) -> int:
    s = base - build_effort * 30.0 * complexity
    return int(round(min(max(s, 10), 98)))

def _impact_score(base, lever_value, max_lever_value) -> int:
    """Tilt the impact prior by how much real value this lever carries; fall back
    to the prior when there is no baseline."""
    if max_lever_value and max_lever_value > 0:
        idx = lever_value / max_lever_value
        return int(round(min(max(base * (0.55 + 0.45 * idx), 5), 100)))
    return int(round(base))

LEVER_DATA_DEPENDENCY = {
    "revenue": 0.50, "oos": 0.70, "inventory": 0.85,
    "margin": 0.50, "opex": 0.30, "cx": 0.50,
}

USE_CASE_LIBRARY = {
    "Revenue Growth": [
        {"name": "Trade Promotion Optimization",      "lever": "revenue",   "base_impact": 88, "base_feasibility": 72, "base_speed": 65, "base_fit": 90, "data_dependency": 0.6, "build_effort": 0.6},
        {"name": "Sales Copilot / Next-Best-Action",  "lever": "revenue",   "base_impact": 80, "base_feasibility": 78, "base_speed": 80, "base_fit": 85, "data_dependency": 0.4, "build_effort": 0.4},
        {"name": "Demand Sensing & Forecasting",      "lever": "inventory", "base_impact": 75, "base_feasibility": 70, "base_speed": 70, "base_fit": 80, "data_dependency": 0.9, "build_effort": 0.7},
        {"name": "Consumer Personalization Engine",   "lever": "revenue",   "base_impact": 70, "base_feasibility": 60, "base_speed": 55, "base_fit": 75, "data_dependency": 0.8, "build_effort": 0.7},
    ],
    "Margin Recovery": [
        {"name": "Procurement AI & Supplier Intelligence", "lever": "margin", "base_impact": 90, "base_feasibility": 74, "base_speed": 60, "base_fit": 92, "data_dependency": 0.6, "build_effort": 0.6},
        {"name": "Manufacturing Yield Optimization",       "lever": "margin", "base_impact": 82, "base_feasibility": 65, "base_speed": 55, "base_fit": 85, "data_dependency": 0.7, "build_effort": 0.8},
        {"name": "Logistics Route & Cost Optimization",    "lever": "opex",   "base_impact": 74, "base_feasibility": 80, "base_speed": 75, "base_fit": 78, "data_dependency": 0.5, "build_effort": 0.4},
        {"name": "Predictive Maintenance AI",              "lever": "opex",   "base_impact": 70, "base_feasibility": 68, "base_speed": 60, "base_fit": 72, "data_dependency": 0.7, "build_effort": 0.7},
    ],
    "Enterprise Productivity": [
        {"name": "Enterprise Knowledge Search",       "lever": "opex", "base_impact": 72, "base_feasibility": 88, "base_speed": 90, "base_fit": 80, "data_dependency": 0.3, "build_effort": 0.2},
        {"name": "Invoice & PO Extraction",           "lever": "opex", "base_impact": 68, "base_feasibility": 85, "base_speed": 88, "base_fit": 76, "data_dependency": 0.3, "build_effort": 0.3},
        {"name": "Field Sales Productivity Platform", "lever": "opex", "base_impact": 78, "base_feasibility": 75, "base_speed": 72, "base_fit": 82, "data_dependency": 0.4, "build_effort": 0.4},
        {"name": "Meeting & Document Intelligence",   "lever": "opex", "base_impact": 62, "base_feasibility": 90, "base_speed": 92, "base_fit": 70, "data_dependency": 0.2, "build_effort": 0.2},
    ],
}


def _build_scoring_matrix(primary_goals, complexity, risk, interdependency,
                          ans=None, levers=None, data_risk=0.0, revenue_base=None):
    """Build the prioritisation matrix spanning ALL selected objectives."""
    ans = ans or {}
    levers = levers or []
    lever_value: dict[str, float] = {}
    for lv in levers:
        if lv.get("quantified"):
            k = lv.get("lever_key", "opex")
            lever_value[k] = lever_value.get(k, 0.0) + lv.get("value_mid", 0.0)
    max_lever_value = max(lever_value.values()) if lever_value else 0.0

    # Map raw Q1.1 answers to pillars
    mapped_goals = []
    for g in (primary_goals or []):
        g_low = g.lower()
        if "revenue" in g_low: mapped_goals.append("Revenue Growth")
        elif "margin" in g_low: mapped_goals.append("Margin Recovery")
        elif "productivity" in g_low: mapped_goals.append("Enterprise Productivity")
    if not mapped_goals:
        mapped_goals = ["Revenue Growth"]

    # --- W3: Sector and Scale logic ---
    sub_sector = ans.get("Q0.1", "Other CPG")
    sector_weights = {
        "Food & Beverage": {
            "Demand Sensing & Forecasting": 1.25, "Consumer Personalization Engine": 0.90, "Trade Promotion Optimization": 1.20,
            "Manufacturing Yield Optimization": 1.15, "Logistics Route & Cost Optimization": 1.20, "Procurement AI & Supplier Intelligence": 1.10,
            "Sales Copilot / Next-Best-Action": 1.00, "Predictive Maintenance AI": 1.10
        },
        "Beauty & Personal Care": {
            "Demand Sensing & Forecasting": 1.10, "Consumer Personalization Engine": 1.30, "Trade Promotion Optimization": 1.10,
            "Manufacturing Yield Optimization": 1.00, "Logistics Route & Cost Optimization": 1.00, "Procurement AI & Supplier Intelligence": 1.10,
            "Sales Copilot / Next-Best-Action": 1.10, "Predictive Maintenance AI": 0.95
        },
        "Home & House Care": {
            "Demand Sensing & Forecasting": 1.10, "Consumer Personalization Engine": 0.85, "Trade Promotion Optimization": 1.15,
            "Manufacturing Yield Optimization": 1.20, "Logistics Route & Cost Optimization": 1.05, "Procurement AI & Supplier Intelligence": 1.10,
            "Sales Copilot / Next-Best-Action": 1.00, "Predictive Maintenance AI": 1.15
        },
        "Health & OTC": {
            "Demand Sensing & Forecasting": 1.15, "Consumer Personalization Engine": 0.90, "Trade Promotion Optimization": 1.00,
            "Manufacturing Yield Optimization": 1.10, "Logistics Route & Cost Optimization": 1.05, "Procurement AI & Supplier Intelligence": 1.10,
            "Sales Copilot / Next-Best-Action": 1.00, "Predictive Maintenance AI": 1.05
        }
    }
    weights = sector_weights.get(sub_sector, {})
    
    scale = "enterprise"
    if revenue_base is not None:
        if revenue_base < 1e9: scale = "challenger"
        elif revenue_base < 10e9: scale = "mid"
        
    heavy_plays = {"End-to-end Supply Chain", "Manufacturing Yield Optimization", "Demand Sensing & Forecasting"}

    # --- W2: Value Pool Boosts ---
    q23 = (ans.get("Q2.3", "") or "").lower()
    q24 = (ans.get("Q2.4", "") or "").lower()
    q12 = str(ans.get("Q1.2", "")).lower()
    
    q23_forecast_error = "high" if any(w in q23 for w in ["high", "poor", "inaccurate", "bad"]) else "ok"
    q23_promo_roi = "weak" if any(w in q23 for w in ["weak", "poor roi", "ineffective", "bad"]) else "ok"
    q24_oos = "frequent" if "frequent" in q24 or "constant" in q24 else "ok"
    margin_pressure = True if "margin" in q12 and ("pressure" in q12 or "shrink" in q12 or "decline" in q12) else False

    q41_adopt = (ans.get("Q4.1", "") or "").lower()
    adoption_penalty = 20 if "voluntary" in q41_adopt or "no strategy" in q41_adopt else 10 if "loose" in q41_adopt else 0

    seen: set[str] = set()
    cases: list[dict] = []
    for pillar, c_list in USE_CASE_LIBRARY.items():
        for c in c_list:
            if c["name"] not in seen:
                c_copy = dict(c)
                c_copy["pillar"] = pillar
                cases.append(c_copy)
                seen.add(c["name"])

    scored = []
    for c in cases:
        base_impact = c["base_impact"]
        
        # W3: Sector weight
        w = weights.get(c["name"], 1.0)
        base_impact *= w
        
        # W2: Anchor canonical CPG margin levers
        if "Margin Recovery" in mapped_goals or "Enterprise Productivity" in mapped_goals: # Approximating supply/margin mandate
            if "Trade Promotion Optimization" in c["name"]: base_impact = max(base_impact, 88)
            if "Demand Sensing & Forecasting" in c["name"]: base_impact = max(base_impact, 84)

        # W2: Value pool boosts
        if q23_forecast_error == "high":
            if "Demand Sensing" in c["name"]: base_impact += 12
            if "Trade Promo" in c["name"]: base_impact += 6
        if q23_promo_roi == "weak" and "Trade Promotion Optimization" in c["name"]:
            base_impact += 14
        if q24_oos == "frequent":
            if "Logistics" in c["name"]: base_impact += 10
            if "Demand Sensing" in c["name"]: base_impact += 8
        if margin_pressure:
            if "Procurement" in c["name"]: base_impact += 8
            if "Trade Promo" in c["name"]: base_impact += 8

        # W2: Objective-alignment weighting
        if c["pillar"] in mapped_goals:
            base_impact += 22
            if c["pillar"] == mapped_goals[0]:
                base_impact += 12  # Primary objective bonus
        else:
            base_impact -= 28
            
        base_impact = min(max(base_impact, 0), 100)
        
        impact = _impact_score(base_impact, lever_value.get(c["lever"], 0.0), max_lever_value)
        feasibility = _feasibility(c["base_feasibility"], c["data_dependency"], data_risk)
        
        # W3: Scale penalty for heavy plays
        if scale == "challenger" and c["name"] in heavy_plays:
            feasibility -= 15
            
        # W2: Adoption penalty
        if "Sales Copilot" in c["name"] or "Field Sales" in c["name"]:
            feasibility -= adoption_penalty
            
        impact = min(max(impact, 0), 100)
        feasibility = min(max(feasibility, 0), 100)
        speed = _speed_score(c["base_speed"], c["build_effort"], complexity)
        fit = c["base_fit"]
        composite = impact * 0.40 + feasibility * 0.25 + speed * 0.20 + fit * 0.15
        composite -= 8.0 * risk
        if interdependency:
            composite -= 3.0
        composite = round(max(composite, 0), 1)

        # Priority tier — three levels so table and chart are consistent (G0.3).
        # Thresholds set to ensure meaningful prioritisation (top ~40% funded).
        if composite >= 80:
            priority = "High"
        elif composite >= 72:
            priority = "Medium"
        else:
            priority = "Watch"

        # M4: plain-English rationale for each use case.
        reasons = []
        if impact >= 80:              reasons.append("high business impact for your goals")
        if feasibility < 60:          reasons.append("feasibility limited by data quality / readiness")
        elif feasibility >= 80:       reasons.append("strong readiness")
        if speed >= 82:               reasons.append("fast to deploy")
        if c["build_effort"] >= 0.7: reasons.append("heavier build effort")
        
        if reasons:
            rationale = "; ".join(reasons) + "."
            rationale = rationale[0].upper() + rationale[1:]
        else:
            rationale = "Moderate impact and feasibility; sequenced after higher-priority initiatives."

        scored.append({
            "name": c["name"], "impact": impact, "feasibility": feasibility,
            "speed": speed, "fit": fit, "composite_score": composite,
            "priority": priority, "rationale": rationale,
        })

    scored.sort(key=lambda x: x["composite_score"], reverse=True)
    return scored


build_investment_plan = calculate_investment_plan
