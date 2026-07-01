"""
ui/theme.py
PwC-inspired visual theme for the AI Investment Advisory Platform.

Design system (rebuilt to Fortune-100 / FANG product standards):
  • Strict 8px spacing grid              → no arbitrary gaps, no dead whitespace
  • Modular type scale (Georgia + Arial) → clear hierarchy, correct sizes
  • Refined neutral ramp + single accent → calm, premium, high-contrast
  • Considered form controls             → cards, selects, sliders, inputs
  • Subtle depth & motion                → restrained shadows, 150ms easing

Injects custom CSS that overrides Streamlit defaults and defines reusable
component classes for the consulting-grade dashboard.
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
/* ══════════════════════════════════════════════════════════════════════════
   DESIGN TOKENS
   Georgia (serif) for headings, Arial/Helvetica (sans) for body — both system
   fonts, so there is no external webfont load and nothing to FOUC.
   ══════════════════════════════════════════════════════════════════════════ */
:root {
    /* ── Brand ── */
    --brand:            #D04A02;   /* PwC orange, primary action */
    --brand-deep:       #A63A01;   /* hover / pressed */
    --brand-press:      #8A3001;
    --brand-tint:       rgba(208, 74, 2, 0.08);
    --brand-tint-2:     rgba(208, 74, 2, 0.14);
    --brand-gradient:   linear-gradient(135deg, #D04A02 0%, #F37021 100%);

    /* ── Ink (neutral ramp, warm-cool balanced) ── */
    --ink-900:          #11161C;   /* near-black headings */
    --ink-800:          #1A1F26;
    --ink-700:          #2E353D;
    --ink-600:          #4A525C;   /* body text */
    --ink-500:          #6B7480;   /* secondary text */
    --ink-400:          #9AA2AD;   /* muted / captions */
    --ink-300:          #C6CCD3;
    --ink-200:          #E3E7EC;   /* borders */
    --ink-150:          #EDF0F3;   /* light borders / hairlines */
    --ink-100:          #F4F6F8;   /* subtle fills */
    --ink-50:           #FAFBFC;   /* page background */
    --white:            #FFFFFF;

    /* ── Status ── */
    --green:            #1B9C6B;
    --green-tint:       rgba(27, 156, 107, 0.10);
    --amber:            #E8A317;
    --amber-tint:       rgba(232, 163, 23, 0.12);
    --red:              #D0342C;
    --red-tint:         rgba(208, 52, 44, 0.10);
    --blue:             #1F6FEB;
    --blue-tint:        rgba(31, 111, 235, 0.10);
    --violet:           #6C5CE7;

    /* ── Spacing scale (8px grid) ── */
    --sp-1: 4px;  --sp-2: 8px;  --sp-3: 12px; --sp-4: 16px;
    --sp-5: 20px; --sp-6: 24px; --sp-8: 32px; --sp-10: 40px; --sp-12: 48px;

    /* ── Radius ── */
    --r-sm: 6px; --r-md: 10px; --r-lg: 14px; --r-pill: 999px;

    /* ── Elevation (soft, layered, never heavy) ── */
    --sh-xs:   0 1px 2px rgba(17, 22, 28, 0.05);
    --sh-sm:   0 1px 3px rgba(17, 22, 28, 0.06), 0 1px 2px rgba(17, 22, 28, 0.04);
    --sh-md:   0 4px 12px rgba(17, 22, 28, 0.07), 0 2px 4px rgba(17, 22, 28, 0.04);
    --sh-lg:   0 12px 28px rgba(17, 22, 28, 0.10), 0 4px 8px rgba(17, 22, 28, 0.05);
    --sh-brand:0 8px 22px rgba(208, 74, 2, 0.22);

    /* ── Motion ── */
    --ease: cubic-bezier(0.22, 0.61, 0.36, 1);

    /* ── Legacy aliases (kept so existing markup never breaks) ── */
    --brand-primary: var(--brand);
    --brand-primary-ghost: var(--brand-tint);
    --pwc-black: var(--ink-900);
    --pwc-orange: var(--brand);
    --pwc-orange-ghost: var(--brand-tint);
    --pwc-red: var(--brand);
    --pwc-yellow: var(--amber);
    --pwc-yellow-ghost: var(--amber-tint);
    --pwc-rose: var(--red);
    --grey-text: var(--ink-500);
    --grey-label: var(--ink-400);
    --grey-border: var(--ink-200);
    --grey-border-light: var(--ink-150);
    --border: var(--ink-200);
    --border-light: var(--ink-150);
    --grey-50: var(--ink-50);
    --grey-100: var(--ink-100);
    --grey-200: var(--ink-150);
    --grey-300: var(--ink-300);
    --grey-400: var(--ink-400);
    --grey-600: var(--ink-600);
    --surface-bg: var(--ink-50);
    --green-ghost: var(--green-tint);
    --blue-ghost: var(--blue-tint);
    --sidebar-bg: #14181E;
    --shadow-sm: var(--sh-sm);
    --shadow-md: var(--sh-md);
    --shadow-hover: var(--sh-lg);
    --phase-teal: var(--green);
}

/* ══════════════════════════════════════════════════════════════════════════
   GLOBAL TYPOGRAPHY & RESET
   ══════════════════════════════════════════════════════════════════════════ */
html, body, [class*="css"], .stMarkdown, .stMarkdown p, .stApp,
[data-testid="stMetricLabel"], [data-testid="stMetricValue"],
input, textarea, button, select,
.stSelectbox, .stSlider, .stRadio, .stTextInput, .stTextArea, .stNumberInput {
    font-family: Arial, 'Helvetica Neue', Helvetica, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-rendering: optimizeLegibility;
}

body, .stApp { color: var(--ink-600); font-size: 14px; line-height: 1.6; }

h1, h2, h3, h4, h5, h6,
.aia-header-title, .lp-h1, .lp-h1-accent, .aia-section-intro-title,
.aia-sec-title, .aia-q-section-title, .lp-sect-h2, .aia-dash-strip-title {
    font-family: Georgia, 'Times New Roman', serif;
    color: var(--ink-900);
    letter-spacing: -0.01em;
}

/* Reusable dashboard section title (serif, tight rhythm) */
.aia-sec-title {
    font-size: 20px;
    font-weight: 700;
    color: var(--ink-900);
    margin: var(--sp-1) 0 var(--sp-4);
    padding-bottom: var(--sp-2);
    border-bottom: 1px solid var(--ink-200);
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }

/* Keep Streamlit header transparent so it doesn't cover the black banner, but allow clicks on the sidebar toggle */
header[data-testid="stHeader"] {
    background: transparent !important;
    pointer-events: none !important;
}

[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] {
    pointer-events: auto !important;
    background-color: var(--brand) !important;
    border: 1px solid rgba(255,255,255,0.3) !important;
    border-radius: var(--r-md) !important;
    margin: 8px !important;
    z-index: 999999 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 44px !important;
    height: 44px !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5) !important;
}
[data-testid="collapsedControl"]:hover,
[data-testid="stSidebarCollapsedControl"]:hover {
    background-color: var(--brand-deep) !important;
    border-color: #fff !important;
}
[data-testid="collapsedControl"] svg,
[data-testid="stSidebarCollapsedControl"] svg {
    fill: #fff !important;
    width: 24px !important;
    height: 24px !important;
}

/* ── App background ── */
.stApp, [data-testid="stAppViewContainer"] { background: var(--ink-50) !important; }

/* ── Layout container: narrower + tighter so content never floats in voids ── */
.block-container, [data-testid="stMainBlockContainer"] {
    padding: 0 var(--sp-6) var(--sp-10) !important;
    max-width: 100% !important;
    padding-top: 0 !important;
}

/* Trim Streamlit's default vertical gaps between blocks (kills dead whitespace) */
[data-testid="stVerticalBlock"] { gap: var(--sp-3) !important; }
.element-container { margin-bottom: 0 !important; }
[data-testid="stHorizontalBlock"] { gap: var(--sp-4) !important; }

/* ══════════════════════════════════════════════════════════════════════════
   SIDEBAR
   ══════════════════════════════════════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #171C23 0%, #0F1318 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
[data-testid="stSidebarUserContent"] { padding-top: var(--sp-6) !important; }
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] label {
    color: rgba(255,255,255,0.82) !important;
    font-size: 11px !important;
    font-weight: 500 !important;
}

/* ══════════════════════════════════════════════════════════════════════════
   TOP HEADER BAR
   ══════════════════════════════════════════════════════════════════════════ */
.aia-header {
    background: var(--ink-900);
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 var(--sp-6) 0 60px;
    margin: 0 calc(-1 * var(--sp-6)) 0;
    border-bottom: 3px solid var(--brand);
}
.aia-header-left { display: flex; flex-direction: column; gap: 2px; }
.aia-header-title {
    font-size: 15px; font-weight: 700; color: #fff;
    letter-spacing: 0.02em;
}
.aia-header-sub {
    font-size: 10.5px; color: rgba(255,255,255,0.50);
    letter-spacing: 0.03em; text-transform: uppercase; font-weight: 600;
}
.aia-header-right { display: flex; align-items: center; gap: var(--sp-3); }
.aia-header-badge {
    font-size: 12px; font-weight: 700; color: #fff;
    background: var(--brand); padding: 4px 12px; border-radius: var(--r-pill);
    letter-spacing: 0.1em; text-transform: uppercase;
}
.aia-header-version {
    font-size: 10px; color: rgba(255,255,255,0.35); letter-spacing: 0.04em;
}

/* ══════════════════════════════════════════════════════════════════════════
   SIDEBAR BRAND PANEL
   ══════════════════════════════════════════════════════════════════════════ */
.aia-sidebar-brand {
    background: rgba(208,74,2,0.10);
    border: 1px solid rgba(208,74,2,0.22);
    border-left: 3px solid var(--brand);
    border-radius: var(--r-sm);
    padding: var(--sp-3) var(--sp-4);
    margin-bottom: var(--sp-5);
}
.aia-sidebar-brand-title {
    font-size: 12px; font-weight: 700; color: #F49B6A;
    letter-spacing: 0.04em; text-transform: uppercase; margin-bottom: 3px;
}
.aia-sidebar-brand-sub {
    font-size: 10.5px; color: rgba(255,255,255,0.55); line-height: 1.55;
}
.aia-sidebar-section-label {
    font-size: 9px; font-weight: 700; letter-spacing: 0.14em;
    text-transform: uppercase; color: rgba(255,255,255,0.38);
    margin-bottom: var(--sp-3); padding-bottom: var(--sp-2);
    border-bottom: 1px solid rgba(255,255,255,0.08);
}

/* ══════════════════════════════════════════════════════════════════════════
   WIZARD STEPPER  (sticky, glassy, refined pills + segmented progress)
   ══════════════════════════════════════════════════════════════════════════ */
.aia-stepper-pills {
    display: flex; align-items: center; justify-content: center;
    flex-wrap: wrap; gap: var(--sp-2);
    padding: var(--sp-3) 0;
    margin: 0 calc(-1 * var(--sp-6)) var(--sp-2);
    background: rgba(250, 251, 252, 0.88);
    backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
    border-bottom: 1px solid var(--ink-150);
    position: sticky; top: 0; z-index: 100;
}
.aia-step-pill {
    display: flex; align-items: center; gap: var(--sp-2);
    padding: 7px 14px; border-radius: var(--r-pill);
    border: 1px solid var(--ink-200); background: var(--white);
    color: var(--ink-500); font-size: 11px; font-weight: 600;
    transition: all 0.18s var(--ease);
}
.aia-step-pill:hover { border-color: var(--ink-300); color: var(--ink-700); }
.aia-step-pill.completed {
    border-color: rgba(27,156,107,0.35); background: var(--green-tint);
    color: var(--green);
}
.aia-step-pill.active {
    background: var(--brand-gradient); border-color: transparent;
    color: #fff; box-shadow: var(--sh-brand);
}
.aia-step-pill-check {
    display: inline-flex; align-items: center; justify-content: center;
    min-width: 16px; height: 16px; border-radius: var(--r-pill);
    font-size: 12px; font-weight: 800;
    background: rgba(0,0,0,0.06);
}
.aia-step-pill.active .aia-step-pill-check { background: rgba(255,255,255,0.25); }
.aia-step-pill.completed .aia-step-pill-check { background: rgba(27,156,107,0.18); }
.aia-step-pill-label { text-transform: uppercase; letter-spacing: 0.06em; }

.aia-progress-bar-wrap {
    height: 4px; background: var(--ink-150);
    margin: 0 calc(-1 * var(--sp-6)) var(--sp-6);
    position: relative; overflow: hidden;
}
.aia-progress-bar-fill {
    height: 100%; background: var(--brand-gradient);
    transition: width 0.45s var(--ease);
}
.aia-progress-text {
    font-size: 11px; color: var(--ink-400); text-align: right; margin: var(--sp-2) 0 0;
}

/* ══════════════════════════════════════════════════════════════════════════
   SECTION INTRO PANEL  (the header at the top of each wizard page)
   ══════════════════════════════════════════════════════════════════════════ */
.aia-section-intro {
    background: var(--white);
    border: 1px solid var(--ink-150);
    border-left: 3px solid var(--brand);
    border-radius: var(--r-md);
    padding: var(--sp-5) var(--sp-6);
    margin: 0 0 var(--sp-5);
    box-shadow: var(--sh-xs);
}
.aia-section-intro-icon { font-size: 20px; margin-bottom: var(--sp-2); }
.aia-section-intro-id {
    font-size: 10px; font-weight: 800; letter-spacing: 0.16em;
    text-transform: uppercase; color: var(--brand); margin-bottom: 6px;
}
.aia-section-intro-title {
    font-size: 22px; font-weight: 700; color: var(--ink-900);
    line-height: 1.25; margin-bottom: 5px;
}
.aia-section-intro-subtitle {
    font-size: 11px; font-weight: 600; color: var(--ink-500);
    text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: var(--sp-3);
}
.aia-section-intro-desc {
    font-size: 13.5px; color: var(--ink-600); line-height: 1.65; max-width: 720px;
}

/* ══════════════════════════════════════════════════════════════════════════
   QUESTION CARDS  (the heart of the intake experience)
   Clean header row · numbered chip · inline rationale · subtle tag pills.
   ══════════════════════════════════════════════════════════════════════════ */
.aia-qcard {
    background: var(--white);
    border: 1px solid var(--ink-150);
    border-radius: var(--r-lg);
    padding: var(--sp-6) var(--sp-8);
    margin-bottom: var(--sp-5);
    box-shadow: 0 4px 16px rgba(0,0,0,0.03);
    transition: all 0.2s var(--ease);
    position: relative;
    overflow: hidden;
}
.aia-qcard::before {
    content: ''; position: absolute; left: 0; top: 0; bottom: 0;
    width: 4px; background: var(--brand); opacity: 1;
}
.aia-qcard:hover {
    border-color: var(--ink-200); box-shadow: 0 8px 24px rgba(0,0,0,0.08);
    transform: translateY(-2px);
}
.aia-qcard:focus-within { border-color: var(--brand); box-shadow: 0 0 0 3px var(--brand-tint); }

.aia-qcard-header {
    display: flex; align-items: flex-start; gap: var(--sp-4); margin-bottom: var(--sp-3);
}
.aia-qcard-id {
    display: inline-flex; align-items: center; justify-content: center;
    min-width: 48px; height: 26px; padding: 0 12px;
    font-size: 11px; font-weight: 800; letter-spacing: 0.05em;
    color: #fff; background: var(--brand);
    border-radius: var(--r-pill); flex-shrink: 0; margin-top: 2px;
    font-family: 'Courier New', monospace;
}
.aia-qcard-text {
    font-size: 18px; font-weight: 600; color: var(--ink-900);
    line-height: 1.4; flex: 1; letter-spacing: -0.01em;
}
.aia-qcard-rationale {
    font-size: 13.5px; color: var(--ink-600); line-height: 1.6;
    padding: var(--sp-1) 0 var(--sp-1) var(--sp-4); 
    border-left: 2px solid var(--ink-200); 
    margin: 0 0 var(--sp-4) 64px;
    font-style: italic;
}
.aia-qcard-rationale::before {
    content: "STRATEGIC RATIONALE — ";
    font-size: 10px; font-weight: 800; letter-spacing: 0.12em;
    color: var(--brand); font-style: normal;
}
.aia-qcard-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: var(--sp-4); margin-left: 64px; }
.aia-qcard-tag {
    display: inline-block; font-size: 10px; font-weight: 700;
    letter-spacing: 0.05em; text-transform: uppercase;
    padding: 4px 10px; border-radius: var(--r-pill);
    background: var(--ink-50); color: var(--ink-600);
    border: 1px solid var(--ink-200);
}
.aia-qcard-input { margin-top: var(--sp-3); margin-left: 64px; }

/* Sub-objective label inside the dynamic KPI block */
.aia-kpi-obj-label {
    font-size: 12px; font-weight: 700; color: var(--ink-800);
    margin: var(--sp-3) 0 var(--sp-1); padding: 6px 10px;
    background: var(--brand-tint); border-left: 3px solid var(--brand);
    border-radius: 0 var(--r-sm) var(--r-sm) 0;
}
.aia-kpi-empty {
    font-size: 12.5px; color: var(--ink-500); padding: var(--sp-3) var(--sp-4);
    background: var(--ink-50); border: 1px dashed var(--ink-200);
    border-radius: var(--r-sm); line-height: 1.55;
}

/* ══════════════════════════════════════════════════════════════════════════
   FORM CONTROLS  (selects, text, number, sliders) — the single biggest
   lever on "does this feel premium". Consistent ~42px control height.
   ══════════════════════════════════════════════════════════════════════════ */

/* Field labels */
.aia-field-label {
    display: block; font-size: 12px; font-weight: 700; color: var(--ink-900);
    margin-bottom: 3px; letter-spacing: 0.01em;
}
.aia-field-sublabel {
    display: block; font-size: 11px; color: var(--ink-400);
    margin-bottom: var(--sp-2); line-height: 1.45;
}

/* Selectbox */
.stSelectbox [data-baseweb="select"] > div {
    border-radius: var(--r-sm) !important;
    border: 1px solid var(--ink-200) !important;
    background: var(--white) !important;
    min-height: 42px !important;
    box-shadow: none !important;
    transition: border-color 0.15s var(--ease), box-shadow 0.15s var(--ease);
}
.stSelectbox [data-baseweb="select"] > div:hover { border-color: var(--ink-300) !important; }
.stSelectbox [data-baseweb="select"]:focus-within > div {
    border-color: var(--brand) !important;
    box-shadow: 0 0 0 3px var(--brand-tint) !important;
}
.stSelectbox [data-baseweb="select"] span,
.stSelectbox [data-baseweb="select"] input {
    font-size: 13px !important; color: var(--ink-800) !important;
}

/* Multiselect tags */
.stMultiSelect [data-baseweb="tag"] {
    background: var(--brand) !important; border-radius: var(--r-sm) !important;
}

/* Dropdown menu popover */
[data-baseweb="popover"] [role="listbox"] {
    border-radius: var(--r-sm) !important; box-shadow: var(--sh-lg) !important;
    border: 1px solid var(--ink-200) !important;
}
[data-baseweb="popover"] [role="option"] { font-size: 13px !important; padding: 9px 12px !important; }

/* Text & number inputs */
.stTextInput input, .stTextArea textarea, .stNumberInput input {
    border: 1px solid var(--ink-200) !important;
    border-radius: var(--r-sm) !important;
    font-size: 13px !important;
    padding: 10px 12px !important;
    background: var(--white) !important;
    color: var(--ink-900) !important;
    box-shadow: none !important;
    transition: border-color 0.15s var(--ease), box-shadow 0.15s var(--ease) !important;
}
.stTextInput input::placeholder, .stTextArea textarea::placeholder { color: var(--ink-400) !important; }
.stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus {
    border-color: var(--brand) !important; outline: none !important;
    box-shadow: 0 0 0 3px var(--brand-tint) !important;
}
.stTextArea textarea { min-height: 84px !important; line-height: 1.55 !important; }

/* Number input stepper buttons */
.stNumberInput button {
    border: 1px solid var(--ink-200) !important; background: var(--ink-50) !important;
    color: var(--ink-600) !important; border-radius: var(--r-sm) !important;
}

/* Sliders — slimmer track, branded thumb */
.stSlider [data-baseweb="slider"] { padding-top: 4px !important; }
.stSlider [data-testid="stTickBar"] { display: none !important; }
.stSlider [role="slider"] {
    background: var(--white) !important;
    border: 3px solid var(--brand) !important;
    box-shadow: var(--sh-sm) !important;
    height: 18px !important; width: 18px !important;
}
.stSlider [data-baseweb="slider"] > div > div { background: var(--brand) !important; }
.stSlider [data-testid="stThumbValue"] {
    color: var(--brand-deep) !important; font-weight: 700 !important; font-size: 12px !important;
}

/* ══════════════════════════════════════════════════════════════════════════
   BUTTONS
   ══════════════════════════════════════════════════════════════════════════ */
div.stButton > button {
    background: var(--brand) !important;
    color: #fff !important;
    border: none !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    padding: 11px 22px !important;
    border-radius: var(--r-sm) !important;
    letter-spacing: 0.01em !important;
    box-shadow: var(--sh-xs) !important;
    transition: background 0.15s var(--ease), transform 0.12s var(--ease),
                box-shadow 0.15s var(--ease) !important;
}
div.stButton > button:hover {
    background: var(--brand-deep) !important;
    transform: translateY(-1px) !important;
    box-shadow: var(--sh-md) !important;
}
div.stButton > button:active {
    background: var(--brand-press) !important; transform: translateY(0) !important;
}
/* Secondary (Previous / Reset) buttons read as outline */
div.stButton > button[kind="secondary"] {
    background: var(--white) !important; color: var(--ink-700) !important;
    border: 1px solid var(--ink-200) !important; box-shadow: none !important;
}
div.stButton > button[kind="secondary"]:hover {
    background: var(--ink-50) !important; border-color: var(--ink-300) !important;
}

/* ══════════════════════════════════════════════════════════════════════════
   PENDING STATE
   ══════════════════════════════════════════════════════════════════════════ */
.aia-pending {
    background: var(--white); border: 1px dashed var(--ink-200);
    border-radius: var(--r-lg); padding: var(--sp-12) var(--sp-6); text-align: center;
}
.aia-pending-icon {
    width: 44px; height: 44px; border-radius: var(--r-md);
    background: var(--brand-tint); border: 1px solid rgba(208,74,2,0.20);
    margin: 0 auto var(--sp-4); display: flex; align-items: center; justify-content: center;
}
.aia-pending-icon-inner { width: 14px; height: 14px; border-radius: 4px; background: var(--brand); }
.aia-pending-title { font-size: 15px; font-weight: 700; color: var(--ink-800); margin-bottom: 6px; font-family: Georgia, serif; }
.aia-pending-sub { font-size: 12.5px; color: var(--ink-400); line-height: 1.6; max-width: 340px; margin: 0 auto; }

/* ══════════════════════════════════════════════════════════════════════════
   GENERIC CARD / METRIC / FLAGS
   ══════════════════════════════════════════════════════════════════════════ */
.aia-card {
    background: var(--white); border: 1px solid var(--ink-150);
    border-radius: var(--r-md); box-shadow: var(--sh-sm);
    padding: var(--sp-5) var(--sp-6); margin-bottom: var(--sp-3);
}
.aia-card.orange-top { border-top: 3px solid var(--brand); }
.aia-card.green-top  { border-top: 3px solid var(--green); }
.aia-card.blue-top   { border-top: 3px solid var(--blue); }
.aia-card.red-top    { border-top: 3px solid var(--red); }

.aia-section-label {
    font-size: 12px; font-weight: 700; letter-spacing: 0.14em;
    text-transform: uppercase; color: var(--ink-400);
    margin-bottom: var(--sp-3); padding-bottom: var(--sp-2);
    border-bottom: 1px solid var(--ink-150);
}
.aia-section-title { font-size: 15px; font-weight: 700; color: var(--ink-900); margin-bottom: 4px; }

.aia-metric-card {
    background: var(--white); border: 1px solid var(--ink-200);
    border-radius: var(--r-md); padding: var(--sp-5); height: 100%;
    box-shadow: var(--sh-sm); transition: all 0.2s var(--ease);
}
.aia-metric-card:hover { transform: translateY(-3px); box-shadow: var(--sh-lg); border-color: var(--ink-300); }
.aia-metric-label { font-size: 11px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: var(--ink-400); margin-bottom: var(--sp-2); }
.aia-metric-value { font-size: 30px; font-weight: 800; line-height: 1; font-variant-numeric: tabular-nums; letter-spacing: -0.02em; color: var(--ink-900); }
.aia-metric-value .sym { font-size: 18px; font-weight: 500; color: var(--ink-400); }

.aia-flag { display: flex; align-items: flex-start; gap: var(--sp-2); padding: var(--sp-3); border: 1px solid; border-radius: var(--r-sm); margin-bottom: var(--sp-2); }
.aia-flag.warning { background: var(--amber-tint); border-color: rgba(232,163,23,0.30); border-left: 3px solid var(--amber); }
.aia-flag.danger  { background: var(--red-tint); border-color: rgba(208,52,44,0.25); border-left: 3px solid var(--red); }
.aia-flag.info    { background: var(--blue-tint); border-color: rgba(31,111,235,0.22); border-left: 3px solid var(--blue); }
.aia-flag-label { font-size: 12px; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 2px; }
.aia-flag.warning .aia-flag-label { color: #9A6B00; }
.aia-flag.danger  .aia-flag-label { color: var(--red); }
.aia-flag.info    .aia-flag-label { color: var(--blue); }
.aia-flag-text { font-size: 12px; color: var(--ink-600); line-height: 1.5; }

/* ══════════════════════════════════════════════════════════════════════════
   CHARTS / TABLES / EXPANDERS / TABS
   ══════════════════════════════════════════════════════════════════════════ */
.stPlotlyChart {
    background: var(--white) !important; border: 1px solid var(--ink-150) !important;
    border-radius: var(--r-md) !important; box-shadow: var(--sh-sm) !important;
    padding: var(--sp-2) !important;
}
[data-testid="stDataFrame"] {
    border: 1px solid var(--ink-150) !important; border-radius: var(--r-md) !important;
    box-shadow: var(--sh-sm) !important; overflow: hidden !important;
}
[data-testid="stExpander"] {
    border: 1px solid var(--ink-150) !important; border-radius: var(--r-md) !important;
    box-shadow: var(--sh-xs) !important; background: var(--white) !important;
}
[data-testid="stExpander"] summary { font-size: 13px !important; font-weight: 600 !important; color: var(--ink-800) !important; }
.stTabs [data-baseweb="tab-list"] { gap: var(--sp-1); border-bottom: 1px solid var(--ink-150); }
.stTabs [data-baseweb="tab"] {
    font-size: 12.5px !important; font-weight: 600 !important; color: var(--ink-500) !important;
    padding: 10px 14px !important;
}
.stTabs [aria-selected="true"] { color: var(--brand) !important; }
.stTabs [data-baseweb="tab-highlight"] { background: var(--brand) !important; }

/* ══════════════════════════════════════════════════════════════════════════
   SCROLLBAR
   ══════════════════════════════════════════════════════════════════════════ */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: var(--ink-100); }
::-webkit-scrollbar-thumb { background: var(--ink-300); border-radius: var(--r-pill); }
::-webkit-scrollbar-thumb:hover { background: var(--ink-400); }

/* ══════════════════════════════════════════════════════════════════════════
   DASHBOARD STRIP
   ══════════════════════════════════════════════════════════════════════════ */
.aia-dash-strip {
    background: var(--ink-900); padding: var(--sp-5) var(--sp-6);
    margin: 0 0 var(--sp-5); border-bottom: 3px solid var(--brand);
    border-radius: var(--r-md) var(--r-md) 0 0;
}
.aia-dash-strip-badge-row { display: flex; align-items: center; gap: var(--sp-2); margin-bottom: var(--sp-2); }
.aia-dash-badge { font-size: 8.5px; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; color: #fff; background: var(--brand); padding: 3px 10px; border-radius: var(--r-pill); }
.aia-dash-strip-title { font-size: 22px; font-weight: 700; color: #fff; line-height: 1.15; margin-bottom: 3px; }
.aia-dash-strip-sub { font-size: 11px; color: rgba(255,255,255,0.50); letter-spacing: 0.02em; }
.aia-dash-strip-date { font-size: 12px; color: rgba(255,255,255,0.30); margin-left: auto; letter-spacing: 0.04em; }

/* ══════════════════════════════════════════════════════════════════════════
   LANDING PAGE
   ══════════════════════════════════════════════════════════════════════════ */
.lp-hero {
    background: radial-gradient(120% 140% at 80% 0%, #2A1A10 0%, #14181E 55%, #0F1318 100%);
    margin: 0 calc(-1 * var(--sp-6));
    padding: var(--sp-12) var(--sp-12);
    display: grid; grid-template-columns: 1.45fr 1fr; gap: var(--sp-12);
    align-items: center; position: relative; overflow: hidden;
    border-bottom: 3px solid var(--brand);
    animation: lp-fade-in 0.5s var(--ease);
}
.lp-hero::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, var(--brand), transparent);
}
.lp-hero-left, .lp-hero-right { min-width: 0; }
.lp-badge {
    display: inline-block; font-size: 12px; font-weight: 700; letter-spacing: 0.14em;
    text-transform: uppercase; color: #F49B6A;
    background: rgba(208,74,2,0.14); border: 1px solid rgba(208,74,2,0.30);
    padding: 5px 14px; border-radius: var(--r-pill); margin-bottom: var(--sp-5);
}
.lp-h1 { font-size: 48px; font-weight: 800; color: #fff; line-height: 1.06; margin: 0 0 var(--sp-4); letter-spacing: -0.025em; }
.lp-h1-accent { color: var(--brand); }
.lp-tagline { font-size: 15px; color: rgba(255,255,255,0.58); line-height: 1.7; max-width: 520px; margin: 0 0 var(--sp-6); }
.lp-tag-row { display: flex; flex-wrap: wrap; gap: var(--sp-2); margin-bottom: var(--sp-5); }
.lp-tag { font-size: 10.5px; font-weight: 600; color: rgba(255,255,255,0.68); background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12); padding: 6px 13px; border-radius: var(--r-pill); letter-spacing: 0.03em; }
.lp-hero-cta-hint { font-size: 11px; color: rgba(255,255,255,0.32); letter-spacing: 0.02em; margin-top: var(--sp-1); }
.lp-hero-cta-hint strong { color: rgba(255,255,255,0.55); }

.lp-dashboard-mock {
    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.10);
    border-top: 3px solid var(--brand); border-radius: var(--r-md);
    overflow: hidden; animation: lp-float 6s ease-in-out infinite; box-shadow: var(--sh-lg);
}
.lp-mock-topbar { display: flex; align-items: center; gap: var(--sp-2); padding: var(--sp-3) var(--sp-4); border-bottom: 1px solid rgba(255,255,255,0.07); background: rgba(255,255,255,0.03); }
.lp-mock-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--brand); }
.lp-mock-topbar-title { font-size: 12px; font-weight: 600; color: rgba(255,255,255,0.55); letter-spacing: 0.08em; text-transform: uppercase; flex: 1; }
.lp-mock-topbar-badge { font-size: 8px; font-weight: 700; color: #F49B6A; border: 1px solid rgba(208,74,2,0.40); padding: 2px 8px; border-radius: var(--r-pill); letter-spacing: 0.10em; }
.lp-mock-kpi-row { display: flex; padding: var(--sp-3); gap: var(--sp-2); }
.lp-mock-kpi { flex: 1; padding: var(--sp-3); text-align: center; border-radius: var(--r-sm); }
.lp-kpi-orange { border-top: 2px solid var(--brand); background: rgba(208,74,2,0.08); }
.lp-kpi-blue   { border-top: 2px solid var(--blue); background: rgba(31,111,235,0.10); }
.lp-kpi-green  { border-top: 2px solid var(--green); background: rgba(27,156,107,0.08); }
.lp-mock-kpi-num { font-size: 17px; font-weight: 800; color: rgba(255,255,255,0.88); line-height: 1; margin-bottom: 4px; }
.lp-mock-kpi-lbl { font-size: 8px; color: rgba(255,255,255,0.38); letter-spacing: 0.08em; text-transform: uppercase; }
.lp-mock-chart-area { display: flex; align-items: flex-end; gap: var(--sp-2); padding: 0 var(--sp-3) var(--sp-3); height: 72px; }
.lp-mock-chart-bar-wrap { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; }
.lp-mock-chart-bar { width: 100%; background: rgba(255,255,255,0.12); border-radius: 3px 3px 0 0; }
.lp-bar-orange { background: rgba(208,74,2,0.55) !important; }
.lp-mock-chart-bar-lbl { font-size: 7px; color: rgba(255,255,255,0.28); text-align: center; letter-spacing: 0.04em; }
.lp-mock-ledger { border-top: 1px solid rgba(255,255,255,0.07); padding: var(--sp-3); }
.lp-mock-ledger-hdr { display: flex; justify-content: space-between; font-size: 8px; color: rgba(255,255,255,0.28); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: var(--sp-2); }
.lp-mock-ledger-row { display: flex; align-items: center; gap: 6px; font-size: 9px; padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.04); }
.lp-mock-ledger-alt { background: rgba(255,255,255,0.02); }
.lp-mock-ledger-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.lp-dot-orange { background: var(--brand); }
.lp-dot-blue   { background: var(--blue); }
.lp-dot-green  { background: var(--green); }
.lp-mock-ledger-name { flex: 1; color: rgba(255,255,255,0.52); }
.lp-mock-ledger-val { color: rgba(255,255,255,0.72); font-weight: 600; }

.lp-stats-ribbon { display: flex; align-items: center; background: var(--white); border-bottom: 1px solid var(--ink-150); box-shadow: var(--sh-sm); padding: var(--sp-6) var(--sp-12); margin: 0 calc(-1 * var(--sp-6)); }
.lp-stat-item { flex: 1; text-align: center; }
.lp-stat-num { font-size: 34px; font-weight: 800; color: var(--ink-900); letter-spacing: -0.02em; line-height: 1; margin-bottom: 6px; font-variant-numeric: tabular-nums; }
.lp-stat-lbl { font-size: 10.5px; font-weight: 600; color: var(--ink-400); text-transform: uppercase; letter-spacing: 0.08em; }
.lp-stat-sep { width: 1px; height: 46px; background: var(--ink-200); flex-shrink: 0; }

.lp-section { padding: var(--sp-12) var(--sp-12); margin: 0 calc(-1 * var(--sp-6)); }
.lp-grey  { background: var(--ink-100); border-top: 1px solid var(--ink-150); }
.lp-white { background: var(--white); border-top: 1px solid var(--ink-150); }
.lp-sect-header { text-align: center; margin-bottom: var(--sp-10); }
.lp-sect-eyebrow { font-size: 12px; font-weight: 700; letter-spacing: 0.16em; text-transform: uppercase; color: var(--brand); margin-bottom: var(--sp-3); }
.lp-sect-h2 { font-size: 28px; font-weight: 700; color: var(--ink-900); line-height: 1.25; margin-bottom: var(--sp-3); }
.lp-sect-sub { font-size: 13.5px; color: var(--ink-600); max-width: 580px; margin: 0 auto; line-height: 1.65; }

.lp-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--sp-5); }
.lp-feat-card { background: var(--white); border: 1px solid var(--ink-150); border-top: 3px solid var(--brand); border-radius: var(--r-md); padding: var(--sp-6); transition: transform 0.2s var(--ease), box-shadow 0.2s var(--ease); box-shadow: var(--sh-xs); }
.lp-feat-card:hover { transform: translateY(-4px); box-shadow: var(--sh-lg); }
.lp-feat-num { font-size: 30px; font-weight: 800; color: var(--brand); opacity: 0.28; margin-bottom: var(--sp-3); letter-spacing: -0.02em; }
.lp-feat-title { font-size: 14px; font-weight: 700; color: var(--ink-900); margin-bottom: var(--sp-2); line-height: 1.3; }
.lp-feat-desc { font-size: 12.5px; color: var(--ink-600); line-height: 1.65; }

.lp-steps-container { display: grid; grid-template-columns: 1fr auto 1fr auto 1fr; gap: 0; align-items: start; }
.lp-step-block { background: var(--white); border: 1px solid var(--ink-150); border-radius: var(--r-md); padding: var(--sp-6); position: relative; box-shadow: var(--sh-xs); }
.lp-step-block:nth-child(1) { border-top: 3px solid var(--brand); }
.lp-step-block:nth-child(3) { border-top: 3px solid var(--amber); }
.lp-step-block:nth-child(5) { border-top: 3px solid var(--blue); }
.lp-step-num-circle { display: inline-flex; align-items: center; justify-content: center; width: 38px; height: 38px; border-radius: var(--r-md); background: var(--ink-900); color: var(--brand); font-size: 14px; font-weight: 700; margin-bottom: var(--sp-3); }
.lp-step-title { font-size: 14px; font-weight: 700; color: var(--ink-900); margin-bottom: var(--sp-2); }
.lp-step-desc { font-size: 12.5px; color: var(--ink-600); line-height: 1.65; margin-bottom: var(--sp-3); }
.lp-step-duration { font-size: 10px; font-weight: 600; color: var(--brand); background: var(--brand-tint); border: 1px solid rgba(208,74,2,0.20); border-radius: var(--r-pill); display: inline-block; padding: 3px 12px; letter-spacing: 0.04em; }
.lp-step-arrow-col { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: var(--sp-6) var(--sp-3); color: var(--brand); }
.lp-arrow-line { width: 1px; height: 20px; background: rgba(208,74,2,0.25); margin-bottom: 4px; }
.lp-arrow-head { font-size: 18px; }

.lp-out-card { border: 1px solid var(--ink-150); border-radius: var(--r-md); padding: var(--sp-6); background: var(--white); transition: transform 0.2s var(--ease), box-shadow 0.2s var(--ease); box-shadow: var(--sh-xs); }
.lp-out-card:hover { transform: translateY(-4px); box-shadow: var(--sh-lg); }
.lp-out-orange { border-top: 3px solid var(--brand); }
.lp-out-blue   { border-top: 3px solid var(--blue); }
.lp-out-yellow { border-top: 3px solid var(--amber); }
.lp-out-label { font-size: 8.5px; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: var(--ink-400); margin-bottom: var(--sp-3); }
.lp-out-title { font-size: 14px; font-weight: 700; color: var(--ink-900); margin-bottom: var(--sp-2); line-height: 1.3; }
.lp-out-desc { font-size: 12.5px; color: var(--ink-600); line-height: 1.65; }

.lp-peer-strip { background: var(--ink-900); padding: var(--sp-5) var(--sp-12); margin: 0 calc(-1 * var(--sp-6)); border-top: 1px solid rgba(255,255,255,0.06); }
.lp-peer-strip-label { font-size: 8.5px; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; color: rgba(255,255,255,0.28); margin-bottom: var(--sp-3); }
.lp-peer-strip-logos { display: flex; flex-wrap: wrap; align-items: center; gap: var(--sp-3); }
.lp-peer-name { font-size: 11.5px; font-weight: 600; color: rgba(255,255,255,0.58); letter-spacing: 0.02em; }
.lp-peer-sep { color: rgba(255,255,255,0.15); font-size: 10px; }

.lp-footer-disc { background: var(--ink-100); border-top: 1px solid var(--ink-150); padding: var(--sp-4) var(--sp-12); font-size: 10.5px; color: var(--ink-400); line-height: 1.65; margin: 0 calc(-1 * var(--sp-6)); }
.lp-footer-disc strong { color: var(--ink-600); }

@keyframes lp-fade-in { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
@keyframes lp-float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }

/* Budget slider display value */
.aia-budget-display { font-size: 28px; font-weight: 800; color: var(--ink-900); letter-spacing: -0.02em; margin-top: -4px; }

/* ══════════════════════════════════════════════════════════════════════════
   FRAMEWORK 2 — VALUE-TYPE PORTFOLIO
   ══════════════════════════════════════════════════════════════════════════ */

/* Tag chips (value type) */
.vt-chip {
    display: inline-flex; align-items: center; gap: 4px;
    font-size: 10.5px; font-weight: 700; letter-spacing: 0.04em;
    padding: 2px 10px; border-radius: 8px; white-space: nowrap; line-height: 1.6;
}
.vt-chip--revenue      { background: rgba(59,109,17,0.12); color: #2a5009; }
.vt-chip--opprofit     { background: rgba(24,95,165,0.12); color: #0e3d6d; }
.vt-chip--productivity { background: rgba(186,117,23,0.12); color: #7a4d0f; }
.vt-chip .vt-cue {
    font-size: 9px; font-weight: 800;
    width: 14px; height: 14px; border-radius: 3px;
    display: inline-flex; align-items: center; justify-content: center;
}

/* Stacked bar */
.vp-bar {
    display: flex; width: 100%; height: 48px;
    border-radius: 10px; overflow: hidden; margin-bottom: 16px;
}
.vp-bar__seg {
    display: flex; align-items: center; justify-content: center;
    color: #fff; font-size: 12px; font-weight: 700;
    padding: 0 10px; white-space: nowrap; min-width: 0;
    transition: flex 0.3s cubic-bezier(0.22,0.61,0.36,1);
}

/* KPI card row */
.vp-kpi-row { display: flex; gap: 16px; margin-bottom: 16px; }
.vp-kpi {
    flex: 1; border-radius: 12px; border: 1px solid var(--ink-150);
    padding: 16px 20px; position: relative; overflow: hidden; background: var(--white);
}
.vp-kpi::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
}
.vp-kpi--revenue::before      { background: #3B6D11; }
.vp-kpi--opprofit::before     { background: #185FA5; }
.vp-kpi--productivity::before { background: #BA7517; }
.vp-kpi--empty { opacity: 0.45; }
.vp-kpi__pct { font-size: 28px; font-weight: 700; line-height: 1.1; margin-bottom: 2px; }
.vp-kpi__usd { font-size: 13px; font-weight: 700; color: var(--ink-600); margin-bottom: 6px; }
.vp-kpi__desc { font-size: 11.5px; color: var(--ink-400); line-height: 1.4; }
.vp-kpi__count { font-size: 10.5px; color: var(--ink-300); margin-top: 4px; }

/* Alignment strip */
.aia-align-strip {
    width: 100%; border-radius: 10px; padding: 14px 20px;
    font-size: 15px; font-weight: 700; line-height: 1.5;
}
.aia-align-strip--green  { background: #e8f5e9; color: #1b5e20; border: 1px solid #a5d6a7; }
.aia-align-strip--amber  { background: #fff8e1; color: #e65100; border: 1px solid #ffe082; }
.aia-align-strip--red    { background: #fce4ec; color: #b71c1c; border: 1px solid #ef9a9a; }

/* Quadrant legend */
.quad-legend {
    display: flex; gap: 24px; margin: 8px 0 4px; flex-wrap: wrap;
}
.quad-legend__item {
    display: flex; align-items: center; gap: 6px;
    font-size: 11px; color: var(--ink-500);
}
.quad-legend__dot { width: 10px; height: 10px; border-radius: 50%; }

/* ── Print overrides ── */
@media print {
    .stSidebar, .stToolbar, button,
    [data-testid="stExpander"] summary::marker { display: none !important; }
    .stApp { background: white !important; }
    .vp-bar, .aia-card, .vp-kpi, .stPlotlyChart { break-inside: avoid; }
}
</style>
"""

_HEADER_HTML = """
<div class="aia-header">
    <div class="aia-header-left">
        <div class="aia-header-title">AI Investment Prioritisation</div>
        <div class="aia-header-sub">FMCG / CPG Strategic Capital Allocation</div>
    </div>
    <div class="aia-header-right">
        <div class="aia-header-version">v1.0 — June 2026</div>
        <div class="aia-header-badge">C-Suite Edition</div>
    </div>
</div>
"""
