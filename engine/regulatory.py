"""
engine/regulatory.py
MMIL-Specific Regulatory Compliance Layer for BFSI AI Investment Engine
Checks AI levers against IRDAI, RBI, and SEBI constraints.
"""
from dataclasses import dataclass

@dataclass
class RegulatoryConstraint:
    name: str
    authority: str
    requirement: str
    impact_on_automation: float
    mitigation: str
    audit_requirement: bool

MMIL_REGULATORY_CONSTRAINTS = [
    RegulatoryConstraint(
        name="Claims Settlement Timeline",
        authority="IRDAI",
        requirement="Claims must be settled within 7-14 days depending on policy type",
        impact_on_automation=0.3,
        mitigation="AI must provide decision within 24 hours; human review within 48 hours for exceptions",
        audit_requirement=True,
    ),
    RegulatoryConstraint(
        name="Explainability in Underwriting",
        authority="IRDAI (Proposed)",
        requirement="Underwriting decisions must be explainable to customer",
        impact_on_automation=0.5,
        mitigation="Use interpretable models; maintain decision rationale logs (MAUDE compliance)",
        audit_requirement=True,
    ),
    RegulatoryConstraint(
        name="Data Localization",
        authority="RBI",
        requirement="Customer data must be stored locally in India",
        impact_on_automation=0.2,
        mitigation="Deploy LLMs in AWS Mumbai or Azure Central India; no cross-border data transfer",
        audit_requirement=True,
    ),
    RegulatoryConstraint(
        name="Grievance Redressal",
        authority="IRDAI",
        requirement="Customer complaints must be resolved within 30 days",
        impact_on_automation=0.4,
        mitigation="Maintain clear AI audit trails for appeals and escalations",
        audit_requirement=True,
    ),
    RegulatoryConstraint(
        name="Solvency Margin Protection",
        authority="IRDAI",
        requirement="Maintain minimum solvency ratio (1.5x)",
        impact_on_automation=0.1,
        mitigation="AI auto-adjudication capped at specific claim amounts; large claims routed to humans",
        audit_requirement=True,
    ),
]

def check_regulatory_compliance(lever_id: str, answers: dict) -> dict:
    """
    Check if a lever can be implemented safely given MMIL regulatory constraints.
    Returns compliant status, relevant constraints, and risk level.
    """
    compliant_constraints = []
    non_compliant_constraints = []
    
    # We apply specific constraints to specific levers based on their domain.
    # E.g. Underwriting (lever_11) gets the explainability constraint.
    active_constraints = []
    
    if lever_id in ["lever_11"]: # Underwriting
        active_constraints = [c for c in MMIL_REGULATORY_CONSTRAINTS if "Explainability" in c.name or "Data Localization" in c.name]
    elif lever_id in ["lever_12"]: # Claims
        active_constraints = [c for c in MMIL_REGULATORY_CONSTRAINTS if "Claims" in c.name or "Solvency" in c.name or "Data Localization" in c.name]
    elif lever_id in ["lever_13", "lever_14"]: # CDP / Onboarding
        active_constraints = [c for c in MMIL_REGULATORY_CONSTRAINTS if "Data Localization" in c.name or "Grievance" in c.name]
    else:
        # Generic levers face standard data localization
        active_constraints = [c for c in MMIL_REGULATORY_CONSTRAINTS if "Data Localization" in c.name]

    # In a real engine, non-compliance would be determined by specific user inputs (e.g., if S1_ARCH == "Cloud Global").
    # Here we mock a basic check: if they have severe data silos, regulatory trace is harder.
    reg_trace = answers.get("S5_REGULATORY_TRACE", 50.0)
    
    for constraint in active_constraints:
        if reg_trace < 40 and constraint.audit_requirement:
            non_compliant_constraints.append(constraint)
        else:
            compliant_constraints.append(constraint)
            
    risk_level = "red" if non_compliant_constraints else ("yellow" if reg_trace < 60 else "green")
    
    return {
        "compliant": len(non_compliant_constraints) == 0,
        "constraints": compliant_constraints + non_compliant_constraints,
        "mitigations": [c.mitigation for c in non_compliant_constraints],
        "audit_requirements": [c.name for c in active_constraints if c.audit_requirement],
        "risk_level": risk_level,
    }
