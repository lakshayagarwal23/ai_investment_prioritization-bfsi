"""
engine/legacy_diagnostic.py

Standalone module handling the Deprecation vs. Reallocation analysis for BFSI.
Calculates Deprecation Score based on Tech Debt, Fragmentation, and Governance.
Determines verdicts (KILL, MODERNIZE, HOLD) and funding linkages.
"""

def calculate_tech_debt_score(annual_maintenance_cost: float, business_value_delivered: float, scaling_factor: float = 100.0) -> float:
    """
    Calculates the Technical Debt Interest Score (Weight 40%).
    """
    if business_value_delivered == 0:
        return 100.0
    tech_debt_interest_ratio = annual_maintenance_cost / business_value_delivered
    tech_debt_score = min(100.0, tech_debt_interest_ratio * scaling_factor)
    return tech_debt_score

def calculate_fragmentation_score(silo_count: int, redundancy_factor: float, integration_complexity: float, data_domains: int) -> float:
    """
    Calculates the Data Fragmentation Score (Weight 35%).
    """
    if data_domains == 0:
        return 100.0
    fragmentation_index = (silo_count * redundancy_factor * integration_complexity) / data_domains
    fragmentation_score = min(100.0, fragmentation_index * 20)  # simple linear scaling
    return fragmentation_score

def calculate_governance_readiness_score(data_ownership_clarity: float, lineage_coverage_pct: float,
                                       data_quality_sla_adherence: float, regulatory_traceability: float,
                                       change_mgmt_maturity: float) -> float:
    """
    Calculates the Governance Readiness Score (Weight 25%, Entered Inversely).
    """
    governance_readiness = (data_ownership_clarity + lineage_coverage_pct +
                            data_quality_sla_adherence + regulatory_traceability +
                            change_mgmt_maturity) / 5.0
    return governance_readiness

def calculate_deprecation_score(tech_debt_score: float, fragmentation_score: float, governance_readiness: float) -> float:
    """
    Calculates the composite Deprecation Score (0-100).
    """
    governance_inverse_score = 100.0 - governance_readiness
    deprecation_score = (0.40 * tech_debt_score) + \
                        (0.35 * fragmentation_score) + \
                        (0.25 * governance_inverse_score)
    return deprecation_score

from dataclasses import dataclass
from typing import Optional

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

def run_diagnostic(inputs: LegacyInputs) -> dict:
    td_score = calculate_tech_debt_score(inputs.maintenance_cost_m, inputs.biz_value_m)
    frag_score = calculate_fragmentation_score(int(inputs.silo_count), 1.0, 1.0, 5)
    gov_score = calculate_governance_readiness_score(inputs.data_ownership, inputs.lineage, inputs.dq_sla, inputs.reg_trace, inputs.change_mgmt)
    
    dep_score = calculate_deprecation_score(td_score, frag_score, gov_score)
    verdict = get_deprecation_verdict(dep_score, gov_score)
    
    return {
        "verdict": verdict,
        "pattern": inputs.architecture,
        "rationale": "Computed from technical debt and fragmentation heuristics.",
        "pillars": {
            "tech_debt_score": round(td_score),
            "fragmentation_score": round(frag_score),
            "governance_readiness": round(gov_score)
        },
        "deprecation_score": round(dep_score),
        "self_funding": {
            "legacy_annual_savings_m": round(inputs.maintenance_cost_m, 1),
            "unlocked_anv_m": round(inputs.unlocked_anv_m, 1),
            "total_annual_value_m": round(inputs.maintenance_cost_m + inputs.unlocked_anv_m, 1),
            "rebuild_cost_estimated": True,
            "rebuild_cost_m": 15.0,
            "first_year_funding_gap_m": round(15.0 - (inputs.maintenance_cost_m + inputs.unlocked_anv_m), 1),
            "payback_months": 18
        }
    }

def get_deprecation_verdict(deprecation_score: float, governance_readiness: float) -> str:
    """
    Determines the deprecation verdict based on the calculated scores.
    """
    if deprecation_score >= 70 and governance_readiness >= 50:
        return "KILL & REBUILD (Data Mesh / Cloud-Native)"
    elif deprecation_score >= 70 and governance_readiness < 50:
        return "REBUILD-BLOCKED → Fix governance first (Stage 0)"
    elif 40 <= deprecation_score < 70:
        return "MODERNIZE (strangler-fig / incremental)"
    else:
        return "HOLD & OPTIMIZE"

def calculate_funding_metrics(rebuild_cost: float, legacy_annual_savings_from_kill: float, enabled_lever_anv: float) -> dict:
    """
    Calculates funding gap and self-funding horizon.
    """
    rebuild_funding_gap = rebuild_cost - legacy_annual_savings_from_kill
    total_annual_value = legacy_annual_savings_from_kill + enabled_lever_anv
    if total_annual_value <= 0:
        self_funding_horizon = float('inf')
    else:
        self_funding_horizon = rebuild_cost / (total_annual_value / 12)
        
    return {
        "rebuild_funding_gap": rebuild_funding_gap,
        "self_funding_horizon_months": self_funding_horizon
    }
