"""
llm/openai_client.py

OpenAI GPT integration for the AI Investment Advisory Platform.
Generates an executive decision payload matching Palantir/Databricks/PwC standards.
"""

import os
import json
from dotenv import load_dotenv
from config.peer_corpus import PEER_INTELLIGENCE
from config.questions import QUESTIONS

load_dotenv()

SYSTEM_PROMPT = """You are a senior AI strategy partner at a top-tier management consulting firm (like PwC, McKinsey, or BCG).
Your task is to analyze a client's discovery inputs and generate a deeply detailed, highly structured JSON payload to drive an interactive Executive Decision Platform.

You MUST output ONLY a raw JSON object with the exact schema below:

{
  "maturity_index": {
    "score": 45,
    "classification": "Laggard | Emerging | Strategic | Leader",
    "summary": "1-sentence summary of their maturity."
  },
  "executive_decision": {
    "action": "PHASED APPROVAL | DELAY | REJECT",
    "initial_investment": "USD 30M",
    "milestone": "Month 12: Data audit completion",
    "next_steps": "Release Phase 2 funding",
    "confidence_score": 85,
    "conditions": ["Condition 1", "Condition 2"]
  },
  "executive_summary": "Provide a HIGHLY PROFESSIONAL, Board-ready Strategic Investment Thesis using polished Markdown formatting. Do not use generic hyphenated bullets. Instead, write a compelling, synthesized opening paragraph establishing the investment logic and baseline constraints, followed by a deeply quantified breakdown of the Tranches (Phases) and tollgates (Gates). Use rich formatting (e.g., bolding key metrics). Adopt the sophisticated, authoritative tone of a Senior Partner addressing a Fortune 500 Board. Never use the word 'Executive' or 'Summary' in your text. CRITICAL: NEVER use the '$' dollar sign character, as it breaks the UI rendering engine. Use 'USD' instead.",
  "interactive_benchmarks": [
    {
      "peer": "Dynamic Competitor Name", 
      "initiative": "AI Initiative", 
      "outcome": "Specific outcome",
      "similarity_score": 90,
      "relevance_score": 85,
      "transferability_score": 70,
      "details": "2 sentences on why this benchmark is relevant and transferable."
    }
  ],
  "five_gates": {
    "business_case": {
      "score": 85, "status": "GREEN", 
      "breakdown": {"ROI Potential": 90, "Strategic Alignment": 80},
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
    "phase1": [{"initiative": "Init 1", "owner": "CTO", "value_pool": "$5M", "dependencies": "None", "milestones": "Go-live M3"}],
    "phase2": [{"initiative": "Init 1", "owner": "CFO", "value_pool": "$15M", "dependencies": "Data Lake", "milestones": "MVP M9"}],
    "phase3": [{"initiative": "Init 1", "owner": "CMO", "value_pool": "$20M", "dependencies": "Full adoption", "milestones": "Rollout M18"}]
  },
  "success_metrics": [
    {"kpi": "Metric Name", "baseline": "Current", "target": "Target", "method": "Measurement method"}
  ]
}

Rules:
- Generate 3 benchmarks, 3-4 risks, and 3-4 success metrics.
- BCG Capital Allocation Framework: Do NOT use a single "APPROVE" or "REJECT". Instead, recommend a phased gate approach (e.g., "APPROVE Phase 1 with $X budget; evaluate at Gate 2 based on data audit completion; if Gate 2 passes, release Phase 2 budget"). Differentiate evaluation criteria based on investment type (efficiency vs. strategic optionality).
- Base everything directly on the user's Q&A.
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
            temperature=0.2,
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

        user_message = f"""Client context for the investment thesis:

Company: {company_name}
Budget: ${budget_usd_m:.0f}M
Primary Goals: {', '.join(primary_goals)}

--- CLIENT DISCOVERY ANSWERS ---
{qa_lines}

--- PEER BENCHMARKS ---
{peer_context}
Use the above generic benchmarks ONLY as inspiration. You MUST generate 3 highly specific, dynamic, and real-world competitor benchmarks that directly relate to the selected client company, their exact tech stack, and their exact primary goal. Do not blindly copy the static benchmarks above.

Please ensure your executive_summary and five_gates (especially Business Case and Feasibility) explicitly reference the client's provided baseline metrics, target uplifts, interdependencies, and data accuracy as provided in the Q&A.

Generate the required JSON payload for this client."""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            max_tokens=4096,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content.strip()
        payload = json.loads(content)
        
        # Fallbacks for missing keys
        payload.setdefault("maturity_index", {"score": 50, "classification": "Emerging", "summary": "Average maturity."})
        payload.setdefault("executive_decision", {
            "action": "PHASED APPROVAL",
            "initial_investment": "USD 10M",
            "milestone": "Month 6: Initial ROI",
            "next_steps": "Evaluate Gate 2",
            "confidence_score": 70, 
            "conditions": []
        })
        payload.setdefault("executive_summary", "<p>Failed to parse summary.</p>")
        payload.setdefault("interactive_benchmarks", [])
        payload.setdefault("five_gates", _fallback_gates())
        payload.setdefault("risk_register", [])
        payload.setdefault("capability_roadmap", {"phase1": [], "phase2": [], "phase3": []})
        payload.setdefault("success_metrics", [])
        
        return payload, True

    except Exception as e:
        print(f"LLM Error: {e}")
        return _static_fallback_payload(budget_usd_m, primary_goals, plan), False


def _build_peer_context(primary_goal: str) -> str:
    png = PEER_INTELLIGENCE["PnG"]
    unilever = PEER_INTELLIGENCE["Unilever"]
    nestle = PEER_INTELLIGENCE["Nestle"]
    coca_cola = PEER_INTELLIGENCE["CocaCola"]
    reckitt = PEER_INTELLIGENCE["Reckitt"]

    lines = [
        f"- P&G: {png['headline_stat']} ({png['margin_uplift']})",
        f"- Unilever: {unilever['headline_stat']} ({unilever['margin_uplift']})",
        f"- Nestle: {nestle['headline_stat']} — payback {nestle['payback_months']} months",
        f"- Coca-Cola: {coca_cola['headline_stat']}",
        f"- Reckitt: {reckitt['headline_stat']}",
    ]
    return "\n".join(lines)

def _fallback_gates():
    return {
        "business_case": {"score": 80, "status": "GREEN", "breakdown": {}, "drivers": [], "recommendations": []},
        "feasibility": {"score": 50, "status": "AMBER", "breakdown": {}, "drivers": [], "recommendations": []},
        "prioritization": {"score": 75, "status": "GREEN", "breakdown": {}, "drivers": [], "recommendations": []},
        "governance": {"score": 40, "status": "RED", "breakdown": {}, "drivers": [], "recommendations": []},
        "validation": {"score": 60, "status": "AMBER", "breakdown": {}, "drivers": [], "recommendations": []}
    }

def _static_fallback_payload(budget_usd_m: float, primary_goals: list, plan: dict) -> dict:
    return {
        "maturity_index": {"score": 40, "classification": "Laggard", "summary": "Needs fundamental data upgrades."},
        "executive_decision": {"phased_recommendation": "APPROVE Phase 1 limited data pilot; evaluate at Gate 2 (Month 3) before full allocation.", "confidence_score": 60, "conditions": ["Upgrade ERP", "Hire CDO"]},
        "executive_summary": "<p>Fallback static summary.</p>",
        "interactive_benchmarks": [{"peer": "P&G", "initiative": "Auto SC", "outcome": "$1.5B", "similarity_score": 80, "relevance_score": 90, "transferability_score": 50, "details": "Static details"}],
        "five_gates": _fallback_gates(),
        "risk_register": [{"risk": "Data", "prob": "HIGH", "impact": "HIGH", "mitigation": "Fix data"}],
        "capability_roadmap": {"phase1": [{"initiative": "Data Lake", "owner": "CIO", "value_pool": "$0", "dependencies": "None", "milestones": "M6"}], "phase2": [], "phase3": []},
        "success_metrics": [{"kpi": "Margin", "baseline": "20%", "target": "25%", "method": "Quarterly"}]
    }
