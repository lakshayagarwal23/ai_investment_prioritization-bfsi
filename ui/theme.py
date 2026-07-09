"""
ui/theme.py
PwC Horizon Visual Theme for the AI Investment Advisory Platform.

Design system (PwC Horizon spec):
  • Strict 8pt spacing grid (4px half-steps)
  • Typography: Georgia (headlines/numerals) + Arial (body)
  • Palette: PwC Flame (Orange, Yellow, Red) + PwC Greys
  • Status: In-family (#2D2D2D ok, #FFB600 warn, #E0301E breach)
  • Flat design, no blurs, no gradients, no glow, 2px/4px radii
"""

import streamlit as st

def inject_theme() -> None:
    """Inject the full CSS theme into the Streamlit app."""
    st.html(_THEME_CSS)

def render_header(firm_name: str = "The Firm", sector: str = "BFSI", run_id: str = "run —") -> None:
    """Render the branded top header bar with firm context pinned."""
    html = f"""
    <div class="hz-header">
        <div class="hz-header-left">
            <span class="hz-header-title">AI Investment Prioritisation</span>
            <span class="hz-header-sub">{firm_name} &nbsp;·&nbsp; {sector}</span>
        </div>
        <div class="hz-header-right">
            <span>{run_id}</span>
            <span>ENG: 5.0.0</span>
        </div>
    </div>
    """
    st.html(html)

_THEME_CSS = """
<style>
/* ══════════════════════════════════════════════════════════════════════════
   PWC HORIZON DESIGN TOKENS
   ══════════════════════════════════════════════════════════════════════════ */
:root {
    /* Brand (PwC flame palette) */
    --pwc-orange: #D04A02;
    --pwc-tangerine: #EB8C00;
    --pwc-yellow: #FFB600;
    --pwc-red: #E0301E;
    --pwc-rose: #DB536A;
    --pwc-maroon: #A32020;

    /* Neutrals (anchored on PwC greys) */
    --black: #000000;
    --g900: #2D2D2D;
    --g700: #464646;
    --g500: #7D7D7D;
    --g300: #BDBDBD;
    --g200: #DEDEDE;
    --g100: #F2F2F2;
    --paper: #FFFFFF;

    /* Tints (6-10% fills) */
    --orange-tint: rgba(208,74,2,0.07);
    --yellow-tint: rgba(255,182,0,0.10);
    --red-tint: rgba(224,48,30,0.06);
    --grey-tint: rgba(45,45,45,0.04);

    /* Status (Option A - in-family) */
    --status-ok: #2D2D2D;
    --status-watch: #FFB600;
    --status-breach: #E0301E;

    /* Geometry & motion */
    --radius: 2px;
    --radius-card: 4px;
    --border: 1px solid var(--g200);
    --dur: 140ms;
    --ease: cubic-bezier(0.2,0,0,1);

    /* Type */
    --font-head: Georgia, 'Times New Roman', serif;
    --font-body: Arial, Helvetica, sans-serif;
    
    /* Spacing */
    --sp-1: 4px; --sp-2: 8px; --sp-3: 12px; --sp-4: 16px;
    --sp-5: 20px; --sp-6: 24px; --sp-8: 32px; --sp-10: 40px; --sp-12: 48px;
}

/* ══════════════════════════════════════════════════════════════════════════
   GLOBAL TYPOGRAPHY & RESET
   ══════════════════════════════════════════════════════════════════════════ */
html, body, [class*="css"], .stMarkdown, .stMarkdown p, .stApp,
[data-testid="stMetricLabel"], [data-testid="stMetricValue"],
input, textarea, button, select,
.stSelectbox, .stSlider, .stRadio, .stTextInput, .stTextArea, .stNumberInput {
    font-family: var(--font-body) !important;
    color: var(--g700) !important;
}

h1, h2, h3, h4, h5, h6, .hz-georgia {
    font-family: var(--font-head) !important;
    color: var(--black) !important;
    font-weight: normal !important;
}

/* Streamlit overrides */
.stApp { background-color: var(--paper); }
.stSidebar { background-color: var(--paper) !important; border-right: var(--border) !important; }
.stSidebar [data-testid="stSidebarNav"] { display: none !important; } /* Hide default nav */
[data-testid="stSidebarUserContent"] { padding: 0 !important; }

/* Remove default Streamlit decoration, header, footer */
#MainMenu { visibility: hidden !important; }
header { visibility: hidden !important; }
footer { visibility: hidden !important; }
[data-testid="stHeader"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stFooter"] { display: none !important; }

/* Push content down so header doesn't overlap, reduce margins/paddings */
.stApp > div.main > div.block-container {
    padding-top: 5rem !important;
    padding-bottom: 2rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 1200px !important;
    margin: 0 auto !important;
}

[data-testid="stSidebarUserContent"] { padding-top: 48px !important; }

/* Overrides for inputs to ensure they sit flat */
.stTextInput>div>div>input {
    border-radius: var(--radius) !important;
    border: var(--border) !important;
    font-family: var(--font-body) !important;
    font-size: 13px !important;
    color: var(--black) !important;
}

/* Overrides for Streamlit native buttons */
button[kind="primary"] {
    background-color: var(--pwc-orange) !important;
    color: white !important;
    border: none !important;
    border-radius: 0px !important;
    font-family: var(--font-body) !important;
    font-weight: bold !important;
    padding: 0.5rem 2rem !important;
    height: auto !important;
    transition: background-color var(--dur) var(--ease) !important;
}
button[kind="primary"]:hover {
    background-color: #a63b01 !important;
}
button[kind="secondary"] {
    background-color: transparent !important;
    color: var(--g700) !important;
    border: 1px solid var(--g300) !important;
    border-radius: 0px !important;
    font-family: var(--font-body) !important;
    padding: 0.5rem 2rem !important;
    height: auto !important;
}
button[kind="secondary"]:hover {
    border-color: var(--black) !important;
    color: var(--black) !important;
}

/* ══════════════════════════════════════════════════════════════════════════
   HEADER (Persistent)
   ══════════════════════════════════════════════════════════════════════════ */
.hz-header {
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 48px;
    background: var(--paper);
    border-bottom: var(--border);
    z-index: 1000000;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 var(--sp-6);
}
.hz-header-left { display: flex; align-items: baseline; gap: var(--sp-4); }
.hz-header-title { font-family: var(--font-head); font-size: 19px; color: var(--black); }
.hz-header-sub { font-family: var(--font-body); font-size: 13px; color: var(--g500); }
.hz-header-right { display: flex; gap: var(--sp-4); font-family: monospace; font-size: 12px; color: var(--g500); }

/* ══════════════════════════════════════════════════════════════════════════
   SIDEBAR & WIZARD
   ══════════════════════════════════════════════════════════════════════════ */
/* Nav active state */
.hz-nav-item {
    padding: var(--sp-3) var(--sp-4);
    font-size: 13px;
    color: var(--g700);
    border-left: 3px solid transparent;
    margin-bottom: var(--sp-1);
    transition: background-color var(--dur) var(--ease);
}
.hz-nav-active {
    border-left-color: var(--pwc-orange);
    color: var(--black);
    font-weight: bold;
    background: var(--orange-tint);
}

/* Stepper (Numbered Squares) */
.hz-stepper {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: var(--sp-4) 0;
    background: var(--paper);
    border-bottom: var(--border);
    margin-bottom: var(--sp-6);
}
.hz-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--sp-1);
}
.hz-step-sq {
    width: 28px; height: 28px;
    display: flex; align-items: center; justify-content: center;
    font-size: 12px; font-weight: bold;
    border-radius: 50%;
    transition: all var(--dur) var(--ease);
}
.hz-step-sq.done { background: var(--black); color: var(--paper); }
.hz-step-sq.active { background: var(--pwc-orange); color: var(--paper); border: 2px solid var(--pwc-orange); }
.hz-step-sq.todo { background: var(--paper); color: var(--g300); border: 2px solid var(--g200); }
.hz-step-lbl {
    font-size: 10px;
    font-weight: 600;
    color: var(--g500);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.hz-step-lbl.active { color: var(--pwc-orange); }
.hz-step-rule { width: 48px; height: 2px; background: var(--g200); margin: -14px var(--sp-2) 0 var(--sp-2); }

/* Question Cards */
.hz-q-group-intro {
    font-family: var(--font-head);
    font-size: 24px;
    color: var(--black);
    margin-bottom: var(--sp-2);
}
.hz-q-card {
    background: var(--paper);
    border: var(--border);
    border-radius: var(--radius-card);
    padding: var(--sp-4);
    margin-bottom: var(--sp-4);
}
.hz-q-row {
    margin-bottom: var(--sp-4);
}
.hz-q-label-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--sp-2);
}
.hz-q-label { font-size: 14px; color: var(--black); font-weight: 600; }
.hz-chip {
    font-size: 9px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.08em;
    padding: 2px 8px; border-radius: var(--radius);
}
.hz-chip.auto { background: var(--orange-tint); color: var(--pwc-orange); border: 1px solid rgba(208,74,2,0.3); }
.hz-chip.verify { background: var(--yellow-tint); color: var(--black); border: 1px solid var(--pwc-yellow); }
.hz-chip.median { background: var(--g100); color: var(--g500); border: 1px solid var(--g200); }
.hz-chip.manual { background: var(--grey-tint); color: var(--g700); border: 1px solid var(--g300); }

/* ══════════════════════════════════════════════════════════════════════════
   DASHBOARD / REPORTING
   ══════════════════════════════════════════════════════════════════════════ */
/* Section Head */
.hz-report-h2 {
    font-family: var(--font-head);
    font-size: 20px;
    color: var(--black);
    margin: var(--sp-6) 0 var(--sp-3) 0;
    border-bottom: 1px solid var(--g200);
    padding-bottom: var(--sp-2);
}
.hz-report-h2-large {
    font-family: var(--font-head);
    font-size: 28px;
    color: var(--black);
    margin-bottom: var(--sp-6);
}

/* KPI Tiles */
.hz-kpi-row { display: flex; gap: var(--sp-4); margin-bottom: var(--sp-6); }
.hz-kpi-tile {
    flex: 1;
    background: var(--paper);
    border: var(--border);
    border-radius: var(--radius-card);
    padding: var(--sp-4);
    display: flex; flex-direction: column; gap: var(--sp-2);
}
.hz-kpi-hero { border-top: 4px solid var(--pwc-orange); }
.hz-kpi-lbl {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--g500);
}
.hz-kpi-num {
    font-family: var(--font-head);
    font-size: 36px;
    color: var(--black);
    font-variant-numeric: tabular-nums;
}

/* Bullet Meters */
.hz-bullet-wrap { margin-bottom: var(--sp-4); }
.hz-bullet-lbl-row { display: flex; justify-content: space-between; margin-bottom: var(--sp-1); }
.hz-bullet-lbl { font-size: 13px; font-weight: 600; color: var(--black); }
.hz-bullet-val { font-family: var(--font-head); font-size: 28px; color: var(--black); }
.hz-bullet-track {
    width: 100%; height: 12px;
    background: var(--g100);
    border-radius: var(--radius);
    position: relative;
    overflow: hidden;
}
.hz-bullet-fill {
    height: 100%;
    background: var(--black);
}
.hz-bullet-thresh {
    position: absolute; top: 0; bottom: 0; width: 2px; background: var(--g300);
}

/* Tables */
.hz-table-wrap {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: var(--sp-6);
    font-size: 13px;
}
.hz-table-wrap th {
    font-size: 11px;
    font-weight: 600;
    color: var(--g500);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-bottom: 2px solid var(--g200);
    padding: var(--sp-3) var(--sp-2);
    text-align: left;
}
.hz-table-wrap td {
    padding: var(--sp-3) var(--sp-2);
    border-bottom: 1px solid var(--g100);
    color: var(--g700);
}
.hz-table-wrap .num { text-align: right; font-variant-numeric: tabular-nums; color: var(--black); }
.hz-table-wrap tr:hover td { background: var(--g100); transition: background var(--dur) var(--ease); }
.hz-table-wrap tr.unfunded td { color: var(--g500); }

/* Status indicators */
.hz-status-breach { color: var(--pwc-red); font-weight: 600; }
.hz-status-watch { color: #d09600; font-weight: 600; }
.hz-status-ok { color: var(--g900); font-weight: 600; }

/* Verdict Banner */
.hz-verdict {
    padding: var(--sp-5);
    margin-bottom: var(--sp-6);
    border-radius: var(--radius-card);
}
.hz-verdict.kill { background: var(--red-tint); color: var(--pwc-red); border-left: 4px solid var(--pwc-red); }
.hz-verdict.blocked { background: var(--red-tint); border-left: 4px solid var(--black); }
.hz-verdict.modernize { background: var(--yellow-tint); color: var(--black); border-left: 4px solid var(--pwc-yellow); }
.hz-verdict.hold { background: var(--grey-tint); color: var(--black); border-left: 4px solid var(--g300); }

.hz-verdict-title { font-family: var(--font-head); font-size: 20px; margin-bottom: var(--sp-2); }
.hz-verdict-body { font-size: 14px; line-height: 1.5; }

/* Callouts (LLM) */
.hz-callout {
    background: var(--paper);
    border: var(--border);
    border-left: 4px solid var(--g300);
    padding: var(--sp-4) var(--sp-5);
    margin: var(--sp-4) 0;
    border-radius: var(--radius-card);
}
.hz-callout.bet { border-left-color: var(--pwc-orange); }
.hz-callout.win { border-left-color: var(--pwc-tangerine); }
.hz-callout.park { border-left-color: var(--pwc-yellow); }
.hz-callout-title { font-weight: bold; font-size: 15px; color: var(--black); margin-bottom: 4px; }
.hz-callout-desc { font-size: 13px; color: var(--g700); line-height: 1.4; }

/* ══════════════════════════════════════════════════════════════════════════
   LANDING PAGE
   ══════════════════════════════════════════════════════════════════════════ */
.hz-landing {
    padding: var(--sp-8) 0;
    max-width: 900px;
    margin: 0 auto;
}
.hz-landing-h1 {
    font-family: var(--font-head);
    font-size: 52px;
    line-height: 1.15;
    color: var(--black);
    margin-bottom: var(--sp-4);
}
.hz-landing-desc {
    font-size: 20px;
    line-height: 1.5;
    color: var(--g700);
    margin-bottom: var(--sp-8);
}
.hz-feat-grid {
    display: flex; gap: var(--sp-8);
    margin-top: var(--sp-8);
}
.hz-feat-col {
    flex: 1;
    border-top: 2px solid var(--g200);
    padding-top: var(--sp-4);
}
.hz-feat-col-title {
    font-family: var(--font-head);
    font-size: 20px;
    color: var(--black);
    margin-bottom: var(--sp-2);
}
.hz-feat-col-desc {
    font-size: 14px; color: var(--g700);
    line-height: 1.4;
}
</style>

"""
