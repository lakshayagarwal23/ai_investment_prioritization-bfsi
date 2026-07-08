"""
ui/sidebar.py — Premium BFSI intake wizard with card-based HTML layout (PwC Horizon spec).
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
    "— Select your firm —", "Aditya Birla Sun Life AMC", "Axis Bank", "Bajaj Finance",
    "Bandhan Bank", "Bank of Baroda", "Canara Bank", "Cholamandalam Investment and Finance",
    "DSP Mutual Fund", "Edelweiss Financial Services", "HDFC AMC", "HDFC Bank",
    "HDFC Life Insurance", "ICICI Bank", "ICICI Lombard General Insurance", "ICICI Prudential AMC",
    "ICICI Prudential Life Insurance", "IDFC First Bank", "IndusInd Bank", "Kotak Mahindra Bank",
    "Kotak Mahindra AMC", "Kotak Life Insurance", "L&T Finance Holdings", "LIC (Life Insurance Corporation of India)",
    "Mahindra Manulife Mutual Fund", "Max Financial Services", "Max Life Insurance", "Muthoot Finance",
    "Nippon India Mutual Fund", "PNB (Punjab National Bank)", "SBI (State Bank of India)", "SBI Life Insurance",
    "SBI Mutual Fund", "Shriram Finance", "Tata AIA Life Insurance", "Tata Mutual Fund",
    "UTI AMC", "Yes Bank", "Other / Confidential",
]

STEPPER_LABELS = ["COMPANY"] + [s["nav_label"] for s in SECTIONS] + ["INVESTMENT"]

_SECTION_DESCS = {
    "S1": ("Technology & Data Infrastructure", "Your data architecture and system health determine the ceiling of every AI lever. Be precise — this drives the Legacy Deprecation Score."),
    "S2": ("Front Office Operations", "How efficiently does your front office operate today? These inputs calibrate the Research, Execution, and Distribution levers."),
    "S3": ("Middle & Back Office Operations", "Post-trade operations are the fastest AI payback in asset management. Your STP rate is the single most important number here."),
    "S4": ("Risk, Compliance & Onboarding", "Regulatory friction and onboarding latency are a silent tax on AUM ramp. Quantify them so we can price the opportunity."),
    "S5": ("Legacy Systems & Governance", "Every kill/modernize/hold decision begins here. Five governance dimensions determine whether a rebuild is safe to execute."),
}

def init_session_state() -> None:
    defaults = {
        "app_phase": 0, "wizard_page": 0,
        "company_name": "", "budget_usd_m": 100.0,
        "primary_goals": ["Margin Expansion (Cost)"],
        "discovery_answers": {},
        "discovery_provenance": {},
        "thesis_generated": False, "thesis_plan": None, "thesis_summary": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def render_sidebar_branding() -> None:
    phase = st.session_state.app_phase
    with st.sidebar:
        st.write("")
        if phase >= 2:
            st.html("""
            <div style="font-family: var(--font-head); font-size: 24px; color: var(--pwc-orange); font-weight: bold; margin-bottom: var(--sp-4); padding-bottom: 8px; border-bottom: 1px solid var(--g200);">
                pwc
            </div>
            """)
            
            # Scenario Selector in Sidebar
            st.html("""
            <div style="font-family: var(--font-head); font-size: 15px; color: var(--black); margin-bottom: var(--sp-2);">
                Execution Scenario
            </div>
            """)
            scenarios = ["conservative", "base", "aggressive"]
            current_sc = st.session_state.get("current_scenario", "base")
            scenario = st.radio("Execution Scenario", scenarios, index=scenarios.index(current_sc), label_visibility="collapsed")
            if scenario != current_sc:
                st.session_state.current_scenario = scenario
                from engine.math_engine import build_investment_plan
                st.session_state.thesis_plan = build_investment_plan(
                    st.session_state.discovery_answers, 
                    st.session_state.budget_usd_m, 
                    st.session_state.primary_goals,
                    scenario=scenario
                )
                st.rerun()
                
            st.write("")
            if st.button("← Restart Analysis", use_container_width=True):
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.rerun()
        else:
            # Clean minimalistic placeholder for the wizard stage to prevent redundancy
            st.html("""
            <div style="font-family: var(--font-head); font-size: 24px; color: var(--pwc-orange); font-weight: bold; margin-bottom: 24px; padding-bottom: 8px; border-bottom: 1px solid var(--g200);">
                pwc
            </div>
            <div style="font-size: 13px; color: var(--g500); line-height: 1.4;">
                C-Suite Transformation Advisory Platform
            </div>
            """)

def _stepper(current: int) -> None:
    parts = []
    for i, label in enumerate(STEPPER_LABELS):
        if i == current:
            state = "active"
            num = str(i+1)
            active_lbl = "active"
        elif i < current:
            state = "done"
            num = "✓"
            active_lbl = ""
        else:
            state = "todo"
            num = str(i+1)
            active_lbl = ""
        
        parts.append(
            f'<div class="hz-step">'
            f'  <div class="hz-step-sq {state}">{num}</div>'
            f'  <div class="hz-step-lbl {active_lbl}">{label}</div>'
            f'</div>'
        )
        if i < len(STEPPER_LABELS) - 1:
            parts.append('<div class="hz-step-rule"></div>')
            
    st.html(f'<div class="hz-stepper">{"".join(parts)}</div>')

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
    <div class="hz-q-group-intro">Firm Profile (Step 1 of 7)</div>
    <div style="font-size: 14px; color: var(--g700); margin-bottom: var(--sp-6);">
        Select your firm to pre-load benchmark peer intelligence, or enter custom details.
        All data remains confidential and is used solely to calibrate the diagnostic engine.
    </div>
    """)

    with st.container(border=True):
        if st.session_state.company_name:
            safe_company = html.escape(st.session_state.company_name)
            st.html(f"""
            <div class="hz-q-row">
                <div class="hz-q-label-row"><span class="hz-q-label">Target Firm</span></div>
                <div style="font-size: 16px; font-family: var(--font-head); color: var(--black);">{safe_company}</div>
            </div>""")
            comp_sel = st.session_state.company_name
            custom = ""
        else:
            st.html("""<div class="hz-q-row"><div class="hz-q-label-row"><span class="hz-q-label">Firm</span></div></div>""")
            comp_sel = st.selectbox("Firm", BFSI_COMPANIES, index=0, label_visibility="hidden")
            custom = ""
            if comp_sel == "Other / Confidential":
                custom = st.text_input("Firm name (will appear in the report)", placeholder="e.g. Quantum Asset Management", label_visibility="hidden")

        st.html("""<div class="hz-q-row" style="margin-top: 16px;"><div class="hz-q-label-row"><span class="hz-q-label">Firm Sector</span></div>
        <div style="font-size: 11px; color: var(--g500); margin-bottom: 8px;">Dictates the specific operational questions you will be asked.</div></div>""")
        sectors = ["Mutual Funds / Asset Management", "Life & General Insurance", "Diversified Financial Services"]
        default_sector = st.session_state.get("target_sector", sectors[0])
        sector = st.radio("Firm Sector", sectors, index=sectors.index(default_sector) if default_sector in sectors else 0, label_visibility="hidden")

        st.html("""<div class="hz-q-row" style="margin-top: 16px;"><div class="hz-q-label-row"><span class="hz-q-label">Primary Strategic Objectives</span></div>
        <div style="font-size: 11px; color: var(--g500); margin-bottom: 8px;">Select all that apply. This weights the engine toward cost vs. revenue vs. risk levers.</div></div>""")
        goals = st.multiselect("Primary Strategic Objectives", options=OBJECTIVE_INPUTS, default=st.session_state.primary_goals, label_visibility="hidden")

    _nav_buttons(None, "Next: Technology & Data", lambda: _advance_company(comp_sel, custom, goals, sector))

def _advance_company(sel, custom, goals, sector):
    company = custom if sel == "Other / Confidential" else sel
    st.session_state.company_name = company
    st.session_state.primary_goals = goals
    st.session_state.target_sector = sector
    
    if company and not getattr(st.session_state, '_search_completed', False):
        with st.spinner("Searching web for firm data to prefill..."):
            extracted_data = extract_company_data(company)
            if "error" not in extracted_data:
                st.session_state._search_success = True
                official_name = extracted_data.pop("company_name", None)
                if official_name:
                    st.session_state.company_name = official_name
                
                for k, v in extracted_data.items():
                    if isinstance(v, dict) and "value" in v:
                        st.session_state.discovery_answers[k] = v["value"]
                        st.session_state.discovery_provenance[k] = v
                    else:
                        st.session_state.discovery_answers[k] = v
            else:
                st.session_state._search_success = False
            st.session_state._search_completed = True
                
    st.session_state.wizard_page += 1

# ── Section Pages ──────────────────────────────────────────────────────────

def _page_section(idx: int) -> None:
    section = SECTIONS[idx]
    sid = section["id"]
    title, desc = _SECTION_DESCS.get(sid, (section["title"], ""))

    st.html(f"""
    <div class="hz-q-group-intro">{title} (Step {idx+2} of 7)</div>
    <div style="font-size: 14px; color: var(--g700); margin-bottom: var(--sp-6);">
        {desc}
    </div>
    """)
    
    if getattr(st.session_state, '_search_success', False):
        safe_company = html.escape(st.session_state.company_name)
        st.html(f"""
        <div style="background: var(--yellow-tint); border: 1px solid var(--pwc-yellow); padding: 12px 16px; border-radius: 2px; margin-bottom: 24px; color: var(--black); font-size: 13px;">
            <strong>Data pre-filled via web search.</strong> 
            Preliminary information for {safe_company} has been extracted automatically. 
            Please verify these values.
        </div>
        """)

    answers = st.session_state.discovery_answers
    sector = st.session_state.get("target_sector", "all")
    questions = get_questions_for_section(sid, sector=sector)
    
    # Chunk questions into groups of 3
    # Evaluate visible_when before chunking
    visible_qs = []
    for q in questions:
        if "visible_when" in q:
            visible = True
            for cond_k, cond_v in q["visible_when"].items():
                check_val = st.session_state.get("target_sector") if cond_k == "sector" else answers.get(cond_k)
                if isinstance(cond_v, list):
                    if check_val not in cond_v:
                        visible = False
                elif check_val != cond_v:
                    visible = False
            if not visible:
                continue
        visible_qs.append(q)
        
    for i in range(0, len(visible_qs), 3):
        chunk = visible_qs[i:i+3]
        with st.container(border=True):
            for j, q in enumerate(chunk):
                q_idx = i + j + 1
                _render_card_question(q_idx, q, answers)

    btn_label = "Next" if idx < len(SECTIONS) - 1 else "Next: Capital Allocation"
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

    chip_class = "manual"
    chip_text = "MANUAL"
    provenance_data = st.session_state.discovery_provenance.get(key)
    
    if provenance_data:
        conf = provenance_data.get("confidence", "Low")
        if conf == "High":
            chip_class = "auto"
            chip_text = "AUTO"
        elif conf == "Med":
            chip_class = "verify"
            chip_text = "VERIFY"
        
        quote = provenance_data.get("quote", "")
        src = provenance_data.get("source_url", "Web")
        help_text = f"Source: {src}<br><em>\"{quote}\"</em>"
    elif q.get("provenance") == "AUTO":
        chip_class = "manual"
        chip_text = "NOT FOUND"
    elif current == q.get("default"):
        chip_class = "median"
        chip_text = "MEDIAN"

    st.html(f"""
    <div class="hz-q-row">
        <div class="hz-q-label-row">
            <span class="hz-q-label">{idx:02d}. {label}</span>
            <span class="hz-chip {chip_class}">{chip_text}</span>
        </div>
        <div style="font-size: 11px; color: var(--g500); margin-bottom: 8px;">{help_text}</div>
    </div>
    """)

    if qtype == "numeric":
        val = st.number_input(label, value=float(current) if current is not None else 0.0, key=f"q_{key}", label_visibility="hidden")
        answers[key] = val
    elif qtype == "percentage":
        val = st.slider(label, min_value=0, max_value=100, value=int(current) if current is not None else 50, step=1, key=f"q_{key}", label_visibility="hidden")
        answers[key] = val
    elif qtype == "categorical":
        opts = q["options"]
        opt_idx = opts.index(current) if current in opts else 0
        val = st.radio(label, opts, index=opt_idx, key=f"q_{key}", label_visibility="hidden", horizontal=False)
        answers[key] = val

# ── Page Final: Investment Budget ──────────────────────────────────────────

def _page_investment() -> None:
    st.html("""
    <div class="hz-q-group-intro">Total AI Transformation Budget (Step 7 of 7)</div>
    <div style="font-size: 14px; color: var(--g700); margin-bottom: var(--sp-6);">
        This defines the capital allocation envelope. The engine will sequence levers to stay within budget
        while maximising risk-adjusted ANV. Peer range for mid-tier BFSI: $25M – $150M.
    </div>
    """)

    with st.container(border=True):
        st.html("""<div class="hz-q-row"><div class="hz-q-label-row"><span class="hz-q-label">Total transformation investment (USD Millions)</span></div></div>""")
        budget = st.slider("Total transformation investment (USD Millions)", min_value=10, max_value=500, value=int(st.session_state.budget_usd_m), step=5, label_visibility="hidden")
        st.html(f'<div style="font-family: var(--font-head); font-size: 34px; color: var(--black);">${budget}M</div>')

    _nav_buttons(
        lambda: setattr(st.session_state, 'wizard_page', st.session_state.wizard_page - 1) or st.rerun(),
        "Generate Diagnostic",
        lambda: _generate(budget)
    )

def _generate(budget):
    st.session_state.budget_usd_m = float(budget)
    st.session_state.discovery_answers["target_sector"] = st.session_state.get("target_sector", "all")
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
        
        from storage.audit import log_run
        run_id = log_run(
            company=st.session_state.company_name,
            inputs=st.session_state.discovery_answers,
            plan=plan,
            payload={"summary": st.session_state.thesis_summary},
            mode="interactive"
        )
        st.session_state.last_run_id = run_id
        
        st.session_state.thesis_generated = True
        st.session_state.app_phase = 2
    st.rerun()

# ── Navigation helpers ─────────────────────────────────────────────────────

def _nav_buttons(back_fn, next_label: str, next_fn) -> None:
    st.write("")
    col_back, _, col_next = st.columns([1.5, 3, 1.5])
    with col_back:
        if back_fn and st.session_state.wizard_page > 0:
            if st.button("Back", key=f"back_{st.session_state.wizard_page}", use_container_width=True):
                back_fn()
    with col_next:
        if st.button(next_label, key=f"next_{st.session_state.wizard_page}", type="primary", use_container_width=True):
            next_fn()