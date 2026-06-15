"""
ui/landing.py

Landing page for the AI Investment Engine.
Renders as Phase 0 — concise C-suite overview before intake begins.
"""

import streamlit as st


# ─────────────────────────────────────────────────────────────────────────────
# HTML SECTIONS
# ─────────────────────────────────────────────────────────────────────────────

_HERO_HTML = """
<div class="lp-hero">
  <div class="lp-hero-left">
    <div class="lp-badge">FMCG / CPG &nbsp;&middot;&nbsp; STRATEGIC INTELLIGENCE v1.0</div>
    <h1 class="lp-h1">
      AI Investment<br>
      <span class="lp-h1-accent">Engine</span>
    </h1>
    <p class="lp-tagline">
      Bottom-up capital allocation for FMCG transformation programmes.
      Peer-benchmarked. Risk-adjusted. Board-ready.
    </p>
    <div class="lp-tag-row">
      <span class="lp-tag">Bottom-Up Financial Modeling</span>
      <span class="lp-tag">10+ Peer Benchmarks</span>
      <span class="lp-tag">Risk-Adjusted Projections</span>
      <span class="lp-tag">GPT-4o Intelligence</span>
    </div>
  </div>
  <div class="lp-hero-right">
    <div class="lp-dashboard-mock">
      <div class="lp-mock-topbar">
        <div class="lp-mock-dot"></div>
        <div class="lp-mock-topbar-title">Investment Thesis</div>
        <div class="lp-mock-topbar-badge">GENERATED</div>
      </div>
      <div class="lp-mock-kpi-row">
        <div class="lp-mock-kpi lp-kpi-orange">
          <div class="lp-mock-kpi-num">185%</div>
          <div class="lp-mock-kpi-lbl">Portfolio ROI</div>
        </div>
        <div class="lp-mock-kpi lp-kpi-blue">
          <div class="lp-mock-kpi-num">21mo</div>
          <div class="lp-mock-kpi-lbl">Payback</div>
        </div>
        <div class="lp-mock-kpi lp-kpi-green">
          <div class="lp-mock-kpi-num">&plusmn;20%</div>
          <div class="lp-mock-kpi-lbl">Confidence</div>
        </div>
      </div>
      <div class="lp-mock-chart-area">
        <div class="lp-mock-chart-bar-wrap"><div class="lp-mock-chart-bar" style="height:62%"></div><div class="lp-mock-chart-bar-lbl">Rev.</div></div>
        <div class="lp-mock-chart-bar-wrap"><div class="lp-mock-chart-bar lp-bar-orange" style="height:40%"></div><div class="lp-mock-chart-bar-lbl">Found.</div></div>
        <div class="lp-mock-chart-bar-wrap"><div class="lp-mock-chart-bar" style="height:55%"></div><div class="lp-mock-chart-bar-lbl">Ops.</div></div>
      </div>
      <div class="lp-mock-ledger">
        <div class="lp-mock-ledger-hdr">
          <span>Use Case</span><span>Allocation</span>
        </div>
        <div class="lp-mock-ledger-row">
          <span class="lp-mock-ledger-dot lp-dot-orange"></span>
          <span class="lp-mock-ledger-name">Demand Sensing AI</span>
          <span class="lp-mock-ledger-val">$18.5M</span>
        </div>
        <div class="lp-mock-ledger-row lp-mock-ledger-alt">
          <span class="lp-mock-ledger-dot lp-dot-blue"></span>
          <span class="lp-mock-ledger-name">Data Platform</span>
          <span class="lp-mock-ledger-val">$30.0M</span>
        </div>
        <div class="lp-mock-ledger-row">
          <span class="lp-mock-ledger-dot lp-dot-green"></span>
          <span class="lp-mock-ledger-name">Trade Promo Opt.</span>
          <span class="lp-mock-ledger-val">$14.2M</span>
        </div>
      </div>
    </div>
  </div>
</div>
"""

_OVERVIEW_HTML = """
<div class="lp-section lp-white">
  <div class="lp-sect-header">
    <div class="lp-sect-eyebrow">PLATFORM CAPABILITIES</div>
    <div class="lp-sect-h2">From intake to board-ready thesis. One session.</div>
  </div>
  <div class="lp-grid-3">
    <div class="lp-feat-card" style="border: 1px solid var(--border); padding: 24px;">
      <div class="lp-feat-title" style="margin-top: 0; color: var(--pwc-orange);">01 &nbsp;&middot;&nbsp; Peer Benchmarks</div>
      <div class="lp-feat-desc">
        Capital allocation triangulated against 10+ public FMCG leaders including P&G, Nestle, and Unilever.
      </div>
    </div>
    <div class="lp-feat-card" style="border: 1px solid var(--border); padding: 24px;">
      <div class="lp-feat-title" style="margin-top: 0; color: var(--blue);">02 &nbsp;&middot;&nbsp; Bottom-Up Financials</div>
      <div class="lp-feat-desc">
        Line-item deployment across 30+ AI use cases with traceable ROI assumptions.
      </div>
    </div>
    <div class="lp-feat-card" style="border: 1px solid var(--border); padding: 24px;">
      <div class="lp-feat-title" style="margin-top: 0; color: var(--pwc-red);">03 &nbsp;&middot;&nbsp; Risk-Adjusted</div>
      <div class="lp-feat-desc">
        Data fragmentation and organisational resistance automatically widen confidence intervals.
      </div>
    </div>
  </div>
</div>
"""

_PEER_STRIP_HTML = """
<div class="lp-peer-strip">
  <div class="lp-peer-strip-label">PEER INTELLIGENCE CORPUS</div>
  <div class="lp-peer-strip-logos">
    <span class="lp-peer-name">Procter &amp; Gamble</span>
    <span class="lp-peer-sep">&middot;</span>
    <span class="lp-peer-name">Nestle</span>
    <span class="lp-peer-sep">&middot;</span>
    <span class="lp-peer-name">Unilever</span>
    <span class="lp-peer-sep">&middot;</span>
    <span class="lp-peer-name">Coca-Cola</span>
    <span class="lp-peer-sep">&middot;</span>
    <span class="lp-peer-name">Mondelez</span>
    <span class="lp-peer-sep">&middot;</span>
    <span class="lp-peer-name">Reckitt Benckiser</span>
    <span class="lp-peer-sep">&middot;</span>
    <span class="lp-peer-name">Colgate-Palmolive</span>
    <span class="lp-peer-sep">&middot;</span>
    <span class="lp-peer-name">Danone</span>
    <span class="lp-peer-sep">&middot;</span>
    <span class="lp-peer-name">Marico</span>
    <span class="lp-peer-sep">&middot;</span>
    <span class="lp-peer-name">ITC</span>
  </div>
</div>
"""

_DISCLAIMER_HTML = """
<div class="lp-footer-disc">
  <strong>Disclaimer:</strong> Output is intended for strategic planning and executive discussion.
  Financial projections are derived from publicly available FMCG industry benchmark data and
  should be validated against internal actuals before board submission.
</div>
"""


# ─────────────────────────────────────────────────────────────────────────────
# RENDER FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def render_landing_page() -> None:
    """
    Render the complete landing page. Phase 0.
    """
    # Hero section
    st.html(_HERO_HTML)

    # Primary CTA
    _, col_cta, _ = st.columns([1, 2, 1])
    with col_cta:
        if st.button(
            "Begin Assessment  \u2192",
            key="btn_begin_top",
            use_container_width=True,
        ):
            st.session_state.app_phase = 1
            st.rerun()

    # Informational sections
    st.html(_OVERVIEW_HTML)
    st.html(_PEER_STRIP_HTML)

    st.html('<div style="height: 32px;"></div>')
    st.html(_DISCLAIMER_HTML)
