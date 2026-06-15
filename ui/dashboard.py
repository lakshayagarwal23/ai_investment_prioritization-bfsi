"""
ui/dashboard.py

Right column (65% width) of the AI Investment Advisory Platform.
Renders an interactive, Palantir/PwC-style Executive Decision Platform.
"""

import streamlit as st
import plotly.graph_objects as go


def _h(html: str) -> None:
    flat = " ".join(line.strip() for line in html.splitlines())
    st.markdown(flat, unsafe_allow_html=True)

def _fmt_usd(val: float) -> str:
    if val >= 1_000_000: return f"${val / 1_000_000:.1f}M"
    if val >= 1_000: return f"${val / 1_000:.0f}K"
    return f"${val:,.0f}"

def _fmt_pct(val: float) -> str:
    return f"{val:.1f}%"

def render_pending_state() -> None:
    st.html("""
    <div class="aia-pending">
        <div class="aia-pending-icon">
            <div class="aia-pending-icon-inner"></div>
        </div>
        <div class="aia-pending-title">Executive Decision Engine Pending</div>
        <div class="aia-pending-sub">
            Complete the discovery flow to generate
            a fully quantified, interactive AI investment decision matrix.
        </div>
    </div>
    """)

def render_decision_banner(payload: dict, plan: dict) -> None:
    dec = payload.get("executive_decision", {})
    action = dec.get("action", "PHASED APPROVAL").upper()
    investment = dec.get("initial_investment", "USD 30M")
    milestone = dec.get("milestone", "Month 12: Value demonstrated")
    next_steps = dec.get("next_steps", "Evaluate Gate 2")
    conf = dec.get("confidence_score", 70)
    conds = dec.get("conditions", [])
    
    color = "#FFB600"
    if "DELAY" in action or "REJECT" in action:
        color = "#D63031"
    elif "APPROVE" in action or "APPROVAL" in action:
        color = "#00B894"
    
    html = f"""
    <div style="background: {color}15; border: 1px solid {color}; border-radius: 12px; padding: 24px; margin-bottom: 30px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px;">
            <div>
                <div style="font-size: 11px; font-weight: 700; color: {color}; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 8px;">CAPITAL ALLOCATION DECISION</div>
                <div style="font-size: 24px; font-weight: 800; color: var(--pwc-black);">{action}</div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 11px; font-weight: 700; color: var(--grey-400); letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 8px;">System Confidence</div>
                <div style="font-size: 32px; font-weight: 900; color: var(--pwc-black); line-height: 1;">{conf}/100</div>
            </div>
        </div>
        
        <div style="display: flex; gap: 16px; background: rgba(255,255,255,0.6); padding: 16px; border-radius: 8px; border: 1px solid rgba(0,0,0,0.05);">
            <div style="flex: 1; border-right: 1px solid rgba(0,0,0,0.1); padding-right: 16px;">
                <div style="font-size: 11px; font-weight: 700; color: var(--grey-text); text-transform: uppercase; margin-bottom: 4px;">Initial Investment</div>
                <div style="font-size: 16px; font-weight: 600; color: var(--pwc-black);">{investment}</div>
            </div>
            <div style="flex: 1; border-right: 1px solid rgba(0,0,0,0.1); padding-right: 16px;">
                <div style="font-size: 11px; font-weight: 700; color: var(--grey-text); text-transform: uppercase; margin-bottom: 4px;">Gate 1 Milestone</div>
                <div style="font-size: 14px; font-weight: 600; color: var(--pwc-black);">{milestone}</div>
            </div>
            <div style="flex: 1;">
                <div style="font-size: 11px; font-weight: 700; color: var(--grey-text); text-transform: uppercase; margin-bottom: 4px;">Next Steps</div>
                <div style="font-size: 14px; font-weight: 600; color: var(--pwc-black);">{next_steps}</div>
            </div>
        </div>
    """
    
    scoring_matrix = plan.get("scoring_matrix", [])
    high_priority = [uc for uc in scoring_matrix if uc.get("priority") == "High"]
    
    if high_priority or conds:
        html += '<div style="margin-top: 20px; padding-top: 16px; border-top: 1px solid rgba(0,0,0,0.1); display: flex; gap: 24px;">'
        
        if high_priority:
            html += '<div style="flex: 1;">'
            html += '<div style="font-size: 12px; font-weight: 600; color: var(--pwc-black); margin-bottom: 8px;">Top Recommended Use Cases:</div>'
            html += '<ul style="margin: 0; padding-left: 20px; font-size: 13px; color: #4A4A4A;">'
            for uc in high_priority[:3]:
                html += f"<li><strong>{uc['name']}</strong> (Score: {uc['composite_score']})</li>"
            html += '</ul></div>'
            
        if conds:
            html += '<div style="flex: 1;">'
            html += '<div style="font-size: 12px; font-weight: 600; color: var(--pwc-black); margin-bottom: 8px;">Required Conditions for Success:</div>'
            html += '<ul style="margin: 0; padding-left: 20px; font-size: 13px; color: #4A4A4A;">'
            for c in conds:
                html += f"<li>{c}</li>"
            html += '</ul></div>'
            
        html += '</div>'
    html += '</div>'
    _h(html)

def render_executive_summary(payload: dict) -> None:
    summary = payload.get("executive_summary", "")
    if summary:
        # Escape any rogue dollar signs to prevent Streamlit from attempting to render them as LaTeX Math
        summary = summary.replace("$", r"\$")
        
        st.markdown('<div style="background: var(--white); border: 1px solid var(--grey-border); border-radius: 12px; padding: 24px; box-shadow: var(--shadow-sm); margin-bottom: 30px;">', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 18px; font-weight: 700; color: var(--pwc-black); margin-bottom: 12px;">Strategic Investment Thesis</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size: 14px; color: #4A4A4A; line-height: 1.6;">\n\n{summary}\n\n</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


def render_maturity_gauge(payload: dict) -> None:
    """Render AI Maturity as a visually striking gauge chart with tier markers."""
    mat = payload.get("maturity_index", {})
    score = mat.get("score", 50)
    classification = mat.get("classification", "Emerging")
    summary = mat.get("summary", "")

    st.markdown('<div style="font-size: 18px; font-weight: 700; color: var(--pwc-black); margin-bottom: 16px;">AI Maturity Assessment</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([1, 2])
    with c1:
        # Gauge chart
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            number={"font": {"size": 52, "color": "#2D2D2D"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#E0E0E0"},
                "bar": {"color": "#D04A02", "thickness": 0.3},
                "bgcolor": "rgba(0,0,0,0)",
                "steps": [
                    {"range": [0, 25], "color": "rgba(214, 48, 49, 0.2)", "name": "Laggard"},
                    {"range": [25, 50], "color": "rgba(255, 182, 0, 0.2)", "name": "Emerging"},
                    {"range": [50, 75], "color": "rgba(0, 184, 148, 0.2)", "name": "Strategic"},
                    {"range": [75, 100], "color": "rgba(0, 150, 255, 0.2)", "name": "Leader"},
                ],
                "threshold": {
                    "line": {"color": "#D04A02", "width": 4},
                    "thickness": 0.8,
                    "value": score,
                },
            },
        ))
        fig.update_layout(
            margin=dict(l=20, r=20, t=40, b=10),
            height=220,
            paper_bgcolor="rgba(0,0,0,0)",
            font={"family": "Inter, sans-serif"},
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with c2:
        tier_color = {"Laggard": "#D63031", "Emerging": "#FFB600", "Strategic": "#00B894", "Leader": "#0096FF"}
        color = tier_color.get(classification, "#FFB600")
        tiers_html = ""
        for tier, (lo, hi) in [("Laggard", (0, 25)), ("Emerging", (25, 50)), ("Strategic", (50, 75)), ("Leader", (75, 100))]:
            is_active = tier == classification
            tc = tier_color[tier]
            opacity = "1" if is_active else "0.35"
            border = f"2px solid {tc}" if is_active else "1px solid #E0E0E0"
            bg = f"{tc}15" if is_active else "transparent"
            tiers_html += f'<div style="opacity:{opacity}; border:{border}; background:{bg}; border-radius:8px; padding:8px 12px; margin-bottom:6px; display:flex; justify-content:space-between; align-items:center;"><span style="font-size:13px; font-weight:600; color:{tc};">{tier}</span><span style="font-size:11px; color:var(--grey-400);">{lo}–{hi}</span></div>'
        _h(f"""
        <div style="padding: 12px 0;">
            <div style="font-size: 12px; font-weight: 700; color: var(--grey-400); letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 10px;">Classification: <span style="color:{color};">{classification}</span></div>
            {tiers_html}
            <div style="font-size: 13px; color: #4A4A4A; line-height: 1.5; margin-top: 12px; padding-top: 10px; border-top: 1px solid #E0E0E0;">{summary}</div>
        </div>
        """)
    st.html('<div style="height: 20px;"></div>')

def render_interactive_financial_model(plan: dict) -> None:
    st.markdown('<div style="font-size: 18px; font-weight: 700; color: var(--pwc-black); margin-bottom: 16px;">Scenario-Based Financial Model</div>', unsafe_allow_html=True)
    
    # Sliders for interactive assumptions
    c1, c2 = st.columns(2)
    with c1:
        roi_adj = st.slider("Expected ROI Adjustment (%)", min_value=-50, max_value=100, value=0, step=5, help="Stress-test the baseline ROI assumption.")
    with c2:
        delay_mo = st.slider("Execution Delay (Months)", min_value=0, max_value=12, value=0, step=1, help="Model the impact of delayed implementation.")
    
    # Math logic for scenarios
    budget_m = plan["budget_usd_m"]
    base_roi_pct = plan["expected_roi_pct"] + roi_adj
    base_npv = budget_m * (base_roi_pct / 100.0)
    
    months = list(range(0, 37, 3))
    
    def generate_cash_flow(npv_target, delay, curve_speed):
        cf = [-budget_m]
        current = -budget_m
        for m in months[1:-1]:
            if m <= delay:
                current -= (budget_m * 0.05) # burn rate during delay
            else:
                current += (npv_target - current) * curve_speed
            cf.append(current)
        cf[-1] = npv_target
        return cf

    cf_base = generate_cash_flow(base_npv, delay_mo, 0.25)
    cf_cons = generate_cash_flow(base_npv * 0.6, delay_mo + 3, 0.15)
    cf_opt = generate_cash_flow(base_npv * 1.3, max(0, delay_mo - 3), 0.35)

    fig = go.Figure()
    
    # Optimistic
    fig.add_trace(go.Scatter(x=[f"M{m}" for m in months], y=cf_opt, mode="lines", name="Optimistic", line=dict(color="#00B894", width=2, dash="dash"), hovertemplate="$%{y:.1f}M"))
    # Base
    fig.add_trace(go.Scatter(x=[f"M{m}" for m in months], y=cf_base, mode="lines", name="Base Case", line=dict(color="#FF5A00", width=4), hovertemplate="$%{y:.1f}M"))
    # Conservative
    fig.add_trace(go.Scatter(x=[f"M{m}" for m in months], y=cf_cons, mode="lines", name="Conservative", line=dict(color="#D63031", width=2, dash="dot"), hovertemplate="$%{y:.1f}M"))
    
    # Breakeven line
    fig.add_hline(y=0, line_dash="solid", line_color="rgba(0,0,0,0.2)")

    # Find payback month for base case
    payback_m = "N/A"
    for i, v in enumerate(cf_base):
        if v >= 0:
            payback_m = f"M{months[i]}"
            fig.add_vline(x=payback_m, line_dash="dash", line_color="#FF5A00")
            fig.add_annotation(x=payback_m, y=1, yref="paper", text="Base Payback", showarrow=False, xanchor="left", yanchor="bottom", font=dict(color="#FF5A00"))
            break

    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=350,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.04)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.04)", tickprefix="$", ticksuffix="M")
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    st.html('<div style="height: 30px;"></div>')

def render_five_gates(payload: dict) -> None:
    st.markdown('<div style="font-size: 18px; font-weight: 700; color: var(--pwc-black); margin-bottom: 16px;">Five-Gate Readiness Assessment</div>', unsafe_allow_html=True)
    gates = payload.get("five_gates", {})
    
    tabs = st.tabs(["01 Business Case", "02 Feasibility", "03 Prioritization", "04 Governance", "05 Validation"])
    
    keys = ["business_case", "feasibility", "prioritization", "governance", "validation"]
    for i, key in enumerate(keys):
        with tabs[i]:
            g = gates.get(key, {})
            score = g.get("score", 0)
            status = g.get("status", "AMBER")
            color_map = {"GREEN": "#00B894", "AMBER": "#FFB600", "RED": "#D63031"}
            color = color_map.get(status.upper(), "#FFB600")
            
            c1, c2 = st.columns([1, 2])
            with c1:
                _h(f"""
                <div style="text-align: center; padding: 20px; background: {color}10; border-radius: 12px; border: 1px solid {color}40;">
                    <div style="font-size: 48px; font-weight: 900; color: {color}; line-height: 1;">{score}</div>
                    <div style="font-size: 12px; font-weight: 700; color: {color}; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 8px;">{status}</div>
                </div>
                """)
                if g.get("breakdown"):
                    st.markdown("<div style='font-size: 12px; font-weight: 600; margin-top: 16px; margin-bottom: 8px;'>Scoring Breakdown</div>", unsafe_allow_html=True)
                    for k, v in g["breakdown"].items():
                        _h(f"""
                        <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px;">
                            <span style="color: #4A4A4A;">{k}</span>
                            <span style="font-weight: 600;">{v}/100</span>
                        </div>
                        <div style="width: 100%; height: 4px; background: var(--grey-100); border-radius: 2px; margin-bottom: 12px;">
                            <div style="width: {v}%; height: 100%; background: var(--grey-400); border-radius: 2px;"></div>
                        </div>
                        """)
            with c2:
                if g.get("drivers"):
                    st.markdown("**Key Drivers**")
                    for d in g["drivers"]:
                        st.markdown(f"- {d}")
                if g.get("recommendations"):
                    st.markdown("**Improvement Recommendations**")
                    for r in g["recommendations"]:
                        st.markdown(f"- {r}")

    st.html('<div style="height: 30px;"></div>')


def render_use_case_prioritization(plan: dict) -> None:
    """Render a bubble chart for use case prioritization."""
    st.markdown('<div style="font-size: 18px; font-weight: 700; color: var(--pwc-black); margin-bottom: 16px;">Use Case Prioritization Matrix</div>', unsafe_allow_html=True)

    scoring = plan.get("scoring_matrix", [])
    if not scoring:
        return

    # Map old priorities to clearer labels for the frontend if needed
    priority_labels = {"High": "Invest Now", "Medium": "Evaluate", "Watch": "Deprioritize"}
    colors_map = {"High": "#00B894", "Medium": "#FFB600", "Watch": "#D63031"}

    fig = go.Figure()
    for uc in scoring:
        color = colors_map.get(uc["priority"], "#FFB600")
        label = priority_labels.get(uc["priority"], uc["priority"])
        fig.add_trace(go.Scatter(
            x=[uc["feasibility"]],
            y=[uc["impact"]],
            mode="markers+text",
            marker=dict(
                size=uc["composite_score"] * 0.6,
                color=color,
                opacity=0.75,
                line=dict(width=2, color=color),
            ),
            text=[uc["name"]],
            textposition="top center",
            textfont=dict(size=10, color="#2D2D2D"),
            name=uc["name"],
            hovertemplate=(
                f"<b>{uc['name']}</b><br>"
                f"Impact: {uc['impact']}<br>"
                f"Feasibility: {uc['feasibility']}<br>"
                f"Speed: {uc['speed']}<br>"
                f"Composite: {uc['composite_score']}<br>"
                f"Action: {label}"
                "<extra></extra>"
            ),
        ))

    # Quadrant lines
    fig.add_hline(y=75, line_dash="dot", line_color="rgba(0,0,0,0.15)")
    fig.add_vline(x=70, line_dash="dot", line_color="rgba(0,0,0,0.15)")

    # Quadrant labels
    fig.add_annotation(x=85, y=92, text="<b>INVEST NOW</b>", showarrow=False, font=dict(size=10, color="#00B894"), opacity=0.6)
    fig.add_annotation(x=55, y=92, text="<b>STRATEGIC BET</b>", showarrow=False, font=dict(size=10, color="#FFB600"), opacity=0.6)
    fig.add_annotation(x=85, y=58, text="<b>QUICK WIN</b>", showarrow=False, font=dict(size=10, color="#0096FF"), opacity=0.6)
    fig.add_annotation(x=55, y=58, text="<b>DEPRIORITIZE</b>", showarrow=False, font=dict(size=10, color="#D63031"), opacity=0.6)

    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=400,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        xaxis=dict(title="Feasibility & Readiness", showgrid=True, gridcolor="rgba(0,0,0,0.04)", range=[40, 100]),
        yaxis=dict(title="Business Impact", showgrid=True, gridcolor="rgba(0,0,0,0.04)", range=[50, 100]),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Scoring table below the chart using Streamlit dataframe for perfect alignment
    _h('<div style="font-size: 12px; font-weight: 700; color: var(--grey-400); letter-spacing: 0.08em; text-transform: uppercase; margin: 16px 0 8px;">Detailed Scoring Breakdown</div>')
    
    # Clean up priorities for the table
    df_data = []
    for uc in scoring:
        df_data.append({
            "Use Case": uc["name"],
            "Impact (40%)": uc["impact"],
            "Feasibility (25%)": uc["feasibility"],
            "Speed (20%)": uc["speed"],
            "Fit (15%)": uc["fit"],
            "Composite": uc["composite_score"],
            "Action": priority_labels.get(uc["priority"], uc["priority"])
        })
    st.dataframe(df_data, use_container_width=True, hide_index=True)
    st.html('<div style="height: 30px;"></div>')


def render_risk_heatmap(payload: dict) -> None:
    """Render risk register as a visual heatmap grid."""
    st.markdown('<div style="font-size: 18px; font-weight: 700; color: var(--pwc-black); margin-bottom: 16px;">Risk Register & Heatmap</div>', unsafe_allow_html=True)
    risks = payload.get("risk_register", [])
    if not risks:
        return

    prob_map = {"HIGH": 3, "MED": 2, "LOW": 1}
    impact_map = {"HIGH": 3, "MED": 2, "LOW": 1}

    fig = go.Figure()
    # Background heatmap grid (rgba format for plotly compatibility)
    grid_colors = [
        ["rgba(0, 184, 148, 0.25)", "rgba(255, 182, 0, 0.25)", "rgba(214, 48, 49, 0.25)"],
        ["rgba(0, 184, 148, 0.25)", "rgba(255, 182, 0, 0.25)", "rgba(255, 90, 0, 0.25)"],
        ["rgba(224, 255, 224, 0.25)", "rgba(0, 184, 148, 0.25)", "rgba(255, 182, 0, 0.25)"],
    ]
    for pi in range(3):
        for ii in range(3):
            fig.add_shape(
                type="rect",
                x0=ii + 0.5, y0=pi + 0.5, x1=ii + 1.5, y1=pi + 1.5,
                fillcolor=grid_colors[pi][ii],
                line=dict(color="rgba(0,0,0,0.08)", width=1),
            )

    for r in risks:
        px = impact_map.get(r.get("impact", "MED").upper(), 2)
        py = prob_map.get(r.get("prob", "MED").upper(), 2)
        risk_score = px * py
        color = "#D63031" if risk_score >= 6 else "#FFB600" if risk_score >= 3 else "#00B894"
        fig.add_trace(go.Scatter(
            x=[px], y=[py],
            mode="markers+text",
            marker=dict(size=30, color=color, opacity=0.85, line=dict(width=2, color="white")),
            text=[r.get("risk", "")[:20]],
            textposition="top center",
            textfont=dict(size=9, color="#2D2D2D"),
            hovertemplate=f"<b>{r.get('risk','')}</b><br>Probability: {r.get('prob','')}<br>Impact: {r.get('impact','')}<br>Mitigation: {r.get('mitigation','')}<extra></extra>",
            showlegend=False,
        ))

    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=300,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(title="Impact", tickvals=[1, 2, 3], ticktext=["Low", "Med", "High"], range=[0.5, 3.5], showgrid=False),
        yaxis=dict(title="Probability", tickvals=[1, 2, 3], ticktext=["Low", "Med", "High"], range=[0.5, 3.5], showgrid=False),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Mitigation table
    _h('<div style="font-size: 12px; font-weight: 700; color: var(--grey-400); letter-spacing: 0.08em; text-transform: uppercase; margin: 12px 0 8px;">Mitigation Strategies</div>')
    for r in risks:
        prob_color = {"HIGH": "#D63031", "MED": "#FFB600", "LOW": "#00B894"}.get(r.get("prob", "MED").upper(), "#FFB600")
        _h(f"""
        <div style="display:flex; gap:12px; align-items:flex-start; padding:10px 0; border-bottom:1px solid var(--grey-border-light);">
            <div style="min-width:8px; width:8px; height:8px; border-radius:50%; background:{prob_color}; margin-top:5px;"></div>
            <div>
                <div style="font-size:13px; font-weight:600; color:var(--pwc-black);">{r.get('risk','')}</div>
                <div style="font-size:12px; color:#4A4A4A; margin-top:2px;">{r.get('mitigation','')}</div>
            </div>
        </div>
        """)
    st.html('<div style="height: 30px;"></div>')


def render_success_metrics(payload: dict) -> None:
    """Render the success metrics / KPI tracking table."""
    st.markdown('<div style="font-size: 18px; font-weight: 700; color: var(--pwc-black); margin-bottom: 16px;">Success Metrics & KPI Tracking</div>', unsafe_allow_html=True)
    metrics = payload.get("success_metrics", [])
    if not metrics:
        return

    _h("""
    <table style="width:100%; border-collapse:collapse; font-size:13px; background:var(--white); border:1px solid var(--grey-border); box-shadow:var(--shadow-sm); border-radius:8px; overflow:hidden;">
        <thead style="background:var(--grey-100); border-bottom:2px solid var(--grey-border);">
            <tr>
                <th style="padding:12px 16px; text-align:left; font-weight:700;">KPI</th>
                <th style="padding:12px 16px; text-align:center; font-weight:700;">Baseline</th>
                <th style="padding:12px 16px; text-align:center; font-weight:700;">Target</th>
                <th style="padding:12px 16px; text-align:left; font-weight:700;">Measurement Method</th>
            </tr>
        </thead><tbody>
    """)
    for m in metrics:
        _h(f"""
        <tr style="border-bottom:1px solid var(--grey-border-light);">
            <td style="padding:12px 16px; font-weight:600;">{m.get('kpi','')}</td>
            <td style="padding:12px 16px; text-align:center; color:var(--grey-400);">{m.get('baseline','')}</td>
            <td style="padding:12px 16px; text-align:center; color:#00B894; font-weight:700;">{m.get('target','')}</td>
            <td style="padding:12px 16px; color:#4A4A4A;">{m.get('method','')}</td>
        </tr>
        """)
    _h('</tbody></table>')
    st.html('<div style="height: 30px;"></div>')


def render_benchmarks(payload: dict) -> None:
    st.markdown('<div style="font-size: 18px; font-weight: 700; color: var(--pwc-black); margin-bottom: 16px;">Interactive Peer Benchmarking</div>', unsafe_allow_html=True)
    peers = payload.get("interactive_benchmarks", [])
    
    for p in peers:
        with st.expander(f"{p.get('peer', 'Peer')} — {p.get('initiative', 'Initiative')}"):
            _h(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid var(--grey-border-light);">
                <div style="font-size: 18px; font-weight: 800; color: #00B894;">{p.get('outcome', '')}</div>
                <div style="display: flex; gap: 16px; text-align: center;">
                    <div>
                        <div style="font-size: 18px; font-weight: 700;">{p.get('similarity_score', 0)}</div>
                        <div style="font-size: 10px; color: var(--grey-400); text-transform: uppercase;">Similarity</div>
                    </div>
                    <div>
                        <div style="font-size: 18px; font-weight: 700;">{p.get('relevance_score', 0)}</div>
                        <div style="font-size: 10px; color: var(--grey-400); text-transform: uppercase;">Relevance</div>
                    </div>
                    <div>
                        <div style="font-size: 18px; font-weight: 700;">{p.get('transferability_score', 0)}</div>
                        <div style="font-size: 10px; color: var(--grey-400); text-transform: uppercase;">Transfer</div>
                    </div>
                </div>
            </div>
            <div style="font-size: 13px; color: #4A4A4A; line-height: 1.6;">
                {p.get('details', '')}
            </div>
            """)
    st.html('<div style="height: 30px;"></div>')


def render_capability_roadmap(payload: dict) -> None:
    st.markdown('<div style="font-size: 18px; font-weight: 700; color: var(--pwc-black); margin-bottom: 16px;">Capability-Led Roadmap</div>', unsafe_allow_html=True)
    rm = payload.get("capability_roadmap", {})
    
    phases = [
        {"name": "Phase 1: Foundations", "items": rm.get("phase1", [])},
        {"name": "Phase 2: Core Scaling", "items": rm.get("phase2", [])},
        {"name": "Phase 3: Advanced", "items": rm.get("phase3", [])},
    ]

    for ph in phases:
        _h(f"""
        <div style="background: var(--grey-100); padding: 8px 12px; border-radius: 4px; font-size: 12px; font-weight: 700; color: var(--pwc-black); text-transform: uppercase; margin-bottom: 8px;">
            {ph['name']}
        </div>
        """)
        for item in ph['items']:
            _h(f"""
            <div style="background: var(--white); border: 1px solid var(--grey-border); border-left: 3px solid var(--brand-primary); padding: 12px; border-radius: 4px; margin-bottom: 8px; font-size: 13px; display: flex; justify-content: space-between; align-items: center; box-shadow: var(--shadow-sm);">
                <div style="flex: 2; font-weight: 600;">{item.get('initiative', '')}</div>
                <div style="flex: 1; color: var(--grey-400);"><span style="font-size: 10px; text-transform: uppercase;">Owner:</span> {item.get('owner', '')}</div>
                <div style="flex: 1; color: #00B894; font-weight: 600; text-align: right;">{item.get('value_pool', '')}</div>
                <div style="flex: 1; color: var(--grey-label); font-size: 11px; text-align: right;">{item.get('milestones', '')}</div>
            </div>
            """)
    st.html('<div style="height: 40px;"></div>')


def render_stacked_bar_allocation(plan: dict) -> None:
    st.markdown('<div style="font-size: 18px; font-weight: 700; color: var(--pwc-black); margin-bottom: 16px;">Phased Capital Allocation</div>', unsafe_allow_html=True)
    
    rows = plan.get("ledger_rows", [])
    if not rows:
        return
        
    phases = ["Phase 1: Foundations", "Phase 2: Scale", "Phase 3: Maturity"]
    
    # Collect unique pillars
    pillars = []
    for r in rows:
        p = r.get("pillar", "Other")
        if p not in pillars:
            pillars.append(p)
            
    # If empty or missing, fallback
    if not pillars:
        return
    
    from collections import defaultdict
    data = defaultdict(lambda: [0.0, 0.0, 0.0])
    
    for r in rows:
        pillar = r.get("pillar", "Other")
        amt = r.get("allocation_usd", 0) / 1_000_000.0  # Convert to Millions
        
        # Distribute budget across phases based on type
        if "Foundation" in pillar:
            data[pillar][0] += amt * 0.8
            data[pillar][1] += amt * 0.2
        elif "Value Driver" in pillar or "Primary" in pillar:
            data[pillar][0] += amt * 0.4
            data[pillar][1] += amt * 0.4
            data[pillar][2] += amt * 0.2
        else:
            data[pillar][0] += amt * 0.1
            data[pillar][1] += amt * 0.5
            data[pillar][2] += amt * 0.4
            
    fig = go.Figure()
    
    # Dynamic coloring for unknown pillars
    colors_palette = ["#00B894", "#FFB600", "#FF5A00", "#0096FF", "#6C5CE7"]
    colors = {}
    for i, p in enumerate(pillars):
        if "Foundation" in p:
            colors[p] = "#2D2D2D"
        elif "Value Driver" in p or "Primary" in p:
            colors[p] = "#D04A02"
        else:
            colors[p] = colors_palette[i % len(colors_palette)]
    
    for pillar in pillars:
        fig.add_trace(go.Bar(
            name=pillar,
            x=phases,
            y=data[pillar],
            marker_color=colors[pillar],
            hovertemplate="$%{y:.1f}M"
        ))
        
    fig.update_layout(
        barmode='stack',
        margin=dict(l=0, r=0, t=10, b=0),
        height=300,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.04)", tickprefix="$", ticksuffix="M")
    )
    
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.html('<div style="height: 30px;"></div>')


def render_investment_ledger(plan: dict) -> None:
    st.markdown('<div style="font-size: 18px; font-weight: 700; color: var(--pwc-black); margin-bottom: 16px;">Strategic Investment Ledger (Use Case Allocation)</div>', unsafe_allow_html=True)
    
    rows = plan.get("ledger_rows", [])
    if not rows:
        return
        
    df_data = []
    for r in rows:
        df_data.append({
            "Pillar": r['pillar'],
            "Use Case / Initiative": r['initiative'],
            "Budget Allocation": _fmt_usd(r['allocation_usd']),
            "Value Driver": r['roi_driver']
        })
        
    st.dataframe(df_data, use_container_width=True, hide_index=True)
    st.html('<div style="height: 30px;"></div>')


def render_full_dashboard() -> None:
    plan = st.session_state.thesis_plan
    payload = st.session_state.get("thesis_payload", {})

    # 1. Executive Recommendation & Confidence (BCG Phased)
    render_decision_banner(payload, plan)

    # 2. Executive Summary & Investment Thesis Rationale
    render_executive_summary(payload)

    # 3. AI Maturity Gauge (visual)
    render_maturity_gauge(payload)

    # 4. Use Case Prioritization Matrix (McKinsey Impact vs Feasibility)
    render_use_case_prioritization(plan)

    # 5. Phased Capital Allocation (Stacked Bar)
    render_stacked_bar_allocation(plan)

    # 6. Strategic Investment Ledger (detailed table)
    render_investment_ledger(plan)

    # 7. Scenario-Based Financial Model (interactive S-curves)
    render_interactive_financial_model(plan)

    # 8. Five-Gate Readiness Assessment
    render_five_gates(payload)

    # 9. Risk Register & Heatmap
    render_risk_heatmap(payload)

    # 10. Peer Benchmarking
    render_benchmarks(payload)

    # 11. Success Metrics / KPI Tracking
    render_success_metrics(payload)
        
    st.html('<div style="height: 50px;"></div>')
    
    # Export to PDF Option
    st.markdown("---")
    colA, colB, colC = st.columns([1, 2, 1])
    with colB:
        if st.button("📄 Export to PDF", use_container_width=True):
            st.components.v1.html(
                "<script>window.parent.print();</script>",
                height=0, width=0
            )

    _h("""
    <div style="font-size: 11px; color: var(--grey-text); line-height: 1.6; border-top: 1px solid var(--grey-border); padding-top: 20px;">
        <strong>Disclaimer:</strong> This executive platform generates illustrative estimates derived from proprietary industry benchmarks and client-reported data. Figures should be validated with professional advisors before investment decisions are made. All projections are subject to stated confidence bands and scenario assumptions. Confidential — not for external distribution.
    </div>
    """)
