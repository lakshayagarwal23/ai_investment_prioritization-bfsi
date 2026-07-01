"""
ui/dashboard.py

Right column of the AI Investment Advisory Platform.
Renders an interactive, board-ready Executive Decision Report.

Report narrative (the order a board actually reads in):
  1. Capital-allocation decision      → the recommendation + readiness
  2. Investment roadmap               → when money is committed, phase by phase
  3. Strategic AI investment prioritisation      → the "why", in plain English
  4. Use-case prioritisation          → WHAT to build first (impact × feasibility)
  5. Strategic investment ledger      → WHERE the money goes + the evidence
  6. Capital allocation by phase      → how the spend is phased
  7. AI maturity assessment           → readiness context
  8. Competitive benchmarking         → sourced peer evidence + transferability
  9. Risk register & heat map         → what could go wrong + mitigations
"""

import re
import html
import streamlit as st
import plotly.graph_objects as go

from config.peer_corpus import PEER_INTELLIGENCE
from config.value_pools import (
    VALUE_TYPE, REVENUE, OPPROFIT, PRODUCTIVITY,
    COLORS as VT_COLORS, DISPLAY_NAME as VT_DISPLAY,
    SHORT_LABEL as VT_SHORT, IMPACT_MID, FEAS_MID
)


# ─────────────────────────────────────────────────────────────────────────────
# SHARED HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _h(html_str: str) -> None:
    flat = " ".join(line.strip() for line in html_str.splitlines())
    st.markdown(flat, unsafe_allow_html=True)


_SCRIPT_RE = re.compile(r"<(script|iframe|object|embed)[^>]*>.*?</\1>", re.I | re.S)


def _field(text: str) -> str:
    """Sanitize model/user text before rendering as HTML.
    Prevents LaTeX ($ → escaped) and strips injection vectors."""
    if not text:
        return ""
    text = str(text)
    text = html.escape(text)
    text = text.replace("$", r"\$")          # prevent Streamlit LaTeX
    return text


def _fmt_usd(val: float) -> str:
    if val >= 1_000_000:
        return f"&#36;{val / 1_000_000:.1f}M"
    if val >= 1_000:
        return f"&#36;{val / 1_000:.0f}K"
    return f"&#36;{val:,.0f}"


def _fmt_pct(val: float) -> str:
    return f"{val:.1f}%"


def _section_title(title: str, sub: str | None = None) -> None:
    """One consistent, serif section header used across the whole report."""
    html = f'<div class="aia-sec-title">{title}</div>'
    if sub:
        html += (f'<div style="font-size:12.5px; color:var(--ink-400); '
                 f'margin:-10px 0 16px; line-height:1.5;">{sub}</div>')
    st.markdown(html, unsafe_allow_html=True)


def _plotly_font() -> dict:
    return {"family": "Arial, Helvetica, sans-serif", "color": "#4A525C", "size": 12}


# ─────────────────────────────────────────────────────────────────────────────
# PENDING / LEGEND
# ─────────────────────────────────────────────────────────────────────────────
def render_pending_state() -> None:
    st.html("""
    <div class="aia-pending">
        <div class="aia-pending-icon">
            <div class="aia-pending-icon-inner"></div>
        </div>
        <div class="aia-pending-title">Executive Decision Engine Pending</div>
        <div class="aia-pending-sub">
            Complete the discovery flow to generate a fully quantified,
            interactive AI investment decision report.
        </div>
    </div>
    """)


def render_how_to_read() -> None:
    """Plain-English legend so a board reader knows the vocabulary."""
    with st.expander("How to read this report"):
        _h("""
        <div style="font-size:13px; color:var(--ink-600); line-height:1.85;">
        <b>Value types</b> — initiatives are classified into three canonical CPG pools: Revenue generation (green), Operating-profit enhancement (blue), and Productivity & scaling (amber).<br>
        <b>Phased funding</b> — the budget is committed in stages, not all at once.<br>
        <b>Phase 1 / 2 / 3</b> — the three stages of the programme.
        <b>Only Phase 1 is committed now</b>; later phases are provisional.<br>
        <b>Phase Validation</b> — a go / no-go review at the end of a phase. Later funding is released
        <i>only</i> if the phase requirements are validated.<br>
        <b>Allocation</b> — share of your budget assigned to this initiative, weighted by its priority and technical feasibility.<br>
        <b>Technical Feasibility</b> — proportion of each initiative deliverable given data quality, tech-debt and execution risk.<br>
        <b>Transferability</b> — how much of a peer's disclosed gain is plausibly attainable for you.
        </div>
        """)


# ─────────────────────────────────────────────────────────────────────────────
# 1 · DECISION BANNER  (R1 — qualitative tiles only, no financial projections)
# ─────────────────────────────────────────────────────────────────────────────
def render_decision_banner(payload: dict, plan: dict) -> None:
    dec = payload.get("executive_decision", {})
    action = plan.get("posture", dec.get("action", "PHASED START RECOMMENDED")).upper()
    # Posture-aware milestone and label text
    if "ADDRESS FOUNDATIONS FIRST" in plan.get("posture", ""):
        default_milestone = "Phase 1 Validation: data-readiness & baseline review"
        default_next = "Begin with the top-ranked prime candidates; release further funding only on Phase 1 Validation pass."
        risk_label = "Primary Risk to Manage"
    elif "INVEST NOW" in plan.get("posture", ""):
        default_milestone = "Phase 1 Delivery: data platform build & first AI pilot deployment"
        default_next = "Commence Phase 1 foundation build in parallel with detailed scoping of the highest-priority AI initiatives."
        risk_label = "Key Execution Consideration"
    else:
        default_milestone = "Phase 1 Validation: data-readiness & baseline review"
        default_next = "Commence Phase 1 foundation build in parallel with detailed scoping of the highest-priority AI initiatives."
        risk_label = "Primary Risk to Manage"
    milestone = _field(dec.get("milestone", default_milestone))
    next_steps = _field(dec.get("next_steps", default_next))
    conds = [_field(c) for c in dec.get("conditions", [])]

    # R1: three posture tiers drive the colour
    if "ADDRESS FOUNDATIONS FIRST" in action:
        color = "#D0342C"   # red  — must fix data estate before scaling AI
    elif "MANAGE EXECUTION RISK" in action:
        color = "#E8A317"   # amber — proceed carefully
    else:
        color = "#1B9C6B"   # green — proceed

    # R1: qualitative tiles (no financial projections — G0.1)
    readiness_tier  = _field(dec.get("readiness_tier", plan.get("maturity_class", "Emerging")))
    top_initiatives = dec.get("top_initiatives", [])
    top_init        = _field(top_initiatives[0] if top_initiatives else "Foundations first")
    primary_risk    = _field(plan.get("primary_risk", dec.get("primary_risk", "No major flags identified")))

    html_str = f"""
    <div style="background:var(--white); border:1px solid var(--ink-200); border-top:3px solid var(--brand);
                border-radius:8px; padding:24px; margin-bottom:16px; box-shadow:0 2px 8px rgba(0,0,0,0.04);">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:20px;">
            <div>
                <div style="font-size:11px; font-weight:700; color:var(--ink-400); letter-spacing:0.12em;
                            text-transform:uppercase; margin-bottom:8px;">Capital Allocation Posture</div>
                <div style="font-size:26px; font-weight:800; color:var(--ink-900); font-family:Georgia,serif;">{action}</div>
            </div>
        </div>
        
        <div style="display:flex; gap:16px; background:var(--ink-50); padding:16px;
                    border-radius:6px; border:1px solid var(--ink-150);">
            <div style="flex:1; border-right:1px solid rgba(0,0,0,0.08); padding-right:16px;">
                <div style="font-size:10.5px; font-weight:700; color:var(--ink-500); text-transform:uppercase;
                            letter-spacing:0.05em; margin-bottom:4px;">{risk_label}</div>
                <div style="font-size:14px; font-weight:600; color:var(--ink-900);">{primary_risk}</div>
            </div>
            <div style="flex:1; border-right:1px solid rgba(0,0,0,0.08); padding-right:16px;">
                <div style="font-size:10.5px; font-weight:700; color:var(--ink-500); text-transform:uppercase;
                            letter-spacing:0.05em; margin-bottom:4px;">Phase 1 Deliverable</div>
                <div style="font-size:14px; font-weight:600; color:var(--ink-900);">{milestone}</div>
            </div>
            <div style="flex:1.5;">
                <div style="font-size:10.5px; font-weight:700; color:var(--ink-500); text-transform:uppercase;
                            letter-spacing:0.05em; margin-bottom:4px;">Next Steps</div>
                <div style="font-size:14px; font-weight:600; color:var(--ink-900);">{next_steps}</div>
            </div>
        </div>
    """

    scoring_matrix = plan.get("scoring_matrix", [])
    if plan.get("posture") == "ADDRESS FOUNDATIONS FIRST":
        high_priority = scoring_matrix[:3]
    else:
        # Fix 5: Show ALL funded use cases, not just High tier
        high_priority = [uc for uc in scoring_matrix if uc.get("priority") in {"High", "Medium"}]

    # Fix 8: SI premium note
    si_inflation = plan.get("si_inflation", 0.0)
    si_cost = plan.get("si_cost", 0.0)
    si_note = ""
    if si_inflation > 0:
        si_pct = int(round(si_inflation * 100))
        si_note = (f'<div style="margin-top:16px; padding:10px 16px; background:var(--ink-50); '
                   f'border:1px solid var(--ink-150); border-radius:6px; font-size:12px; color:var(--ink-600);'
                   f' line-height:1.5;">'
                   f'<strong>Note:</strong> A {si_pct}% Systems Integrator delivery premium '
                   f'({_fmt_usd(si_cost)}) applies on top of the stated budget envelope '
                   f'based on the current delivery model selection.</div>')

    if high_priority or conds:
        html_str += '<div style="margin-top:20px; padding-top:16px; border-top:1px solid rgba(0,0,0,0.08); display:flex; gap:24px;">'
        if high_priority:
            title_text = "Highest-priority once validated" if plan.get("posture") == "ADDRESS FOUNDATIONS FIRST" else "Recommended Initiatives"
            html_str += f'<div style="flex:1;"><div style="font-size:12px; font-weight:700; color:var(--ink-900); margin-bottom:8px;">{title_text}</div>'
            html_str += '<ul style="margin:0; padding-left:18px; font-size:13px; color:var(--ink-600); line-height:1.7;">'
            for uc in high_priority[:6]:
                if plan.get("posture") == "ADDRESS FOUNDATIONS FIRST":
                    tier_label = "Highest-priority once validated"
                else:
                    tier_label = "Accelerate" if uc.get("priority") == "High" else "Sequence"
                html_str += f"<li><strong>{_field(uc['name'])}</strong> \u2014 {tier_label} \u00b7 {_field(uc.get('rationale',''))}</li>"
            html_str += '</ul></div>'
        if conds:
            html_str += '<div style="flex:1;"><div style="font-size:12px; font-weight:700; color:var(--ink-900); margin-bottom:8px;">Conditions for Success</div>'
            html_str += '<ul style="margin:0; padding-left:18px; font-size:13px; color:var(--ink-600); line-height:1.7;">'
            for c in conds:
                html_str += f"<li>{c}</li>"
            html_str += '</ul></div>'
        html_str += '</div>'
    html_str += si_note
    html_str += '</div>'
    _h(html_str)

    # H1: state the no-returns principle explicitly (spec requirement)
    _h("""
    <div style="background:var(--ink-50); border:1px solid var(--ink-150); border-radius:8px;
                padding:14px 18px; margin-bottom:20px; font-size:12.5px; color:var(--ink-600);
                line-height:1.6; font-style:italic;">
        This tool deliberately does not project ROI or payback — those depend on execution specifics
        beyond a diagnostic. It prioritises where to invest first and how to stage the spend,
        against peer evidence.
    </div>
    """)



# ─────────────────────────────────────────────────────────────────────────────
# 2 · INVESTMENT ROADMAP (phase timeline)
# ─────────────────────────────────────────────────────────────────────────────
def render_phase_timeline(plan: dict) -> None:
    phases = plan.get("phases", [])
    if not phases:
        return
    
    foundations_first = plan.get("posture") == "ADDRESS FOUNDATIONS FIRST"
    _section_title("Investment Roadmap",
                   "Only Phase 1 is committed today \u2014 each later phase requires preceding phase delivery." if foundations_first else "Proposed staging for capital allocation.")
    
    palette = ["#D04A02", "#1F6FEB", "#1B9C6B"]
    cols = st.columns(len(phases))
    for i, (col, ph) in enumerate(zip(cols, phases)):
        color = palette[i % len(palette)]
        phase_gate = ph.get("gate") or "—"
        gate_txt = phase_gate if phase_gate and phase_gate != "—" else "Programme complete"
        
        usd_val = _fmt_usd(ph['usd'])
        if foundations_first and i > 0:
            usd_str = f'{usd_val} <br><span style="font-size: 13px; font-weight: normal; color: var(--ink-500);">(Pending Phase 1 Delivery)</span>'
        else:
            usd_str = usd_val
            
        with col:
            _h(f"""
            <div style="border:1px solid var(--ink-150); border-top:3px solid {color};
                        background:var(--white); border-radius:10px; padding:18px; min-height:212px;
                        box-shadow:var(--sh-sm);">
              <div style="font-size:10.5px; font-weight:700; color:{color}; text-transform:uppercase;
                          letter-spacing:0.06em;">{ph['window']}</div>
              <div style="font-size:15px; font-weight:800; color:var(--ink-900); margin:5px 0 8px;">{ph['name']}</div>
              <div style="font-size:24px; font-weight:800; color:var(--ink-900); margin-bottom:10px;">{usd_str}</div>
              <div style="font-size:12px; color:var(--ink-600); line-height:1.55; margin-bottom:12px;">{ph['focus']}</div>
              <div style="font-size:11px; color:var(--ink-400); border-top:1px solid var(--ink-150);
                          padding-top:8px;"><b>Next step:</b> {gate_txt}</div>
            </div>
            """)
    st.html('<div style="height: 8px;"></div>')


# ─────────────────────────────────────────────────────────────────────────────
# 3 · STRATEGIC AI INVESTMENT PRIORITISATION
# ─────────────────────────────────────────────────────────────────────────────
def render_executive_summary(payload: dict) -> None:
    pass # Removed per PwC/FANG design requirements

# ─────────────────────────────────────────────────────────────────────────────
# 3.5 · VALUE PORTFOLIO (Framework 2)
# ─────────────────────────────────────────────────────────────────────────────
def render_value_portfolio(plan: dict) -> None:
    vp = plan.get("value_portfolio")
    if not vp:
        return
        
    _section_title("Value-Pool Portfolio", "Planned mix once Phase 1 unlocks funding." if plan.get("posture") == "ADDRESS FOUNDATIONS FIRST" else "Where capital is directed across the three canonical CPG value pools.")
    
    # Alignment strip
    align_pct = vp["aligned_pct"]
    if align_pct >= 80:
        strip_class = "aia-align-strip--green"
        icon = "✓"
    elif align_pct >= 60:
        strip_class = "aia-align-strip--amber"
        icon = "⚠"
    else:
        strip_class = "aia-align-strip--red"
        icon = "✕"
        
    _h(f'<div class="aia-align-strip {strip_class}" style="margin-bottom:20px;">'
       f'{icon} {vp["alignment_sentence"]}</div>')

    pct = vp["pct"]
    usd = vp["usd"]
    
    # KPI Cards using Streamlit columns
    counts = {REVENUE: 0, OPPROFIT: 0, PRODUCTIVITY: 0}
    for r in plan.get("ledger_rows", []):
        if r.get("pillar") == "Value Initiative":
            vt = r.get("value_type", PRODUCTIVITY)
            if vt in counts:
                counts[vt] += 1
                
    kpi_cols = st.columns(3)
    kpis_data = [(REVENUE, "revenue", "#3B6D11"), (OPPROFIT, "opprofit", "#185FA5"), (PRODUCTIVITY, "productivity", "#BA7517")]
    
    for i, (vt, tag_class, top_color) in enumerate(kpis_data):
        with kpi_cols[i]:
            empty_style = "opacity: 0.5;" if pct[vt] == 0 else ""
            _h(f"""
            <div style="border-radius: 8px; border: 1px solid var(--ink-150);
                        padding: 18px 20px; background: var(--white);
                        border-top: 3px solid {top_color}; box-shadow: 0 2px 8px rgba(0,0,0,0.03); {empty_style}">
                <div style="font-size:10.5px; font-weight:700; color:var(--ink-500); letter-spacing:0.06em; text-transform:uppercase; margin-bottom:12px; display:flex; align-items:center; gap:6px;">
                    <span style="display:inline-block; width:16px; height:16px; border-radius:50%; background:{top_color}; color:#fff; font-size:10px; text-align:center; line-height:16px;">{VT_SHORT[vt]}</span>
                    {VT_DISPLAY[vt]}
                </div>
                <div style="font-size:28px; font-weight:800; color:var(--ink-900); font-family:Arial,sans-serif; margin-bottom:2px; line-height:1;">{pct[vt]}%</div>
                <div style="font-size:14px; font-weight:700; color:var(--ink-600); margin-bottom:8px;">{_fmt_usd(usd[vt])}</div>
                <div style="font-size:11.5px; color:var(--ink-400); line-height:1.4;">Share of deployable capital targeting {VT_DISPLAY[vt].lower()} plays.</div>
                <div style="font-size:11px; font-weight:700; color:var(--ink-900); margin-top:12px; padding-top:12px; border-top:1px solid var(--ink-100);">{counts[vt]} initiative{'s' if counts[vt] != 1 else ''} recommended</div>
            </div>
            """)
    st.html('<div style="height: 4px;"></div>')


# ─────────────────────────────────────────────────────────────────────────────
# 4 · USE-CASE PRIORITISATION MATRIX  (G0.3 + M3 — TIER map drives all surfaces)
# ─────────────────────────────────────────────────────────────────────────────

# Single source of truth for tier labels + colours (G0.3).
# Both bubble and table Action column read from this map.
TIER: dict[str, tuple[str, str]] = {
    "High":   ("Accelerate", "#1B9C6B"),
    "Medium": ("Sequence",   "#E8A317"),
    "Watch":  ("Defer",      "#D0342C"),
}


def _band(score: float) -> str:
    """Convert a 0-100 score to a qualitative band label (M3)."""
    if score >= 75:
        return "High"
    if score >= 55:
        return "Medium"
    return "Low"


def render_use_case_prioritization(plan: dict) -> None:
    _section_title("Use-Case Prioritisation",
                   "Where to deploy first — business impact vs. delivery feasibility. "
                   "Bubble size reflects funded allocation; deferred items are outlined.")
    _h('<div style="font-size:11px; color:var(--ink-400); margin-top:-10px; margin-bottom:12px;"><b>Composite</b> = Impact 40% + Feasibility 25% + Speed 20% + Fit 15%, less an execution-risk discount.</div>')
    scoring = plan.get("scoring_matrix", [])
    if not scoring:
        return

    # Extract allocations for bubble sizing
    allocs = {}
    for r in plan.get("ledger_rows", []):
        if r.get("pillar") == "Value Initiative":
            allocs[r["initiative"]] = r["allocation_usd"]

    # Calculate dynamic boundaries based on data points to prevent clipping
    x_min = min([uc.get("feasibility", 50) for uc in scoring] + [30]) - 5
    x_max = max([uc.get("feasibility", 50) for uc in scoring] + [120]) + 5
    y_min = min([uc.get("impact", 50) for uc in scoring] + [40]) - 5
    y_max = max([uc.get("impact", 50) for uc in scoring] + [115]) + 5

    fig = go.Figure()
    
    # Render quadrant background rectangles for subtle tints
    fig.add_shape(type="rect", x0=FEAS_MID, x1=x_max, y0=IMPACT_MID, y1=y_max, fillcolor="rgba(27,156,107,0.03)", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=x_min, x1=FEAS_MID, y0=IMPACT_MID, y1=y_max, fillcolor="rgba(232,163,23,0.03)", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=FEAS_MID, x1=x_max, y0=y_min, y1=IMPACT_MID, fillcolor="rgba(232,163,23,0.03)", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=x_min, x1=FEAS_MID, y0=y_min, y1=IMPACT_MID, fillcolor="rgba(208,52,44,0.03)", line_width=0, layer="below")

    for i, uc in enumerate(scoring):
        vt = uc.get("value_type", PRODUCTIVITY)
        color = VT_COLORS.get(vt, "#4A525C")
        alloc = allocs.get(uc["name"], 0)
        
        # Sizing and fill based on funding
        is_deferred = uc["priority"] == "Watch"
        base_size = max(12, min(40, (alloc / 1e6) * 15)) if alloc > 0 else 12
        marker_size = base_size if not is_deferred else 10
        fill_color = color
        line_color = "rgba(255,255,255,0.4)" if is_deferred else "rgba(255,255,255,0.8)"
        line_width = 1.5 if is_deferred else 1

        label, _ = TIER.get(uc.get("priority", "Medium"), ("Evaluate", "#E8A317"))
        rationale = uc.get("rationale", "")
        qaction = uc.get("quadrant_action", "")
        
        # Fix 9: Show text labels only for funded items; deferred items show on hover only
        mode = "markers+text" if not is_deferred else "markers"
        fig.add_trace(go.Scatter(
            x=[uc["feasibility"]], y=[uc["impact"]],
            mode=mode,
            marker=dict(size=marker_size, color=fill_color, opacity=0.85,
                        line=dict(width=line_width, color=line_color)),
            text=[uc["name"]], textposition="top center",
            textfont=dict(size=10, color="#2E353D"),
            name=uc["name"],
            hovertemplate=(
                f"<b>{uc['name']}</b><br>"
                f"Value type: {VT_DISPLAY[vt]} [{VT_SHORT[vt]}]<br>"
                f"Quadrant action: {qaction}<br>"
                f"{rationale}<br>"
                f"Composite: {uc['composite_score']}<extra></extra>"
            ),
        ))

    # Dividing lines at the true medians
    fig.add_hline(y=IMPACT_MID, line_dash="dot", line_color="rgba(0,0,0,0.15)")
    fig.add_vline(x=FEAS_MID, line_dash="dot", line_color="rgba(0,0,0,0.15)")
    
    # Quadrant labels
    fig.add_annotation(x=x_max-2, y=y_max-2, text="<b>PRIME CANDIDATES</b>", showarrow=False, font=dict(size=10, color="#1B9C6B"), opacity=0.4, xanchor="right")
    fig.add_annotation(x=x_min+2, y=y_max-2, text="<b>STRATEGIC BETS</b>", showarrow=False, font=dict(size=10, color="#E8A317"), opacity=0.4, xanchor="left")
    fig.add_annotation(x=x_max-2, y=y_min+2, text="<b>TACTICAL ADD-ONS</b>", showarrow=False, font=dict(size=10, color="#E8A317"), opacity=0.4, xanchor="right")
    fig.add_annotation(x=x_min+2, y=y_min+2, text="<b>MARGINAL</b>", showarrow=False, font=dict(size=10, color="#D0342C"), opacity=0.4, xanchor="left")
    
    fig.update_layout(
        margin=dict(l=10, r=20, t=10, b=10), height=650,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False,
        font=_plotly_font(),
        xaxis=dict(title="Feasibility & Readiness (relative)", showgrid=True,
                   gridcolor="rgba(0,0,0,0.04)", range=[x_min, x_max]),
        yaxis=dict(title="Business Impact (relative)", showgrid=True,
                   gridcolor="rgba(0,0,0,0.04)", range=[y_min, y_max]),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Add the legend below the chart
    legend_html = '<div class="quad-legend" style="border-bottom:1px solid var(--ink-150); padding-bottom:12px; margin-bottom:16px;">'
    legend_html += '<div style="font-size:10px; font-weight:700; color:var(--ink-400); text-transform:uppercase; letter-spacing:0.1em; margin-right:8px;">Bubble Color</div>'
    for vt in [REVENUE, OPPROFIT, PRODUCTIVITY]:
        legend_html += f'<div class="quad-legend__item"><div class="quad-legend__dot" style="background:{VT_COLORS[vt]};"></div> {VT_DISPLAY[vt]}</div>'
    legend_html += '<div style="width:16px;"></div>'
    legend_html += '<div style="font-size:10px; font-weight:700; color:var(--ink-400); text-transform:uppercase; letter-spacing:0.1em; margin-right:8px;">Bubble Size</div>'
    legend_html += '<div class="quad-legend__item"><div class="quad-legend__dot" style="background:var(--ink-400); width:14px; height:14px;"></div> Funded Allocation</div>'
    legend_html += '<div class="quad-legend__item"><div class="quad-legend__dot" style="background:var(--ink-400); width:10px; height:10px;"></div> Deferred</div>'
    legend_html += '</div>'
    _h(legend_html)

    # M3: table shows tiers, not raw decimals
    _h('<div style="font-size:10px; font-weight:700; color:var(--ink-400); letter-spacing:0.1em; '
       'text-transform:uppercase; margin:16px 0 8px;">Priority Breakdown</div>')
    df_data = [{
        "Use Case":    uc["name"],
        "Quadrant":    uc.get("quadrant_name", ""),
        "Priority":    TIER.get(uc.get("priority", "Medium"), ("Evaluate",))[0],
        "Value Type":  VT_DISPLAY[uc.get("value_type", PRODUCTIVITY)],
        "Impact":      _band(uc["impact"]),
        "Technical Feasibility": _band(uc["feasibility"]),
    } for uc in scoring]
    st.dataframe(df_data, use_container_width=True, hide_index=True)

    # H2: "How we ranked this" expander
    with st.expander("How to read this matrix"):
        _h("""
        <div style="font-size:13px; color:var(--ink-600); line-height:1.8;">
        <b>Matrix layout:</b> The midlines represent static industry thresholds. Items in the top right (Prime Candidates) are funded first.<br>
        <b>Quadrant consistency:</b> If a use case lands in "Strategic Bets", it is automatically deferred pending Phase 1 foundation delivery.<br>
        <b>Bubble sizing:</b> Area is proportional to the dollar allocation for funded items. Deferred items are small and hollow.<br>
        <b>Composite score formula:</b> Impact × 40% + Technical Feasibility × 25% + Speed × 20% + Strategic Fit × 15%,
        reduced by an execution-risk discount.
        </div>
        """)
    st.html('<div style="height: 10px;"></div>')



# ─────────────────────────────────────────────────────────────────────────────
# 5 · STRATEGIC INVESTMENT LEDGER  (L1: evidence + rationale + deliverability; no projected dollar)
# ─────────────────────────────────────────────────────────────────────────────
_LEDGER_CSS = """
<style>
.aia-ledger { width:100%; border-collapse:collapse; font-family:Georgia, serif; border-top:2px solid var(--ink-900); border-bottom:2px solid var(--ink-900); }
.aia-ledger th { font-family:Arial, sans-serif; font-size:10px; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; color:var(--ink-500); text-align:left; padding:12px 16px; border-bottom:1px solid var(--ink-200); }
.aia-ledger th.num { text-align:right; }
.aia-ledger tbody tr.data-row { background:var(--white); transition:background 0.15s ease; border-bottom:1px solid var(--ink-150); }
.aia-ledger tbody tr.data-row:hover { background:var(--ink-50); }
.aia-ledger td { padding:16px; vertical-align:top; border:none; }
.aia-ledger td.num { text-align:right; font-size:15px; font-weight:600; color:var(--ink-900); white-space:nowrap; font-family:Arial, sans-serif; vertical-align:middle; }
.aia-ledger .init { font-family:Arial, sans-serif; font-weight:700; color:var(--ink-900); font-size:14px; margin-bottom:4px; line-height:1.4; }
.aia-ledger .evi { font-family:Georgia, serif; font-size:13px; color:var(--ink-600); line-height:1.5; font-style:italic; max-width:90%; }
.aia-ledger .cite { font-family:Arial, sans-serif; font-size:11px; color:var(--ink-400); line-height:1.4; margin-top:8px; }
.aia-ledger tr.grp td { background:var(--ink-50); font-family:Arial, sans-serif; font-size:11px; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:var(--ink-900); padding:16px; border-bottom:1px solid var(--ink-200); border-top:1px solid var(--ink-200); }
.aia-ledger tr.sub td { font-family:Arial, sans-serif; font-weight:600; color:var(--ink-600); font-size:12px; padding:12px 16px; border-bottom:1px solid var(--ink-200); }
.aia-ledger tr.sub td.num { font-size:14px; color:var(--ink-800); }
.aia-ledger tr.total td { background:var(--white); color:var(--ink-900); font-family:Arial, sans-serif; font-weight:700; font-size:14px; padding:16px; border-top:2px solid var(--ink-900); border-bottom:1px solid var(--ink-200); }
.aia-ledger tr.total td.num { font-size:18px; }
.lg-phase { font-family:Arial, sans-serif; display:inline-block; font-size:11px; font-weight:600; padding:4px 10px; border-radius:4px; background:var(--ink-100); color:var(--ink-700); white-space:nowrap; }
.lg-deliv { font-family:Arial, sans-serif; display:inline-block; font-size:10px; font-weight:600; padding:3px 6px; border:1px solid var(--ink-200); color:var(--ink-600); margin-top:8px; }
</style>
"""


def _ledger_row(r: dict) -> str:
    """L1: render initiative + evidence/rationale + deliverability chip + allocation.
    No projected dollar, value_at_stake, or roi_driver shown."""
    evi    = r.get("evidence", "")         # sourced or labelled illustrative
    why    = r.get("rationale", "")         # plain-English ranking reason (M4)
    deliv  = r.get("deliverability_pct")    # = feasibility from matrix (L4)
    vt     = r.get("value_type")
    
    vt_html = ""
    if vt:
        tag_class = "revenue" if vt == REVENUE else "opprofit" if vt == OPPROFIT else "productivity"
        vt_html = f'<span class="vt-chip vt-chip--{tag_class}" style="margin-right:8px; margin-bottom:4px; transform:scale(0.85); transform-origin:left center;"><span class="vt-cue">{VT_SHORT[vt]}</span> {VT_DISPLAY[vt]}</span>'
        
    why_html   = f'<div class="evi">{why}</div>'   if why   else ""
    deliv_html = (f'<div style="margin-top:6px;"><span class="lg-deliv">Feasibility: {deliv}%</span></div>'
                  if deliv is not None else "")
    cite_html  = f'<div class="cite">{evi}</div>'  if evi   else ""
    return (
        f'<tr class="data-row"><td><div class="init">{vt_html}{_field(r["initiative"])}</div>'
        f'{why_html}{cite_html}{deliv_html}</td>'
        f'<td><span class="lg-phase">{r.get("phase","\u2014")}</span></td>'
        f'<td class="num">{_fmt_usd(r["allocation_usd"])}</td></tr>'
    )


def _ledger_group(title: str, rows: list) -> str:
    if not rows:
        return ""
    html_str = f'<tr class="grp"><td colspan="3">{title}</td></tr>'
    html_str += "".join(_ledger_row(r) for r in rows)
    alloc = sum(r["allocation_usd"] for r in rows)
    html_str += (f'<tr class="sub"><td>Subtotal</td><td></td>'
                 f'<td class="num">{_fmt_usd(alloc)}</td></tr>')
    return html_str


def render_investment_ledger(plan: dict) -> None:
    _section_title("Strategic Investment Ledger",
                   "A transparent accounting of the capital deployment strategy. Allocations are strictly weighted by priority tier and technical feasibility rather than theoretical return.")
    rows = plan.get("ledger_rows", [])
    if not rows:
        return

    value_rows = [r for r in rows if r.get("pillar", "").startswith("Value Initiative")]
    found_rows = [r for r in rows if r.get("pillar", "").startswith("Foundation")]
    deliv_rows = [r for r in rows if r.get("pillar", "").startswith("Delivery")]

    total_alloc = sum(r["allocation_usd"] for r in rows)
    budget = plan.get("total_budget", 0.0)
    si_cost = plan.get("si_cost", 0.0)
    si_inf_pct = plan.get("si_inflation", 0.0)
    total_cost = plan.get("total_cost", 0.0)

    deferred = plan.get("deferred_initiatives", [])
    deferred_html = ""
    foundations_first = plan.get("posture") == "ADDRESS FOUNDATIONS FIRST"
    
    if deferred and not foundations_first:
        deferred_html = (
            '<tr><td colspan="3" style="color:var(--ink-500); font-size:13px; padding:12px 24px;">'
            '<b>Not funded in current cycle:</b>'
            '<ul style="margin:6px 0 0 0; padding-left:18px; line-height:1.8;">'
        )
        for name in deferred:
            deferred_html += f'<li>{name}</li>'
        deferred_html += (
            '</ul>'
            '<div style="margin-top:6px; font-style:italic; font-size:12px; color:var(--ink-400);">'
            'These rank below the readiness threshold for the current data estate; '
            're-evaluate once Phase 1 foundations are delivered.</div>'
            '</td></tr>'
        )

    # Value Initiatives manually constructed to inject subtotals
    value_html = f'<tr class="grp"><td colspan="3">Value Initiatives</td></tr>'
    if foundations_first:
        names = ", ".join(deferred)
        value_html += (
            f'<tr><td colspan="3" style="color:var(--ink-500); font-size:13px; padding:12px 24px;">'
            f'<b>Not funded in current cycle:</b> {names}. '
            f'All value initiatives are pending Phase 1 foundation delivery.</td></tr>'
        )
        value_html += (f'<tr class="sub"><td>Value Initiatives Subtotal</td><td></td>'
                       f'<td class="num">$0</td></tr>')
    elif value_rows:
        value_html += "".join(_ledger_row(r) for r in value_rows)
        vp = plan.get("value_portfolio")
        if vp and vp.get("usd"):
            for vt in [REVENUE, OPPROFIT, PRODUCTIVITY]:
                if vp["usd"][vt] > 0:
                    value_html += (f'<tr>'
                                   f'<td><span style="font-size:13px; font-weight:600; color:var(--ink-500); padding-left:24px;">\u21b3 {VT_DISPLAY[vt]} allocation</span></td><td></td>'
                                   f'<td class="num" style="color:var(--ink-600); font-size:14px;">{_fmt_usd(vp["usd"][vt])}</td></tr>')
        value_html += (f'<tr class="sub"><td>Value Initiatives Subtotal</td><td></td>'
                       f'<td class="num">{_fmt_usd(sum(r["allocation_usd"] for r in value_rows))}</td></tr>')
    else:
        value_html = ""

    body = (
        value_html
        + deferred_html
        + _ledger_group("Foundation (Data &amp; Controls)", found_rows)
        + _ledger_group("Delivery", deliv_rows)
    )
    body += (f'<tr class="total"><td>Client mandate (hard envelope)</td><td></td>'
             f'<td class="num">{_fmt_usd(budget)}</td></tr>')
    if si_cost > 0:
        body += (f'<tr class="total" style="background:var(--ink-50);color:var(--ink-800);font-weight:700;"><td>Systems-integrator premium (+{si_inf_pct:.0%}, on top)</td><td></td>'
                 f'<td class="num" style="color:var(--ink-800);">{_fmt_usd(si_cost)}</td></tr>')
    body += (f'<tr class="total"><td>Total Programme Cost</td><td></td>'
             f'<td class="num">{_fmt_usd(total_cost)}</td></tr>')

    table = (
        _LEDGER_CSS
        + '<table class="aia-ledger"><thead><tr>'
        + '<th style="width:60%">Initiative &amp; Evidence</th>'
        + '<th style="width:14%">Phase</th>'
        + '<th class="num" style="width:26%">Allocation</th>'
        + f'</tr></thead><tbody>{body}</tbody></table>'
    )
    _h(table)
    # L2: state the allocation methodology explicitly
    _h('<div style="font-size: 11.5px; color: var(--ink-500); margin-top: 10px; line-height: 1.6;">'
       '<em>Note: The capital allocation model distributes the budget pool proportionally across approved initiatives based on their matrix priority score and technical feasibility weighting. '
       'Initiatives deferred to subsequent phases receive zero capital allocation in the current cycle.</em><br>'
       '<em>Technical Feasibility</em> reflects the inverse execution risk from the prioritisation matrix. '
       'Any System Integrator (SI) delivery premiums are modelled as additions to the base envelope; selecting a "fully internal" operating model removes this premium.</div>')
    st.html('<div style="height: 10px;"></div>')

    # H2: ranking methodology expander for ledger
    with st.expander("How we ranked and sized these initiatives"):
        _h("""
        <div style="font-size:13px; color:var(--ink-600); line-height:1.8;">
        <b>Allocation formula:</b> each value initiative receives a share of the deployable budget
        proportional to <em>composite score × (feasibility / 100)</em>.
        Higher-scoring and more-deliverable initiatives receive more capital.<br>
        <b>Foundation spend</b> is sized as 20–55% of total budget, scaling with your data-estate
        complexity and compliance burden (Q3.1, Q3.2, Q4.2).<br>
        <b>Evidence chips</b> are labelled “illustrative — unverified” until confirmed against
        the source annual report or Capital Markets Day disclosure.
        </div>
        """)


# ─────────────────────────────────────────────────────────────────────────────
# 6 · CAPITAL ALLOCATION BY PHASE
# ─────────────────────────────────────────────────────────────────────────────
def render_stacked_bar_allocation(plan: dict) -> None:
    _section_title("Capital Allocation by Phase",
                   "Foundation is front-loaded; value initiatives unlock as phases are validated.")
    phases = plan.get("phases", [])
    if not phases:
        return
    foundation_usd = plan.get("foundation_usd", 0.0)
    x = [f"{p['name']}<br>{p['window']}" for p in phases]
    foundation_series = [foundation_usd / 1e6] + [0.0] * (len(phases) - 1)
    value_series = [0.0] + [p["usd"] / 1e6 for p in phases[1:]]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Foundation (Data &amp; Controls)", x=x, y=foundation_series,
                         marker_color="#2E353D", hovertemplate="$%{y:.1f}M<extra></extra>"))
    fig.add_trace(go.Bar(name="Value Initiatives", x=x, y=value_series,
                         marker_color="#D04A02", hovertemplate="$%{y:.1f}M<extra></extra>"))
    fig.update_layout(
        barmode="stack", margin=dict(l=0, r=0, t=10, b=0), height=300,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=_plotly_font(),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.04)", tickprefix="$", ticksuffix="M"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.html('<div style="height: 10px;"></div>')


# ─────────────────────────────────────────────────────────────────────────────
# 7 · AI MATURITY ASSESSMENT
# ─────────────────────────────────────────────────────────────────────────────
def render_maturity_gauge(payload: dict, plan: dict = None) -> None:
    pass # Removed per PwC/FANG design requirements


# ─────────────────────────────────────────────────────────────────────────────
# 8 · COMPETITIVE BENCHMARKING  (sourced chart + tailored cards + sources)
# ─────────────────────────────────────────────────────────────────────────────
def _extract_bps(text: str) -> int:
    m = re.search(r"(\d+)\s*bps", text or "")
    return int(m.group(1)) if m else 0


def _transfer_bar(label: str, val: int, color: str) -> str:
    val = max(0, min(int(val or 0), 100))
    return (f'<div style="margin-bottom:9px;">'
            f'<div style="display:flex; justify-content:space-between; font-size:11px; color:var(--ink-500); margin-bottom:3px;">'
            f'<span>{label}</span><span style="font-weight:700; color:var(--ink-800);">{val}</span></div>'
            f'<div style="height:6px; background:var(--ink-100); border-radius:999px; overflow:hidden;">'
            f'<div style="height:100%; width:{val}%; background:{color}; border-radius:999px;"></div></div></div>')


def render_benchmarks(payload: dict) -> None:
    _section_title("Competitive Benchmarking (Total Gross Uplifts)",
                   "How FMCG leaders have monetised AI (including broader market factors) — and how transferable each play is to you.")

    SELF_ALIASES = [{"unilever","hindustan unilever","hul"}, {"procter","p&g","pandg","procter & gamble","procter and gamble"}, {"itc"}]
    def _is_self(peer, target):
        t, p = (target or "").lower(), (peer or "").lower()
        # Direct substring match (both directions)
        if t and p and (t in p or p in t):
            return True
        if any(tok in p for tok in t.split() if len(tok) > 3): return True
        return any((any(al in t for al in grp) and any(al in p for al in grp)) for grp in SELF_ALIASES)

    target_company = st.session_state.get("company_name", "")

    # Fix 7: Determine if regional peers should be included.
    # Show regional peers only if the client's region matches.
    region_display = st.session_state.get("region", "")
    include_regional = "india" in (region_display or "").lower() or "south asia" in (region_display or "").lower()

    peers = []
    for v in PEER_INTELLIGENCE.values():
        if _is_self(v["company"], target_company):
            continue
        # Filter out regional peers for non-India clients
        if v.get("tier") == "regional" and not include_regional:
            continue
        bps = _extract_bps(v.get("margin_uplift", ""))
        if bps:
            peers.append((v["company"], bps, v.get("payback_months", 0), v.get("headline_stat", "")))
    peers.sort(key=lambda t: t[1])  # ascending so the longest bar sits on top

    if peers:
        names = [p[0] for p in peers]
        vals = [p[1] for p in peers]
        # Darker brand for the top performers, lighter for the rest.
        top_cut = sorted(vals, reverse=True)[: max(1, len(vals) // 3)][-1]
        colors = ["#D04A02" if v >= top_cut else "#F0A579" for v in vals]
        fig = go.Figure(go.Bar(
            x=vals, y=names, orientation="h",
            marker_color=colors,
            text=[f"{v} bps" for v in vals], textposition="outside",
            textfont=dict(size=11, color="#2E353D"),
            hovertemplate="<b>%{y}</b><br>%{x} bps gross-margin expansion<extra></extra>",
        ))
        fig.update_layout(
            margin=dict(l=0, r=30, t=8, b=0), height=max(260, 26 * len(peers) + 60),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=_plotly_font(),
            xaxis=dict(title="Disclosed gross-margin expansion from AI (bps)", showgrid=True,
                       gridcolor="rgba(0,0,0,0.05)", range=[0, max(vals) * 1.25]),
            yaxis=dict(showgrid=False),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── 8b. Tailored, client-specific benchmark cards (from the LLM) ────────
    raw_bms = payload.get("interactive_benchmarks", [])
    bms = [p for p in raw_bms if not _is_self(p.get("peer", ""), target_company)]
    
    if bms:
        _h('<div style="font-size:10px; font-weight:700; color:var(--ink-400); letter-spacing:0.1em; '
           'text-transform:uppercase; margin:18px 0 10px;">Most Relevant Plays for You</div>')
        cols = ["#1B9C6B", "#1F6FEB", "#D04A02"]
        for i, p in enumerate(bms):
            accent = cols[i % len(cols)]
            with st.expander(f"{p.get('initiative', 'AI initiative')} — Transferability: {p.get('transferability_score', 0)}/100", expanded=(i == 0)):
                bars = (_transfer_bar("Similarity", p.get("similarity_score", 0), "#1F6FEB")
                        + _transfer_bar("Relevance", p.get("relevance_score", 0), "#1B9C6B")
                        + _transfer_bar("Transferability", p.get("transferability_score", 0), "#D04A02"))
                _h(f"""
                <div style="display:flex; gap:24px; align-items:flex-start;">
                  <div style="flex:1.3;">
                    <div style="font-size:18px; font-weight:800; color:{accent}; line-height:1.1; margin-bottom:6px;">
                        {_field(p.get('initiative', ''))}</div>
                    <div style="font-size:12px; font-weight:600; color:var(--ink-500); margin-bottom:10px;">
                        {p.get('peer', 'Peer')} reported: {_field(p.get('outcome', ''))}</div>
                    <div style="font-size:13px; color:var(--ink-600); line-height:1.65;">{_field(p.get('details', ''))}</div></div>
                  </div>
                  <div style="flex:1; min-width:200px;">{bars}</div>
                </div>
                """)


    # Fix #8: distinguish corpus-sourced bars from LLM-generated cards.
    _h('<div style="font-size:11px; color:var(--ink-400); line-height:1.65; margin-top:14px; '
       'border-top:1px solid var(--ink-150); padding-top:10px;">'
       '<b style="color:var(--ink-500);">Sources (bar chart):</b> Company Annual Reports 2023\u201324 · '
       'Investor Capital Markets Day disclosures. '
       'The gross-margin figures above are drawn from our sourced peer corpus. '
       '<b style="color:var(--ink-500);">"Most Relevant Plays" cards:</b> Indicative \u2014 modelled from '
       'public disclosures and company intelligence; treat as directional, not audited.'
       '</div>')
    st.html('<div style="height: 10px;"></div>')



# ─────────────────────────────────────────────────────────────────────────────
# 9 · RISK REGISTER & HEAT MAP
# ─────────────────────────────────────────────────────────────────────────────
def render_risk_register(plan: dict) -> None:
    pass # Removed per PwC/FANG design requirements



# ─────────────────────────────────────────────────────────────────────────────
# 10 · SENSITIVITY ANALYSIS / BIGGEST UNLOCK
# ─────────────────────────────────────────────────────────────────────────────
def render_biggest_unlocks(plan: dict) -> None:
    unlocks = plan.get("biggest_unlocks", [])
    if not unlocks:
        return
        
    _section_title("The Biggest Unlocks", "Counterfactual levers that significantly change your investment posture or value-delivery capacity.")
    
    for u in unlocks:
        flip_text = f"flips posture to <b style='color:var(--brand);'>{u['posture_flip']}</b>" if u.get("posture_flip") else ""
        delta_text = f"unlocks <b>{u['delta_funded']}</b> additional use cases above the readiness bar" if u.get("delta_funded", 0) > 0 else ""
        impact = " and ".join(filter(None, [flip_text, delta_text]))
        
        _h(f"""
        <div style="background:var(--ink-50); border:1px solid var(--ink-150); border-left:4px solid var(--brand);
                    border-radius:8px; padding:16px; margin-bottom:12px;">
            <div style="font-size:15px; font-weight:700; color:var(--ink-900); margin-bottom:6px;">If you: {u['lever']}</div>
            <div style="font-size:13px; color:var(--ink-700);">Result: It {impact}.</div>
        </div>
        """)
    st.html('<div style="height: 10px;"></div>')



def render_company_header() -> None:
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
    
    html = f"""
    <div style="background: var(--white); border: 1px solid var(--ink-150); border-radius: 12px; padding: 20px 24px; margin-bottom: 24px; margin-top: 10px; display: flex; justify-content: space-between; align-items: center; box-shadow: var(--sh-sm);">
        <div style="display: flex; align-items: center; gap: 16px;">
            <div style="width: 52px; height: 52px; border-radius: 10px; background: linear-gradient(135deg, var(--ink-900) 0%, var(--ink-700) 100%); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 22px; font-weight: 800; font-family: Georgia, serif; letter-spacing: 0.05em; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                {initials}
            </div>
            <div>
                <div style="font-size: 10.5px; font-weight: 700; color: var(--ink-400); letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 4px;">Target Enterprise</div>
                <div style="font-size: 24px; font-weight: 800; color: var(--ink-900); font-family: Georgia, serif; line-height: 1;">{_field(company)}</div>
            </div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 10.5px; font-weight: 700; color: var(--ink-400); letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 6px;">Operating Region <span style="font-size:9px; font-weight:500; color:var(--ink-300);">(display only)</span></div>
            <div style="display: inline-block; background: var(--ink-50); border: 1px solid var(--ink-200); padding: 4px 12px; border-radius: 999px; font-size: 12.5px; font-weight: 600; color: var(--ink-700);">
                <span style="color:var(--brand); margin-right:4px;">&#9679;</span>{_field(geo)}
            </div>
        </div>
    </div>
    """
    _h(html)

# ─────────────────────────────────────────────────────────────────────────────
# ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────────
def render_full_dashboard() -> None:
    plan = st.session_state.thesis_plan
    payload = st.session_state.get("thesis_payload", {})

    nav_l, _ = st.columns([1.7, 4])
    with nav_l:
        if st.button("\u2190 Review & Edit Answers", key="edit_answers_top",
                     type="secondary", use_container_width=True):
            st.session_state.app_phase = 1
            st.session_state.wizard_page = 5
            st.rerun()

    # Header & posture
    render_company_header()
    render_how_to_read()
    render_decision_banner(payload, plan)

    # Executive thesis (with alignment sentence)
    render_executive_summary(payload)

    # Value-pool portfolio (Framework 2)
    render_value_portfolio(plan)

    # Named-quadrant matrix (Framework 1)
    render_use_case_prioritization(plan)

    # Phase timeline (roadmap)
    render_phase_timeline(plan)

    # Ledger (with value-type column + subtotals)
    render_investment_ledger(plan)

    # Capital allocation by phase removed as requested
    # 7 · Readiness context
    render_maturity_gauge(payload, plan)

    # 8 · Sourced peer evidence + transferability
    render_benchmarks(payload)

    # 9 · What could go wrong + mitigations
    render_risk_register(plan)

    # 10 · Sensitivity levers
    render_biggest_unlocks(plan)

    # G0.1: render_interactive_financial_model removed (no ROI / NPV / payback)

    st.html('<div style="height: 20px;"></div>')

    # Navigation + export
    st.markdown("---")
    colA, _, colC = st.columns([1.6, 1.2, 1.4])
    with colA:
        if st.button("\u2190 Review & Edit Answers", key="edit_answers_bottom",
                     type="secondary", use_container_width=True):
            st.session_state.app_phase = 1
            st.session_state.wizard_page = 5
            st.rerun()
    with colC:
        if st.button("Export to PDF", key="export_pdf", use_container_width=True):
            st.components.v1.html("""
                <script>
                    window.parent.document.querySelectorAll('details').forEach(el => el.open = true);
                    setTimeout(function(){ window.parent.print(); }, 400);
                </script>
            """, height=0, width=0)

    # Audit footer (E2 — run_id stamped if audit logger is active)
    run_id  = st.session_state.get("run_id",  "n/a")
    eng_ver = st.session_state.get("engine_version", "4.0.0")
    corp_ver = st.session_state.get("corpus_version", "0.1.0-unverified")
    mode    = st.session_state.get("report_mode", "deterministic")
    import datetime
    stamp_utc = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ")
    _h(f"""
    <div style="font-size:11px; color:var(--ink-400); line-height:1.6; border-top:1px solid var(--ink-150); padding-top:18px;">
        <strong>Disclaimer:</strong> This report produces a prioritisation diagnostic, not a financial forecast.
        No ROI, NPV, or payback figures are presented. Allocation figures represent the client's own stated
        budget, not projected returns. Evidence is labelled illustrative until confirmed against source disclosures.
        Confidential — not for external distribution.<br>
        <span style="color:var(--ink-300); font-size:10.5px;">
            Run {_field(run_id)} &middot; Engine {_field(eng_ver)} &middot; Corpus {_field(corp_ver)}
            &middot; Mode: {_field(mode)} &middot; {stamp_utc}
        </span>
    </div>
    """)

