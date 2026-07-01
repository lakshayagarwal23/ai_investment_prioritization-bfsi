"""
llm/openai_client.py

OpenAI GPT integration for the AI Investment Advisory Platform.
Generates an executive decision payload matching Palantir/Databricks/PwC standards.
"""

import os
import json
from dotenv import load_dotenv
import pydantic
from pydantic import BaseModel
from config.peer_corpus import PEER_INTELLIGENCE
from config.questions import QUESTIONS

class MaturityIndex(BaseModel):
    score: int
    classification: str
    summary: str

class ExecutiveDecision(BaseModel):
    action: str
    readiness_tier: str
    top_initiatives: list[str]
    primary_risk: str
    milestone: str
    next_steps: str
    conditions: list[str]

class Benchmark(BaseModel):
    peer: str
    initiative: str
    outcome: str
    similarity_score: int
    relevance_score: int
    transferability_score: int
    details: str

class PhaseDetails(BaseModel):
    score: int
    status: str
    breakdown: dict
    drivers: list[str]
    recommendations: list[str]

class FivePhases(BaseModel):
    business_case: PhaseDetails
    feasibility: PhaseDetails
    prioritization: PhaseDetails
    governance: PhaseDetails
    validation: PhaseDetails

class Risk(BaseModel):
    risk: str
    prob: str
    impact: str
    mitigation: str

class CapabilityRoadmap(BaseModel):
    phase1: list[dict]
    phase2: list[dict]
    phase3: list[dict]

class SuccessMetric(BaseModel):
    kpi: str
    baseline: str
    target: str
    method: str

class ExecutiveSummaryPayload(BaseModel):
    maturity_index: MaturityIndex
    executive_decision: ExecutiveDecision
    executive_summary: str
    interactive_benchmarks: list[Benchmark]
    five_phases: FivePhases
    risk_register: list[Risk]
    capability_roadmap: CapabilityRoadmap
    success_metrics: list[SuccessMetric]

load_dotenv()

import re

SYSTEM_PROMPT = """You are a senior AI strategy partner at a top-tier management consulting firm (like PwC, McKinsey, or BCG).
Your task is to analyze a client's discovery inputs and generate a deeply detailed, highly structured JSON payload to drive an interactive Executive Decision Platform.

This is a PRIORITISATION AND READINESS DIAGNOSTIC, not a financial forecast. You MUST NOT state, estimate,
or imply any ROI %, NPV, return percentage, or payback period anywhere. Do not invent any projected dollar
value figures for the client. Speak in terms of sequencing, readiness, peer evidence, and execution risk.

You MUST output ONLY a raw JSON object with the exact schema below:

{
  "maturity_index": {
    "score": "[Integer 0-100 — this will be overridden by the deterministic engine; provide a best-effort value]",
    "classification": "Laggard | Emerging | Strategic | Leader",
    "summary": "1-sentence summary of their readiness position."
  },
  "executive_decision": {
    "action": "Choose ADDRESS FOUNDATIONS FIRST, PHASED START — MANAGE EXECUTION RISK, or PHASED START RECOMMENDED based on THIS client's readiness — do not default to one.",
    "readiness_tier": "<Laggard | Emerging | Strategic | Leader based on answers>",
    "top_initiatives": ["<top ranked use case>", "<second ranked use case>"],
    "primary_risk": "<a full, verbose sentence explaining the single most important execution risk for this client, detailing WHY it is a risk>",
    "milestone": "<the specific Phase 1 Deliverable tied to this client's single weakest area>",
    "next_steps": "<the concrete next action for this client>",
    "conditions": ["<condition specific to this client>", "<another specific condition>"]
  },
  "executive_summary": "Provide a HIGHLY PROFESSIONAL, Board-ready Strategic AI Investment Prioritisation using polished Markdown. CRITICAL: Format the prioritisation in clean, structured, and highly readable bullet points with bold headers (e.g., **Strategic Objective:**, **Execution Risk:**). DO NOT write long cluttered paragraphs. Adopt the sophisticated, authoritative tone of a Senior Partner addressing a Fortune 500 Board. Never use the word 'Executive' or 'Summary' in your text. CRITICAL: NEVER use the '$' dollar sign character, as it breaks the UI rendering engine. Use 'USD' instead. CRITICAL: Do NOT include any ROI, NPV, payback period, or projected return figures.",
  "interactive_benchmarks": [
    {
      "peer": "Dynamic Competitor Name",
      "initiative": "AI Initiative",
      "outcome": "Specific outcome (qualitative or peer-disclosed — no invented numbers)",
      "similarity_score": 90,
      "relevance_score": 85,
      "transferability_score": 70,
      "details": "2 sentences on why this benchmark is relevant and transferable."
    }
  ],
  "five_phases": {
    "business_case": {
      "score": 85, "status": "GREEN",
      "breakdown": {"Strategic Alignment": 90, "Sequencing Logic": 80},
      "drivers": ["Driver 1", "Driver 2"], "recommendations": ["Rec 1", "Rec 2"]
    },
    "feasibility": {
      "score": 60, "status": "AMBER",
      "breakdown": {"Data Cleanliness": 50, "Integration Ease": 70},
      "drivers": ["Driver 1", "Driver 2"], "recommendations": ["Rec 1", "Rec 2"]
    },
    "prioritization": {
      "score": 75, "status": "GREEN",
      "breakdown": {"Speed to Value": 80, "Resource Availability": 70},
      "drivers": ["Driver 1", "Driver 2"], "recommendations": ["Rec 1", "Rec 2"]
    },
    "governance": {
      "score": 40, "status": "RED",
      "breakdown": {"Compliance": 40, "Risk Controls": 40},
      "drivers": ["Driver 1", "Driver 2"], "recommendations": ["Rec 1", "Rec 2"]
    },
    "validation": {
      "score": 65, "status": "AMBER",
      "breakdown": {"User Adoption": 60, "Feedback Loop": 70},
      "drivers": ["Driver 1", "Driver 2"], "recommendations": ["Rec 1", "Rec 2"]
    }
  },
  "risk_register": [
    {"risk": "Specific Risk", "prob": "HIGH|MED|LOW", "impact": "HIGH|MED|LOW", "mitigation": "Mitigation strategy"}
  ],
  "capability_roadmap": {
    "phase1": [{"initiative": "Init 1", "owner": "CTO", "value_pool": "Enablement", "dependencies": "None", "milestones": "Go-live M3"}],
    "phase2": [{"initiative": "Init 1", "owner": "CFO", "value_pool": "Scale", "dependencies": "Data Lake", "milestones": "MVP M9"}],
    "phase3": [{"initiative": "Init 1", "owner": "CMO", "value_pool": "Expand", "dependencies": "Full adoption", "milestones": "Rollout M18"}]
  },
  "success_metrics": [
    {"kpi": "Tooling adoption rate", "baseline": "Current MAU %", "target": "Field-KPI-linked", "method": "MAU / adoption telemetry"},
    {"kpi": "Data readiness score", "baseline": "Current state", "target": "Phase 1 Validation threshold", "method": "Data audit at Phase 1"},
    {"kpi": "Model accuracy / error rate", "baseline": "Baseline forecast error", "target": "Peer benchmark", "method": "Weekly model evaluation"},
    {"kpi": "Deliverability", "baseline": "Current feasibility %", "target": "Target feasibility %", "method": "Quarterly readiness review"}
  ]
}

Rules:
- Generate 3 benchmarks, 3-4 risks, and 4 success metrics.
- BCG Capital Allocation Framework: Do NOT use a single 'APPROVE' or 'REJECT'. Recommend a phased milestone approach.
- Base everything directly on the user's Q&A.
- NEVER invent a peer statistic. Use only qualitative outcomes or outcomes the client supplied.
- success_metrics must be leading indicators (adoption, data-readiness, deliverability) — NEVER financial targets.
"""

INTEL_SYSTEM_PROMPT = """You are an expert corporate intelligence AI for a top-tier management consultancy.
The user will provide a company name. You must generate a highly accurate, tailored JSON profile of that company to pre-configure an AI transformation diagnostic questionnaire.

You MUST output ONLY a raw JSON object with the exact schema below:

{
  "geographies": [
    "Primary Region 1 (e.g., North America)", 
    "Primary Region 2", 
    "Primary Region 3"
  ],
  "tailored_options": {
    "Q2.1": ["Tailored option 1 (e.g., Over 10,000 SKUs)", "Option 2", "Option 3"],
    "Q2.2": ["Tailored option 1 (e.g., Over 50 Global DCs)", "Option 2", "Option 3"],
    "Q3.1": ["Tailored option 1 (e.g., Centralized SAP S/4HANA)", "Option 2", "Option 3"]
  }
}

Rules:
1. Provide 3-6 specific "geographies" where the company actually operates or has major headquarters (e.g., if HUL, list "India", "South Asia", etc.).
2. For "tailored_options", provide custom dropdown options for questions:
   - Q2.1 (Number of SKUs)
   - Q2.2 (Number of Warehouses/DCs)
   - Q3.1 (ERP Architecture)
   Make the options highly specific to the company's publicly known scale and tech stack. Include 3-4 options per question.
"""

def generate_company_intelligence(company_name: str) -> dict:
    if not company_name or company_name == "— Select your company —":
        return _fallback_intel()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.strip() == "your_openai_api_key_here":
        return _fallback_intel(company_name)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": INTEL_SYSTEM_PROMPT},
                {"role": "user", "content": f"Company: {company_name}"},
            ],
            temperature=0,  # determinism (D5)
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content.strip()
        payload = json.loads(content)
        
        # Ensure fallbacks exist in case the LLM misses a key
        payload.setdefault("geographies", ["North America", "Europe", "APAC", "Global"])
        payload.setdefault("tailored_options", {})
        
        return payload

    except Exception as e:
        print(f"Intel LLM Error: {e}")
        return _fallback_intel(company_name)

def _fallback_intel(company_name: str = "") -> dict:
    return {
        "geographies": [
            "India & South Asia", "North America", "Europe", "APAC",
            "Middle East & Africa", "Latin America", "Global / Multi-Region"
        ],
        "tailored_options": {}
    }


def generate_executive_summary(
    company_name: str,
    plan: dict,
    answers: dict[str, str],
) -> tuple[dict, bool]:
    budget_usd_m: float = plan.get("budget_usd_m", 100.0)
    primary_goals: list = plan.get("primary_goals", ["Revenue Growth"])

    if "strict" in answers.get("Q4.2", "").lower():
        return _static_fallback_payload(budget_usd_m, primary_goals, plan, mode_override="deterministic_by_policy"), False

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.strip() == "your_openai_api_key_here":
        return _static_fallback_payload(budget_usd_m, primary_goals, plan), False

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        main_goal = primary_goals[0] if primary_goals else "Revenue Growth"
        peer_context = _build_peer_context(main_goal)

        qa_lines = ""
        for q in QUESTIONS:
            q_id = q["id"]
            if q_id in answers and answers[q_id]:
                qa_lines += f"Q: {q['text']}\nA: {answers[q_id]}\n\n"

        phase1_m = round(plan.get("foundation_usd", 0) / 1e6, 1)
        user_message = f"""Client context for the prioritisation diagnostic:

Company: {company_name}
Budget: USD {budget_usd_m:.0f}M
Phase 1 Foundation Allocation: USD {phase1_m}M  ← USE THIS EXACT FIGURE FOR PHASE 1 IN ALL PROSE. DO NOT RECALCULATE.
Primary Goals: {', '.join(primary_goals)}
Readiness / Maturity Tier: {plan.get('maturity_class', 'Emerging')}
Top-Ranked Use Cases: {', '.join(uc['name'] for uc in plan.get('scoring_matrix', [])[:2])}

--- CLIENT DISCOVERY ANSWERS ---
{qa_lines}

--- PEER BENCHMARKS ---
{peer_context}
Use the above generic benchmarks ONLY as inspiration. You MUST generate 3 highly specific, dynamic benchmarks
that directly relate to the selected client company, their exact tech stack, and their exact primary goal.
Do not blindly copy the static benchmarks above. Do NOT invent peer statistics — use only qualitative
outcomes or figures the client supplied.

CRITICAL INSTRUCTION ON METRICS:
This is a prioritisation and readiness diagnostic, NOT a financial forecast.
You MUST NOT state, estimate, or imply any ROI, NPV, return percentage, or payback period anywhere.
Do not invent projected dollar value figures for the client.
Speak in terms of sequencing, readiness, peer evidence, and execution risk.

Please ensure your executive_summary and five_phases (especially Business Case and Feasibility) explicitly
reference the client's data readiness, sponsor strength, adoption risk, and delivery model as provided
in the Q&A.

Generate the required JSON payload for this client."""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0,   # determinism (D5)
            max_tokens=4096,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content.strip()
        try:
            payload = json.loads(content)
            ExecutiveSummaryPayload(**payload)
            
            # FIX 3: Post-generation validation for drift (objectives and posture)
            llm_action = payload.get("executive_decision", {}).get("action", "")
            engine_posture = plan.get("posture")
            if engine_posture and llm_action and llm_action.upper() != engine_posture.upper():
                print(f"Validation Error: LLM drifted on posture (expected {engine_posture}, got {llm_action})")
                return _static_fallback_payload(budget_usd_m, primary_goals, plan, mode_override="deterministic_by_fallback"), False
                
            # Check for hallucinated objectives (if none of the selected goals are found in the summary)
            summary_lower = payload.get("executive_summary", "").lower()
            if primary_goals and not any(g.lower() in summary_lower for g in primary_goals):
                print("Validation Error: LLM drifted on objectives (none of the primary goals found in summary)")
                return _static_fallback_payload(budget_usd_m, primary_goals, plan, mode_override="deterministic_by_fallback"), False

        except (json.JSONDecodeError, pydantic.ValidationError) as e:
            print(f"Validation Error: {e}")
            return _static_fallback_payload(budget_usd_m, primary_goals, plan, mode_override="deterministic_by_fallback"), False
        
        # D5: strip financial sentences even if the model disobeys.
        if "executive_summary" in payload:
            payload["executive_summary"] = _strip_financial_sentences(
                payload["executive_summary"]
            )

        # Ground the headline decision in the deterministic engine (R1).
        payload["executive_decision"] = _ground_decision(payload.get("executive_decision", {}), plan)

        # Override maturity score + tier with the deterministic engine value (R2).
        maturity_score = plan.get("maturity_score", payload["maturity_index"].get("score", 50))
        maturity_class = plan.get("maturity_class", payload["maturity_index"].get("classification", "Emerging"))
        payload["maturity_index"]["score"] = maturity_score
        payload["maturity_index"]["classification"] = maturity_class
        payload["maturity_index"]["summary"] = (
            f"{company_name} is classified as a {maturity_class} AI adopter based on "
            f"its data estate, ERP topology, and execution-risk profile "
            f"(score: {maturity_score}/100)."
        )

        return payload, True

    except Exception as e:
        print(f"LLM Error: {e}")
        return _static_fallback_payload(budget_usd_m, primary_goals, plan, mode_override="deterministic_by_fallback"), False


def _build_peer_context(primary_goal: str) -> str:
    png = PEER_INTELLIGENCE["PnG"]
    unilever = PEER_INTELLIGENCE["Unilever"]
    nestle = PEER_INTELLIGENCE["Nestle"]
    coca_cola = PEER_INTELLIGENCE["CocaCola"]
    reckitt = PEER_INTELLIGENCE["Reckitt"]

    lines = [
        f"- P&G: {png['headline_stat']} ({png['margin_uplift']})",
        f"- Unilever: {unilever['headline_stat']} ({unilever['margin_uplift']})",
        f"- Nestle: {nestle['headline_stat']}",
        f"- Coca-Cola: {coca_cola['headline_stat']}",
        f"- Reckitt: {reckitt['headline_stat']}",
    ]
    return "\n".join(lines)


_FIN = re.compile(
    r'(?:\bROI\b|\bNPV\b|payback|return on investment|'
    r'\d+(?:\.\d+)?\s*%\s*(?:roi|return)|payback\s+of\s+\d+)',
    re.I,
)


def _strip_financial_sentences(prose: str) -> str:
    """Remove any sentence that contains a financial-projection term (D5 guard).
    Preserves Markdown structure by processing line-by-line.
    """
    if not prose:
        return prose
        
    lines = prose.split('\n')
    new_lines = []
    total_sentences = 0
    kept_sentences = 0
    
    for line in lines:
        if not line.strip():
            new_lines.append(line)
            continue
            
        sentences = re.split(r'(?<=[.!?])\s+', line)
        kept = []
        for s in sentences:
            if s.strip():
                total_sentences += 1
                if not _FIN.search(s):
                    kept.append(s)
                    kept_sentences += 1
                    
        if kept:
            new_lines.append(" ".join(kept))

    if total_sentences > 0 and kept_sentences < max(1, total_sentences * 0.5):
        # The model's output was mostly financial projections — fall back to template.
        return (
            "**Strategic Objective:** This diagnostic prioritises where to invest first and how to stage the spend, against peer evidence.\n\n"
            "**Return Projections:** Projected returns depend on execution specifics beyond a diagnostic scope."
        )
        
    return "\n".join(new_lines)


def _ground_decision(dec: dict, plan: dict) -> dict:
    """Force the headline recommendation to come from deterministic engine signals.

    Posture tiers (R1):
    - ADDRESS FOUNDATIONS FIRST: complexity >= 0.30 or data_eng_line_item present
    - PHASED START — MANAGE EXECUTION RISK: risk >= 0.30
    - PHASED START RECOMMENDED: clean estate, manageable risk
    """
    data_badness = plan.get("data_badness", 0.0)
    complexity   = plan.get("complexity_score", 0.0)
    risk         = plan.get("risk_score", 0.0)
    maturity     = plan.get("maturity_score", 50)
    matrix       = plan.get("scoring_matrix", [])
    drivers      = plan.get("derivation", {})

    if plan.get("posture"):
        action = plan.get("posture")
    elif data_badness >= 0.5 or complexity >= 0.55:
        action = "ADDRESS FOUNDATIONS FIRST"
    elif risk >= 0.35:
        action = "PHASED START — MANAGE EXECUTION RISK"
    elif maturity >= 65:
        action = "INVEST NOW — PHASED"
    else:
        action = "PHASED START RECOMMENDED"

    dec = dict(dec or {})
    dec["action"]          = action
    dec["readiness_tier"]  = plan.get("maturity_class", "Emerging")
    dec["top_initiatives"] = [uc["name"] for uc in matrix[:2]]
    risk_list = (drivers.get("risk_drivers") or drivers.get("complexity_drivers") or ["No major flags identified"])
    dec["primary_risk"]    = risk_list[0] if risk_list else "No major flags identified"
    # Force posture-appropriate milestone (override LLM output)
    if "INVEST NOW" in action:
        dec["milestone"] = "Phase 1 Delivery: data platform build & first AI pilot deployment"
    else:
        dec["milestone"] = "Phase 1 Validation: data-readiness & baseline review"
    # Force posture-appropriate next_steps (override LLM output)
    if action == "ADDRESS FOUNDATIONS FIRST":
        dec["next_steps"] = ("Begin with the top-ranked quick wins; release further "
                            "funding only on Phase 1 Validation pass.")
    else:
        dec["next_steps"] = ("Commence Phase 1 foundation build in parallel with "
                            "detailed scoping of the highest-priority AI initiatives.")
    dec.setdefault("conditions", [])
    # Remove all financial keys (Invariant 1)
    for k in ("initial_investment", "roi", "npv", "payback", "confidence_score",
              "payback_label", "expected_roi_pct"):
        dec.pop(k, None)
    return dec



def _fallback_phases():
    return {
        "business_case": {"score": 80, "status": "GREEN", "breakdown": {}, "drivers": [], "recommendations": []},
        "feasibility": {"score": 50, "status": "AMBER", "breakdown": {}, "drivers": [], "recommendations": []},
        "prioritization": {"score": 75, "status": "GREEN", "breakdown": {}, "drivers": [], "recommendations": []},
        "governance": {"score": 40, "status": "RED", "breakdown": {}, "drivers": [], "recommendations": []},
        "validation": {"score": 60, "status": "AMBER", "breakdown": {}, "drivers": [], "recommendations": []}
    }

def _static_fallback_payload(budget_usd_m: float, primary_goals: list, plan: dict, mode_override: str = None) -> dict:
    """Deterministic payload used when no OpenAI key is configured.

    IMPORTANT: this is the path most users hit first (no key set), so it must
    (a) match the exact schema the dashboard reads, and (b) reflect the REAL
    numbers the math engine produced rather than hardcoded placeholders.
    """
    derivation = plan.get("derivation", {})
    value_known = derivation.get("value_known", False)
    # G0.2: no ROI / payback in the fallback summary
    band = plan.get("confidence_band_pct", 40.0)
    # Confidence score is the inverse of the uncertainty band (wider band → less confident).
    confidence_score = int(max(35, round(100 - band)))
    phase1_usd_m = plan.get("foundation_usd", budget_usd_m * 0.30 * 1_000_000) / 1_000_000
    phase1_usd_m = int(phase1_usd_m) if phase1_usd_m.is_integer() else round(phase1_usd_m, 1)
    goal_label = plan.get("primary_goal_label", ", ".join(primary_goals))

    # Risk/complexity drivers become honest, plan-derived conditions.
    conditions = []
    if derivation.get("complexity_drivers"):
        conditions.append("Remediate data/ERP debt before scaling (see foundation allocation)")
    if derivation.get("risk_drivers"):
        conditions.append("Secure a single executive sponsor and tie adoption to field KPIs")
    if not value_known:
        conditions.append("Supply baseline metrics (Q1.2 / Q2.3) to enable full scoring")
    if not conditions:
        conditions = ["Confirm baselines at Phase 1 Validation", "Stand up MLOps foundation in Phase 1"]

    # G0.2: no ROI / payback in the fallback summary
    summary = (
        f"**Strategic Objective:** Recommends a phased capital allocation of USD {budget_usd_m:.0f}M toward {goal_label}. The prioritisation matrix identifies "
        f"the highest-readiness, highest-impact use cases for your data estate and objectives.\n\n"
        f"**Capital Sequencing:** Staged against strict milestones. Phase 1 (USD {phase1_usd_m}M) funds the "
        f"data/MLOps foundation and the top-ranked quick wins; subsequent phases unlock only "
        f"on Phase 1 Validation data-readiness pass.\n\n"
        f"**Execution Posture:** This sequencing is grounded in peer evidence and "
        f"reflects your readiness tier: **{plan.get('maturity_class', 'Emerging')}**.\n\n"
        f"**Return Projections:** This diagnostic deliberately does not project ROI or payback — those depend "
        f"on execution specifics beyond the scope of a readiness assessment."
    )

    # Fix 2 (fallback path): read the engine's own maturity score instead of
    # recomputing with a different formula that gives a different answer.
    maturity_score = plan.get("maturity_score", int(max(20, round(60 - 30 * plan.get("complexity_score", 0.5)))))
    maturity_class = plan.get("maturity_class",
                              "Leader" if maturity_score >= 75 else
                              "Strategic" if maturity_score >= 50 else
                              "Emerging" if maturity_score >= 25 else "Laggard")
    return {
        "maturity_index": {
            "score": maturity_score,
            "classification": maturity_class,
            "summary": (
                f"This company is classified as a {maturity_class} AI adopter "
                f"based on its data estate, ERP topology, and execution-risk profile "
                f"(score: {maturity_score}/100)."
            ),
        },
        "executive_decision": {**_ground_decision({}, plan), **({"mode_override": mode_override} if mode_override else {})},
        "executive_summary": summary,
        "interactive_benchmarks": [
            {"peer": "Procter & Gamble", "initiative": "End-to-end supply chain AI", "outcome": "USD 1.5B savings",
             "similarity_score": 80, "relevance_score": 90, "transferability_score": 55,
             "details": "Demand sensing and supply optimization at global scale; transferable share is conservative for a first programme."},
            {"peer": "Unilever", "initiative": "AI demand sensing", "outcome": "15% inventory reduction",
             "similarity_score": 78, "relevance_score": 85, "transferability_score": 60,
             "details": "Working-capital release via forecasting; directly relevant to the inventory lever in this plan."},
            {"peer": "Nestle", "initiative": "Trade promotion optimization", "outcome": "12-pt NPS uplift",
             "similarity_score": 72, "relevance_score": 80, "transferability_score": 50,
             "details": "Trade-promo AI improves margin and customer outcomes; relevant where promo spend is material."},
        ],
        "five_phases": _fallback_phases(),
        "risk_register": [
            {"risk": "Data quality / fragmentation", "prob": "HIGH", "impact": "HIGH",
             "mitigation": "Front-load data remediation in Phase 1; phase scaling on data-readiness."},
            {"risk": "Low user adoption", "prob": "MED", "impact": "HIGH",
             "mitigation": "Front-load data remediation in Phase 1; phase scaling on data-readiness."},
            {"risk": "Benefit Realization", "prob": "MED", "impact": "MED",
             "mitigation": "Validate each value lever against its baseline at every phase before scaling."},
        ],
        "capability_roadmap": {
            "phase1": [{"initiative": "Data Platform & MLOps Foundation", "owner": "CIO",
                        "value_pool": f"USD {phase1_usd_m}M", "dependencies": "None", "milestones": "Go-live M3"}],
            "phase2": [{"initiative": "Highest-priority value levers", "owner": "CFO",
                        "value_pool": "Phased", "dependencies": "Phase 2 pass", "milestones": "MVP M9"}],
            "phase3": [],
        },
        "success_metrics": [
            {"kpi": "Tooling adoption",    "baseline": "Current %",  "target": "Field-KPI-linked",   "method": "MAU / adoption telemetry"},
            {"kpi": "Data readiness",      "baseline": "Current tier", "target": "Phase 1 Validation pass",      "method": "Data quality scorecard"},
            {"kpi": "Deliverability score", "baseline": "Current %",  "target": "Improve each phase", "method": "Matrix feasibility re-score at each phase"},
        ],
    }
