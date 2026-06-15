"""
config/questions.py

Refined discovery question framework — 12 questions across 4 executive phases.
Rewritten in a professional, McKinsey-diagnostic tone suitable for Fortune 500 C-suite users.
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# SECTION DEFINITIONS
# ─────────────────────────────────────────────────────────────────────────────

SECTIONS: list[dict] = [
    {
        "id": "S1",
        "title": "Phase 1: Strategic Mandate",
        "nav_label": "STRATEGY",
        "subtitle": "Value drivers, hurdle rates, and capital thresholds.",
        "description": "Define the mathematical target and strategic sponsor for this capital allocation.",
        "color": "#FF5A00", 
        "icon": "",
    },
    {
        "id": "S2",
        "title": "Phase 2: Operational Baselines",
        "nav_label": "OPERATIONS",
        "subtitle": "Sizing the mathematical upside.",
        "description": "Establish current operational baselines to calculate potential working capital and margin recovery.",
        "color": "#1A1A1A",
        "icon": "",
    },
    {
        "id": "S3",
        "title": "Phase 3: Data & Infrastructure Debt",
        "nav_label": "INFRASTRUCTURE",
        "subtitle": "Calculating the implementation cost and engineering effort.",
        "description": "Assess the state of the data estate and ERP topology to forecast data engineering requirements.",
        "color": "#00B894",
        "icon": "",
    },
    {
        "id": "S4",
        "title": "Phase 4: Execution & Governance Risk",
        "nav_label": "RISK",
        "subtitle": "Calculating risk overlays and confidence bands.",
        "description": "Identify change management friction, SI dependencies, and compliance constraints to bound the risk variance.",
        "color": "#6C5CE7",
        "icon": "",
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# QUESTIONS
# ─────────────────────────────────────────────────────────────────────────────

QUESTIONS: list[dict] = [
    # Phase 1: Strategic Mandate
    {
        "id": "Q1.1", "section": "S1",
        "text": "What are your company's critical strategic objectives right now? (Select all that apply)",
        "rationale": "Directly determines primary goal allocation and multi-KPI alignment in the financial model.",
        "tags": ["Financial Model"],
        "input_type": "multi_select",
        "options": ["Grow revenue and market share fast", "Protect our profit margins from rising costs", "Improve customer satisfaction dramatically", "Cut operating expenses", "Make the supply chain bulletproof"],
    },
    {
        "id": "Q1.2", "section": "S1",
        "text": "For the KPIs selected above, what are your current baseline metrics and your specific target percentage improvements?",
        "rationale": "Sets the starting point and specific hurdle rate to calculate the absolute required ROI and financial uplift.",
        "tags": ["ROI Threshold", "Baseline Metrics"],
        "input_type": "dynamic_kpi_targets",
        "options": None,
    },
    {
        "id": "Q1.3", "section": "S1",
        "text": "What is the maximum acceptable payback period (time-to-value) for this capital allocation?",
        "rationale": "Filters out high-ROI but slow-maturing use cases if they exceed the board's patience threshold.",
        "tags": ["Scoring Input"],
        "input_type": "single_select",
        "options": ["Under 12 months", "12 to 18 months", "18 to 24 months", "24 to 36 months", "No strict timeline if ROI is compelling"],
    },
    {
        "id": "Q1.4", "section": "S1",
        "text": "Who is the main executive sponsoring this project?",
        "rationale": "Sponsor seniority correlates directly with cross-functional barrier removal.",
        "tags": ["Risk Modifier"],
        "input_type": "single_select",
        "options": ["The CEO or Board", "The CFO", "The Head of Tech / IT", "The Head of Sales or Marketing", "The Head of Supply Chain", "We don't have one clear sponsor"],
    },
    {
        "id": "Q1.5", "section": "S1",
        "text": "Are there any known interdependencies or trade-offs between these objectives? (e.g., will increasing sales strain the supply chain?)",
        "rationale": "Addresses the complexity of real-world business metrics to incorporate realistic constraints and potential penalties.",
        "tags": ["Complexity Modifier", "Risk"],
        "input_type": "text",
        "options": None,
    },

    # Phase 2: Operational Baselines
    {
        "id": "Q2.1", "section": "S2",
        "text": "How many different products (SKUs) do you actively sell?",
        "rationale": "SKU density determines the computational complexity required for demand forecasting.",
        "tags": ["Complexity Modifier"],
        "input_type": "single_select",
        "options": ["Under 500", "500 to 2,000", "2,000 to 5,000", "Over 5,000"],
    },
    {
        "id": "Q2.2", "section": "S2",
        "text": "How many regional warehouses or distribution centers do you operate?",
        "rationale": "Node complexity exponentially increases the value derived from AI-driven logistics routing.",
        "tags": ["Complexity Modifier"],
        "input_type": "single_select",
        "options": ["Under 5", "5 to 15", "15 to 30", "Over 30"],
    },
    {
        "id": "Q2.3", "section": "S2",
        "text": "What is your current baseline for Trade Promotion ROI, and what is your average SKU forecast error rate?",
        "rationale": "Calculates the exact dollar value of the working capital and margin release.",
        "tags": ["ROI Projection"],
        "input_type": "text",
        "options": None,
    },
    {
        "id": "Q2.4", "section": "S2",
        "text": "How frequently do out-of-stock (OOS) events impact top-line revenue?",
        "rationale": "Determines the urgency and baseline for supply chain interventions.",
        "tags": ["Risk Modifier"],
        "input_type": "single_select",
        "options": ["Rarely", "Occasionally", "Frequently", "Constantly"],
    },

    # Phase 3: Data & Infrastructure Debt
    {
        "id": "Q3.1", "section": "S3",
        "text": "Is your core ERP architecture centralized or highly fragmented?",
        "rationale": "ERP fragmentation is universally the most underestimated cost and timeline driver in enterprise AI.",
        "tags": ["Complexity Modifier"],
        "input_type": "single_select",
        "options": ["Fully centralized (e.g., global SAP S/4HANA instance)", "Mostly centralized, minor legacy systems", "Highly fragmented across business units", "Complete lack of centralized ERP architecture"],
    },
    {
        "id": "Q3.2", "section": "S3",
        "text": "Is all your important company data stored safely in the cloud?",
        "rationale": "Lack of a unified data lake/warehouse necessitates foundational capital expenditure before AI ROI can be realized.",
        "tags": ["Complexity Modifier"],
        "input_type": "single_select",
        "options": ["Yes, all of it is in a modern cloud", "Some of it is in the cloud, some is on old servers", "No, almost all of it is on old, slow local servers", "We are currently trying to move it to the cloud right now"],
    },
    {
        "id": "Q3.3", "section": "S3",
        "text": "How frequently is your core business data updated and refreshed, and how accurate is it perceived to be?",
        "rationale": "The freshness of data is critical for AI. Stale or inaccurate data directly impacts the system's confidence score and feasibility.",
        "tags": ["Confidence Modifier", "Data Quality"],
        "input_type": "single_select",
        "options": ["Real-time/near real-time & highly accurate", "Daily & generally accurate", "Weekly/Monthly & occasionally inaccurate", "Less frequently & historically unreliable"],
    },

    # Phase 4: Execution & Governance Risk
    {
        "id": "Q4.1", "section": "S4",
        "text": "Are field-level KPIs aligned to the adoption of new digital tooling, or is adoption purely voluntary?",
        "rationale": "Identifies if change management will face structural resistance or is supported by incentive alignment.",
        "tags": ["Risk Modifier"],
        "input_type": "single_select",
        "options": ["Strongly aligned; adoption is mandatory and tied to KPIs", "Somewhat aligned, but loosely enforced", "Poorly aligned; adoption is voluntary", "We have no strategy for driving field adoption"],
    },
    {
        "id": "Q4.2", "section": "S4",
        "text": "Does your data footprint require GDPR, HIPAA, or strict localized data residency compliance?",
        "rationale": "Data residency, privacy laws, and compliance audits significantly inflate the cost of the MLOps foundation.",
        "tags": ["Compliance Cost"],
        "input_type": "single_select",
        "options": ["Yes, strict multiregional compliance required", "Moderate compliance requirements", "Minimal regulatory constraints", "Unknown"],
    },
    {
        "id": "Q4.3", "section": "S4",
        "text": "Who is actually going to build this AI for you?",
        "rationale": "SI dependencies inflate total program costs by 30-40% compared to internal builds.",
        "tags": ["Programme Cost"],
        "input_type": "single_select",
        "options": ["External Systems Integrator (SI)", "Hybrid: Internal team with SI support", "Fully internal engineering team"],
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def get_section(section_id: str) -> dict | None:
    for s in SECTIONS:
        if s["id"] == section_id:
            return s
    return None

def get_questions_for_section(section_id: str) -> list[dict]:
    return [q for q in QUESTIONS if q["section"] == section_id]
