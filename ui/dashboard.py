"""
ui/dashboard.py — Premium BFSI AI Investment Engine results dashboard (PwC Horizon spec).
"""
from __future__ import annotations
import streamlit as st
import plotly.graph_objects as go
import html
from engine.legacy_diagnostic import run_diagnostic, LegacyInputs
from engine.competitive import compute_competitive_advantage_score

# ── Main Entry Point ───────────────────────────────────────────────────────

def render_dashboard() -> None:
    if not st.session_state.get("thesis_generated"):
        st.warning("Please complete the intake form first.")
        return

    scenario = st.radio("Execution Scenario", ["conservative", "base", "aggressive"], index=1, horizontal=True)
    if scenario != st.session_state.get("current_scenario", "base"):
        st.session_state.current_scenario = scenario
        from engine.math_engine import build_investment_plan
        st.session_state.thesis_plan = build_investment_plan(
            st.session_state.discovery_answers, 
            st.session_state.budget_usd_m, 
            st.session_state.primary_goals,
            scenario=scenario
        )
        st.rerun()

    plan = st.session_state.thesis_plan or []
    answers = st.session_state.discovery_answers or {}
    company = html.escape(st.session_state.company_name) if st.session_state.company_name else "The Firm"
    _render_kpi_header(plan, answers, company)

    tab1, tab2, tab3, tab4 = st.tabs([
        "Prioritization Matrix",
        "Legacy Deprecation",
        "Strategic Memo",
        "Risk & Competitiveness",
    ])
    with tab1: _tab_matrix(plan)
    with tab2: _tab_deprecation(answers, plan)
    with tab3: _tab_memo()
    with tab4: _tab_risk_competitive(plan, answers)


# ── KPI Header Row ─────────────────────────────────────────────────────────

def _render_kpi_header(plan, answers, company):
    approved_plan = [p for p in plan if p.get("budget_approved", False)]
    total_anv  = sum(p["anv"] for p in approved_plan) / 1e6
    total_cost = sum(p["impl_cost"] for p in approved_plan) / 1e6
    
    from engine.math_engine import compute_execution_risk, payback_months
    exec_risk = compute_execution_risk(answers)
    risk_adj_anv = total_anv * (1.0 - exec_risk)
    
    payback = payback_months(total_cost * 1e6, total_anv * 1e6)
    quick_wins = sum(1 for p in approved_plan if p["quadrant"] == "Quick Wins / Fill-ins")
    bets       = sum(1 for p in approved_plan if p["quadrant"] == "Strategic Bets")
    aum        = answers.get("S1_AUM", 50)

    st.html(f"""
    <div style="margin-bottom: var(--sp-6);">
        <div style="font-family: var(--font-head); font-size: 26px; color: var(--black); line-height: 1.2;">
            AI Investment Roadmap: <span style="color: var(--pwc-orange);">{company}</span>
        </div>
        <div style="font-size: 14px; color: var(--g500); margin-top: var(--sp-1);">
            ${aum}B AUM · {len(plan)} AI Levers Scored
        </div>
    </div>
    <div class="hz-kpi-row">
        <div class="hz-kpi-tile hz-kpi-hero">
            <div class="hz-kpi-lbl">Risk-Adjusted Annual Net Value</div>
            <div class="hz-kpi-num">${risk_adj_anv:.1f}M</div>
            <div style="font-size: 11px; color: var(--pwc-orange); border-top: 1px solid var(--pwc-orange); margin-top: 8px; padding-top: 4px;">
                Raw ANV: ${total_anv:.1f}M
            </div>
        </div>
        <div class="hz-kpi-tile">
            <div class="hz-kpi-lbl">Strategic Bets</div>
            <div class="hz-kpi-num">{bets}</div>
        </div>
        <div class="hz-kpi-tile">
            <div class="hz-kpi-lbl">Quick Wins</div>
            <div class="hz-kpi-num">{quick_wins}</div>
        </div>
        <div class="hz-kpi-tile">
            <div class="hz-kpi-lbl">Portfolio Payback</div>
            <div class="hz-kpi-num">{payback:.0f}mo</div>
        </div>
    </div>
    """)


# ── Tab 1: Prioritization Matrix ──────────────────────────────────────────

def _tab_matrix(plan: list[dict]) -> None:
    st.html('<div class="hz-report-h2">AI Use Case Prioritization Matrix</div>')
    
    # Thresholds match engine classification exactly
    thresh_imp = 65
    thresh_feas = 60

    x_vals = []
    y_vals = []
    sizes = []
    labels = []
    funded = []

    for i, p in enumerate(plan):
        x_vals.append(p["feasibility"])
        y_vals.append(p["impact"])
        # Scale area, not diameter
        area = max(12, p["anv_m"] * 3)
        sizes.append(area ** 0.5 * 3) # approx sqrt scaling
        labels.append(p["name"].split("&")[0].strip())
        funded.append(p.get("budget_approved", False))

    fig = go.Figure()

    # Split into funded and unfunded to style them correctly
    for i, p in enumerate(plan):
        name = labels[i]
        
        if funded[i]:
            marker = dict(size=sizes[i], color="#D04A02", line=dict(color="white", width=1))
        else:
            marker = dict(size=sizes[i], color="rgba(0,0,0,0)", line=dict(color="#D04A02", width=1.5))

        # Only show labels for top 5 (which are usually first in the plan sorted by ANV/Priority)
        mode = "markers+text" if i < 5 else "markers"
        
        hovertemplate = (
            f"<b>{p['name']}</b>{' (Unfunded)' if not funded[i] else ''}<br>"
            f"ANV: ${p['anv_m']:.1f}M/yr<br>"
            f"Payback: {p['payback']:.0f} months<br>"
            f"Cost: ${p.get('impl_cost', 0)/1e6:.1f}M<br>"
            f"Priority: {p['priority']}<br>"
            f"<extra>{p['quadrant']}</extra>"
        )

        fig.add_trace(go.Scatter(
            x=[x_vals[i]], y=[y_vals[i]],
            mode=mode,
            text=[name],
            textposition="top center",
            textfont=dict(size=11, color="#2D2D2D", family="Arial"),
            marker=marker,
            name=p["name"],
            hovertemplate=hovertemplate,
            showlegend=False,
        ))

    # Add quadrant tint for Strategic Bets
    fig.add_shape(type="rect", x0=thresh_feas, y0=thresh_imp, x1=105, y1=105,
                  fillcolor="rgba(208,74,2,0.07)", line=dict(width=0), layer="below")

    # Lines
    fig.add_hline(y=thresh_imp, line_dash="dash", line_color="#DEDEDE", line_width=1)
    fig.add_vline(x=thresh_feas, line_dash="dash", line_color="#DEDEDE", line_width=1)

    # Annotations
    annotations = [
        dict(x=thresh_feas + 2, y=103, text="Strategic bets", font=dict(color="#D04A02", size=11, family="Arial"), showarrow=False, xanchor="left"),
    ]
    fig.update_layout(
        annotations=annotations,
        xaxis=dict(range=[0, 105], showgrid=False, zeroline=False, tickfont=dict(size=11, color="#7D7D7D"), title=dict(text="Feasibility Score →", font=dict(color="#7D7D7D"))),
        yaxis=dict(range=[0, 105], showgrid=False, zeroline=False, tickfont=dict(size=11, color="#7D7D7D"), title=dict(text="Business Impact Score →", font=dict(color="#7D7D7D"))),
        height=500, margin=dict(l=40, r=40, t=20, b=40),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Arial"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Lever Table
    st.html('<div class="hz-report-h2">Full Lever Scorecard</div>')
    rows = ""
    for p in plan:
        funded = p.get("budget_approved", False)
        tr_cls = "" if funded else "unfunded"
        funded_tag = "" if funded else f'<span class="hz-chip median" style="margin-left:8px;">UNFUNDED</span>'
        
        # Negative ANV handling
        if p["anv_m"] < 0:
            payback_str = "n/a — negative ANV"
            val_str = f"<span class='hz-status-breach'>${p['anv_m']:.1f}M</span>"
            warn = f'<span class="hz-status-breach" style="font-size:11px; margin-left:8px;">△ value-destructive</span>'
        else:
            payback_str = f"{p['payback']:.0f} mo"
            val_str = f"${p['anv_m']:.1f}M"
            warn = ""
            
        rows += f"""
        <tr class="{tr_cls}">
            <td><strong>{p['name']}</strong>{warn}{funded_tag}</td>
            <td>{p['priority']}</td>
            <td>{p['quadrant']}</td>
            <td class="num">{val_str}</td>
            <td class="num">{payback_str}</td>
            <td class="num">{p['impact']}/100</td>
            <td class="num">{p['feasibility']}/100</td>
        </tr>"""
        
    st.html(f"""
    <table class="hz-table-wrap">
        <thead>
            <tr>
                <th>AI Use Case</th><th>Priority</th><th>Quadrant</th>
                <th style="text-align:right;">ANV / Year</th><th style="text-align:right;">Payback</th>
                <th style="text-align:right;">Impact</th><th style="text-align:right;">Feasibility</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    """)


# ── Tab 2: Legacy Deprecation ──────────────────────────────────────────────

def _tab_deprecation(answers: dict, plan: list[dict]) -> None:
    st.html('<div class="hz-report-h2">Legacy System Deprecation Diagnostic</div>')

    PLATFORM_GATED_LEVERS = {"lever_2", "lever_8", "lever_11", "lever_13"}
    unlocked_anv_m = sum(p["anv"] for p in plan if p.get("id") in PLATFORM_GATED_LEVERS) / 1e6

    inputs = LegacyInputs(
        maintenance_cost_m=answers.get("S5_MAINTENANCE_COST", 6.5),
        biz_value_m=answers.get("S5_BIZ_VALUE", 20.0),
        silo_count=answers.get("S1_SILO", 5.0),
        architecture=answers.get("S1_ARCH", "Hybrid — partial cloud, many point-to-point feeds"),
        api_maturity=answers.get("S1_API_GATEWAY", "Internal REST APIs (Point-to-point)"),
        data_ownership=answers.get("S5_DATA_OWNERSHIP", 55.0),
        lineage=answers.get("S5_LINEAGE", 35.0),
        dq_sla=answers.get("S5_DQ_SLA", 72.0),
        reg_trace=answers.get("S5_REGULATORY_TRACE", 50.0),
        change_mgmt=answers.get("S5_CHANGE_MGMT", 45.0),
        unlocked_anv_m=unlocked_anv_m,
        rebuild_cost_m=None 
    )

    result = run_diagnostic(inputs)
    pillars = result["pillars"]

    col1, col2 = st.columns([1, 1])
    with col1:
        vcls = "modernize"
        if result["verdict"] == "KILL & REBUILD": vcls = "kill"
        elif result["verdict"] == "REBUILD-BLOCKED": vcls = "blocked"
        elif result["verdict"] == "HOLD & OPTIMIZE": vcls = "hold"
        
        st.html(f"""
        <div class="hz-verdict {vcls}">
            <div class="hz-verdict-title">{result['verdict']}</div>
            <div class="hz-verdict-body">
                <strong>Architecture Pattern:</strong> {result['pattern']}<br><br>
                {result['rationale']}
            </div>
        </div>
        """)

    with col2:
        def b_status(s):
            if s > 70: return "<span class='hz-status-ok'>● Good</span>"
            if s > 40: return "<span class='hz-status-watch'>● Watch</span>"
            return "<span class='hz-status-breach'>● Breach</span>"
            
        st.html(f"""
        <table class="hz-table-wrap">
            <thead><tr><th>Diagnostic Pillar</th><th style="text-align:right;">Score</th><th>Status</th></tr></thead>
            <tbody>
                <tr><td>Tech Debt Score</td><td class="num">{pillars['tech_debt_score']}/100</td><td>{b_status(pillars['tech_debt_score'])}</td></tr>
                <tr><td>Fragmentation Score</td><td class="num">{pillars['fragmentation_score']}/100</td><td>{b_status(pillars['fragmentation_score'])}</td></tr>
                <tr><td>Governance Readiness</td><td class="num">{pillars['governance_readiness']}/100</td><td>{b_status(pillars['governance_readiness'])}</td></tr>
                <tr><td><strong>Overall Deprecation Score</strong></td><td class="num"><strong>{result['deprecation_score']}/100</strong></td><td></td></tr>
            </tbody>
        </table>
        """)

    if result.get("self_funding"):
        sf = result["self_funding"]
        st.html('<div class="hz-report-h2" style="margin-top: 2rem;">Self-Funding Horizon</div>')
        payback_str = f"{sf['payback_months']} months" if sf['payback_months'] else "Does not pay back"
        funding_gap_str = f"${sf['first_year_funding_gap_m']}M"
        if sf['first_year_funding_gap_m'] <= 0:
            funding_gap_str = "Fully Funded"
        
        st.html(f"""
        <table class="hz-table-wrap">
            <thead><tr><th>Metric</th><th style="text-align:right;">Value</th></tr></thead>
            <tbody>
                <tr><td>Legacy Annual Savings (Retained)</td><td class="num">${sf['legacy_annual_savings_m']}M</td></tr>
                <tr><td>Unlocked AI Value (Platform-Gated)</td><td class="num">${sf['unlocked_anv_m']}M</td></tr>
                <tr><td><strong>Total Annual Value</strong></td><td class="num"><strong>${sf['total_annual_value_m']}M</strong></td></tr>
                <tr><td>Rebuild Capex {"(Estimated)" if sf['rebuild_cost_estimated'] else ""}</td><td class="num">${sf['rebuild_cost_m']}M</td></tr>
                <tr><td>First Year Funding Gap</td><td class="num">{funding_gap_str}</td></tr>
                <tr><td><strong>Payback Period</strong></td><td class="num"><strong>{payback_str}</strong></td></tr>
            </tbody>
        </table>
        """)

# ── Tab 3: Strategic Memo ──────────────────────────────────────────────────

def _tab_memo() -> None:
    summary = st.session_state.get("thesis_summary", "")
    if not summary:
        st.info("Complete the intake form to generate the strategic memo.")
        return
    st.html(f"""
    <div style="max-width: 800px;">
        <div style="font-family: var(--font-head); font-size: 26px; color: var(--black); margin: var(--sp-6) 0;">Executive Summary</div>
        {summary}
        <div style="margin-top: var(--sp-6); font-size: 11px; color: var(--g500); border-top: 1px solid var(--g200); padding-top: var(--sp-2);">
            Generated by Gemini. Review for accuracy.
        </div>
    </div>
    """)

# ── Tab 4: Risk & Competitiveness ──────────────────────────────────────────

def _tab_risk_competitive(plan: list[dict], answers: dict) -> None:
    st.html('<div class="hz-report-h2">Competitive Positioning (vs. LIC, HDFC Life, ICICI Pru)</div>')
    
    comp_score = compute_competitive_advantage_score(plan, answers)
    c_score = comp_score["overall_score"]
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.html(f"""
        <div class="hz-bullet-wrap" style="margin-top: var(--sp-4);">
            <div class="hz-bullet-lbl-row">
                <span class="hz-bullet-lbl">Defensibility Index</span>
                <span class="hz-bullet-val">{c_score}/100</span>
            </div>
            <div class="hz-bullet-track">
                <div class="hz-bullet-thresh" style="left: 40%;"></div>
                <div class="hz-bullet-thresh" style="left: 70%;"></div>
                <div class="hz-bullet-fill" style="width: {c_score}%;"></div>
            </div>
        </div>
        """)
        
    with col2:
        if c_score >= 70:
            st.html("""
            <div class="hz-callout win">
                <div class="hz-callout-title">Market Leading Advantage</div>
                <div class="hz-callout-desc">This plan leverages highly defensible MMIL assets (e.g. Rural Distribution or MAUDE). 
                Competitors will take 18-24 months to reach parity with these specific levers.</div>
            </div>
            """)
        else:
            st.html("""
            <div class="hz-callout park">
                <div class="hz-callout-title">Catch-Up Strategy</div>
                <div class="hz-callout-desc">The current plan focuses on generic IT modernization. While necessary, 
                it does not provide a distinctive competitive moat against tier-1 incumbents like HDFC Life.</div>
            </div>
            """)
            
        adv_html = ""
        for adv in comp_score["advantages"]:
            adv_html += f"<li><strong>{adv.name}:</strong> {adv.mmil_advantage} (<em>Parity: {adv.time_to_parity}</em>)</li>"
        
        if adv_html:
            st.html(f"<ul style='font-size:13px; color:var(--g700);'>{adv_html}</ul>")


    st.html('<div class="hz-report-h2" style="margin-top: 32px;">Regulatory Compliance Constraints</div>')
    
    reg_rows = ""
    for p in plan:
        rs = p.get("reg_status", {})
        if not rs: continue
        
        r_level = rs.get("risk_level", "green")
        status_text = "<span class='hz-status-ok'>● Compliant</span>" if r_level == "green" else ("<span class='hz-status-watch'>● Requires Mitigation</span>" if r_level == "yellow" else "<span class='hz-status-breach'>● High Risk</span>")
        
        constraints_html = "<br>".join([f"• {c.name} ({c.authority})" for c in rs.get("constraints", [])])
        if not constraints_html: constraints_html = "Standard IT hygiene"
        
        mitigations = "<br>".join([f"• {m}" for m in rs.get("mitigations", [])])
        if not mitigations: mitigations = "None required"
        
        reg_rows += f"""
        <tr>
            <td><strong>{p['name']}</strong></td>
            <td>{status_text}</td>
            <td>{constraints_html}</td>
            <td>{mitigations}</td>
        </tr>
        """
        
    st.html(f"""
    <table class="hz-table-wrap">
        <thead>
            <tr>
                <th>Investment Lever</th>
                <th>Risk Profile</th>
                <th>Key Constraints</th>
                <th>Required Mitigations</th>
            </tr>
        </thead>
        <tbody>
            {reg_rows}
        </tbody>
    </table>
    """)
