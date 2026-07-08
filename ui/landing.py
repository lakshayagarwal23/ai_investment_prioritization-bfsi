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

_HERO_HTML = """
<div class="hz-landing">
    <div style="font-family: var(--font-body); font-size: 11px; font-weight: 600; color: var(--g500); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: var(--sp-4);">
        BFSI / Asset Management &nbsp;·&nbsp; Strategic Intelligence
    </div>
    <h1 class="hz-landing-h1">
        AI investment prioritisation &mdash;<br>
        <span style="color: var(--pwc-orange);">BFSI diagnostic</span>
    </h1>
    <p class="hz-landing-desc">
        Bottom-up capital allocation for Asset Management transformation programmes.<br>
        Peer-benchmarked. Risk-adjusted. Board-ready.
    </p>

    <div class="hz-feat-grid">
        <div class="hz-feat-col">
            <div class="hz-feat-col-title">Peer Benchmarks</div>
            <div class="hz-feat-col-desc">Capital allocation triangulated against 10+ public BFSI leaders including BlackRock, Vanguard, and Fidelity.</div>
        </div>
        <div class="hz-feat-col">
            <div class="hz-feat-col-title">Bottom-Up Financials</div>
            <div class="hz-feat-col-desc">Line-item deployment across 30+ AI use cases with traceable ROI assumptions.</div>
        </div>
        <div class="hz-feat-col">
            <div class="hz-feat-col-title">Risk-Adjusted</div>
            <div class="hz-feat-col-desc">Data fragmentation and organisational resistance automatically widen confidence intervals.</div>
        </div>
    </div>
    
    <div style="margin-top: var(--sp-12); border-top: 1px solid var(--g200); padding-top: var(--sp-4);">
        <span style="font-family: var(--font-head); font-size: 24px; color: var(--pwc-orange); font-weight: bold;">pwc</span>
    </div>
</div>
"""

def render_landing_page() -> None:
    """Render the landing hero and handle the intake initiation."""
    st.html(_HERO_HTML)
    
    col1, col2, _ = st.columns([1, 1, 2])
    with col1:
        st.write("") 
        st.write("") 
        if st.button("Begin Diagnostic", type="primary", use_container_width=True):
            st.session_state.app_phase = 1
            st.rerun()

    with col2:
        # P0: Removed the fake metrics, keep it simple.
        pass
