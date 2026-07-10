"""
ui/landing.py

Landing page for the AI Investment Engine.
Renders as Phase 0: a concise C-suite overview before intake begins.
Design rules: one type scale (Georgia display / Arial body), one accent
color, no fabricated numbers, every claim true of the product.
"""

import streamlit as st

_HERO_BANNER_HTML = """
<div class="hz-hero-container">
    <div style="flex: 1.15; max-width: 620px;">
        <span class="hz-hero-pill-orange">BFSI &middot; AI INVESTMENT DIAGNOSTIC</span>
        <h1 style="font-family: var(--font-head); font-size: 46px; color: #FFFFFF; margin: 20px 0 16px; font-weight: bold; line-height: 1.12;">
            Where should your<br>next AI dollar go?
        </h1>
        <p style="font-family: var(--font-body); font-size: 16px; color: var(--g300); line-height: 1.55; margin-bottom: 28px; max-width: 520px;">
            A 15-minute diagnostic that turns your operating data into a board-ready
            AI investment plan: prioritised, budget-constrained, and traceable
            down to every constant in the model.
        </p>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <span class="hz-hero-badge">14 value levers</span>
            <span class="hz-hero-badge">3 execution scenarios</span>
            <span class="hz-hero-badge">IRDAI / RBI / SEBI overlay</span>
            <span class="hz-hero-badge">Fully auditable math</span>
        </div>
    </div>
    <div style="flex: 0.85; display: flex; justify-content: flex-end;">
        <div class="hz-hero-card">
            <div style="font-size: 10px; font-weight: bold; color: var(--g300); text-transform: uppercase; letter-spacing: 0.08em; border-bottom: 1px solid #333333; padding-bottom: 12px; margin-bottom: 4px;">
                What you receive
            </div>
            <div class="hz-hero-row">
                <span class="hz-hero-row-num">01</span>
                <div>
                    <div class="hz-hero-row-title">A prioritised, funded portfolio</div>
                    <div class="hz-hero-row-desc">Every AI use case scored on value and readiness, ranked against your budget</div>
                </div>
            </div>
            <div class="hz-hero-row">
                <span class="hz-hero-row-num">02</span>
                <div>
                    <div class="hz-hero-row-title">A verdict on your legacy estate</div>
                    <div class="hz-hero-row-desc">Keep, modernize in phases, or replace, with a bottom-up cost estimate and break-even</div>
                </div>
            </div>
            <div class="hz-hero-row" style="border-bottom: none;">
                <span class="hz-hero-row-num">03</span>
                <div>
                    <div class="hz-hero-row-title">A compliance-checked roadmap</div>
                    <div class="hz-hero-row-desc">Each use case screened against Indian regulatory constraints before it is funded</div>
                </div>
            </div>
            <div style="font-size: 10.5px; color: var(--g500); border-top: 1px solid #333333; padding-top: 12px; margin-top: 4px;">
                Every number traces back to your answers. Nothing is estimated silently.
            </div>
        </div>
    </div>
</div>
"""

_CAPABILITIES_HTML = """
<div style="text-align: center; margin: 56px 0 8px;">
    <div style="font-size: 11px; font-weight: bold; color: var(--pwc-orange); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px;">How it works</div>
    <h2 style="font-family: var(--font-head); font-size: 30px; color: var(--black); font-weight: bold; margin: 0;">From intake to board-ready plan in one session</h2>
</div>

<div style="display: flex; gap: 24px; margin: 32px 0 48px;">
    <div class="hz-step-card">
        <div class="hz-step-card-num">01</div>
        <div class="hz-step-card-title">Answer 16 questions</div>
        <div class="hz-step-card-desc">Your scale, operations, compliance posture and legacy footprint.
        Public data is pre-filled from cited sources; you confirm or correct it.</div>
    </div>
    <div class="hz-step-card">
        <div class="hz-step-card-num">02</div>
        <div class="hz-step-card-title">The engine computes</div>
        <div class="hz-step-card-desc">Deterministic financial models size each use case from your answers,
        haircut them for realism, and screen them against regulation.</div>
    </div>
    <div class="hz-step-card">
        <div class="hz-step-card-num">03</div>
        <div class="hz-step-card-title">Decide with evidence</div>
        <div class="hz-step-card-desc">A funded portfolio, a legacy verdict with break-even, and an
        executive memo, with every assumption on the table.</div>
    </div>
</div>

<div style="border-top: 1px solid var(--g200); padding-top: 16px; display: flex; justify-content: space-between; align-items: center;">
    <span style="font-family: var(--font-head); font-size: 22px; color: var(--pwc-orange); font-weight: bold;">pwc</span>
    <span style="font-size: 11px; color: var(--g500);">Deterministic math &middot; Sourced benchmarks &middot; Narrative by Gemini, grounded in the computed plan</span>
</div>
"""


def render_landing_page() -> None:
    """Render the landing hero and handle the intake initiation."""
    st.html(_HERO_BANNER_HTML)
    st.write("")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Begin the diagnostic", type="primary", use_container_width=True):
            st.session_state.app_phase = 1
            st.rerun()
        st.html('<div style="text-align:center; font-size:11.5px; color:var(--g500); margin-top:6px;">'
                'About 15 minutes &middot; No data leaves the session without your say</div>')

    st.html(_CAPABILITIES_HTML)
