"""
engine/regulatory.py

India BFSI regulatory compliance layer.
Checks AI levers against IRDAI, RBI, and SEBI constraints, driven by the
firm's ACTUAL answers (governance maturity, data architecture) — not a
static default. A red result caps the lever's automation benefit in the
engine (Reg_NonCompliant_Automation_Cap_Pct in config/value_pools.py).
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


BFSI_REGULATORY_CONSTRAINTS = [
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
        requirement="Underwriting decisions must be explainable to the customer",
        impact_on_automation=0.5,
        mitigation="Use interpretable models; maintain decision-rationale logs",
        audit_requirement=True,
    ),
    RegulatoryConstraint(
        name="Data Localization",
        authority="RBI",
        requirement="Customer data must be stored locally in India",
        impact_on_automation=0.2,
        mitigation="Deploy models in-region (e.g. AWS Mumbai / Azure Central India); no cross-border transfer",
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
    RegulatoryConstraint(
        name="Algorithmic Accountability (Markets)",
        authority="SEBI",
        requirement="Order-routing and advisory algorithms require approval, audit trails and kill-switches",
        impact_on_automation=0.3,
        mitigation="Register algos; log every automated decision with a replayable audit trail",
        audit_requirement=True,
    ),
]

# Which constraints bite which levers
_LEVER_CONSTRAINTS = {
    "lever_2":  ["Algorithmic Accountability (Markets)", "Data Localization"],
    "lever_11": ["Explainability in Underwriting", "Data Localization"],
    "lever_12": ["Claims Settlement Timeline", "Solvency Margin Protection", "Data Localization"],
    "lever_13": ["Data Localization", "Grievance Redressal"],
    "lever_14": ["Data Localization", "Grievance Redressal"],
}
_DEFAULT_CONSTRAINTS = ["Data Localization"]


def check_regulatory_compliance(lever_id: str, answers: dict) -> dict:
    """Assess a lever against its constraints using ASKED inputs:
    - S5_GOVERNANCE_SCORE proxies audit-trail / traceability readiness
    - S1_ARCH flags data-residency exposure for cloud estates
    """
    names = _LEVER_CONSTRAINTS.get(lever_id, _DEFAULT_CONSTRAINTS)
    active = [c for c in BFSI_REGULATORY_CONSTRAINTS if c.name in names]

    try:
        governance = float(answers.get("S5_GOVERNANCE_SCORE", 50.0))
    except (TypeError, ValueError):
        governance = 50.0
    governance = max(0.0, min(100.0, governance))
    arch = str(answers.get("S1_ARCH", "")).lower()

    compliant, non_compliant, mitigations = [], [], []
    for c in active:
        failed = False
        # Weak governance cannot evidence the audit trail regulators demand
        if c.audit_requirement and governance < 35:
            failed = True
        # Cloud estates must evidence in-region residency for localization rules
        if c.name == "Data Localization" and "cloud-native" in arch and governance < 60:
            failed = True
        if failed:
            non_compliant.append(c)
            mitigations.append(c.mitigation)
        else:
            compliant.append(c)

    if non_compliant:
        risk_level = "red"
    elif governance < 60:
        risk_level = "yellow"
        mitigations = [c.mitigation for c in active if c.impact_on_automation >= 0.3]
    else:
        risk_level = "green"

    return {
        "compliant": not non_compliant,
        "constraints": compliant + non_compliant,
        "mitigations": mitigations,
        "audit_requirements": [c.name for c in active if c.audit_requirement],
        "risk_level": risk_level,
        "max_automation_impact": max((c.impact_on_automation for c in non_compliant), default=0.0),
    }
