"""
ui/theme.py
PwC-inspired visual theme for the AI Investment Advisory Platform.
Injects custom CSS that overrides Streamlit defaults and defines
reusable component classes for the consulting-grade dashboard.
"""

import streamlit as st


def inject_theme() -> None:
    """Inject the full CSS theme into the Streamlit app."""
    st.html(_THEME_CSS)


def render_header() -> None:
    """Render the branded top header bar."""
    st.html(_HEADER_HTML)


_THEME_CSS = """
<style>
/* ── FONT ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
    /* Dynamic Brand Colors */
    --brand-primary:     #FF5A00;
    --brand-primary-ghost: rgba(255, 90, 0, 0.08);
    --brand-gradient:    linear-gradient(135deg, #FF5A00 0%, #FF8E53 100%);
    
    --pwc-black:         #1A1A1A;
    --grey-text:         #5A5A5A;
    --grey-label:        #8E8E8E;
    --grey-border:       #EAEAEA;
    --grey-border-light: #F0F0F0;
    --surface-bg:        #FDFDFD;
    --white:             #FFFFFF;
    
    /* Modern Phase Colors */
    --phase-teal:        #00B894;
    --phase-red:         #FF5A00;
    --phase-amber:       #FDCB6E;
    
    --pillar-rev:        #FF5A00;
    --pillar-margin:     #FDCB6E;
    --pillar-prod:       #00B894;
    --pillar-found:      #6C5CE7;
    
    /* Shadows for Depth & Micro-animations */
    --shadow-sm:         0 4px 12px rgba(0, 0, 0, 0.05);
    --shadow-md:         0 8px 24px rgba(0, 0, 0, 0.08);
    --shadow-hover:      0 12px 32px rgba(255, 90, 0, 0.15);
    
    /* Legacy variables mapping for compatibility */
    --pwc-orange:        #FF5A00; 
    --pwc-orange-ghost:  rgba(255, 90, 0, 0.08);
    --pwc-red:           #FF5A00;
    --border:            #EAEAEA;
    --grey-400:          #8E8E8E;
    --grey-200:          #F0F0F0;
}

/* ── GLOBAL FONT ── */
html, body, [class*="css"], .stMarkdown, .stMarkdown p,
[data-testid="stMetricLabel"], [data-testid="stMetricValue"],
.stSelectbox, .stSlider, .stRadio, .stTextInput, .stTextArea {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* ── HIDE STREAMLIT CHROME ── */
#MainMenu, footer, [data-testid="stToolbar"],
header[data-testid="stHeader"] { display: none !important; }

/* ── APP BACKGROUND ── */
.stApp, [data-testid="stAppViewContainer"] {
    background: var(--grey-100) !important;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: var(--sidebar-bg) !important;
    border-right: none !important;
}
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stSlider label,
[data-testid="stSidebar"] .stSelectbox label {
    color: rgba(255,255,255,0.85) !important;
    font-size: 11px !important;
    font-weight: 500 !important;
}
[data-testid="stSidebar"] .stSlider [data-testid="stSlider"] {
    color: var(--pwc-orange) !important;
}
[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] {
    background: rgba(255,255,255,0.08) !important;
    border-color: rgba(255,255,255,0.15) !important;
}
[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] span {
    color: #fff !important;
}
[data-testid="stSidebarUserContent"] {
    padding-top: 1.5rem !important;
}

/* ── BLOCK CONTAINER ── */
.block-container {
    padding: 0 1.5rem 2rem !important;
    max-width: 1400px !important;
}

/* ── HEADER BAR ── */
.aia-header {
    background: var(--pwc-black);
    height: 56px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 24px;
    margin: 0 -1.5rem 0;
    border-bottom: 3px solid var(--pwc-orange);
}
.aia-header-left { display: flex; flex-direction: column; gap: 1px; }
.aia-header-title {
    font-size: 13px;
    font-weight: 700;
    color: #fff;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.aia-header-sub {
    font-size: 10px;
    color: rgba(255,255,255,0.40);
    letter-spacing: 0.02em;
}
.aia-header-right { display: flex; align-items: center; gap: 12px; }
.aia-header-badge {
    font-size: 9px;
    font-weight: 700;
    color: var(--pwc-orange);
    background: rgba(208,74,2,0.18);
    padding: 4px 12px;
    border: 1px solid rgba(208,74,2,0.35);
    letter-spacing: 0.12em;
    text-transform: uppercase;
}
.aia-header-version {
    font-size: 9px;
    color: rgba(255,255,255,0.25);
    letter-spacing: 0.06em;
}

/* ── SIDEBAR BRAND PANEL ── */
.aia-sidebar-brand {
    background: rgba(208,74,2,0.12);
    border: 1px solid rgba(208,74,2,0.25);
    border-left: 3px solid var(--pwc-orange);
    padding: 12px 14px;
    margin-bottom: 20px;
}
.aia-sidebar-brand-title {
    font-size: 11px;
    font-weight: 700;
    color: var(--pwc-orange);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 3px;
}
.aia-sidebar-brand-sub {
    font-size: 10px;
    color: rgba(255,255,255,0.50);
    line-height: 1.5;
}
.aia-sidebar-section-label {
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.35);
    margin-bottom: 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid rgba(255,255,255,0.08);
}
.aia-sidebar-value-display {
    font-size: 26px;
    font-weight: 800;
    color: #fff;
    letter-spacing: -0.02em;
    margin: 4px 0;
}
.aia-sidebar-value-sub {
    font-size: 10px;
    color: rgba(255,255,255,0.40);
}

/* ── SLIDER TRACK ACCENT ── */
[data-testid="stSidebar"] .stSlider [role="slider"] {
    background: var(--pwc-orange) !important;
    border-color: var(--pwc-orange) !important;
}
[data-testid="stSidebar"] .stSlider [data-testid="stTickBar"] > div {
    background: var(--pwc-orange) !important;
}

/* ── CHAT INTERFACE ── */
.aia-chat-wrapper {
    background: var(--white);
    border: 1px solid var(--border);
    box-shadow: var(--shadow-md);
    padding: 0;
    margin-bottom: 0;
    overflow: hidden;
}
.aia-chat-header {
    background: var(--white);
    padding: 14px 20px;
    border-top: 1px solid var(--border);
    border-bottom: 2px solid var(--pwc-orange);
    display: flex;
    align-items: center;
    gap: 10px;
}
.aia-chat-header-dot {
    width: 8px;
    height: 8px;
    background: var(--pwc-orange);
}
.aia-chat-header-title {
    font-size: 11px;
    font-weight: 700;
    color: var(--pwc-black);
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
.aia-chat-header-sub {
    font-size: 9px;
    color: var(--grey-400);
    margin-left: auto;
    letter-spacing: 0.04em;
}
.aia-chat-body {
    padding: 20px;
    min-height: 200px;
    background: var(--grey-50);
}
.aia-chat-progress {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 20px;
}
.aia-chat-progress-step {
    height: 3px;
    flex: 1;
    background: var(--grey-200);
    transition: background 0.3s;
}
.aia-chat-progress-step.done { background: var(--pwc-orange); }
.aia-chat-progress-step.active { background: var(--pwc-yellow); }
.aia-chat-progress-label {
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--grey-400);
    margin-bottom: 14px;
}

/* ── CHAT BUBBLES ── */
.aia-bubble-agent {
    background: var(--white);
    border: 1px solid var(--border);
    border-left: 3px solid var(--pwc-orange);
    padding: 14px 16px;
    margin-bottom: 12px;
    box-shadow: var(--shadow-sm);
}
.aia-bubble-agent-source {
    font-size: 8px;
    font-weight: 700;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    color: var(--pwc-orange);
    margin-bottom: 6px;
}
.aia-bubble-agent-text {
    font-size: 12px;
    color: var(--pwc-black);
    line-height: 1.60;
    font-weight: 400;
}
.aia-bubble-agent-context {
    font-size: 10px;
    color: var(--grey-400);
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px solid var(--border-light);
    line-height: 1.5;
    font-style: italic;
}
.aia-bubble-user {
    background: var(--pwc-orange-ghost);
    border: 1px solid rgba(208,74,2,0.15);
    padding: 10px 14px;
    margin-bottom: 12px;
    text-align: right;
}
.aia-bubble-user-label {
    font-size: 8px;
    font-weight: 700;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    color: var(--pwc-orange);
    margin-bottom: 4px;
}
.aia-bubble-user-text {
    font-size: 12px;
    color: var(--pwc-black);
    line-height: 1.5;
}
.aia-chat-input-area {
    padding: 16px 20px;
    background: var(--white);
    border-top: 1px solid var(--border);
}
.aia-chat-input-label {
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--grey-400);
    margin-bottom: 6px;
}
.aia-chat-complete-badge {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 16px;
    background: var(--green-ghost);
    border: 1px solid rgba(27,127,79,0.20);
    border-left: 3px solid var(--green);
}
.aia-chat-complete-text {
    font-size: 11px;
    font-weight: 600;
    color: var(--green);
}

/* ── DASHBOARD HEADER STRIP ── */
.aia-dash-strip {
    background: var(--pwc-black);
    padding: 18px 24px;
    margin: 0 0 20px;
    border-bottom: 3px solid var(--pwc-orange);
    border-left: none;
}
.aia-dash-strip-badge-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
}
.aia-dash-badge {
    font-size: 8px;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--pwc-orange);
    background: rgba(208,74,2,0.15);
    padding: 3px 10px;
    border: 1px solid rgba(208,74,2,0.30);
}
.aia-dash-badge-blue {
    font-size: 8px;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #5BAFD6;
    background: rgba(0,91,130,0.20);
    padding: 3px 10px;
    border: 1px solid rgba(0,91,130,0.30);
}
.aia-dash-strip-date {
    font-size: 9px;
    color: rgba(255,255,255,0.25);
    margin-left: auto;
    letter-spacing: 0.04em;
}
.aia-dash-strip-title {
    font-size: 20px;
    font-weight: 700;
    color: #fff;
    line-height: 1.15;
    margin-bottom: 3px;
}
.aia-dash-strip-sub {
    font-size: 10px;
    color: rgba(255,255,255,0.45);
    letter-spacing: 0.02em;
}

/* ── PENDING STATE PLACEHOLDER ── */
.aia-pending {
    background: var(--white);
    border: 1px dashed var(--border);
    padding: 48px 24px;
    text-align: center;
}
.aia-pending-icon {
    width: 40px;
    height: 40px;
    background: var(--pwc-orange-ghost);
    border: 1px solid rgba(208,74,2,0.20);
    margin: 0 auto 16px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.aia-pending-icon-inner {
    width: 12px;
    height: 12px;
    background: var(--pwc-orange);
    opacity: 0.5;
}
.aia-pending-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--grey-600);
    margin-bottom: 6px;
}
.aia-pending-sub {
    font-size: 11px;
    color: var(--grey-400);
    line-height: 1.55;
    max-width: 320px;
    margin: 0 auto;
}

/* ── SECTION CARD ── */
.aia-card {
    background: var(--white);
    border: 1px solid var(--border);
    box-shadow: var(--shadow-sm);
    padding: 20px 22px;
    margin-bottom: 14px;
}
.aia-card.orange-top { border-top: 3px solid var(--pwc-orange); }
.aia-card.yellow-top { border-top: 3px solid var(--pwc-yellow); }
.aia-card.blue-top   { border-top: 3px solid var(--blue); }
.aia-card.green-top  { border-top: 3px solid var(--green); }
.aia-card.red-top    { border-top: 3px solid var(--pwc-rose); }

.aia-section-label {
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--grey-400);
    margin-bottom: 14px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--border-light);
}
.aia-section-title {
    font-size: 14px;
    font-weight: 700;
    color: var(--pwc-black);
    margin-bottom: 4px;
}

/* ── EXECUTIVE SUMMARY CARD ── */
.aia-exec-summary {
    background: var(--white);
    border: 1px solid var(--border);
    border-top: 4px solid var(--pwc-orange);
    box-shadow: var(--shadow-md);
    padding: 24px 26px;
    margin-bottom: 14px;
}
.aia-exec-summary-eyebrow {
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--pwc-orange);
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.aia-exec-summary-tag {
    font-size: 8px;
    font-weight: 700;
    padding: 2px 8px;
    border: 1px solid;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.aia-exec-summary-tag.ai {
    color: var(--blue);
    border-color: rgba(0,91,130,0.30);
    background: var(--blue-ghost);
}
.aia-exec-summary-tag.static {
    color: var(--grey-400);
    border-color: var(--border);
    background: var(--grey-100);
}
.aia-exec-summary-body {
    font-size: 12.5px;
    color: var(--grey-600);
    line-height: 1.75;
}
.aia-exec-summary-body p {
    margin: 0 0 14px !important;
}
.aia-exec-summary-body p:last-child {
    margin-bottom: 0 !important;
}

/* ── METRIC CARDS ── */
.aia-metric-card {
    background: var(--white);
    border: 1px solid var(--grey-border);
    border-radius: 16px;
    padding: 24px;
    height: 100%;
    box-shadow: var(--shadow-sm);
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}
.aia-metric-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-hover);
    border-color: var(--brand-primary);
}
.aia-metric-label {
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--grey-text);
    margin-bottom: 8px;
}
.aia-metric-value {
    font-size: 32px;
    font-weight: 500;
    line-height: 1;
    font-variant-numeric: tabular-nums;
    letter-spacing: -0.01em;
}
.aia-metric-value .sym {
    font-size: 20px;
    font-weight: 400;
    color: var(--grey-label);
}
.aia-metric-sub {
    line-height: 1.45;
}

/* ── RISK & MODIFIER FLAGS ── */
.aia-flag {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 10px 12px;
    border: 1px solid;
    margin-bottom: 8px;
}
.aia-flag.warning {
    background: rgba(255,182,0,0.07);
    border-color: rgba(255,182,0,0.25);
    border-left: 3px solid var(--pwc-yellow);
}
.aia-flag.danger {
    background: rgba(224,48,30,0.06);
    border-color: rgba(224,48,30,0.20);
    border-left: 3px solid var(--pwc-rose);
}
.aia-flag.info {
    background: var(--blue-ghost);
    border-color: rgba(0,91,130,0.20);
    border-left: 3px solid var(--blue);
}
.aia-flag-label {
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 3px;
}
.aia-flag.warning .aia-flag-label { color: #9A6B00; }
.aia-flag.danger  .aia-flag-label { color: var(--pwc-rose); }
.aia-flag.info    .aia-flag-label { color: var(--blue); }
.aia-flag-text {
    font-size: 11px;
    color: var(--grey-600);
    line-height: 1.5;
}

/* ── LEDGER TABLE ── */
.aia-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 11.5px;
}
.aia-table th {
    font-size: 8.5px;
    font-weight: 700;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    color: var(--grey-400);
    text-align: left;
    padding: 7px 10px 10px;
    border-bottom: 1.5px solid var(--border);
    background: var(--grey-50);
}
.aia-table th.num { text-align: right; }
.aia-table td {
    padding: 9px 10px;
    border-bottom: 1px solid var(--border-light);
    color: var(--grey-600);
    vertical-align: top;
}
.aia-table td.num {
    font-family: 'Inter', monospace;
    font-weight: 600;
    color: var(--pwc-black);
    text-align: right;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
}
.aia-table td.pct {
    font-family: 'Inter', monospace;
    font-size: 10px;
    color: var(--grey-400);
    text-align: right;
}
.aia-table td.formula {
    font-family: 'Inter', monospace;
    font-size: 10px;
    color: var(--blue);
    font-weight: 500;
}
.aia-table tr.total-row td {
    font-weight: 700;
    color: var(--pwc-black);
    border-top: 2px solid var(--border);
    border-bottom: none;
    background: var(--grey-50);
}
.aia-table tr:hover td { background: var(--grey-50); }
.aia-pillar-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    margin-right: 7px;
    vertical-align: middle;
    flex-shrink: 0;
}

/* ── SCORING TABLE ── */
.aia-score-badge {
    display: inline-block;
    padding: 2px 8px;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
.aia-score-badge.high   { background: var(--green-ghost);  color: var(--green); }
.aia-score-badge.medium { background: var(--pwc-yellow-ghost); color: #7A5800; }
.aia-score-badge.watch  { background: var(--blue-ghost); color: var(--blue); }

/* ── DYNAMIC CARDS ── */
.aia-phase-card {
    background: var(--white);
    border: 1px solid var(--grey-border);
    border-radius: 12px;
    padding: 16px 20px;
    height: 100%;
    box-shadow: var(--shadow-sm);
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}
.aia-phase-card:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-md);
    border-color: var(--grey-border-light);
}

.aia-confidence-card {
    background: var(--white);
    border: 1px solid var(--grey-border);
    border-radius: 8px;
    padding: 16px 20px;
    box-shadow: var(--shadow-sm);
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}
.aia-confidence-card:hover {
    box-shadow: var(--shadow-md);
}

.aia-section-header {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.1em;
    color: var(--grey-label);
    text-transform: uppercase;
    margin-bottom: 16px;
}

/* ── DATAFRAME OVERRIDES ── */
.stPlotlyChart {
    background: var(--white) !important;
    border: 1px solid var(--border) !important;
    box-shadow: var(--shadow-sm) !important;
    padding: 6px !important;
}

/* ── BUTTONS ── */
div.stButton > button {
    background: var(--pwc-orange) !important;
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
    font-size: 12px !important;
    padding: 9px 22px !important;
    border-radius: 0 !important;
    letter-spacing: 0.02em !important;
    transition: background 0.15s !important;
}
div.stButton > button:hover {
    background: #B83E02 !important;
}
div.stButton > button:active {
    background: #9C3301 !important;
}

/* ── TEXT INPUTS & TEXTAREAS IN MAIN AREA ── */
.stTextInput input, .stTextArea textarea {
    border: 1px solid var(--border) !important;
    border-radius: 0 !important;
    font-size: 12px !important;
    font-family: 'Inter', sans-serif !important;
    padding: 10px 12px !important;
    background: var(--white) !important;
    color: var(--pwc-black) !important;
    box-shadow: none !important;
    transition: border-color 0.15s !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--pwc-orange) !important;
    outline: none !important;
    box-shadow: 0 0 0 2px rgba(208,74,2,0.12) !important;
}

/* ── DISCLAIMER ── */
.aia-disclaimer {
    background: var(--white);
    border: 1px solid var(--border);
    border-left: 3px solid var(--pwc-yellow);
    padding: 10px 14px;
    font-size: 10.5px;
    color: var(--grey-400);
    line-height: 1.55;
    margin-top: 16px;
}

/* ── DATA ENG CALLOUT ── */
.aia-de-callout {
    background: rgba(0,91,130,0.05);
    border: 1px solid rgba(0,91,130,0.20);
    border-left: 4px solid var(--blue);
    padding: 14px 16px;
    margin-bottom: 14px;
}
.aia-de-callout-label {
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    color: var(--blue);
    margin-bottom: 6px;
}
.aia-de-callout-formula {
    font-family: 'Inter', monospace;
    font-size: 14px;
    font-weight: 700;
    color: var(--pwc-black);
    margin-bottom: 4px;
}
.aia-de-callout-sub {
    font-size: 10px;
    color: var(--grey-400);
    line-height: 1.5;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--grey-100); }
::-webkit-scrollbar-thumb { background: var(--grey-300); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--grey-400); }

/* ── INTAKE FORM ── */
.aia-intake-header {
    padding: 24px 0 20px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 24px;
}
.aia-intake-eyebrow {
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--pwc-orange);
    margin-bottom: 8px;
}
.aia-intake-title {
    font-size: 22px;
    font-weight: 700;
    color: var(--pwc-black);
    margin-bottom: 6px;
    line-height: 1.2;
}
.aia-intake-sub {
    font-size: 12px;
    color: var(--grey-600);
    line-height: 1.6;
    max-width: 760px;
}

/* Form section divider labels */
.aia-form-section-label {
    display: block;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--grey-400);
    margin-bottom: 10px;
    padding-bottom: 7px;
    border-bottom: 1px solid var(--border-light);
}

/* Individual field labels */
.aia-field-label {
    display: block;
    font-size: 11px;
    font-weight: 600;
    color: var(--pwc-black);
    margin-bottom: 4px;
    letter-spacing: 0.01em;
}
.aia-field-sublabel {
    display: block;
    font-size: 10px;
    color: var(--grey-400);
    margin-bottom: 8px;
    line-height: 1.4;
}

/* Selectbox sharp edge overrides */
.stSelectbox [data-baseweb="select"] {
    border-radius: 0 !important;
    border-color: var(--border) !important;
    box-shadow: none !important;
}
.stSelectbox [data-baseweb="select"]:focus-within {
    border-color: var(--pwc-orange) !important;
    box-shadow: 0 0 0 2px rgba(208,74,2,0.12) !important;
}
.stSelectbox [data-baseweb="select"] [data-testid="stMarkdownContainer"] p {
    font-size: 12px !important;
    color: var(--pwc-black) !important;
}

/* KPI Checkbox chip styling */
.block-container [data-testid="stCheckbox"] {
    border: 1px solid var(--border);
    padding: 9px 10px !important;
    background: var(--white);
    margin-bottom: 2px !important;
    transition: border-color 0.15s, background 0.15s;
}
.block-container [data-testid="stCheckbox"] label p {
    font-size: 11px !important;
    font-weight: 500 !important;
    color: var(--grey-600) !important;
    line-height: 1.35 !important;
}
.block-container [data-testid="stCheckbox"]:has(input:checked) {
    border-color: var(--pwc-orange) !important;
    background: var(--pwc-orange-ghost) !important;
}
.block-container [data-testid="stCheckbox"]:has(input:checked) label p {
    color: var(--pwc-black) !important;
    font-weight: 600 !important;
}

/* ══════════════════════════════════════════════════════════════════════════════
   WIZARD STEPPER NAVIGATION
   ══════════════════════════════════════════════════════════════════════════════ */

/* Container for the entire stepper */
.aia-stepper-pills {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-wrap: wrap;
    gap: 8px;
    padding: 16px 0;
    margin: 0 -1.5rem 24px;
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--grey-border);
    position: sticky;
    top: 0;
    z-index: 100;
}

.aia-step-pill {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    border-radius: 20px;
    border: 1px solid var(--grey-border-light);
    background: var(--white);
    color: var(--grey-text);
    font-size: 11px;
    font-weight: 600;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}
.aia-step-pill:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-sm);
    border-color: var(--grey-label);
}

.aia-step-pill.completed {
    border-color: var(--phase-teal);
    color: var(--phase-teal);
}

.aia-step-pill.active {
    background: var(--brand-gradient);
    border-color: transparent;
    color: var(--white);
    box-shadow: var(--shadow-hover);
}

.aia-step-pill-check {
    font-weight: 700;
}

.aia-step-pill-label {
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Progress indicator "X of Y" */
.aia-progress-text {
    font-size: 11px;
    color: var(--grey-400);
    text-align: right;
    margin: 8px 0 0;
}

/* Progress bar under stepper */
.aia-progress-bar-wrap {
    height: 3px;
    background: var(--grey-200);
    margin: 0 -1.5rem 20px;
    position: relative;
}
.aia-progress-bar-fill {
    height: 100%;
    background: var(--pwc-orange);
    transition: width 0.4s ease;
}

/* ══════════════════════════════════════════════════════════════════════════════
   SECTION INTRO PANEL
   ══════════════════════════════════════════════════════════════════════════════ */

.aia-section-intro {
    background: var(--white);
    border-left: 4px solid var(--pwc-orange);
    padding: 20px 24px;
    margin: 0 0 24px;
    border-bottom: 1px solid var(--border);
}
.aia-section-intro-icon {
    font-size: 22px;
    margin-bottom: 8px;
}
.aia-section-intro-id {
    font-size: 9px;
    font-weight: 800;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--grey-400);
    margin-bottom: 4px;
}
.aia-section-intro-title {
    font-size: 18px;
    font-weight: 700;
    color: var(--pwc-black);
    letter-spacing: -0.01em;
    line-height: 1.3;
    margin-bottom: 4px;
}
.aia-section-intro-subtitle {
    font-size: 10px;
    font-weight: 600;
    color: var(--pwc-orange);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 8px;
}
.aia-section-intro-desc {
    font-size: 12px;
    color: var(--grey-600);
    line-height: 1.6;
    max-width: 700px;
}

/* ══════════════════════════════════════════════════════════════════════════════
   QUESTION CARDS
   ══════════════════════════════════════════════════════════════════════════════ */

.aia-qcard {
    background: var(--white);
    border: 1px solid var(--border);
    border-left: 4px solid var(--pwc-orange);
    padding: 20px 24px 16px;
    margin-bottom: 14px;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.aia-qcard:hover {
    border-color: var(--grey-300);
    box-shadow: var(--shadow-sm);
}

/* Card header: ID badge + question text */
.aia-qcard-header {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    margin-bottom: 10px;
}
.aia-qcard-id {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 46px;
    height: 24px;
    padding: 0 10px;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.06em;
    color: var(--white);
    background: var(--pwc-orange);
    flex-shrink: 0;
    margin-top: 2px;
}
.aia-qcard-text {
    font-size: 14px;
    font-weight: 600;
    color: var(--pwc-black);
    line-height: 1.5;
    flex: 1;
}

/* Rationale block */
.aia-qcard-rationale {
    font-size: 11px;
    color: var(--grey-600);
    line-height: 1.6;
    padding: 10px 14px;
    background: var(--grey-50);
    border-left: 3px solid var(--border);
    margin: 8px 0 12px;
}

/* Tags row */
.aia-qcard-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 14px;
}
.aia-qcard-tag {
    display: inline-block;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    padding: 3px 10px;
    background: var(--pwc-orange-ghost);
    color: var(--pwc-orange);
    border: 1px solid rgba(208,74,2,0.12);
}

/* Input styling within cards */
.aia-qcard-input {
    margin-top: 6px;
}

/* Navigation buttons row */
.aia-nav-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 0;
    margin-top: 12px;
    border-top: 1px solid var(--border);
}
.aia-nav-hint {
    font-size: 10px;
    color: var(--grey-400);
    line-height: 1.5;
}


.aia-q-section {
    margin: 32px 0 18px;
    padding: 16px 20px 14px;
    background: var(--white);
    border-left: 4px solid var(--pwc-orange);
    border-bottom: 1px solid var(--border);
    position: relative;
}
.aia-q-section-id {
    font-size: 9px;
    font-weight: 800;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--grey-400);
    margin-bottom: 4px;
}
.aia-q-section-title {
    font-size: 16px;
    font-weight: 700;
    color: var(--pwc-black);
    letter-spacing: -0.01em;
    line-height: 1.3;
}
.aia-q-section-sub {
    font-size: 10px;
    color: var(--grey-400);
    margin-top: 4px;
    font-style: italic;
}

/* ── QUESTION CARD ── */
.aia-qcard {
    background: var(--white);
    border: 1px solid var(--border);
    border-left: 4px solid var(--pwc-orange);
    padding: 18px 20px 14px;
    margin-bottom: 10px;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.aia-qcard:hover {
    border-color: var(--grey-300);
    box-shadow: var(--shadow-sm);
}

/* Card header row: ID + question text */
.aia-qcard-header {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 8px;
}
.aia-qcard-id {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 42px;
    height: 22px;
    padding: 0 8px;
    font-size: 9px;
    font-weight: 800;
    letter-spacing: 0.08em;
    color: var(--white);
    background: var(--pwc-orange);
    flex-shrink: 0;
    margin-top: 1px;
}
.aia-qcard-text {
    font-size: 13px;
    font-weight: 600;
    color: var(--pwc-black);
    line-height: 1.45;
    flex: 1;
}

/* Rationale block */
.aia-qcard-rationale {
    font-size: 10.5px;
    color: var(--grey-600);
    line-height: 1.55;
    padding: 8px 12px;
    background: var(--grey-50);
    border-left: 2px solid var(--border);
    margin: 6px 0 10px;
}
.aia-qcard-rationale::before {
    content: "ℹ ";
    font-size: 10px;
    color: var(--grey-400);
}

/* Tags row */
.aia-qcard-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    margin-bottom: 12px;
}
.aia-qcard-tag {
    display: inline-block;
    font-size: 8.5px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 2px 8px;
    background: var(--pwc-orange-ghost);
    color: var(--pwc-orange);
    border: 1px solid rgba(208,74,2,0.15);
}

/* Input area wrapper inside card */
.aia-qcard-input {
    margin-top: 4px;
}

/* Override Streamlit text area within cards to be properly sized */
.aia-qcard-input .stTextArea textarea {
    min-height: 72px !important;
    font-size: 12px !important;
    line-height: 1.5 !important;
    border-radius: 0 !important;
    border-color: var(--border) !important;
}
.aia-qcard-input .stTextArea textarea:focus {
    border-color: var(--pwc-orange) !important;
    box-shadow: 0 0 0 2px rgba(208,74,2,0.12) !important;
}
.aia-qcard-input .stSelectbox [data-baseweb="select"] {
    font-size: 12px !important;
}

/* Progress indicator for sections */
.aia-q-progress {
    display: flex;
    gap: 4px;
    margin-bottom: 20px;
}
.aia-q-progress-step {
    flex: 1;
    height: 3px;
    background: var(--grey-200);
    transition: background 0.3s;
}
.aia-q-progress-step.active {
    background: var(--pwc-orange);
}

/* ── LANDING PAGE ──────────────────────────────────────────────────────────── */

/* Hero */
.lp-hero {
    background: var(--pwc-black);
    background-image: linear-gradient(150deg, #1A1A1A 0%, #2D1505 100%);
    margin: 0 -1.5rem;
    padding: 56px 80px;
    display: grid;
    grid-template-columns: 1.5fr 1fr;
    gap: 60px;
    align-items: center;
    position: relative;
    overflow: hidden;
    border-bottom: 3px solid var(--pwc-orange);
    animation: lp-fade-in 0.5s ease-out;
}
.lp-hero::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, var(--pwc-orange), transparent);
}
.lp-badge {
    display: inline-block;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--pwc-orange);
    background: rgba(208,74,2,0.15);
    border: 1px solid rgba(208,74,2,0.30);
    padding: 5px 14px;
    margin-bottom: 20px;
}
.lp-h1 {
    font-size: 44px;
    font-weight: 800;
    color: #FFFFFF;
    line-height: 1.08;
    margin: 0 0 18px;
    letter-spacing: -0.02em;
}
.lp-h1-accent { color: var(--pwc-orange); }
.lp-tagline {
    font-size: 14px;
    color: rgba(255,255,255,0.55);
    line-height: 1.70;
    max-width: 520px;
    margin: 0 0 24px;
}
.lp-tag-row { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; }
.lp-tag {
    font-size: 10px;
    font-weight: 600;
    color: rgba(255,255,255,0.65);
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.12);
    padding: 5px 12px;
    letter-spacing: 0.04em;
}
.lp-hero-cta-hint {
    font-size: 10.5px;
    color: rgba(255,255,255,0.30);
    letter-spacing: 0.02em;
    margin-top: 4px;
}
.lp-hero-cta-hint strong { color: rgba(255,255,255,0.50); }

/* Mock dashboard in hero */
.lp-dashboard-mock {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.10);
    border-top: 3px solid var(--pwc-orange);
    padding: 0;
    animation: lp-float 5s ease-in-out infinite;
}
.lp-mock-topbar {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    border-bottom: 1px solid rgba(255,255,255,0.07);
    background: rgba(255,255,255,0.03);
}
.lp-mock-dot {
    width: 7px; height: 7px;
    background: var(--pwc-orange);
}
.lp-mock-topbar-title {
    font-size: 9px;
    font-weight: 600;
    color: rgba(255,255,255,0.50);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    flex: 1;
}
.lp-mock-topbar-badge {
    font-size: 8px;
    font-weight: 700;
    color: var(--pwc-orange);
    border: 1px solid rgba(208,74,2,0.40);
    padding: 2px 8px;
    letter-spacing: 0.10em;
}
.lp-mock-kpi-row {
    display: flex;
    padding: 12px;
    gap: 8px;
}
.lp-mock-kpi {
    flex: 1;
    padding: 10px;
    text-align: center;
}
.lp-kpi-orange { border-top: 2px solid var(--pwc-orange); background: rgba(208,74,2,0.08); }
.lp-kpi-blue   { border-top: 2px solid #5BAFD6; background: rgba(0,91,130,0.10); }
.lp-kpi-green  { border-top: 2px solid #1B7F4F; background: rgba(27,127,79,0.08); }
.lp-mock-kpi-num {
    font-size: 16px;
    font-weight: 800;
    color: rgba(255,255,255,0.85);
    line-height: 1;
    margin-bottom: 4px;
}
.lp-mock-kpi-lbl {
    font-size: 8px;
    color: rgba(255,255,255,0.35);
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.lp-mock-chart-area {
    display: flex;
    align-items: flex-end;
    gap: 8px;
    padding: 0 12px 12px;
    height: 70px;
}
.lp-mock-chart-bar-wrap { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; }
.lp-mock-chart-bar {
    width: 100%;
    background: rgba(255,255,255,0.12);
    transition: height 0.3s;
}
.lp-bar-orange { background: rgba(208,74,2,0.50) !important; }
.lp-mock-chart-bar-lbl {
    font-size: 7px;
    color: rgba(255,255,255,0.25);
    text-align: center;
    letter-spacing: 0.04em;
}
.lp-mock-ledger {
    border-top: 1px solid rgba(255,255,255,0.07);
    padding: 10px 12px;
}
.lp-mock-ledger-hdr {
    display: flex;
    justify-content: space-between;
    font-size: 8px;
    color: rgba(255,255,255,0.25);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 8px;
}
.lp-mock-ledger-row {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 9px;
    padding: 4px 0;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}
.lp-mock-ledger-alt { background: rgba(255,255,255,0.02); }
.lp-mock-ledger-dot { width: 6px; height: 6px; flex-shrink: 0; }
.lp-dot-orange { background: var(--pwc-orange); }
.lp-dot-blue   { background: #5BAFD6; }
.lp-dot-green  { background: #1B7F4F; }
.lp-mock-ledger-name { flex: 1; color: rgba(255,255,255,0.50); }
.lp-mock-ledger-val { color: rgba(255,255,255,0.70); font-weight: 600; }

/* Stats ribbon */
.lp-stats-ribbon {
    display: flex;
    align-items: center;
    background: var(--white);
    border-bottom: 1px solid var(--border);
    box-shadow: var(--shadow-sm);
    padding: 24px 80px;
    margin: 0 -1.5rem;
}
.lp-stat-item { flex: 1; text-align: center; }
.lp-stat-num {
    font-size: 32px;
    font-weight: 800;
    color: var(--pwc-black);
    letter-spacing: -0.02em;
    line-height: 1;
    margin-bottom: 6px;
    font-variant-numeric: tabular-nums;
}
.lp-stat-lbl {
    font-size: 10px;
    font-weight: 500;
    color: var(--grey-400);
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.lp-stat-sep {
    width: 1px;
    height: 44px;
    background: var(--border);
    flex-shrink: 0;
}

/* Content sections */
.lp-section {
    padding: 56px 80px;
    margin: 0 -1.5rem;
}
.lp-grey  { background: var(--grey-100); border-top: 1px solid var(--border); }
.lp-white { background: var(--white); border-top: 1px solid var(--border); }
.lp-sect-header { text-align: center; margin-bottom: 40px; }
.lp-sect-eyebrow {
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--pwc-orange);
    margin-bottom: 12px;
}
.lp-sect-h2 {
    font-size: 26px;
    font-weight: 700;
    color: var(--pwc-black);
    line-height: 1.25;
    margin-bottom: 12px;
    letter-spacing: -0.01em;
}
.lp-sect-sub {
    font-size: 13px;
    color: var(--grey-600);
    max-width: 560px;
    margin: 0 auto;
    line-height: 1.65;
}

/* 3-column grid */
.lp-grid-3 {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
}

/* Feature cards */
.lp-feat-card {
    background: var(--white);
    border: 1px solid var(--border);
    border-top: 3px solid var(--pwc-orange);
    padding: 24px 22px;
    transition: transform 0.2s, box-shadow 0.2s;
}
.lp-feat-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-md); }
.lp-feat-num {
    font-size: 28px;
    font-weight: 800;
    color: var(--pwc-orange);
    opacity: 0.30;
    margin-bottom: 12px;
    letter-spacing: -0.02em;
}
.lp-feat-title {
    font-size: 13px;
    font-weight: 700;
    color: var(--pwc-black);
    margin-bottom: 10px;
    line-height: 1.3;
}
.lp-feat-desc {
    font-size: 12px;
    color: var(--grey-600);
    line-height: 1.65;
}

/* Steps (How it works) */
.lp-steps-container {
    display: grid;
    grid-template-columns: 1fr auto 1fr auto 1fr;
    gap: 0;
    align-items: start;
}
.lp-step-block {
    background: var(--white);
    border: 1px solid var(--border);
    padding: 24px 22px;
    position: relative;
}
.lp-step-block:nth-child(1) { border-left: 4px solid var(--pwc-orange); }
.lp-step-block:nth-child(3) { border-left: 4px solid var(--pwc-yellow); }
.lp-step-block:nth-child(5) { border-left: 4px solid var(--blue); }
.lp-step-num-circle {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    background: var(--pwc-black);
    color: var(--pwc-orange);
    font-size: 13px;
    font-weight: 700;
    margin-bottom: 14px;
    letter-spacing: 0.04em;
}
.lp-step-title {
    font-size: 13px;
    font-weight: 700;
    color: var(--pwc-black);
    margin-bottom: 10px;
}
.lp-step-desc {
    font-size: 12px;
    color: var(--grey-600);
    line-height: 1.65;
    margin-bottom: 14px;
}
.lp-step-duration {
    font-size: 10px;
    font-weight: 600;
    color: var(--pwc-orange);
    background: var(--pwc-orange-ghost);
    border: 1px solid rgba(208,74,2,0.20);
    display: inline-block;
    padding: 3px 12px;
    letter-spacing: 0.04em;
}
.lp-step-arrow-col {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 24px 10px;
    color: var(--pwc-orange);
}
.lp-arrow-line {
    width: 1px;
    height: 20px;
    background: rgba(208,74,2,0.25);
    margin-bottom: 4px;
}
.lp-arrow-head { font-size: 18px; }

/* Deliverable cards */
.lp-out-card {
    border: 1px solid var(--border);
    padding: 26px 22px;
    background: var(--white);
    transition: transform 0.2s, box-shadow 0.2s;
}
.lp-out-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-md); }
.lp-out-orange { border-top: 4px solid var(--pwc-orange); }
.lp-out-blue   { border-top: 4px solid var(--blue); }
.lp-out-yellow { border-top: 4px solid var(--pwc-yellow); }
.lp-out-label {
    font-size: 8px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--grey-400);
    margin-bottom: 12px;
}
.lp-out-title {
    font-size: 14px;
    font-weight: 700;
    color: var(--pwc-black);
    margin-bottom: 10px;
    line-height: 1.3;
}
.lp-out-desc {
    font-size: 12px;
    color: var(--grey-600);
    line-height: 1.65;
}

/* Peer strip */
.lp-peer-strip {
    background: var(--pwc-black);
    padding: 20px 80px;
    margin: 0 -1.5rem;
    border-top: 1px solid rgba(255,255,255,0.06);
}
.lp-peer-strip-label {
    font-size: 8px;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.25);
    margin-bottom: 12px;
}
.lp-peer-strip-logos {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px;
}
.lp-peer-name {
    font-size: 11px;
    font-weight: 600;
    color: rgba(255,255,255,0.55);
    letter-spacing: 0.02em;
}
.lp-peer-sep { color: rgba(255,255,255,0.15); font-size: 10px; }

/* Footer disclaimer */
.lp-footer-disc {
    background: var(--grey-100);
    border-top: 1px solid var(--border);
    padding: 16px 80px;
    font-size: 10.5px;
    color: var(--grey-400);
    line-height: 1.65;
    margin: 0 -1.5rem;
}
.lp-footer-disc strong { color: var(--grey-600); }

/* Landing animations */
@keyframes lp-fade-in {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes lp-float {
    0%, 100% { transform: translateY(0); }
    50%       { transform: translateY(-8px); }
}

/* Budget slider display value */
.aia-budget-display {
    font-size: 26px;
    font-weight: 800;
    color: var(--pwc-black);
    letter-spacing: -0.02em;
    margin-top: -4px;
}

</style>
"""

_HEADER_HTML = """
<div class="aia-header">
    <div class="aia-header-left">
        <div class="aia-header-title">AI Investment Engine</div>
        <div class="aia-header-sub">FMCG / CPG Strategic Capital Allocation</div>
    </div>
    <div class="aia-header-right">
        <div class="aia-header-version">v1.0 — June 2026</div>
        <div class="aia-header-badge">C-Suite Edition</div>
    </div>
</div>
"""
