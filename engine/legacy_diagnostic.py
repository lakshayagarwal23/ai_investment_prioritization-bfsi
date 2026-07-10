"""
engine/legacy_diagnostic.py

Legacy-estate deprecation diagnostic (TCO framework).

Follows the standard decommissioning decision framework (DXC / TechTarget):
  1. ROI & cost analysis     -> TCO-to-value ratio (maintenance vs business value)
  2. Technical health & deps -> fragmentation (silos, architecture, API maturity)
  3. Modern alternatives     -> rebuild capex vs self-funding horizon
  4. Retirement strategy     -> verdict-specific transition guardrails

EXPLAINABILITY CONTRACT: every score this module returns carries the exact
inputs and arithmetic used to produce it ("score_math", per-pillar "explain").
The UI renders these verbatim — no black-box numbers.
"""

from dataclasses import dataclass
from typing import Optional

# Composite weights — surfaced verbatim in the UI.
WEIGHTS = {"tech_debt": 0.40, "fragmentation": 0.35, "governance_gap": 0.25}


def calculate_tech_debt_score(annual_maintenance_cost: float, business_value_delivered: float,
                              scaling_factor: float = 100.0) -> float:
    """Technical-debt interest: annual TCO as a share of the business value the
    estate delivers. Ratio 0.5 (spending 50c to earn $1) -> score 50/100."""
    if business_value_delivered <= 0:
        return 100.0
    tech_debt_interest_ratio = annual_maintenance_cost / business_value_delivered
    return min(100.0, tech_debt_interest_ratio * scaling_factor)


def calculate_fragmentation_score(silo_count: int, architecture: str, api_maturity: str) -> float:
    """Technical health & dependency risk: silo count scaled by how hard the
    architecture and integration layer make decoupling."""
    base = min(100.0, silo_count * 12.5)

    arch_lower = architecture.lower()
    if "siloed" in arch_lower:
        arch_modifier = 1.2
    elif "cloud-native" in arch_lower:
        arch_modifier = 0.5
    else:
        arch_modifier = 1.0

    api_lower = api_maturity.lower()
    if "batch" in api_lower or "etl" in api_lower or "monolith" in api_lower:
        api_modifier = 1.3
    elif "cloud-native" in api_lower or "graphql" in api_lower or "event-driven" in api_lower:
        api_modifier = 0.6
    else:
        api_modifier = 1.0

    return min(100.0, base * arch_modifier * api_modifier)


def calculate_deprecation_score(tech_debt_score: float, fragmentation_score: float,
                                governance_readiness: float) -> float:
    """Composite 0-100. Governance enters inversely: weak governance raises
    the case for intervention (you cannot safely keep patching what you
    cannot trace)."""
    governance_gap = 100.0 - governance_readiness
    return (WEIGHTS["tech_debt"] * tech_debt_score
            + WEIGHTS["fragmentation"] * fragmentation_score
            + WEIGHTS["governance_gap"] * governance_gap)


def get_deprecation_verdict(deprecation_score: float, governance_readiness: float) -> str:
    if deprecation_score >= 70 and governance_readiness >= 50:
        return "REPLACE THE CORE"
    elif deprecation_score >= 70 and governance_readiness < 50:
        return "FIX GOVERNANCE FIRST"
    elif 40 <= deprecation_score < 70:
        return "MODERNIZE IN PHASES"
    else:
        return "KEEP AND OPTIMIZE"


# Verdict playbook: plain-English meaning, recommended decision, and
# retirement-strategy safeguards. No jargon; a BFSI executive should be able
# to read every line without a glossary.
VERDICT_PLAYBOOK = {
    "REPLACE THE CORE": {
        "css": "kill",
        "recommend_funding": True,
        "action": "Retire the legacy estate and rebuild on a modern platform. "
                  "What you spend keeping it alive, plus the AI value it blocks, "
                  "now outweighs what it still delivers.",
        "guardrails": [
            "Archive all historical data to meet statutory retention rules before any switch-over",
            "Map every system that feeds or depends on the estate before removing anything",
            "Move in stages, running old and new side by side. Never switch everything at once",
            "Decommission retired hardware securely, with certified data wiping or destruction",
        ],
    },
    "FIX GOVERNANCE FIRST": {
        "css": "blocked",
        "recommend_funding": False,
        "action": "The estate deserves retirement, but your data governance is too weak "
                  "to migrate safely. You cannot move data you cannot trace. Fix data "
                  "ownership and lineage first, then re-run this diagnostic.",
        "guardrails": [
            "Establish clear data ownership and lineage before any migration planning",
            "Do not start a rebuild while governance is below 50: migration errors would be untraceable",
        ],
    },
    "MODERNIZE IN PHASES": {
        "css": "modernize",
        "recommend_funding": True,
        "action": "Do not replace everything at once. Put a modern access layer in front "
                  "of the old systems, then move one function at a time onto the new "
                  "platform. Each move retires part of the old cost before the next "
                  "begins. At your debt level this is cheaper and safer than a full rewrite.",
        "guardrails": [
            "Build new capabilities against the modern access layer, never directly on the old core",
            "Retire the most expensive-to-maintain functions first, so savings arrive early",
            "Archive each function's data as it is retired, to preserve the audit trail",
        ],
    },
    "KEEP AND OPTIMIZE": {
        "css": "hold",
        "recommend_funding": False,
        "action": "The estate earns its keep today. Contain its costs, keep security "
                  "patched, and re-run this diagnostic annually.",
        "guardrails": [
            "Renegotiate legacy vendor licensing regularly. It drifts upward silently",
            "Watch the cost-to-value ratio each year. Above 50% this verdict changes",
        ],
    },
}


@dataclass
class LegacyInputs:
    maintenance_cost_m: float
    biz_value_m: float
    silo_count: float
    architecture: str
    api_maturity: str
    data_ownership: float
    lineage: float
    dq_sla: float
    reg_trace: float
    change_mgmt: float
    unlocked_anv_m: float
    rebuild_cost_m: Optional[float] = None
    governance_score: float = 50.0


def run_diagnostic(inputs: LegacyInputs) -> dict:
    td_score = calculate_tech_debt_score(inputs.maintenance_cost_m, inputs.biz_value_m)
    frag_score = calculate_fragmentation_score(int(inputs.silo_count), inputs.architecture,
                                               inputs.api_maturity)
    gov_score = max(0.0, min(100.0, inputs.governance_score))
    gov_gap = 100.0 - gov_score

    dep_score = calculate_deprecation_score(td_score, frag_score, gov_score)
    verdict = get_deprecation_verdict(dep_score, gov_score)
    playbook = VERDICT_PLAYBOOK[verdict]

    # 1. ROI & cost analysis — TCO position
    if inputs.biz_value_m > 0:
        tco_ratio_pct = (inputs.maintenance_cost_m / inputs.biz_value_m) * 100.0
    else:
        tco_ratio_pct = float("inf")
    if tco_ratio_pct < 25:
        tco_band = "healthy"
        tco_verdict = "The estate earns its keep. Maintenance is a small share of the value it delivers."
    elif tco_ratio_pct < 50:
        tco_band = "watch"
        tco_verdict = "A meaningful share of the estate's value is consumed just keeping it alive."
    elif tco_ratio_pct <= 100:
        tco_band = "critical"
        tco_verdict = "Maintenance consumes most of the value the estate delivers."
    else:
        tco_band = "value-negative"
        tco_verdict = ("The estate costs more to run than the value it generates. "
                       "Retirement is the actionable path.")

    # Security & compliance exposure (framework step 1b) — from asked inputs
    security_flag = ("monolith" in inputs.api_maturity.lower()
                     or "siloed" in inputs.architecture.lower())

    # 3. Modern alternatives — rebuild vs status quo
    rebuild_cost = inputs.rebuild_cost_m if inputs.rebuild_cost_m is not None \
        else (inputs.maintenance_cost_m * 3.5)
    legacy_annual_savings = inputs.maintenance_cost_m * 0.65
    funding = calculate_funding_metrics(rebuild_cost, legacy_annual_savings, inputs.unlocked_anv_m)

    return {
        "verdict": verdict,
        "verdict_css": playbook["css"],
        "verdict_action": playbook["action"],
        "recommend_funding": playbook["recommend_funding"],
        "guardrails": playbook["guardrails"],
        "pattern": inputs.architecture,
        "rationale": f"Computed dynamically: Tech Debt ({td_score:.1f}/100) vs Fragmentation ({frag_score:.1f}/100)",
        "pillars": {
            "tech_debt_score": round(td_score),
            "fragmentation_score": round(frag_score),
            "governance_readiness": round(gov_score),
        },
        "pillar_explain": {
            "tech_debt": (f"${inputs.maintenance_cost_m:g}M annual maintenance divided by "
                          f"${inputs.biz_value_m:g}M business value = "
                          f"{tco_ratio_pct:.0f}% cost-to-value ratio, giving {td_score:.0f}/100"
                          if tco_ratio_pct != float("inf") else
                          f"${inputs.maintenance_cost_m:g}M maintenance against zero stated "
                          f"business value, giving 100/100"),
            "fragmentation": (f"{int(inputs.silo_count)} systems hold the same data, on a "
                              f"\"{inputs.architecture}\" architecture with a "
                              f"\"{inputs.api_maturity}\" core, giving {frag_score:.0f}/100"),
            "governance": (f"Your governance maturity of {gov_score:.0f}/100 counts inversely: "
                           f"the weaker the governance, the stronger the case to intervene "
                           f"(gap = {gov_gap:.0f}/100)"),
        },
        "deprecation_score": round(dep_score),
        "score_math": (f"{WEIGHTS['tech_debt']:.2f} × {td_score:.0f} (tech debt) + "
                       f"{WEIGHTS['fragmentation']:.2f} × {frag_score:.0f} (fragmentation) + "
                       f"{WEIGHTS['governance_gap']:.2f} × {gov_gap:.0f} (governance gap) "
                       f"= {dep_score:.0f} / 100"),
        "tco": {
            "annual_maintenance_m": round(inputs.maintenance_cost_m, 1),
            "business_value_m": round(inputs.biz_value_m, 1),
            "ratio_pct": None if tco_ratio_pct == float("inf") else round(tco_ratio_pct),
            "band": tco_band,
            "verdict": tco_verdict,
            "security_flag": security_flag,
        },
        "self_funding": {
            "legacy_annual_savings_m": round(legacy_annual_savings, 1),
            "unlocked_anv_m": round(inputs.unlocked_anv_m, 1),
            "total_annual_value_m": round(legacy_annual_savings + inputs.unlocked_anv_m, 1),
            "rebuild_cost_estimated": inputs.rebuild_cost_m is None,
            "rebuild_cost_m": round(rebuild_cost, 1),
            "first_year_funding_gap_m": round(funding["rebuild_funding_gap"], 1),
            "payback_months": round(funding["self_funding_horizon_months"])
                if funding["self_funding_horizon_months"] != float("inf") else None,
        },
    }


def calculate_funding_metrics(rebuild_cost: float, legacy_annual_savings_from_kill: float,
                              enabled_lever_anv: float) -> dict:
    rebuild_funding_gap = rebuild_cost - legacy_annual_savings_from_kill
    total_annual_value = legacy_annual_savings_from_kill + enabled_lever_anv
    if total_annual_value <= 0:
        self_funding_horizon = float("inf")
    else:
        self_funding_horizon = rebuild_cost / (total_annual_value / 12)
    return {
        "rebuild_funding_gap": rebuild_funding_gap,
        "self_funding_horizon_months": self_funding_horizon,
    }
