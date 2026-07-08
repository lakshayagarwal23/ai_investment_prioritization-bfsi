"""
config/questions.py

Trimmed BFSI intake questionnaire with dynamic routing.
Implements the 48 -> 16 question trim, explicit AI provenance tags,
and declarative visible_when gating for the PwC Horizon redesign.
"""

SECTIONS = [
    {"id": "S1", "nav_label": "Technology", "title": "Technology & Data Infrastructure"},
    {"id": "S2", "nav_label": "Front Office", "title": "Front Office Operations"},
    {"id": "S3", "nav_label": "Middle/Back", "title": "Middle & Back Office Operations"},
    {"id": "S4", "nav_label": "Risk & KYC", "title": "Risk, Compliance & Onboarding"},
    {"id": "S5", "nav_label": "Legacy", "title": "Legacy Systems & Governance"},
]

def get_section(section_id: str) -> dict:
    for s in SECTIONS:
        if s["id"] == section_id:
            return s
    return SECTIONS[0]

def get_questions_for_section(section_id: str, sector: str = "all") -> list[dict]:
    # Returns questions that match the section
    return [q for q in QUESTIONS if q["section"] == section_id]

OTHER_OPTION = "Other (type below)"

OBJECTIVE_INPUTS = [
    "Margin Expansion (Cost)",
    "Alpha Generation (Revenue)",
    "Regulatory Resilience (Risk)",
    "Client Coverage Scaling",
]

QUESTIONS = [
    # ─── S1: Technology & Data Infrastructure ─────────────────────────────────
    {
        "id": "S1_AUM",
        "section": "S1",
        "question": "Total AUM / Gross Written Premium ($B)",
        "type": "numeric",
        "help": "Enter in Billions USD (e.g. 50 for $50B). Primary scaling factor for all revenue levers.",
        "default": 50.0,
        "provenance": "AUTO",
        "sectors": ["all"]
    },
    {
        "id": "S1_ARCH",
        "section": "S1",
        "question": "Core data warehouse / platform architecture",
        "type": "categorical",
        "options": [
            "Siloed On-Premises (Batch)",
            "Hybrid — partial cloud",
            "Cloud-Native (AWS/Azure/GCP)"
        ],
        "default": "Hybrid — partial cloud",
        "provenance": "AUTO",
        "sectors": ["all"]
    },
    {
        "id": "S1_ERP",
        "section": "S1",
        "question": "Core ERP / Policy Admin System status",
        "type": "categorical",
        "options": [
            "Legacy monolith (>10 years old)",
            "On-prem with API layer",
            "Modern cloud-native"
        ],
        "default": "On-prem with API layer",
        "provenance": "AUTO",
        "sectors": ["all"]
    },
    {
        "id": "S1_KTLO",
        "section": "S1",
        "question": "Maintenance-to-Innovation ratio (% of IT budget on Run)",
        "type": "percentage",
        "default": 72,
        "provenance": "MANUAL",
        "sectors": ["all"]
    },
    {
        "id": "S1_SILO",
        "section": "S1",
        "question": "Number of distinct systems holding core data entities",
        "type": "numeric",
        "default": 5.0,
        "provenance": "MANUAL",
        "sectors": ["all"]
    },

    # ─── S2: Front Office ─────────────────────────────────────────────────────
    {
        "id": "S2_ELECTRONIC_FLOW",
        "section": "S2",
        "question": "Share of order/application flow that is already electronic (STP)",
        "type": "percentage",
        "default": 60,
        "provenance": "MANUAL",
        "sectors": ["all"]
    },
    {
        "id": "S2_ANNUAL_UNDERWRITING_APPS",
        "section": "S2",
        "question": "Annual life insurance / policy applications",
        "type": "numeric",
        "default": 50000.0,
        "provenance": "AUTO",
        "visible_when": {"sector": ["Life & General Insurance", "Diversified Financial Services"]},
    },
    {
        "id": "S2_QUOTE_TO_BIND_DAYS",
        "section": "S2",
        "question": "Average quote-to-bind / turnaround (days)",
        "type": "numeric",
        "default": 7.0,
        "provenance": "MANUAL",
        "visible_when": {"sector": ["Life & General Insurance", "Diversified Financial Services"]},
    },

    # ─── S3: Middle & Back Office ─────────────────────────────────────────────
    {
        "id": "S3_STP",
        "section": "S3",
        "question": "Current overall Straight-Through Processing (STP) rate",
        "type": "percentage",
        "default": 65,
        "provenance": "MANUAL",
        "sectors": ["all"]
    },
    {
        "id": "S3_TOTAL_OPS_FTE",
        "section": "S3",
        "question": "Total FTEs dedicated to manual operations (Recon, Claims, Onboarding)",
        "type": "numeric",
        "default": 50.0,
        "provenance": "MANUAL",
        "sectors": ["all"],
        "help": "Merged FTE pool representing the addressable base for operational automation."
    },
    {
        "id": "S3_ANNUAL_CLAIMS",
        "section": "S3",
        "question": "Annual insurance claims processed",
        "type": "numeric",
        "default": 100000.0,
        "provenance": "AUTO",
        "visible_when": {"sector": ["Life & General Insurance", "Diversified Financial Services"]},
    },

    # ─── S4: Risk & Compliance ────────────────────────────────────────────────
    {
        "id": "S4_AML_FALSE_POS",
        "section": "S4",
        "question": "AML false-positive alert rate",
        "type": "percentage",
        "default": 85,
        "provenance": "VERIFY",
        "sectors": ["all"]
    },
    {
        "id": "S4_REG_MONTHS",
        "section": "S4",
        "question": "Time to operationalize a new regulatory reporting requirement (months)",
        "type": "numeric",
        "default": 6.0,
        "provenance": "MANUAL",
        "sectors": ["all"]
    },

    # ─── S5: Legacy Diagnostics & Governance ─────────────────────────────────
    {
        "id": "S5_MAINTENANCE_COST",
        "section": "S5",
        "question": "Annual legacy system maintenance cost ($M)",
        "type": "numeric",
        "default": 6.5,
        "provenance": "MANUAL",
        "sectors": ["all"]
    },
    {
        "id": "S5_BIZ_VALUE",
        "section": "S5",
        "question": "Business value delivered by legacy systems annually ($M)",
        "type": "numeric",
        "default": 20.0,
        "provenance": "MANUAL",
        "sectors": ["all"]
    },
    {
        "id": "S5_GOVERNANCE_SCORE",
        "section": "S5",
        "question": "Overall Data Governance Maturity (1-100)",
        "type": "numeric",
        "default": 50,
        "provenance": "MANUAL",
        "sectors": ["all"],
        "help": "Composite 1-100 score encompassing Ownership, Lineage, DQ, and Change Management."
    },
]