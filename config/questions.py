"""
config/questions.py

Trimmed BFSI intake questionnaire with dynamic routing.
Implements the 48 -> 16 question trim, explicit AI provenance tags,
and declarative visible_when gating for the PwC Horizon redesign.
Updated: Jargon eliminated for C-suite readability.
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

# Single source of truth: the goal strings levers align to in value_pools.py.
from config.value_pools import GOALS as OBJECTIVE_INPUTS

QUESTIONS = [
    # ─── S1: Technology & Data Infrastructure ─────────────────────────────────
    {
        "id": "S1_AUM",
        "section": "S1",
        "question": "What is the total size of assets or premiums your firm manages ($ Billions)?",
        "type": "numeric",
        "help": "This helps us estimate the dollar value of revenue-focused AI investments.",
        "default": 50.0,
        "provenance": "AUTO",
        "sectors": ["all"]
    },
    {
        "id": "S1_ARCH",
        "section": "S1",
        "question": "Where is your core business data primarily stored?",
        "type": "categorical",
        "help": "This determines how easily AI can access your data. Older, on-premise systems require more effort to integrate.",
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
        "question": "How modern is your core administrative system?",
        "type": "categorical",
        "help": "Older systems increase the difficulty and cost of rolling out complex operational AI.",
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
        "question": "What percentage of your IT budget is spent just \"keeping the lights on\"?",
        "type": "percentage",
        "help": "A high maintenance budget means less funding is available for deploying new AI capabilities.",
        "default": 72,
        "provenance": "MANUAL",
        "sectors": ["all"]
    },
    {
        "id": "S1_SILO",
        "section": "S1",
        "question": "How many separate systems hold your critical customer or product data?",
        "type": "numeric",
        "help": "More fragmented systems make it harder and more expensive to connect AI agents to your workflows.",
        "default": 5.0,
        "provenance": "MANUAL",
        "sectors": ["all"]
    },

    # ─── S2: Front Office ─────────────────────────────────────────────────────
    {
        "id": "S2_ELECTRONIC_FLOW",
        "section": "S2",
        "question": "What percentage of your customer applications are handled completely digitally?",
        "type": "percentage",
        "help": "This shows how much manual work remains. Lower digital adoption means a larger opportunity for AI automation.",
        "default": 60,
        "provenance": "MANUAL",
        "sectors": ["all"]
    },
    {
        "id": "S2_ANNUAL_UNDERWRITING_APPS",
        "section": "S2",
        "question": "How many policy applications do you process annually?",
        "type": "numeric",
        "help": "This sets the baseline to calculate potential savings from automated underwriting.",
        "default": 250000.0,
        "provenance": "AUTO",
        "visible_when": {"sector": ["Life & General Insurance", "Diversified Financial Services"]},
    },
    {
        "id": "S2_QUOTE_TO_BIND_DAYS",
        "section": "S2",
        "question": "How many days does it take on average to onboard a new customer?",
        "type": "numeric",
        "help": "Longer wait times suggest a strong business case for using AI to speed up approvals.",
        "default": 7.0,
        "provenance": "MANUAL",
        "visible_when": {"sector": ["Life & General Insurance", "Diversified Financial Services"]},
    },

    # ─── S3: Middle & Back Office ─────────────────────────────────────────────
    {
        "id": "S3_STP",
        "section": "S3",
        "question": "What percentage of transactions are processed without any human intervention?",
        "type": "percentage",
        "help": "Identifies room for back-office efficiency. AI focuses on the gap between your current rate and full automation.",
        "default": 65,
        "provenance": "MANUAL",
        "sectors": ["all"]
    },
    {
        "id": "S3_TOTAL_OPS_FTE",
        "section": "S3",
        "question": "How many full-time employees handle manual back-office tasks?",
        "type": "numeric",
        "help": "This number is used to estimate the direct cost savings AI could achieve in operations.",
        "default": 400.0,
        "provenance": "MANUAL",
        "sectors": ["all"]
    },
    {
        "id": "S3_ANNUAL_CLAIMS",
        "section": "S3",
        "question": "How many insurance claims do you process annually?",
        "type": "numeric",
        "help": "This helps us calculate the financial impact of automating claims and detecting fraud.",
        "default": 500000.0,
        "provenance": "AUTO",
        "visible_when": {"sector": ["Life & General Insurance", "Diversified Financial Services"]},
    },

    # ─── S4: Risk & Compliance ────────────────────────────────────────────────
    {
        "id": "S4_AML_FALSE_POS",
        "section": "S4",
        "question": "What is your false-positive rate for compliance alerts (e.g., AML/KYC)?",
        "type": "percentage",
        "help": "High false positives waste valuable analyst time. This measures the immediate potential for AI triaging.",
        "default": 85,
        "provenance": "VERIFY",
        "sectors": ["all"]
    },
    {
        "id": "S4_REG_MONTHS",
        "section": "S4",
        "question": "How many months does it take to implement a new regulatory reporting requirement?",
        "type": "numeric",
        "help": "This highlights compliance bottlenecks and the potential for AI to accelerate reporting cycles.",
        "default": 6.0,
        "provenance": "MANUAL",
        "sectors": ["all"]
    },

    # ─── S5: Legacy Diagnostics & Governance ─────────────────────────────────
    {
        "id": "S5_MAINTENANCE_COST",
        "section": "S5",
        "question": "What is the annual cost of maintaining your legacy systems ($ Millions)?",
        "type": "numeric",
        "help": "This defines your technical debt and the pool of savings available if systems are modernized.",
        "default": 6.5,
        "provenance": "MANUAL",
        "sectors": ["all"]
    },
    {
        "id": "S5_BIZ_VALUE",
        "section": "S5",
        "question": "What is the estimated annual business value driven by your legacy systems ($ Millions)?",
        "type": "numeric",
        "help": "We compare this against maintenance costs to determine the true financial health of your legacy tech.",
        "default": 20.0,
        "provenance": "MANUAL",
        "sectors": ["all"]
    },
    {
        "id": "S5_GOVERNANCE_SCORE",
        "section": "S5",
        "question": "How would you rate your organization's data governance maturity (0-100)?",
        "type": "percentage",
        "help": "A low score means data quality issues could block advanced AI projects until resolved.",
        "default": 50,
        "provenance": "MANUAL",
        "sectors": ["all"]
    },
]