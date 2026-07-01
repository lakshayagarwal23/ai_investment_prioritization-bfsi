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
    OBJECTIVE_INPUTS, OTHER_OPTION,
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

# Number of discovery questions (derived from config so counts never drift).
TOTAL_QUESTIONS = len(QUESTIONS)

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
      <div class="aia-sidebar-brand-title">Investment Prioritisation</div>
      <div class="aia-sidebar-brand-sub">
        Complete the intake questionnaire to generate your AI investment prioritisation.
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
    st.html(f"""
    <div style="font-size:10.5px; color:rgba(255,255,255,0.50); line-height:2.0;">
      <span style="color:rgba(255,255,255,0.25); font-size:9px;">
        {len(SECTIONS)} sections &nbsp;&middot;&nbsp; {TOTAL_QUESTIONS} questions
      </span><br>
      <span style="color:rgba(255,255,255,0.25); font-size:9px;">
        Drives: Financial Model, Scoring, Risk, Roadmap
      </span>
    </div>
    """)
    st.empty()


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
    
    st.empty()


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

    # Denominator = all discovery questions + 1 for the company step.
    pct = min(int((total_answered / (TOTAL_QUESTIONS + 1)) * 100), 100)
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
    <div class="aia-qcard">
      <div class="aia-qcard-header">
        <span class="aia-qcard-id">{q["id"]}</span>
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
        base_opts = q.get("options", [])
        opts = list(base_opts) + [OTHER_OPTION]
        full = ["— Select —"] + opts
        idx, custom_default = 0, ""
        if stored:
            if stored in full:
                idx = full.index(stored)
            else:  # a previously typed custom value
                idx = full.index(OTHER_OPTION)
                custom_default = stored
        sel = st.selectbox(q["id"], full, index=idx, key=input_key, label_visibility="collapsed")
        if sel == OTHER_OPTION:
            custom = st.text_input(
                f"{q['id']}_other", value=custom_default, placeholder="Please specify…",
                key=f"{input_key}_other", label_visibility="collapsed",
            ).strip()
            answer = custom
        else:
            answer = sel if sel != "— Select —" else ""

    elif q["input_type"] == "multi_select":
        base_opts = q.get("options", [])
        opts = list(base_opts) + [OTHER_OPTION]
        prior = stored if isinstance(stored, list) else []
        known = [o for o in prior if o in base_opts]
        custom_prior = [o for o in prior if o not in base_opts and o != OTHER_OPTION]
        defaults = known + ([OTHER_OPTION] if custom_prior else [])
        sel = st.multiselect(q["id"], opts, default=defaults, key=input_key, label_visibility="collapsed")
        chosen = [s for s in sel if s != OTHER_OPTION]
        if OTHER_OPTION in sel:
            custom = st.text_input(
                f"{q['id']}_other", value=", ".join(custom_prior),
                placeholder="Add your own (comma-separated)…",
                key=f"{input_key}_other", label_visibility="collapsed",
            ).strip()
            if custom:
                chosen += [c.strip() for c in custom.split(",") if c.strip()]
        answer = chosen

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
        # Structured, dynamic follow-ups per selected objective. Reading live page
        # answers keeps it reactive on the same page.
        selected_kpis = []
        if current_page_answers and "Q1.1" in current_page_answers:
            selected_kpis = current_page_answers["Q1.1"]
        else:
            selected_kpis = st.session_state.discovery_answers.get("Q1.1", [])

        if not selected_kpis:
            st.html('<div class="aia-kpi-empty">'
                    'Select your strategic objectives in Q1.1 above, and tailored '
                    'baseline &amp; target inputs will appear here automatically.</div>')
            answer = {}
        else:
            answer = {}
            for kpi in selected_kpis:
                cfg = OBJECTIVE_INPUTS.get(kpi)
                stored_obj = stored.get(kpi, {}) if isinstance(stored, dict) and isinstance(stored.get(kpi), dict) else {}
                st.html(f'<div class="aia-kpi-obj-label">{kpi}</div>')

                if cfg is None:  # a custom "Other" objective
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        amt = st.number_input(
                            "Current baseline value (USD M)", min_value=0.0,
                            value=float(stored_obj.get("amount_usd_m", 0.0) or 0.0), step=10.0,
                            key=f"{input_key}_{kpi}_amt", label_visibility="collapsed")
                    with c2:
                        tgt = st.slider("Target improvement (%)", 0, 30,
                                        int(stored_obj.get("target_pct", 5) or 5),
                                        key=f"{input_key}_{kpi}_tgt", label_visibility="collapsed")
                    answer[kpi] = {"category": "", "amount_usd_m": float(amt),
                                   "target_pct": float(tgt), "amount_is_money": True, "engine": "custom"}
                    continue

                cat_opts = cfg.get("category_options") or []
                suffix = cfg.get("target_suffix", "%")
                fmt = "%d%%" if suffix == "%" else "%d" + suffix
                cols = st.columns(3 if cat_opts else 2)
                ci, category = 0, ""
                if cat_opts:
                    with cols[ci]:
                        cat_default = stored_obj.get("category", cat_opts[0])
                        if cat_default not in cat_opts:
                            cat_default = cat_opts[0]
                        category = st.selectbox(cfg["category_label"], cat_opts,
                                                index=cat_opts.index(cat_default),
                                                key=f"{input_key}_{kpi}_cat")
                    ci += 1
                with cols[ci]:
                    amt = st.number_input(
                        cfg["amount_label"], min_value=0.0,
                        value=float(stored_obj.get("amount_usd_m", cfg["amount_default"]) or cfg["amount_default"]),
                        step=10.0, key=f"{input_key}_{kpi}_amt")
                    ci += 1
                with cols[ci]:
                    tgt = st.slider(cfg["target_label"], 0, cfg["target_max"],
                                    int(stored_obj.get("target_pct", cfg["target_default"]) or cfg["target_default"]),
                                    format=fmt, key=f"{input_key}_{kpi}_tgt")
                answer[kpi] = {"category": category, "amount_usd_m": float(amt),
                               "target_pct": float(tgt),
                               "amount_is_money": cfg.get("amount_is_money", True),
                               "engine": cfg["engine"]}

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

    if page > 0:
        company = st.session_state.get("company_name", "Unknown Company")
        geo = st.session_state.get("geography", "Global")
        # Generate dynamic initials for the logo
        words = company.replace("&", "").replace("-", " ").split()
        if not words:
            initials = "C"
        elif len(words) == 1:
            initials = words[0][:2].upper()
        else:
            initials = (words[0][0] + words[1][0]).upper()
        
        st.html(f"""
        <div style="background: var(--white); border: 1px solid var(--ink-150); border-radius: 12px; padding: 20px 24px; margin-bottom: 24px; margin-top: 10px; display: flex; justify-content: space-between; align-items: center; box-shadow: var(--sh-sm);">
            <div style="display: flex; align-items: center; gap: 16px;">
                <div style="width: 52px; height: 52px; border-radius: 10px; background: linear-gradient(135deg, var(--ink-900) 0%, var(--ink-700) 100%); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 22px; font-weight: 800; font-family: Georgia, serif; letter-spacing: 0.05em; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                    {initials}
                </div>
                <div>
                    <div style="font-size: 10.5px; font-weight: 700; color: var(--ink-400); letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 4px;">Target Enterprise</div>
                    <div style="font-size: 24px; font-weight: 800; color: var(--ink-900); font-family: Georgia, serif; line-height: 1;">{company}</div>
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 10.5px; font-weight: 700; color: var(--ink-400); letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 6px;">Operating Region</div>
                <div style="display: inline-block; background: var(--ink-50); border: 1px solid var(--ink-200); padding: 4px 12px; border-radius: 999px; font-size: 12.5px; font-weight: 600; color: var(--ink-700);">
                    <span style="color:var(--brand); margin-right:4px;">●</span>{geo}
                </div>
            </div>
        </div>
        """)

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
        
        # --- For Company Selection ---
        current_company = st.session_state.get("company_name", "")
        default_idx = 0
        if current_company:
            for i, opt in enumerate(FMCG_COMPANIES):
                if current_company in opt:
                    default_idx = i
                    break

        selected = st.selectbox("Company", FMCG_COMPANIES, index=default_idx, key="fi_company_select", label_visibility="collapsed")
        
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
                'Note: External benchmark data is not available for unlisted entities. '
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
            
        # --- For Geography Selection ---
        current_geo = st.session_state.get("geography", geo_opts[0])
        geo_idx = 0
        if current_geo in geo_opts:
            geo_idx = geo_opts.index(current_geo)
            
        geography = st.selectbox(
            "Geography", geo_opts, index=geo_idx, key="fi_geography", label_visibility="collapsed",
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
    <div class="aia-section-intro">
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
    <div class="aia-section-intro">
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
        st.html('<span class="aia-field-label">AI Transformation Budget</span>')
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
            f'{total_answered} of {TOTAL_QUESTIONS} questions answered across all sections'
            f'</div>'
        )

    with col_gen:
        all_answers = st.session_state.discovery_answers
        
        tensions = _evaluate_strategic_tensions(all_answers, budget_m, timeline_mo)
        if tensions:
            st.html('<div style="font-size:11px; font-weight:700; color:var(--ink-500); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Programme Validation</div>')
            for t in tensions:
                st.warning(t, icon="⚠️")
            st.html('<div style="height:12px;"></div>')

        if st.button("Generate AI Investment Prioritisation  →", key="btn_generate", use_container_width=True):
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
# STRATEGIC TENSIONS VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

def _evaluate_strategic_tensions(answers: dict, budget_m: float, timeline_mo: int) -> list[str]:
    tensions = []
    
    payback = answers.get("Q1.3", "")
    erp = answers.get("Q3.1", "")
    cloud = answers.get("Q3.2", "")
    adoption = answers.get("Q4.1", "")
    goals = answers.get("Q1.1", [])
    if isinstance(goals, str): 
        goals = [goals]
    si = answers.get("Q4.3", "")

    # 1. Payback vs Timeline
    if "Under 12 months" in payback and timeline_mo > 12:
        tensions.append(f"**Tension Detected:** Your programme spans {timeline_mo} months, but you demand a payback of under 12 months. This requires aggressive quick-wins in Phase 1 to self-fund later phases.")
        
    # 2. Tech Debt vs Timeline
    if ("fragmented" in erp.lower() or "old, slow local servers" in cloud.lower() or "Complete lack" in erp) and timeline_mo <= 12:
        tensions.append(f"**Risk Flag:** You have a highly fragmented or legacy data estate, but a tight timeline ({timeline_mo} months). Data consolidation alone typically takes 9-15 months.")
        
    # 3. Change Management vs Goals
    aggressive_goals = any(g in ["Accelerate revenue and market share growth", "Preserve and expand operating margins"] for g in goals)
    if ("voluntary" in adoption.lower() or "no strategy" in adoption.lower()) and aggressive_goals:
        tensions.append("**Execution Risk:** You are targeting aggressive value creation, but field adoption is voluntary. Value realization will likely stall without mandated KPIs.")
        
    # 4. Delivery Model vs Budget
    if "External Systems Integrator" in si and budget_m <= 25:
        tensions.append(f"**Budget Warning:** External SIs carry a ~30-40% delivery premium. With a budget of ${int(budget_m)}M, high overhead may consume your capital before value-generating use cases are built.")
        
    return tensions


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
    from storage.audit import log_run

    q11 = discovery_answers.get("Q1.1", [])
    if isinstance(q11, str):
        q11 = [q11]
    elif not q11:
        q11 = ["Accelerate revenue and market share growth"]

    _goal_map = {
        "Accelerate revenue and market share growth": "Revenue Growth",
        "Preserve and expand operating margins": "Margin Recovery",
        "Enhance customer experience and satisfaction": "Revenue Growth",
        "Optimize operating expenses and efficiency": "Enterprise Productivity",
        "Build a resilient and agile supply chain": "Margin Recovery",
    }
    
    # Map and deduplicate goals
    primary_goals = list(dict.fromkeys(_goal_map.get(ans, "Revenue Growth") for ans in q11))

    st.session_state.company_name = company_name
    st.session_state.geography = geography
    st.session_state.budget_usd_m = budget_usd_m
    st.session_state.budget_option = f"${int(budget_usd_m)}M"
    st.session_state.timeline_months = timeline_months
    st.session_state.primary_goals = primary_goals
    st.session_state.discovery_answers = discovery_answers

    with st.spinner("Generating your AI investment prioritisation..."):
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

        mode = "LLM" if is_ai else "deterministic"
        mode = "deterministic_by_policy" if payload.get("executive_decision", {}).get("mode_override") == "deterministic_by_policy" else mode
        run_id = log_run(
            company=company_name,
            inputs=discovery_answers,
            plan=plan,
            payload=payload,
            mode=mode,
        )

        st.session_state.run_id = run_id
        st.session_state.report_mode = mode
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
        # Structured per-objective inputs (Q1.2): {objective: {category, amount_usd_m, target_pct}}
        if any(isinstance(v, dict) and "amount_usd_m" in v for v in val.values()):
            lines = []
            for obj, d in val.items():
                if not isinstance(d, dict):
                    continue
                cat = f" ({d['category']})" if d.get("category") else ""
                amt = d.get("amount_usd_m", 0)
                unit = "USD M" if d.get("amount_is_money", True) else "pts/score"
                tgt = d.get("target_pct", 0)
                lines.append(f"{obj}{cat}: baseline {amt:g} {unit}, target {tgt:g}%")
            return "; ".join(lines)
        return "; ".join(f"[{k}] {v}" for k, v in val.items() if v)
    return str(val)


# ─────────────────────────────────────────────────────────────────────────────
# RESET
# ─────────────────────────────────────────────────────────────────────────────

def _reset_all() -> None:
    keys_to_delete = [
        "company_name", "geography", "budget_option", "timeline_months",
        "budget_usd_m", "primary_goals", "discovery_answers", "wizard_page",
        "thesis_generated", "thesis_plan", "thesis_payload", "thesis_summary", "thesis_is_ai",
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