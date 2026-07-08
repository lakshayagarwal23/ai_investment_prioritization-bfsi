"""
ui/sidebar.py — Premium BFSI intake wizard with card-based HTML layout.
"""
from __future__ import annotations
import streamlit as st
import time
import html
from config.questions import (
    SECTIONS, QUESTIONS, get_questions_for_section, OTHER_OPTION, OBJECTIVE_INPUTS
)
from llm.search_client import extract_company_data
from llm.openai_client import generate_executive_summary, generate_company_intelligence

BFSI_COMPANIES = [
    "— Select your firm —",
    "Aditya Birla Sun Life AMC",
    "Axis Bank",
    "Bajaj Finance",
    "Bandhan Bank",
    "Bank of Baroda",
    "Canara Bank",
    "Cholamandalam Investment and Finance",
    "DSP Mutual Fund",
    "Edelweiss Financial Services",
    "HDFC AMC",
    "HDFC Bank",
    "HDFC Life Insurance",
    "ICICI Bank",
    "ICICI Lombard General Insurance",
    "ICICI Prudential AMC",
    "ICICI Prudential Life Insurance",
    "IDFC First Bank",
    "IndusInd Bank",
    "Kotak Mahindra Bank",
    "Kotak Mahindra AMC",
    "Kotak Life Insurance",
    "L&T Finance Holdings",
    "LIC (Life Insurance Corporation of India)",
    "Mahindra Manulife Mutual Fund",
    "Max Financial Services",
    "Max Life Insurance",
    "Muthoot Finance",
    "Nippon India Mutual Fund",
    "PNB (Punjab National Bank)",
    "SBI (State Bank of India)",
    "SBI Life Insurance",
    "SBI Mutual Fund",
    "Shriram Finance",
    "Tata AIA Life Insurance",
    "Tata Mutual Fund",
    "UTI AMC",
    "Yes Bank",
    "Other / Confidential",
]

STEPPER_LABELS = ["COMPANY"] + [s["nav_label"] for s in SECTIONS] + ["INVESTMENT"]

_SECTION_DESCS = {
    "S1": ("INFRASTRUCTURE", "Technology & Data Infrastructure",
           "Your data architecture and system health determine the ceiling of every AI lever. Be precise — this drives the Legacy Deprecation Score."),
    "S2": ("FRONT OFFICE", "Research, Distribution & Execution",
           "How efficiently does your front office operate today? These inputs calibrate the Research, Execution, and Distribution levers."),
    "S3": ("MIDDLE / BACK OFFICE", "Reconciliation, NAV & Post-Trade",
           "Post-trade operations are the fastest AI payback in asset management. Your STP rate is the single most important number here."),
    "S4": ("RISK & COMPLIANCE", "Compliance, KYC/AML & Onboarding",
           "Regulatory friction and onboarding latency are a silent tax on AUM ramp. Quantify them so we can price the opportunity."),
    "S5": ("LEGACY DIAGNOSTIC", "Legacy Systems & Governance Readiness",
           "Every kill/modernize/hold decision begins here. Five governance dimensions determine whether a rebuild is safe to execute."),
}

def init_session_state() -> None:
    defaults = {
        "app_phase": 0, "wizard_page": 0,
        "company_name": "", "budget_usd_m": 100.0,
        "primary_goals": ["Margin Expansion (Cost)"],
        "discovery_answers": {},
        "thesis_generated": False, "thesis_plan": None, "thesis_summary": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def render_sidebar_branding() -> None:
    phase = st.session_state.app_phase
    with st.sidebar:
        st.html("""
        <div class="aia-sidebar-brand">
          <div class="aia-sidebar-brand-title">BFSI Investment Prioritisation</div>
          <div class="aia-sidebar-brand-sub">AI-powered diagnostic for Life Insurance & Mutual Funds</div>
        </div>
        """)
        if phase >= 2:
            if st.button("← Restart Analysis", use_container_width=True):
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.rerun()

def _stepper(current: int) -> None:
    parts = []
    for i, label in enumerate(STEPPER_LABELS):
        cls = "active" if i == current else ("completed" if i < current else "")
        parts.append(f'<div class="aia-step {cls}"><div class="aia-step-circle">{"✓" if cls=="completed" else i+1}</div><div class="aia-step-label">{label}</div></div>')
        if i < len(STEPPER_LABELS) - 1:
            lc = "completed" if i < current else ""
            parts.append(f'<div class="aia-step-line {lc}"></div>')
    progress_pct = int(current / (len(STEPPER_LABELS) - 1) * 100)
    st.html(f"""
    <div class="aia-stepper-container">{''.join(parts)}</div>
    <div class="bfsi-progress-bar"><div class="bfsi-progress-fill" style="width:{progress_pct}%"></div></div>
    """)

def render_intake_wizard() -> None:
    page = st.session_state.wizard_page
    _stepper(page)
    if page == 0:
        _page_company()
    elif 1 <= page <= len(SECTIONS):
        _page_section(page - 1)
    else:
        _page_investment()

# ── Page 0: Company ────────────────────────────────────────────────────────

def _page_company() -> None:
    st.html("""
    <div class="bfsi-section-banner">
        <div class="bfsi-section-banner-eyebrow">STEP 1 OF 7 · FIRM PROFILE</div>
        <div class="bfsi-section-banner-title">Who are we diagnosing?</div>
        <div class="bfsi-section-banner-desc">
            Select your firm to pre-load benchmark peer intelligence, or enter custom details.
            All data remains confidential and is used solely to calibrate the diagnostic engine.
        </div>
    </div>
    """)

    if st.session_state.company_name:
        safe_company = html.escape(st.session_state.company_name)
        st.html(f"""<div class="bfsi-q-card">
            <div class="bfsi-q-label" style="color: #6b7280;">Target Firm</div>
            <div style="font-size: 16px; font-weight: 700; color: #1E3A8A;">{safe_company}</div>
        </div>""")
        comp_sel = st.session_state.company_name
        custom = ""
    else:
        comp_sel = st.selectbox("Firm", BFSI_COMPANIES, index=0, label_visibility="collapsed")
        custom = ""
        if comp_sel == "Other / Confidential":
            custom = st.text_input("Firm name (will appear in the report)", placeholder="e.g. Quantum Asset Management")

    st.html("""<div class="bfsi-q-card">
        <div class="bfsi-q-label">Firm Sector</div>
        <div class="bfsi-q-help">Dictates the specific operational questions you will be asked.</div>
    </div>""")
    sectors = ["Mutual Funds / Asset Management", "Life & General Insurance", "Diversified Financial Services"]
    default_sector = st.session_state.get("target_sector", sectors[0])
    sector = st.radio("", sectors, index=sectors.index(default_sector) if default_sector in sectors else 0, label_visibility="collapsed")

    st.html("""<div class="bfsi-q-card">
        <div class="bfsi-q-label">Primary Strategic Objectives</div>
        <div class="bfsi-q-help">Select all that apply. This weights the engine toward cost vs. revenue vs. risk levers.</div>
    </div>""")
    goals = st.multiselect("", options=OBJECTIVE_INPUTS, default=st.session_state.primary_goals, label_visibility="collapsed")

    _nav_buttons(None, "Next: Technology & Data →", lambda: _advance_company(comp_sel, custom, goals, sector))

def _advance_company(sel, custom, goals, sector):
    # Only update the company if it wasn't already set from the landing page
    company = custom if sel == "Other / Confidential" else sel
    st.session_state.company_name = company
    st.session_state.primary_goals = goals
    st.session_state.target_sector = sector
    
    # Perform web search to prefill
    if company:
        # Avoid re-searching if they just go back and forth
        if not getattr(st.session_state, '_search_completed', False):
            # We don't have st.spinner available in a callback in a great way, but we can try
            with st.spinner(f"🔍 Searching web for {company} data to prefill..."):
                extracted_data = extract_company_data(company)
                
                if "error" not in extracted_data:
                    st.session_state._search_success = True
                    # Auto-correct the company name if Gemini found the official spelling
                    official_name = extracted_data.pop("company_name", None)
                    if official_name:
                        st.session_state.company_name = official_name
                        
                    st.session_state.discovery_answers.update(extracted_data)
                else:
                    st.session_state._search_success = False
                    
                st.session_state._search_completed = True
                
    st.session_state.wizard_page += 1

# ── Section Pages ──────────────────────────────────────────────────────────

def _page_section(idx: int) -> None:
    section = SECTIONS[idx]
    sid = section["id"]
    eyebrow, title, desc = _SECTION_DESCS.get(sid, ("SECTION", section["title"], ""))

    st.html(f"""
    <div class="bfsi-section-banner">
        <div class="bfsi-section-banner-eyebrow">STEP {idx+2} OF 7 · {eyebrow}</div>
        <div class="bfsi-section-banner-title">{title}</div>
        <div class="bfsi-section-banner-desc">{desc}</div>
    </div>
    """)
    
    if getattr(st.session_state, '_search_success', False):
        safe_company = html.escape(st.session_state.company_name)
        st.html(f"""
        <div style="background: #fdfaf5; border: 1px solid #f2dfce; padding: 12px 16px; border-radius: 6px; margin-bottom: 24px;">
            <div style="font-size: 12.5px; color: #8c5020; line-height: 1.5;">
                <strong>⚠️ Data Pre-filled via Web Search.</strong> 
                Preliminary information for <strong>{safe_company}</strong> has been extracted automatically. 
                Please verify these values. Questions regarding internal metrics (e.g., Data Silos, KTLO) must be manually entered.
            </div>
        </div>
        """)

    answers = st.session_state.discovery_answers
    sector = st.session_state.get("target_sector", "all")
    for i, q in enumerate(get_questions_for_section(sid, sector=sector), 1):
        _render_card_question(i, q, answers)

    btn_label = "Next →" if idx < len(SECTIONS) - 1 else "Next: Capital Allocation →"
    _nav_buttons(
        lambda: setattr(st.session_state, 'wizard_page', st.session_state.wizard_page - 1) or st.rerun(),
        btn_label,
        lambda: _advance_section(answers)
    )

def _advance_section(answers):
    st.session_state.discovery_answers = answers
    st.session_state.wizard_page += 1

def _render_card_question(idx: int, q: dict, answers: dict) -> None:
    key = q["id"]
    current = answers.get(key, q.get("default"))
    help_text = q.get("help", "")
    qtype = q["type"]
    label = q["question"]

    st.html(f"""
    <div class="bfsi-q-card">
        <div class="bfsi-q-label"><span style="color:#D04A02; font-family: 'Courier New', Courier, monospace; font-weight: 800; margin-right: 8px;">{idx:02d}.</span>{label}</div>
        <div class="bfsi-q-help">{help_text}</div>
    </div>
    """)

    if qtype == "numeric":
        val = st.number_input("", value=float(current) if current is not None else 0.0, key=f"q_{key}", label_visibility="collapsed")
        answers[key] = val
    elif qtype == "percentage":
        val = st.slider("", min_value=0, max_value=100, value=int(current) if current is not None else 50, step=1, key=f"q_{key}", label_visibility="collapsed")
        answers[key] = val
    elif qtype == "categorical":
        opts = q["options"]
        idx = opts.index(current) if current in opts else 0
        val = st.radio("", opts, index=idx, key=f"q_{key}", label_visibility="collapsed", horizontal=False)
        answers[key] = val

# ── Page Final: Investment Budget ──────────────────────────────────────────

def _page_investment() -> None:
    st.html("""
    <div class="bfsi-section-banner">
        <div class="bfsi-section-banner-eyebrow">STEP 7 OF 7 · CAPITAL SCOPE</div>
        <div class="bfsi-section-banner-title">Total AI Transformation Budget</div>
        <div class="bfsi-section-banner-desc">
            This defines the capital allocation envelope. The engine will sequence levers to stay within budget
            while maximising risk-adjusted ANV. Peer range for mid-tier BFSI: $25M – $150M.
        </div>
    </div>
    """)

    budget = st.slider("", min_value=10, max_value=500, value=int(st.session_state.budget_usd_m), step=5, label_visibility="collapsed")
    st.html(f'<div class="aia-budget-display">${budget}M</div><div style="font-size:12px;color:#6b7280;margin-top:-4px;margin-bottom:20px;">Total transformation investment</div>')

    _nav_buttons(
        lambda: setattr(st.session_state, 'wizard_page', st.session_state.wizard_page - 1) or st.rerun(),
        "⚡ Generate Diagnostic & Roadmap",
        lambda: _generate(budget)
    )

def _generate(budget):
    st.session_state.budget_usd_m = float(budget)
    with st.spinner("Computing ANV across 14 levers · Benchmarking against peers..."):
        from engine.math_engine import build_investment_plan
        plan = build_investment_plan(st.session_state.discovery_answers, st.session_state.budget_usd_m, st.session_state.primary_goals)
        st.session_state.thesis_plan = plan
        st.session_state.thesis_summary = generate_executive_summary(
            st.session_state.company_name,
            plan,
            st.session_state.discovery_answers,
            st.session_state.get("target_sector", "Financial Services")
        )
        st.session_state.thesis_generated = True
        st.session_state.app_phase = 2
    st.rerun()

# ── Navigation helpers ─────────────────────────────────────────────────────

def _nav_buttons(back_fn, next_label: str, next_fn) -> None:
    st.html('<div style="height:20px;"></div>')
    col_back, _, col_next = st.columns([1, 2, 2])
    with col_back:
        if back_fn and st.session_state.wizard_page > 0:
            if st.button("← Back", use_container_width=True):
                st.session_state.wizard_page -= 1
                st.rerun()
    with col_next:
        if st.button(next_label, use_container_width=True, type="primary"):
            next_fn()
            st.rerun()