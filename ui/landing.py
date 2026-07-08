"""
ui/landing.py

Landing page for the AI Investment Engine.
Renders as Phase 0 — concise C-suite overview before intake begins.
"""

import streamlit as st
from llm.search_client import extract_company_data

# ─────────────────────────────────────────────────────────────────────────────
# HTML SECTIONS (PwC Horizon Redesign)
# ─────────────────────────────────────────────────────────────────────────────

_HERO_HTML_TOP = """
<div class="hz-landing" style="padding-bottom: var(--sp-4);">
    <div style="font-family: var(--font-body); font-size: 11px; font-weight: 600; color: var(--g500); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: var(--sp-4);">
        BFSI / Asset Management &nbsp;·&nbsp; Strategic Intelligence
    </div>
    <h1 class="hz-landing-h1">
        AI investment prioritisation &mdash;<br>
        <span style="color: var(--pwc-orange);">BFSI diagnostic</span>
    </h1>
    <p class="hz-landing-desc" style="margin-bottom: var(--sp-4);">
        Bottom-up capital allocation for Asset Management transformation programmes.<br>
        Peer-benchmarked. Risk-adjusted. Board-ready.
    </p>
</div>
"""

_HERO_HTML_BOTTOM = """
<div class="hz-landing" style="padding-top: var(--sp-6);">
    <div class="hz-feat-grid" style="margin-top: 0;">
        <div class="hz-feat-col">
            <div class="hz-feat-col-title">Peer Benchmarks</div>
            <div class="hz-feat-col-desc">Capital allocation triangulated against 10+ public BFSI leaders including BlackRock, Vanguard, and HDFC.</div>
        </div>
        <div class="hz-feat-col">
            <div class="hz-feat-col-title">Bottom-Up Financials</div>
            <div class="hz-feat-col-desc">Line-item deployment across 14 distinct BFSI use cases with traceable ROI assumptions.</div>
        </div>
        <div class="hz-feat-col">
            <div class="hz-feat-col-title">Risk-Adjusted</div>
            <div class="hz-feat-col-desc">Data fragmentation and organisational resistance automatically adjust execution feasibility.</div>
        </div>
    </div>
    
    <div style="margin-top: var(--sp-10); border-top: 1px solid var(--g200); padding-top: var(--sp-6);">
        <div style="font-family: var(--font-head); font-size: 20px; color: var(--black); margin-bottom: var(--sp-4);">How It Works</div>
        <div style="display: flex; gap: var(--sp-6); font-size: 13px; line-height: 1.4; color: var(--g700);">
            <div style="flex:1;">
                <strong style="color: var(--pwc-orange); font-family: var(--font-head); font-size: 16px;">1. Strategic Intake</strong><br>
                Calibrate baseline KPIs, operations, regulatory posture, and legacy system context in 7 quick steps.
            </div>
            <div style="flex:1;">
                <strong style="color: var(--pwc-orange); font-family: var(--font-head); font-size: 16px;">2. Scenario Evaluation</strong><br>
                The engine applies multi-year benefit realization curves and data constraint penalties.
            </div>
            <div style="flex:1;">
                <strong style="color: var(--pwc-orange); font-family: var(--font-head); font-size: 16px;">3. Executive Output</strong><br>
                Produce a board-ready prioritization matrix, custom implementation roadmap, and strategic executive memo.
            </div>
        </div>
    </div>

    <div style="margin-top: var(--sp-12); border-top: 1px solid var(--g200); padding-top: var(--sp-4); display: flex; justify-content: space-between; align-items: center;">
        <span style="font-family: var(--font-head); font-size: 24px; color: var(--pwc-orange); font-weight: bold;">pwc</span>
        <span style="font-size: 11px; color: var(--g500);">Powered by Gemini 2.5 Flash &middot; 14 BFSI Value Pools &middot; v4.0.0</span>
    </div>
</div>
"""

def render_landing_page() -> None:
    """Render the landing hero and handle the intake initiation."""
    st.html(_HERO_HTML_TOP)
    
    import os
    if not os.environ.get("GEMINI_API_KEY") and not st.session_state.get("gemini_api_key"):
        st.html("""
        <div style="background: var(--orange-tint); border: 1px solid var(--pwc-orange); padding: var(--sp-4); border-radius: var(--radius-card); margin-bottom: var(--sp-4);">
            <strong style="color: var(--pwc-orange);">LLM Narrative & Search Prefill Enabled</strong><br>
            <span style="font-size: 13px; color: var(--g700);">Provide a Gemini API Key to activate web scraping and executive summary generation.</span>
        </div>
        """)
        api_key_val = st.text_input("Gemini API Key", type="password", key="gemini_key_input")
        if api_key_val:
            st.session_state.gemini_api_key = api_key_val
            st.rerun()
            
    # Left align the button within the landing container limit
    col1, _ = st.columns([1, 3])
    with col1:
        if st.button("Begin Diagnostic", type="primary", use_container_width=True):
            st.session_state.app_phase = 1
            st.rerun()

    st.html(_HERO_HTML_BOTTOM)
