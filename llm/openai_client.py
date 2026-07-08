"""
llm/openai_client.py — Premium HTML-rich Strategic Investment Memo (Powered by Gemini).
"""
from __future__ import annotations
import os
from google import genai
from google.genai import types

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def generate_executive_summary(company: str, plan: list[dict], answers: dict, sector: str = "Financial Services") -> str:
    # 1. Gather data
    strategic_bets = [p for p in plan if p["quadrant"] == "Strategic Bets"]
    quick_wins     = [p for p in plan if p["quadrant"] == "Quick Wins / Fill-ins"]
    parked         = [p for p in plan if p["quadrant"] == "Park (Data-Blocked)"]
    
    top_levers = [p["name"] for p in strategic_bets[:3]]
    if not top_levers:
        top_levers = [p["name"] for p in plan[:3]]
        
    sbet_html = "".join(
        f'<div class="hz-callout win">'
        f'<div class="hz-callout-title">{p["name"]}</div>'
        f'<div class="hz-callout-desc">'
        f'Why it\'s a bet: High Impact ({p["impact"]}/100) and High Feasibility ({p["feasibility"]}/100).'
        f'</div></div>'
        for p in strategic_bets[:3]
    )
    
    qw_html = "".join(
        f'<div class="hz-callout" style="border-left-color: var(--blue);">'
        f'<div class="hz-callout-title">{p["name"]}</div>'
        f'<div class="hz-callout-desc">'
        f'Why it\'s a quick win: Low friction to implement (Feasibility {p["feasibility"]}/100) yielding immediate value.'
        f'</div></div>'
        for p in quick_wins[:3]
    )
    
    parked_html = "".join(
        f'<div class="hz-callout park">'
        f'<div class="hz-callout-title">{p["name"]}</div>'
        f'<div class="hz-callout-desc">'
        f'Why it\'s parked: High impact, but blocked by data debt (Feasibility {p["feasibility"]}/100). Requires data foundation first.'
        f'</div></div>'
        for p in parked[:3]
    )
    
    # 2. Prompt Gemini for the hero narrative
    if not GEMINI_API_KEY:
        ai_narrative = "<div class='hz-status-breach' style='padding: 12px; margin-bottom: 20px;'><strong>Configuration Error:</strong> GEMINI_API_KEY is missing. Narrative generation is disabled. Please provide a valid API key to enable LLM features.</div>"
    else:
        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = f"""
        You are a tier-1 management consultant (McKinsey/PwC) advising the C-suite of {company}, a firm in the {sector} sector.
        We have just generated an AI Use Case Prioritization Matrix for them. 
        
        The top 'Strategic Bets' are: {', '.join(top_levers)}.
        
        Write a 3-paragraph executive memo explaining WHY a matrix-driven approach is critical for AI transformation, rather than random experimentation. 
        Focus on how we balanced "Business Impact" vs "Feasibility" (data readiness, legacy constraints) to place these specific use cases in the 'Strategic Bets' quadrant. 
        
        CRITICAL INSTRUCTIONS:
        - Base all claims strictly on the provided Strategic Bets and the concepts of technical debt, legacy architecture, and data governance.
        - Do NOT hallucinate specific technologies or generic industry buzzwords (e.g., do NOT mention UPI, Account Aggregator, or MAUDE unless they are explicitly in the provided Strategic Bets).
        - Do NOT include any financial calculations, ROIs, NPVs, or dollar amounts.
        - Tone: Professional, strategic, visionary, C-suite ready.
        - Format: Output exactly 3 HTML paragraphs (<p class="hz-p">). Do not include the <h2> title or markdown code blocks.
        """
        
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            ai_narrative = response.text.replace("```html", "").replace("```", "")
        except Exception as e:
            print(f"Gemini API Error: {e}")
            ai_narrative = f'''<p class="hz-p">
            AI transformation fails when firms chase hype rather than feasibility. For <strong>{company}</strong>, success requires a disciplined, matrix-driven approach that plots use cases against actual data readiness and business impact.
            </p>'''

    # 3. Build the Memo HTML
    memo = f"""
<div class="hz-report-h2">I. The AI Prioritization Strategy (Synthesized for {company})</div>

{ai_narrative}

<div class="hz-report-h2" style="margin-top: var(--sp-8);">II. Matrix Deep-Dive: Strategic Bets</div>
<p class="hz-p" style="margin-bottom: var(--sp-4);">
    These use cases scored high in both Business Impact and Feasibility. They are your primary engines for transformation and should receive the bulk of immediate capital allocation.
</p>
{sbet_html if sbet_html else "<p class='hz-p'>No strategic bets identified. All high-impact initiatives are currently blocked by legacy debt.</p>"}

<div class="hz-report-h2" style="margin-top: var(--sp-8);">III. Matrix Deep-Dive: Quick Wins</div>
<p class="hz-p" style="margin-bottom: var(--sp-4);">
    These use cases have lower overall transformational impact, but extremely high feasibility. They are fast to deploy and critical for building momentum and proving early ROI.
</p>
{qw_html if qw_html else "<p class='hz-p'>No quick wins identified.</p>"}

<div class="hz-report-h2" style="margin-top: var(--sp-8);">IV. Matrix Deep-Dive: Parked (Data-Blocked)</div>
<p class="hz-p" style="margin-bottom: var(--sp-4);">
    These use cases have massive potential impact, but their feasibility is too low due to current data silos, legacy architecture, or poor data governance. They are parked until the data foundation is modernized.
</p>
{parked_html if parked_html else "<p class='hz-p'>No parked initiatives. Your data foundation supports all evaluated use cases.</p>"}

<hr style="border:none;border-top:1px solid var(--g200);margin: 32px 0 16px;">
<p style="font-size:11px;color:var(--g500);line-height:1.6;">
    <em>This matrix was computed dynamically based on the firm's specific architectural, operational, and governance constraints. Feasibility is heavily penalized by data silos, monolithic ERPs, and poor API gateways.</em>
</p>
"""
    return memo

def generate_company_intelligence(company: str) -> dict:
    return {"summary": f"Diagnostic for {company}.", "geographies": ["Global"], "tailored_options": {}}
