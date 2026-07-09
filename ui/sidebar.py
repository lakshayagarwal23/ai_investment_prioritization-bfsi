"""
ui/sidebar.py — Single-column intake wizard (PwC Horizon v5).

NOTE: filename retained for import stability, but the left sidebar is GONE.
This module now renders only the top-of-page stepper + intake cards in the
main column. Scenario selection lives on the dashboard, not a sidebar.
"""
from __future__ import annotations
import streamlit as st
import html
from config.questions import SECTIONS, get_questions_for_section, OBJECTIVE_INPUTS
from llm.search_client import extract_company_data
from llm.openai_client import generate_executive_summary

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
    "S1": ("Technology & Data Infrastructure", "Your data architecture and system health set the ceiling of every AI lever. This drives the Legacy Deprecation score and lever feasibility."),
    "S2": ("Front Office Operations", "How efficiently the front office runs today calibrates the Research, Execution, and Distribution levers."),
    "S3": ("Middle & Back Office Operations", "Post-trade and claims operations are the fastest AI payback. Your STP rate is the single most important number here."),
    "S4": ("Risk, Compliance & Onboarding", "Regulatory friction and onboarding latency are a silent tax on growth. Quantify them so the engine can price the opportunity."),
    "S5": ("Legacy Systems & Governance", "Every kill / modernize / hold decision begins here."),
}


def init_session_state() -> None:
    defaults = {
        "app_phase": 0, "wizard_page": 0,
        "company_name": "", "budget_usd_m": 100.0,
        "primary_goals": ["Margin Expansion (Cost)"],
        "discovery_answers": {}, "discovery_provenance": {},
        "target_sector": "Mutual Funds / Asset Management",
        "current_scenario": "base",
        "thesis_generated": False, "thesis_plan": None, "thesis_summary": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _stepper(current: int) -> None:
    parts = []
    for i, label in enumerate(STEPPER_LABELS):
        if i == current:
            state, num, active_lbl = "active", str(i + 1), "active"
        elif i < current:
            state, num, active_lbl = "done", "✓", ""
        else:
            state, num, active_lbl = "todo", str(i + 1), ""
        parts.append(
            f'<div class="hz-step"><div class="hz-step-sq {state}">{num}</div>'
            f'<div class="hz-step-lbl {active_lbl}">{label}</div></div>'
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


# ── Page 0: Company ─────────────────────────────────────────────────────────

def _page_company() -> None:
    st.html("""
    <div class="hz-q-group-intro">Firm Profile (Step 1 of 7)</div>
    <div style="font-size:14px; color:var(--g700); margin-bottom:var(--sp-6);">
        Select your firm to pre-load benchmark peer intelligence, or enter custom details.
        Data is used solely to calibrate the diagnostic engine.
    </div>
    """)

    with st.container(border=True):
        if st.session_state.company_name:
            safe = html.escape(st.session_state.company_name)
            st.html(f"""<div class="hz-q-row"><div class="hz-q-label-row"><span class="hz-q-label">Target Firm</span></div>
            <div style="font-size:16px; font-family:var(--font-head); color:var(--black);">{safe}</div></div>""")
            comp_sel, custom = st.session_state.company_name, ""
        else:
            st.html("""<div class="hz-q-row"><div class="hz-q-label-row"><span class="hz-q-label">Firm</span></div></div>""")
            comp_sel = st.selectbox("Firm", BFSI_COMPANIES, index=0, label_visibility="collapsed")
            custom = ""
            if comp_sel == "Other / Confidential":
                custom = st.text_input("Firm name (appears in the report)", placeholder="e.g. Quantum Asset Management", label_visibility="collapsed")

        st.html("""<div class="hz-q-row" style="margin-top:16px;"><div class="hz-q-label-row"><span class="hz-q-label">Firm Sector</span></div>
        <div style="font-size:11px; color:var(--g500); margin-bottom:8px;">Determines which operational questions you are asked, and which levers are scored.</div></div>""")
        sectors = ["Mutual Funds / Asset Management", "Life & General Insurance", "Diversified Financial Services"]
        default_sector = st.session_state.get("target_sector", sectors[0])
        sector = st.radio("Firm Sector", sectors, index=sectors.index(default_sector) if default_sector in sectors else 0, label_visibility="collapsed")

        st.html("""<div class="hz-q-row" style="margin-top:16px;"><div class="hz-q-label-row"><span class="hz-q-label">Primary Strategic Objectives</span></div>
        <div style="font-size:11px; color:var(--g500); margin-bottom:8px;">Levers serving a selected goal reach full impact; off-goal levers are dampened (not hidden). Leave empty to rank purely on value and urgency.</div></div>""")
        goals = st.multiselect("Primary Strategic Objectives", options=OBJECTIVE_INPUTS, default=st.session_state.primary_goals, label_visibility="collapsed")

    _nav_buttons(None, "Next: Technology & Data", lambda: _advance_company(comp_sel, custom, goals, sector))


def _advance_company(sel, custom, goals, sector):
    company = custom if sel == "Other / Confidential" else sel
    if company == "— Select your firm —":
        company = ""
    st.session_state.company_name = company
    st.session_state.primary_goals = goals
    st.session_state.target_sector = sector

    if company and not st.session_state.get("_search_completed", False):
        with st.spinner("Searching public sources to prefill firm data…"):
            extracted = extract_company_data(company)
            if "error" not in extracted:
                st.session_state._search_success = bool(extracted)
                official = extracted.pop("company_name", None)
                if official:
                    st.session_state.company_name = official
                for k, v in extracted.items():
                    if isinstance(v, dict) and "value" in v:
                        st.session_state.discovery_answers[k] = v["value"]
                        st.session_state.discovery_provenance[k] = v
                    else:
                        st.session_state.discovery_answers[k] = v
            else:
                st.session_state._search_success = False
            st.session_state._search_completed = True

    st.session_state.wizard_page += 1


# ── Section pages ───────────────────────────────────────────────────────────

def _page_section(idx: int) -> None:
    section = SECTIONS[idx]
    sid = section["id"]
    title, desc = _SECTION_DESCS.get(sid, (section["title"], ""))

    st.html(f"""
    <div class="hz-q-group-intro">{title} (Step {idx+2} of 7)</div>
    <div style="font-size:14px; color:var(--g700); margin-bottom:var(--sp-6);">{desc}</div>
    """)

    if st.session_state.get("_search_success", False):
        filled = list(st.session_state.discovery_provenance.keys())
        if filled:
            safe = html.escape(st.session_state.company_name)
            st.html(f"""
            <div style="background:var(--yellow-tint); border:1px solid var(--pwc-yellow); padding:12px 16px; border-radius:2px; margin-bottom:24px; color:var(--black); font-size:13px;">
                <strong>{len(filled)} field(s) pre-filled for {safe}.</strong>
                Each carries a source chip below — please verify before continuing.
            </div>
            """)

    answers = st.session_state.discovery_answers
    sector = st.session_state.get("target_sector", "all")
    questions = get_questions_for_section(sid, sector=sector)

    visible_qs = []
    for q in questions:
        if "visible_when" in q:
            ok = True
            for cond_k, cond_v in q["visible_when"].items():
                check = st.session_state.get("target_sector") if cond_k == "sector" else answers.get(cond_k)
                if isinstance(cond_v, list):
                    if check not in cond_v:
                        ok = False
                elif check != cond_v:
                    ok = False
            if not ok:
                continue
        visible_qs.append(q)

    for i in range(0, len(visible_qs), 3):
        with st.container(border=True):
            for j, q in enumerate(visible_qs[i:i + 3]):
                _render_card_question(i + j + 1, q, answers)

    btn = "Next" if idx < len(SECTIONS) - 1 else "Next: Capital Allocation"
    _nav_buttons(lambda: _go_back(), btn, lambda: _advance_section(answers))


def _advance_section(answers):
    st.session_state.discovery_answers = answers
    st.session_state.wizard_page += 1


def _render_card_question(idx: int, q: dict, answers: dict) -> None:
    key = q["id"]
    current = answers.get(key, q.get("default"))
    help_text = q.get("help", "")
    qtype = q["type"]
    label = q["question"]

    chip_class, chip_text = "manual", "MANUAL"
    prov = st.session_state.discovery_provenance.get(key)
    if prov:
        conf = prov.get("confidence", "Low")
        if conf == "High":
            chip_class, chip_text = "auto", "AUTO"
        elif conf == "Med":
            chip_class, chip_text = "verify", "VERIFY"
        else:
            chip_class, chip_text = "verify", "VERIFY"
        quote = html.escape(str(prov.get("quote", "")))[:160]
        src = html.escape(str(prov.get("source_url", "public source")))
        help_text = f"Source: {src}<br><em>\"{quote}\"</em>"
    elif q.get("provenance") == "AUTO":
        chip_class, chip_text = "median", "NOT FOUND — using default"
    elif current == q.get("default"):
        chip_class, chip_text = "median", "MEDIAN"

    st.html(f"""
    <div class="hz-q-row">
        <div class="hz-q-label-row">
            <span class="hz-q-label">{idx:02d}. {label}</span>
            <span class="hz-chip {chip_class}">{chip_text}</span>
        </div>
        <div style="font-size:11px; color:var(--g500); margin-bottom:8px;">{help_text}</div>
    </div>
    """)

    if qtype == "numeric":
        answers[key] = st.number_input(label, value=float(current) if current is not None else 0.0,
                                       min_value=0.0, key=f"q_{key}", label_visibility="collapsed")
    elif qtype == "percentage":
        answers[key] = st.slider(label, 0, 100, int(current) if current is not None else 50, 1,
                                 key=f"q_{key}", label_visibility="collapsed")
    elif qtype == "categorical":
        opts = q["options"]
        idx0 = opts.index(current) if current in opts else 0
        answers[key] = st.radio(label, opts, index=idx0, key=f"q_{key}", label_visibility="collapsed")


# ── Final page: budget ──────────────────────────────────────────────────────

def _page_investment() -> None:
    st.html("""
    <div class="hz-q-group-intro">Total AI Transformation Budget (Step 7 of 7)</div>
    <div style="font-size:14px; color:var(--g700); margin-bottom:var(--sp-6);">
        The capital envelope. The engine sequences levers to stay within budget while maximising
        risk-adjusted ANV. Peer range for mid-tier BFSI: $25M – $150M.
    </div>
    """)
    with st.container(border=True):
        st.html("""<div class="hz-q-row"><div class="hz-q-label-row"><span class="hz-q-label">Total transformation investment (USD Millions)</span></div></div>""")
        budget = st.slider("Total transformation investment (USD Millions)", 10, 500, int(st.session_state.budget_usd_m), 5, label_visibility="collapsed")
        st.html(f'<div style="font-family:var(--font-head); font-size:34px; color:var(--black);">${budget}M</div>')

    _nav_buttons(lambda: _go_back(), "Generate Diagnostic", lambda: _generate(budget))


def _generate(budget):
    st.session_state.budget_usd_m = float(budget)
    st.session_state.discovery_answers["target_sector"] = st.session_state.get("target_sector", "all")
    with st.spinner("Computing ANV across levers · benchmarking against peers…"):
        from engine.math_engine import build_investment_plan
        plan = build_investment_plan(
            st.session_state.discovery_answers, st.session_state.budget_usd_m,
            st.session_state.primary_goals, scenario=st.session_state.get("current_scenario", "base"))
        st.session_state.thesis_plan = plan
        st.session_state.thesis_summary = generate_executive_summary(
            st.session_state.company_name, plan, st.session_state.discovery_answers,
            st.session_state.get("target_sector", "Financial Services"))

        from storage.audit import log_run
        st.session_state.last_run_id = log_run(
            company=st.session_state.company_name, inputs=st.session_state.discovery_answers,
            plan=plan, payload={"summary": st.session_state.thesis_summary}, mode="interactive")

        st.session_state.thesis_generated = True
        st.session_state.app_phase = 2
    st.rerun()


# ── Navigation helpers ──────────────────────────────────────────────────────

def _go_back():
    st.session_state.wizard_page = max(0, st.session_state.wizard_page - 1)
    st.rerun()


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