"""
ui/dashboard.py — Premium BFSI AI Investment Engine results dashboard.
"""
from __future__ import annotations
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from engine.legacy_diagnostic import calculate_deprecation_score
from engine.competitive import compute_competitive_advantage_score

# ── Colour helpers ────────────────────────────────────────────────────────

def _quad_cls(q: str) -> str:
    m = {"Strategic Bets": "bfsi-quad-strategic", "Quick Wins / Fill-ins": "bfsi-quad-quick",
         "Park (Data-Blocked)": "bfsi-quad-park", "Evaluate": "bfsi-quad-evaluate"}
    return m.get(q, "bfsi-quad-evaluate")

def _priority_cls(p: str) -> str:
    return {"P0": "bfsi-p0", "P1": "bfsi-p1", "P2": "bfsi-p2", "P3": "bfsi-p3"}.get(p, "bfsi-p3")

# ── Main Entry Point ───────────────────────────────────────────────────────

def render_dashboard() -> None:
    if not st.session_state.get("thesis_generated"):
        st.warning("Please complete the intake form first.")
        return

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
    # Only aggregate levers that fit within the budget limit
    approved_plan = [p for p in plan if p.get("budget_approved", False)]
    
    total_anv  = sum(p["anv"] for p in approved_plan) / 1e6
    top_lever  = approved_plan[0]["name"] if approved_plan else (plan[0]["name"] if plan else "—")
    payback    = approved_plan[0]["payback"] if approved_plan else 0
    quick_wins = sum(1 for p in approved_plan if p["quadrant"] == "Quick Wins / Fill-ins")
    bets       = sum(1 for p in approved_plan if p["quadrant"] == "Strategic Bets")
    aum        = answers.get("S1_AUM", 50)

    st.html(f"""
    <div style="margin-bottom:8px;">
        <div style="font-size:11px;font-weight:700;letter-spacing:0.10em;text-transform:uppercase;color:var(--ink-500);margin-bottom:4px;">DIAGNOSTIC COMPLETE</div>
        <div style="font-family:'Outfit',sans-serif;font-size:24px;font-weight:700;color:var(--ink-900);line-height:1.2;">
            AI Investment Roadmap: <span style="color:var(--brand);">{company}</span>
        </div>
        <div style="font-size:12.5px;color:var(--ink-600);margin-top:4px;">
            ${aum}B AUM · 14 AI Levers Scored
        </div>
    </div>
    <div class="bfsi-kpi-grid">
        <div class="bfsi-kpi-tile bfsi-kpi-orange">
            <div class="bfsi-kpi-num">${total_anv:.0f}M</div>
            <div class="bfsi-kpi-label">Total Annual Net Value</div>
            <div class="bfsi-kpi-delta bfsi-delta-pos">↑ 25–35% cost reduction potential</div>
        </div>
        <div class="bfsi-kpi-tile bfsi-kpi-green">
            <div class="bfsi-kpi-num">{bets}</div>
            <div class="bfsi-kpi-label">Strategic Bets</div>
            <div class="bfsi-kpi-delta bfsi-delta-pos">High impact · Fast execution</div>
        </div>
        <div class="bfsi-kpi-tile bfsi-kpi-amber">
            <div class="bfsi-kpi-num">{quick_wins}</div>
            <div class="bfsi-kpi-label">Quick Wins</div>
            <div class="bfsi-kpi-delta bfsi-delta-warn">Deploy first · Prove ROI</div>
        </div>
        <div class="bfsi-kpi-tile bfsi-kpi-red">
            <div class="bfsi-kpi-num">{payback:.0f}mo</div>
            <div class="bfsi-kpi-label">Fastest Payback</div>
            <div class="bfsi-kpi-delta bfsi-delta-pos">↑ {top_lever[:28]}…</div>
        </div>
    </div>
    """)


# ── Tab 1: Prioritization Matrix ──────────────────────────────────────────

def _tab_matrix(plan: list[dict]) -> None:
    st.html('<div class="bfsi-report-h2">AI Use Case Prioritization Matrix — Impact × Feasibility</div>')
    # Scatter 2x2
    names   = [p["name"] for p in plan]
    x_vals  = [p["feasibility"] for p in plan]
    y_vals  = [p["impact"] for p in plan]
    sizes   = [min(80, max(12, p["anv_m"] * 3)) for p in plan]
    
    # Subtle Colors for Light Mode
    colors  = ["#D04A02" if p["quadrant"] == "Strategic Bets"       # Brand Orange
               else "#1B9C6B" if p["quadrant"] == "Quick Wins / Fill-ins" # Green
               else "#E8A317" if p["quadrant"] == "Park (Data-Blocked)"   # Amber
               else "#6B7480" for p in plan]                              # Cool Gray

    fig = go.Figure()
    for i, p in enumerate(plan):
        # Visually de-emphasize unfunded levers
        opacity = 0.9 if p.get("budget_approved", False) else 0.3
        funded_text = "" if p.get("budget_approved", False) else " (Unfunded)"
        
        fig.add_trace(go.Scatter(
            x=[x_vals[i]], y=[y_vals[i]],
            mode="markers+text",
            text=[p["name"].split("&")[0].strip()[:22] + funded_text],
            textposition="top center",
            textfont=dict(size=10, color="#4A525C"),
            marker=dict(size=sizes[i], color=colors[i], opacity=opacity,
                        line=dict(color="white", width=2)),
            name=p["quadrant"],
            hovertemplate=(
                f"<b>{p['name']}</b>{funded_text}<br>"
                f"ANV: ${p['anv_m']:.1f}M/yr<br>"
                f"Payback: {p['payback']:.0f} months<br>"
                f"Cost: ${p.get('impl_cost', 0)/1e6:.1f}M<br>"
                f"Priority: {p['priority']}<br>"
                f"<extra>{p['quadrant']}</extra>"
            ),
            showlegend=False,
        ))

    # Quadrant lines
    fig.add_hline(y=50, line_dash="dash", line_color="#E3E7EC", line_width=1)
    fig.add_vline(x=50, line_dash="dash", line_color="#E3E7EC", line_width=1)

    # Quadrant labels
    annotations = [
        dict(x=82, y=95, text="STRATEGIC BETS", font=dict(color="#D04A02", size=10, family="Inter"), showarrow=False),
        dict(x=18, y=95, text="PARK", font=dict(color="#E8A317", size=10, family="Inter"), showarrow=False),
        dict(x=82, y=5,  text="QUICK WINS / FILL-INS", font=dict(color="#1B9C6B", size=10, family="Inter"), showarrow=False),
        dict(x=18, y=5,  text="EVALUATE", font=dict(color="#6B7480", size=10, family="Inter"), showarrow=False),
    ]
    fig.update_layout(
        annotations=annotations,
        xaxis=dict(range=[0, 108],
                   showgrid=False, zeroline=False, tickfont=dict(size=10, color="#6B7480"), title=dict(text="Feasibility Score →", font=dict(color="#6B7480"))),
        yaxis=dict(range=[0, 108],
                   showgrid=False, zeroline=False, tickfont=dict(size=10, color="#6B7480"), title=dict(text="Business Impact Score →", font=dict(color="#6B7480"))),
        height=500, margin=dict(l=40, r=40, t=20, b=40),
        plot_bgcolor="#FAFBFC", paper_bgcolor="white",
        font=dict(family="Inter"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Lever Table
    st.html('<div class="bfsi-report-h2">Full Lever Scorecard</div>')
    rows = ""
    for p in plan:
        qcls = _quad_cls(p["quadrant"])
        pcls = _priority_cls(p["priority"])
        warn = f'<span style="background:rgba(239,68,68,0.15);color:#EF4444;padding:2px 6px;border-radius:4px;font-size:10px;margin-left:8px;font-weight:700;">{p["warning"]}</span>' if p.get("warning") else ""
        funded_tag = "" if p.get("budget_approved", False) else f'<span style="background:var(--ink-200);color:var(--ink-500);padding:2px 6px;border-radius:4px;font-size:10px;margin-left:8px;font-weight:700;">UNFUNDED</span>'
        row_style = "opacity: 0.4;" if not p.get("budget_approved", False) else ""
        rows += f"""
        <tr style="{row_style}">
            <td><strong>{p['name']}</strong>{warn}{funded_tag}</td>
            <td><span class="bfsi-priority-chip {pcls}">{p['priority']}</span></td>
            <td class="{qcls}">{p['quadrant']}</td>
            <td><strong>${p['anv_m']:.1f}M</strong></td>
            <td>{p['payback']:.0f} mo</td>
            <td>{p['impact']}/100</td>
            <td>{p['feasibility']}/100</td>
        </tr>"""
    st.html(f"""
    <table class="bfsi-lever-table">
        <thead>
            <tr>
                <th>AI Use Case</th><th>Priority</th><th>Quadrant</th>
                <th>ANV / Year</th><th>Payback</th><th>Impact</th><th>Feasibility</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    """)


# ── Tab 2: Legacy Deprecation ──────────────────────────────────────────────

def _tab_deprecation(answers: dict, plan: list[dict]) -> None:
    st.html('<div class="bfsi-report-h2">Legacy System Deprecation Diagnostic</div>')

    # Platform-gated levers that depend on killing legacy
    PLATFORM_GATED_LEVERS = {"lever_2", "lever_8", "lever_11", "lever_13"}
    unlocked_anv_m = sum(p["anv"] for p in plan if p.get("id") in PLATFORM_GATED_LEVERS) / 1e6

    # Instantiate inputs
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
        rebuild_cost_m=None  # Can be added to questionnaire later
    )

    result = run_diagnostic(inputs)
    pillars = result["pillars"]

    col1, col2 = st.columns([1, 1])
    with col1:
        # Verdict Card
        vcls = "bfsi-verdict-modern"
        if result["verdict"] == "KILL & REBUILD": vcls = "bfsi-verdict-kill"
        elif result["verdict"] == "REBUILD-BLOCKED": vcls = "bfsi-verdict-blocked"
        elif result["verdict"] == "HOLD & OPTIMIZE": vcls = "bfsi-verdict-hold"
        
        st.html(f"""
        <div class="bfsi-verdict-card {vcls}">
            <h3>VERDICT: {result['verdict']}</h3>
            <p><strong>Architecture Pattern:</strong> {result['pattern']}</p>
            <p>{result['rationale']}</p>
        </div>
        """)

    with col2:
        # Diagnostic Table
        st.html(f"""
        <table class="bfsi-diag-table">
            <thead><tr><th>Pillar</th><th>Score</th></tr></thead>
            <tbody>
                <tr><td>Tech Debt Score</td><td>{pillars['tech_debt_score']}/100</td></tr>
                <tr><td>Fragmentation Score</td><td>{pillars['fragmentation_score']}/100</td></tr>
                <tr><td>Governance Readiness</td><td>{pillars['governance_readiness']}/100</td></tr>
                <tr><td><strong>Overall Deprecation Score</strong></td><td><strong>{result['deprecation_score']}/100</strong></td></tr>
            </tbody>
        </table>
        """)

    # Self Funding Horizon
    if result.get("self_funding"):
        sf = result["self_funding"]
        st.html('<div class="bfsi-report-h2" style="margin-top: 2rem;">Self-Funding Horizon</div>')
        payback_str = f"{sf['payback_months']} months" if sf['payback_months'] else "Does not pay back"
        funding_gap_str = f"${sf['first_year_funding_gap_m']}M"
        if sf['first_year_funding_gap_m'] <= 0:
            funding_gap_str = "<span style='color:green;'>Fully Funded</span>"
        
        st.html(f"""
        <table class="bfsi-diag-table">
            <thead><tr><th>Metric</th><th>Value</th></tr></thead>
            <tbody>
                <tr><td>Legacy Annual Savings (Retained)</td><td>${sf['legacy_annual_savings_m']}M</td></tr>
                <tr><td>Unlocked AI Value (Platform-Gated)</td><td>${sf['unlocked_anv_m']}M</td></tr>
                <tr><td><strong>Total Annual Value</strong></td><td><strong>${sf['total_annual_value_m']}M</strong></td></tr>
                <tr><td>Rebuild Capex {"(Estimated)" if sf['rebuild_cost_estimated'] else ""}</td><td>${sf['rebuild_cost_m']}M</td></tr>
                <tr><td>First Year Funding Gap</td><td>{funding_gap_str}</td></tr>
                <tr><td><strong>Payback Period</strong></td><td><strong>{payback_str}</strong></td></tr>
            </tbody>
        </table>
        """)


def _governance(a: dict) -> float:
    return (a.get("S5_DATA_OWNERSHIP", 55) + a.get("S5_LINEAGE", 35) +
            a.get("S5_DQ_SLA", 72) + a.get("S5_REGULATORY_TRACE", 50) +
            a.get("S5_CHANGE_MGMT", 45)) / 5.0


# ── Tab 3: Strategic Memo ──────────────────────────────────────────────────

def _tab_memo() -> None:
    summary = st.session_state.get("thesis_summary", "")
    if not summary:
        st.info("Complete the intake form to generate the strategic memo.")
        return
    st.html(summary)

# ── Tab 4: Risk & Competitiveness ──────────────────────────────────────────

def _tab_risk_competitive(plan: list[dict], answers: dict) -> None:
    st.html('<div class="bfsi-report-h2">Competitive Positioning (vs. LIC, HDFC Life, ICICI Pru)</div>')
    
    comp_score = compute_competitive_advantage_score(plan, answers)
    c_score = comp_score["overall_score"]
    
    col1, col2 = st.columns([1, 2])
    with col1:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=c_score,
            number={"suffix": "/100", "font": {"size": 32, "color": "#11161C"}},
            title={"text": "Defensibility Index", "font": {"size": 13, "color": "#6b7280"}},
            gauge={
                "axis": {"range": [0, 100], "tickfont": {"size": 10}},
                "bar": {"color": "#4F46E5", "thickness": 0.25},
                "steps": [
                    {"range": [0,  40], "color": "#fee2e2"},
                    {"range": [40, 70], "color": "#fef3c7"},
                    {"range": [70, 100], "color": "#d1fae5"},
                ],
                "threshold": {"line": {"color": "#D04A02", "width": 3}, "thickness": 0.75, "value": c_score},
            }
        ))
        fig.update_layout(height=260, margin=dict(l=20, r=20, t=30, b=10), paper_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        if c_score >= 70:
            st.html("""
            <div class="bfsi-callout" style="background:#f0fdf8; border-color:#1B9C6B;">
                <strong>Market Leading Advantage:</strong> This plan leverages highly defensible MMIL assets (e.g. Rural Distribution or MAUDE). 
                Competitors will take 18-24 months to reach parity with these specific levers.
            </div>
            """)
        else:
            st.html("""
            <div class="bfsi-callout" style="background:#fffbeb; border-color:#E8A317;">
                <strong>Catch-Up Strategy:</strong> The current plan focuses on generic IT modernization. While necessary, 
                it does not provide a distinctive competitive moat against tier-1 incumbents like HDFC Life.
            </div>
            """)
            
        adv_html = ""
        for adv in comp_score["advantages"]:
            adv_html += f"<li><strong>{adv.name}:</strong> {adv.mmil_advantage} (<em>Parity: {adv.time_to_parity}</em>)</li>"
        
        if adv_html:
            st.html(f"<ul style='font-size:13px; color:#374151;'>{adv_html}</ul>")


    st.html('<div class="bfsi-report-h2">Regulatory Compliance Constraints (IRDAI, RBI, SEBI)</div>')
    
    reg_rows = ""
    for p in plan:
        rs = p.get("reg_status", {})
        if not rs: continue
        
        r_level = rs.get("risk_level", "green")
        badge_cls = "bfsi-diag-ok" if r_level == "green" else ("bfsi-diag-warn" if r_level == "yellow" else "bfsi-diag-bad")
        status_text = "Compliant" if r_level == "green" else ("Requires Mitigation" if r_level == "yellow" else "High Risk")
        
        constraints_html = "<br>".join([f"• {c.name} ({c.authority})" for c in rs.get("constraints", [])])
        if not constraints_html: constraints_html = "Standard IT hygiene"
        
        mitigations = "<br>".join([f"• {m}" for m in rs.get("mitigations", [])])
        if not mitigations: mitigations = "None required"
        
        reg_rows += f"""
        <tr>
            <td><strong>{p['name']}</strong></td>
            <td><span class="{badge_cls}" style="padding:4px 8px;border-radius:4px;">{status_text}</span></td>
            <td style="font-size:12px;color:#4b5563;">{constraints_html}</td>
            <td style="font-size:12px;color:#4b5563;">{mitigations}</td>
        </tr>
        """
        
    st.html(f"""
    <table class="bfsi-lever-table">
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
