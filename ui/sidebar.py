"""
ui/sidebar.py

Multi-page wizard intake form + sidebar branding for the AI Investment Engine.

Pages:
  Page 0: Company Identity (name, geography)
  Pages 1–7: Discovery sections S1–S7 (8 questions each, shown as cards)
  Page 8: Investment Scope (budget, timeline) + Generate button

Navigation: Previous / Next buttons, with a horizontal stepper at the top
showing numbered circles and section labels (like the reference screenshot).
"""

from __future__ import annotations

import streamlit as st

from config.questions import (
    SECTIONS, QUESTIONS,
    get_section, get_questions_for_section,
)
from llm.openai_client import generate_executive_summary, generate_company_intelligence


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

FMCG_COMPANIES: list[str] = [
    "— Select your company —",
    "Procter & Gamble (NYSE: PG)",
    "Unilever PLC (LSE: ULVR)",
    "Nestle S.A. (SWX: NESN)",
    "The Coca-Cola Company (NYSE: KO)",
    "PepsiCo Inc. (NASDAQ: PEP)",
    "Colgate-Palmolive (NYSE: CL)",
    "Mondelez International (NASDAQ: MDLZ)",
    "Reckitt Benckiser Group (LSE: RKT)",
    "Kimberly-Clark (NYSE: KMB)",
    "Kraft Heinz (NASDAQ: KHC)",
    "Danone S.A. (EPA: BN)",
    "L'Oreal (EPA: OR)",
    "Henkel AG (ETR: HEN3)",
    "General Mills (NYSE: GIS)",
    "Church & Dwight (NYSE: CHD)",
    "Hindustan Unilever Ltd (NSE: HINDUNILVR)",
    "Marico Limited (NSE: MARICO)",
    "Dabur India (NSE: DABUR)",
    "ITC Limited (NSE: ITC)",
    "Britannia Industries (NSE: BRITANNIA)",
    "Godrej Consumer Products (NSE: GODREJCP)",
    "Emami Limited (NSE: EMAMILTD)",
    "Bajaj Consumer Care (NSE: BAJAJCON)",
    "Other (type below)",
]

GEOGRAPHY_OPTIONS: list[str] = [
    "India & South Asia", "North America", "Europe", "APAC",
    "Middle East & Africa", "Latin America", "Global / Multi-Region",
]

TIMELINE_MIN_MO, TIMELINE_MAX_MO, TIMELINE_DEFAULT_MO, TIMELINE_STEP_MO = 6, 60, 24, 6
BUDGET_MIN_M, BUDGET_MAX_M, BUDGET_DEFAULT_M, BUDGET_STEP_M = 10, 500, 100, 5

# Total wizard pages: 0 (company) + 4 (sections) + 1 (budget) = 6
TOTAL_PAGES = 6

# ─── page labels for stepper (9 steps) ────────────────────────────────────────
STEPPER_LABELS = ["COMPANY"] + [s["nav_label"] for s in SECTIONS] + ["INVESTMENT"]


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────

def init_session_state() -> None:
    defaults: dict = {
        "app_phase": 0,
        "wizard_page": 0,
        "company_name": "",
        "geography": GEOGRAPHY_OPTIONS[0],
        "company_intel": {"geographies": GEOGRAPHY_OPTIONS, "tailored_options": {}},
        "budget_usd_m": float(BUDGET_DEFAULT_M),
        "budget_option": f"${BUDGET_DEFAULT_M}M",
        "timeline_months": TIMELINE_DEFAULT_MO,
        "primary_goals": ["Revenue Growth"],
        "discovery_answers": {},
        "thesis_generated": False,
        "thesis_plan": None,
        "thesis_summary": "",
        "thesis_is_ai": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR BRANDING
# ─────────────────────────────────────────────────────────────────────────────

def render_sidebar_branding() -> None:
    phase = st.session_state.app_phase
    with st.sidebar:
        if phase <= 1:
            _sidebar_landing_content()
        else:
            _sidebar_session_content()


def _sidebar_landing_content() -> None:
    st.html("""
    <div class="aia-sidebar-brand">
      <div class="aia-sidebar-brand-title">Investment Engine</div>
      <div class="aia-sidebar-brand-sub">
        Complete the intake questionnaire to generate your investment thesis.
      </div>
    </div>
    """)
    st.html('<div class="aia-sidebar-section-label">Intelligence Sources</div>')
    st.html("""
    <div style="font-size:10.5px; color:rgba(255,255,255,0.50); line-height:2.0; margin-bottom:20px;">
      <span style="color:rgba(255,255,255,0.25); font-size:9px; display:block; margin-bottom:6px;">
        PEER BENCHMARKS
      </span>
      <span style="color:var(--brand-primary); font-weight:700; font-size:10px;">P&amp;G</span>
      &nbsp; $1.5B supply chain savings<br>
      <span style="color:var(--brand-primary); font-weight:700; font-size:10px;">Nestle</span>
      &nbsp; 12-pt NPS via Trade Promo AI<br>
      <span style="color:var(--brand-primary); font-weight:700; font-size:10px;">Unilever</span>
      &nbsp; 15% inventory reduction<br>
      <span style="color:var(--brand-primary); font-weight:700; font-size:10px;">Reckitt</span>
      &nbsp; 14-pt NPS via Digital Shelf AI<br>
      <span style="color:var(--brand-primary); font-weight:700; font-size:10px;">Coca-Cola</span>
      &nbsp; $500M AI cost reduction<br>
    </div>
    """)
    st.html('<div class="aia-sidebar-section-label">Questionnaire</div>')
    st.html("""
    <div style="font-size:10.5px; color:rgba(255,255,255,0.50); line-height:2.0;">
      <span style="color:rgba(255,255,255,0.25); font-size:9px;">
        7 sections &nbsp;&middot;&nbsp; 56 questions
      </span><br>
      <span style="color:rgba(255,255,255,0.25); font-size:9px;">
        Drives: Financial Model, Scoring, Risk, Roadmap
      </span>
    </div>
    """)


def _sidebar_session_content() -> None:
    company = st.session_state.company_name or "—"
    geo = st.session_state.geography
    budget_str = f"${st.session_state.budget_usd_m:.0f}M"
    timeline = f"{st.session_state.timeline_months} months"

    st.html(f"""
    <div class="aia-sidebar-brand">
      <div class="aia-sidebar-brand-title">{company}</div>
      <div class="aia-sidebar-brand-sub" style="margin-top:6px;">
        {budget_str} &nbsp;&middot;&nbsp; {timeline}<br>{geo}
      </div>
    </div>
    """)

    if st.button("Reset Assessment", key="btn_reset", use_container_width=True):
        _reset_all()
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# WIZARD STEPPER NAV (HTML)
# ─────────────────────────────────────────────────────────────────────────────

def _render_stepper(current_page: int) -> None:
    """Render the horizontal stepper navigation bar."""
    steps_html = ""
    answers = st.session_state.get("discovery_answers", {})
    company = st.session_state.get("company_name", "")

    # Helper to check if a section has any answers
    def is_section_completed(page_idx: int) -> bool:
        if page_idx == 0:
            return bool(company)
        if 1 <= page_idx <= 4:
            section_id = f"S{page_idx}"
            # Check if any question in this section is answered
            for q_id, ans in answers.items():
                if q_id.startswith(section_id) and ans and ans != "" and ans != [] and ans != {"select": "", "text": ""}:
                    return True
            return False
        return False # Page 8 is never "completed" until generation

    for i, label in enumerate(STEPPER_LABELS):
        is_completed = is_section_completed(i)
        
        if i == current_page:
            cls = "active"
        elif is_completed:
            cls = "completed"
        else:
            cls = ""
            
        check = "✓" if is_completed else str(i + 1)
        steps_html += f"""
        <div class="aia-step-pill {cls}">
          <span class="aia-step-pill-check">{check}</span>
          <span class="aia-step-pill-label">{label}</span>
        </div>
        """

    st.html(f'<div class="aia-stepper-pills">{steps_html}</div>')

    # Progress bar calculation (Total 13 questions + 1 for company)
    total_answered = sum(
        1 for ans in answers.values()
        if ans and ans != "" and ans != [] and ans != {"select": "", "text": ""}
    )
    if company:
        total_answered += 1
        
    pct = int((total_answered / 14) * 100)
    st.html(
        f'<div class="aia-progress-bar-wrap">'
        f'<div class="aia-progress-bar-fill" style="width:{pct}%;"></div>'
        f'</div>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# QUESTION CARD RENDERER
# ─────────────────────────────────────────────────────────────────────────────

def _render_question_card(q: dict, section_color: str, current_page_answers: dict = None) -> tuple[str, any]:
    """Render a single question as a styled card. Returns (q_id, answer)."""
    
    # --- DYNAMIC INTELLIGENCE INJECTION ---
    # If the LLM fetched tailored options for this company and this question, overwrite them.
    intel = st.session_state.get("company_intel", {}).get("tailored_options", {})
    if q["id"] in intel and intel[q["id"]]:
        q = dict(q)  # clone to avoid modifying the static config globally
        q["options"] = intel[q["id"]]
        
    tags_html = "".join(f'<span class="aia-qcard-tag">{t}</span>' for t in q["tags"])

    st.html(f"""
    <div class="aia-qcard" style="border-left-color: {section_color};">
      <div class="aia-qcard-header">
        <span class="aia-qcard-id" style="background: {section_color};">{q["id"]}</span>
        <span class="aia-qcard-text">{q["text"]}</span>
      </div>
      <div class="aia-qcard-rationale">{q["rationale"]}</div>
      <div class="aia-qcard-tags">{tags_html}</div>
    </div>
    """)

    input_key = f"fi_{q['id']}"
    stored = st.session_state.discovery_answers.get(q["id"], "")
    answer = None

    if q["input_type"] == "text":
        answer = st.text_area(
            q["id"], value=stored if isinstance(stored, str) else "",
            placeholder="Type your response...", height=90,
            key=input_key, label_visibility="collapsed",
        ).strip()

    elif q["input_type"] == "single_select":
        opts = q.get("options", [])
        full = ["— Select —"] + opts
        idx = 0
        if stored and stored in opts:
            idx = full.index(stored)
        sel = st.selectbox(q["id"], full, index=idx, key=input_key, label_visibility="collapsed")
        answer = sel if sel != "— Select —" else ""

    elif q["input_type"] == "multi_select":
        opts = q.get("options", [])
        defaults = stored if isinstance(stored, list) else []
        defaults = [o for o in defaults if o in opts]
        answer = st.multiselect(q["id"], opts, default=defaults, key=input_key, label_visibility="collapsed")

    elif q["input_type"] == "select_text":
        opts = q.get("options", [])
        full = ["— Select —"] + opts
        c1, c2 = st.columns(2)
        with c1:
            sv = stored.get("select", "") if isinstance(stored, dict) else ""
            idx = full.index(sv) if sv in full else 0
            sel = st.selectbox(f"{q['id']}_s", full, index=idx, key=f"{input_key}_s", label_visibility="collapsed")
        with c2:
            tv = stored.get("text", "") if isinstance(stored, dict) else ""
            txt = st.text_input(f"{q['id']}_t", value=tv, placeholder="Elaborate...", key=f"{input_key}_t", label_visibility="collapsed")
        answer = {"select": sel if sel != "— Select —" else "", "text": txt.strip()}

    elif q["input_type"] == "dynamic_kpi_targets":
        # Read from live page answers to ensure immediate reactivity on the same page
        selected_kpis = []
        if current_page_answers and "Q1.1" in current_page_answers:
            selected_kpis = current_page_answers["Q1.1"]
        else:
            # Fallback to session state if rendering across pages (though S1 is all one page)
            selected_kpis = st.session_state.discovery_answers.get("Q1.1", [])
            
        if not selected_kpis:
            st.html('<div style="font-size:12px; color:var(--grey-400); padding:10px; background:rgba(0,0,0,0.05); border-radius:4px;">Please select Strategic Objectives above first.</div>')
            answer = {}
        else:
            answer = {}
            for kpi in selected_kpis:
                stored_val = stored.get(kpi, "") if isinstance(stored, dict) else ""
                val = st.text_input(
                    kpi, 
                    value=stored_val,
                    placeholder="e.g. Baseline $100M, Target +10%", 
                    key=f"{input_key}_{kpi}"
                ).strip()
                if val:
                    answer[kpi] = val

    st.html('<div style="height:4px;"></div>')
    return q["id"], answer


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 1: MULTI-PAGE WIZARD INTAKE FORM
# ─────────────────────────────────────────────────────────────────────────────

def render_intake_form() -> None:
    """
    Phase 1 — Multi-page wizard.
    Page 0: Company Identity
    Pages 1–7: Discovery sections S1–S7
    Page 8: Investment Scope (budget/timeline) + Generate
    """
    page = st.session_state.wizard_page

    # ── Stepper nav ───────────────────────────────────────────────────────────
    _render_stepper(page)

    # ── Page routing ──────────────────────────────────────────────────────────
    if page == 0:
        _page_company_identity()
    elif 1 <= page <= 4:
        section = SECTIONS[page - 1]
        _page_discovery_section(section)
    elif page == 5:
        _page_investment_scope()


# ─── Page 0: Company Identity ─────────────────────────────────────────────────

def _page_company_identity() -> None:
    st.html("""
    <div class="aia-section-intro">
      <div class="aia-section-intro-icon">🏢</div>
      <div class="aia-section-intro-id">STEP 1 OF 6</div>
      <div class="aia-section-intro-title">Company Identity</div>
      <div class="aia-section-intro-subtitle">Required — Enables peer benchmarking</div>
      <div class="aia-section-intro-desc">
        Select your company from the curated list for pre-loaded peer benchmarking context,
        or enter a custom name for unlisted entities.
      </div>
    </div>
    """)

    col_company, col_geo = st.columns([3, 2])

    with col_company:
        st.html('<span class="aia-field-label">Company Name</span>')
        st.html('<span class="aia-field-sublabel">Select your company or enter a custom name below.</span>')
        selected = st.selectbox("Company", FMCG_COMPANIES, key="fi_company_select", label_visibility="collapsed")
        
        company_changed = False
        if selected == "Other (type below)":
            company_name_raw = st.text_input(
                "Custom name", placeholder="Enter your company name...",
                key="fi_company_custom", label_visibility="collapsed",
            ).strip()
            st.html(
                '<div style="font-size:11px; color:var(--brand-primary); padding:6px 10px; '
                'line-height:1.5; border-left:3px solid var(--brand-primary); margin-top:4px; '
                'background:var(--pwc-orange-ghost);">'
                '⚠ External benchmark data is not available for unlisted entities. '
                'The thesis will use industry-level benchmarks and your self-reported inputs only.'
                '</div>'
            )
        elif selected == "— Select your company —":
            company_name_raw = ""
        else:
            company_name_raw = selected.split(" (")[0].strip()

        if company_name_raw and company_name_raw != st.session_state.company_name:
            company_changed = True

        if company_changed:
            with st.spinner(f"Fetching intelligence profile for {company_name_raw}..."):
                st.session_state.company_intel = generate_company_intelligence(company_name_raw)
            st.session_state.company_name = company_name_raw
            # Set default geography to the first one from intel
            st.session_state.geography = st.session_state.company_intel.get("geographies", GEOGRAPHY_OPTIONS)[0]
            st.rerun()

    with col_geo:
        st.html('<span class="aia-field-label">Primary Geography</span>')
        st.html('<span class="aia-field-sublabel">Where the majority of your revenue is generated.</span>')
        
        geo_opts = st.session_state.get("company_intel", {}).get("geographies", GEOGRAPHY_OPTIONS)
        if not geo_opts:
            geo_opts = GEOGRAPHY_OPTIONS
            
        geography = st.selectbox(
            "Geography", geo_opts, key="fi_geography", label_visibility="collapsed",
        )

    # Store immediately
    st.session_state.company_name = company_name_raw
    st.session_state.geography = geography

    # Navigation
    st.html('<div style="height:24px;"></div>')
    _, col_next = st.columns([3, 1])
    with col_next:
        if st.button("Next →  Strategy", key="btn_next_0", use_container_width=True):
            if not company_name_raw:
                st.error("Please select or enter a company name.")
            else:
                st.session_state.wizard_page = 1
                st.rerun()


# ─── Pages 1–7: Discovery Sections ───────────────────────────────────────────

def _page_discovery_section(section: dict) -> None:
    page = st.session_state.wizard_page
    section_idx = page - 1
    questions = get_questions_for_section(section["id"])

    # Section intro panel
    st.html(f"""
    <div class="aia-section-intro" style="border-left-color: {section['color']};">
      <div class="aia-section-intro-icon">{section['icon']}</div>
      <div class="aia-section-intro-id">STEP {page + 1} OF {TOTAL_PAGES} &nbsp;—&nbsp; {len(questions)} QUESTIONS</div>
      <div class="aia-section-intro-title">{section['title']}</div>
      <div class="aia-section-intro-subtitle">{section['subtitle']}</div>
      <div class="aia-section-intro-desc">{section['description']}</div>
    </div>
    """)

    # Render question cards
    page_answers: dict = {}
    for q in questions:
        q_id, answer = _render_question_card(q, section["color"], current_page_answers=page_answers)
        page_answers[q_id] = answer

    # Persist answers immediately
    current = dict(st.session_state.discovery_answers)
    current.update(page_answers)
    st.session_state.discovery_answers = current

    # Navigation
    st.html('<div style="height:16px;"></div>')
    col_prev, col_mid, col_next = st.columns([1, 2, 1])

    with col_prev:
        if st.button("← Previous", key=f"btn_prev_{page}", use_container_width=True):
            st.session_state.wizard_page = page - 1
            st.rerun()

    with col_mid:
        answered = sum(1 for v in page_answers.values() if v and v != "" and v != [] and v != {"select": "", "text": ""})
        st.html(
            f'<div style="text-align:center; font-size:11px; color:var(--grey-400); padding-top:10px;">'
            f'{answered} of {len(questions)} answered on this page'
            f'</div>'
        )

    with col_next:
        next_label = "Next →" if page < 4 else "Next →  Investment Scope"
        if st.button(next_label, key=f"btn_next_{page}", use_container_width=True):
            st.session_state.wizard_page = page + 1
            st.rerun()


# ─── Page 8: Investment Scope ─────────────────────────────────────────────────

def _page_investment_scope() -> None:
    page = st.session_state.wizard_page

    st.html("""
    <div class="aia-section-intro" style="border-left-color: #D04A02;">
      <div class="aia-section-intro-icon">💰</div>
      <div class="aia-section-intro-id">FINAL STEP — STEP 6 OF 6</div>
      <div class="aia-section-intro-title">Investment Scope</div>
      <div class="aia-section-intro-subtitle">Budget & Timeline — Asked last per consultant best practice</div>
      <div class="aia-section-intro-desc">
        Set your total transformation budget and delivery timeline.
        These parameters determine the portfolio allocation model and phased deployment schedule.
      </div>
    </div>
    """)

    col_budget, col_timeline = st.columns([3, 2])

    with col_budget:
        st.html('<span class="aia-field-label">Transformation Budget</span>')
        st.html('<span class="aia-field-sublabel">Total investment envelope (USD millions).</span>')
        budget_m = st.slider(
            "Budget", min_value=BUDGET_MIN_M, max_value=BUDGET_MAX_M,
            value=int(st.session_state.budget_usd_m), step=BUDGET_STEP_M,
            format="$%dM", key="fi_budget", label_visibility="collapsed",
        )
        st.html(
            f'<div style="font-size:26px; font-weight:800; color:var(--pwc-black); '
            f'letter-spacing:-0.02em; margin:-6px 0 0;">'
            f'<span style="font-size:15px; font-weight:400; color:var(--grey-400);">USD </span>'
            f'${budget_m}M</div>'
        )

    with col_timeline:
        st.html('<span class="aia-field-label">Target Timeline</span>')
        st.html('<span class="aia-field-sublabel">Programme delivery horizon.</span>')
        timeline_mo = st.slider(
            "Timeline", min_value=TIMELINE_MIN_MO, max_value=TIMELINE_MAX_MO,
            value=int(st.session_state.timeline_months), step=TIMELINE_STEP_MO,
            format="%d months", key="fi_timeline", label_visibility="collapsed",
        )
        st.html(
            f'<div style="font-size:26px; font-weight:800; color:var(--pwc-black); '
            f'letter-spacing:-0.02em; margin:-6px 0 0;">'
            f'{timeline_mo}<span style="font-size:15px; font-weight:400; color:var(--grey-400);"> months</span></div>'
        )

    st.html('<div style="height:24px;"></div>')

    # Navigation + Generate
    col_prev, col_hint, col_gen = st.columns([1, 2, 1])

    with col_prev:
        if st.button("← Previous", key="btn_prev_8", use_container_width=True):
            st.session_state.wizard_page = 4
            st.rerun()

    with col_hint:
        all_answers = st.session_state.discovery_answers
        total_answered = sum(
            1 for v in all_answers.values()
            if v and v != "" and v != [] and v != {"select": "", "text": ""}
        )
        st.html(
            f'<div style="text-align:center; font-size:11px; color:var(--grey-400); padding-top:10px;">'
            f'{total_answered} of 13 questions answered across all sections'
            f'</div>'
        )

    with col_gen:
        if st.button("Generate Investment Thesis  →", key="btn_generate", use_container_width=True):
            if total_answered < 5:
                st.error(f"Please answer at least 5 questions. Currently: {total_answered}.")
            else:
                _save_and_generate_thesis(
                    company_name=st.session_state.company_name,
                    geography=st.session_state.geography,
                    budget_usd_m=float(budget_m),
                    timeline_months=timeline_mo,
                    discovery_answers=dict(all_answers),
                )


# ─────────────────────────────────────────────────────────────────────────────
# THESIS GENERATION
# ─────────────────────────────────────────────────────────────────────────────

def _save_and_generate_thesis(
    company_name: str,
    geography: str,
    budget_usd_m: float,
    timeline_months: int,
    discovery_answers: dict,
) -> None:
    from engine.math_engine import build_investment_plan

    q11 = discovery_answers.get("Q1.1", [])
    if isinstance(q11, str):
        q11 = [q11]
    elif not q11:
        q11 = ["Grow revenue and market share fast"]

    _goal_map = {
        "Grow revenue and market share fast": "Revenue Growth",
        "Protect our profit margins from rising costs": "Margin Recovery",
        "Improve customer satisfaction dramatically": "Revenue Growth",
        "Cut operating expenses": "Enterprise Productivity",
        "Make the supply chain bulletproof": "Revenue Growth",
    }
    
    # Map and deduplicate goals
    primary_goals = list(set(_goal_map.get(ans, "Revenue Growth") for ans in q11))

    st.session_state.company_name = company_name
    st.session_state.geography = geography
    st.session_state.budget_usd_m = budget_usd_m
    st.session_state.budget_option = f"${int(budget_usd_m)}M"
    st.session_state.timeline_months = timeline_months
    st.session_state.primary_goals = primary_goals
    st.session_state.discovery_answers = discovery_answers

    with st.spinner("Generating your investment thesis..."):
        # NOTE: engine v2 reads every discovery answer by its correct ID internally
        # (complexity ← Q3.1/Q3.2/Q2.1, risk ← Q4.1/Q1.4/Q3.3, value ← Q1.2/Q2.3).
        # The text params below are vestigial and kept only for signature compatibility.
        # v1 mapped q3 to "Q5.2" — a question ID that does not exist — so the risk
        # modifier never fired. That bug is now moot because the engine ignores these.
        q1_text = _flatten(discovery_answers.get("Q1.5", ""))
        q2_text = _flatten(discovery_answers.get("Q3.1", ""))
        q3_text = _flatten(discovery_answers.get("Q4.1", ""))

        plan = build_investment_plan(
            budget_usd_m=budget_usd_m,
            primary_goals=primary_goals,
            timeline_months=timeline_months,
            q1_answer=q1_text,
            q2_answer=q2_text,
            q3_answer=q3_text,
            discovery_answers=discovery_answers,
        )

        flat_answers = {}
        for q in QUESTIONS:
            av = discovery_answers.get(q["id"], "")
            flat = _flatten(av)
            if flat:
                flat_answers[q["id"]] = flat

        payload, is_ai = generate_executive_summary(
            company_name=company_name,
            plan=plan,
            answers=flat_answers,
        )

        st.session_state.thesis_plan = plan
        st.session_state.thesis_payload = payload
        st.session_state.thesis_is_ai = is_ai
        st.session_state.thesis_generated = True
        st.session_state.app_phase = 3
        st.rerun()


def _flatten(val) -> str:
    if val is None:
        return ""
    if isinstance(val, str):
        return val
    if isinstance(val, list):
        return ", ".join(str(v) for v in val)
    if isinstance(val, dict):
        if "select" in val or "text" in val:
            parts = [v for v in [val.get("select", ""), val.get("text", "")] if v]
            return " — ".join(parts)
        else:
            return "; ".join(f"[{k}] {v}" for k, v in val.items() if v)
    return str(val)


# ─────────────────────────────────────────────────────────────────────────────
# RESET
# ─────────────────────────────────────────────────────────────────────────────

def _reset_all() -> None:
    keys_to_delete = [
        "company_name", "geography", "budget_option", "timeline_months",
        "budget_usd_m", "primary_goals", "discovery_answers", "wizard_page",
        "thesis_generated", "thesis_plan", "thesis_summary", "thesis_is_ai",
        "fi_company_select", "fi_company_custom", "fi_geography",
        "fi_budget", "fi_timeline",
    ]
    for key in list(st.session_state.keys()):
        if key.startswith("fi_"):
            keys_to_delete.append(key)
    for key in set(keys_to_delete):
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.app_phase = 1