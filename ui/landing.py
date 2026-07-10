"""
ui/landing.py

Landing page for the AI Investment Engine.
Renders as Phase 0 — concise C-suite overview before intake begins.
"""

import streamlit as st

_HERO_BANNER_HTML = """
<div class="hz-hero-container">
    <div style="flex: 1.2;">
        <span class="hz-hero-pill-orange">BFSI &middot; STRATEGIC INTELLIGENCE V5.0</span>
        <h1 style="font-family: var(--font-head); font-size: 48px; color: #FFFFFF; margin-top: 16px; margin-bottom: 16px; font-weight: bold; line-height: 1.1;">
            AI Investment<br><span style="color: var(--pwc-orange);">Prioritisation</span>
        </h1>
        <p style="font-size: 16px; color: var(--g300); line-height: 1.4; margin-bottom: 24px;">
            Bottom-up capital allocation for Asset & Wealth Management transformation programmes.<br>
            Peer-benchmarked. Risk-adjusted. Board-ready.
        </p>
        <div style="display: flex; gap: var(--sp-2); flex-wrap: wrap;">
            <span class="hz-hero-badge">Bottom-Up Financial Modeling</span>
            <span class="hz-hero-badge">14 Peer Levers</span>
            <span class="hz-hero-badge">Risk-Adjusted Projections</span>
            <span class="hz-hero-badge">Gemini AI Intel</span>
        </div>
    </div>
    <div style="flex: 0.8; display: flex; justify-content: flex-end;">
        <div class="hz-hero-card">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #333333; padding-bottom: 12px; margin-bottom: 16px;">
                <span style="font-size: 10px; font-weight: bold; color: var(--g300); text-transform: uppercase; letter-spacing: 0.05em;">● AI Investment Prioritisation</span>
                <span style="background: #2a1e17; color: var(--pwc-orange); border: 1px solid var(--pwc-orange); font-size: 9px; font-weight: bold; padding: 2px 6px; border-radius: 2px;">WHAT YOU GET</span>
            </div>
            <div style="display: flex; gap: var(--sp-2); margin-bottom: 16px;">
                <div class="hz-hero-mini-card">
                    <div style="font-size: 16px; font-weight: bold; color: #FFFFFF;">14</div>
                    <div style="font-size: 8px; color: var(--g300); text-transform: uppercase;">Value Levers</div>
                </div>
                <div class="hz-hero-mini-card">
                    <div style="font-size: 16px; font-weight: bold; color: #FFFFFF;">3</div>
                    <div style="font-size: 8px; color: var(--g300); text-transform: uppercase;">Scenarios</div>
                </div>
                <div class="hz-hero-mini-card">
                    <div style="font-size: 16px; font-weight: bold; color: #FFFFFF;">100%</div>
                    <div style="font-size: 8px; color: var(--g300); text-transform: uppercase;">Auditable Math</div>
                </div>
            </div>
            <div style="font-size: 10px; color: var(--g300); text-transform: uppercase; margin-bottom: 8px; font-weight: bold;">Board-Ready Outputs</div>
            <div style="display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 6px;">
                <span style="color: #FFFFFF;">● Budget-constrained prioritisation matrix</span>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 6px;">
                <span style="color: #FFFFFF;">● Legacy kill / modernize / hold verdict</span>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 11px;">
                <span style="color: #FFFFFF;">● IRDAI / RBI / SEBI compliance overlay</span>
            </div>
        </div>
    </div>
</div>
"""

_CAPABILITIES_HTML = """
<div style="text-align: center; margin-top: 48px; margin-bottom: 24px;">
    <div style="font-size: 11px; font-weight: bold; color: var(--pwc-orange); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px;">Platform Capabilities</div>
    <h2 style="font-family: var(--font-head); font-size: 32px; color: var(--black); font-weight: bold; margin: 0;">From intake to board-ready thesis. One session.</h2>
</div>

<div style="display: flex; gap: var(--sp-6); margin-top: 24px; margin-bottom: 48px;">
    <div style="flex: 1; padding: 24px; border: 1px solid var(--g200); border-radius: 4px;">
        <div style="font-family: var(--font-head); font-size: 36px; color: var(--pwc-orange); opacity: 0.3; margin-bottom: 12px; line-height: 1;">01</div>
        <div style="font-family: var(--font-head); font-size: 16px; font-weight: bold; color: var(--black); margin-bottom: 6px;">Strategic Intake</div>
        <div style="font-size: 13px; color: var(--g700); line-height: 1.4;">Calibrate baseline KPIs, tech stack maturity, compliance posture, and legacy footprint.</div>
    </div>
    <div style="flex: 1; padding: 24px; border: 1px solid var(--g200); border-radius: 4px;">
        <div style="font-family: var(--font-head); font-size: 36px; color: var(--pwc-orange); opacity: 0.3; margin-bottom: 12px; line-height: 1;">02</div>
        <div style="font-family: var(--font-head); font-size: 16px; font-weight: bold; color: var(--black); margin-bottom: 6px;">Scenario Evaluation</div>
        <div style="font-size: 13px; color: var(--g700); line-height: 1.4;">Evaluate multi-year realization curves, platform prerequisites, and governance constraints.</div>
    </div>
    <div style="flex: 1; padding: 24px; border: 1px solid var(--g200); border-radius: 4px;">
        <div style="font-family: var(--font-head); font-size: 36px; color: var(--pwc-orange); opacity: 0.3; margin-bottom: 12px; line-height: 1;">03</div>
        <div style="font-family: var(--font-head); font-size: 16px; font-weight: bold; color: var(--black); margin-bottom: 6px;">Executive Output</div>
        <div style="font-size: 13px; color: var(--g700); line-height: 1.4;">Produce a prioritized investment roadmap, legacy verdicts, and strategic C-suite memo.</div>
    </div>
</div>

<div style="margin-top: 48px; border-top: 1px solid var(--g200); padding-top: 16px; display: flex; justify-content: space-between; align-items: center;">
    <span style="font-family: var(--font-head); font-size: 24px; color: var(--pwc-orange); font-weight: bold;">pwc</span>
    <span style="font-size: 11px; color: var(--g500);">Powered by Gemini 2.5 Flash &middot; 14 BFSI Value Pools &middot; v5.1.0</span>
</div>
"""

def render_landing_page() -> None:
    """Render the landing hero and handle the intake initiation."""
    st.html(_HERO_BANNER_HTML)
    st.write("")
    
    # Centered wide assessment button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Begin Assessment →", type="primary", use_container_width=True):
            st.session_state.app_phase = 1
            st.rerun()

    st.html(_CAPABILITIES_HTML)
