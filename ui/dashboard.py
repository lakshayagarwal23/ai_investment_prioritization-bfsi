"""
ui/dashboard.py — BFSI AI Investment results dashboard (PwC Horizon v5).

Changes: scenario toggle moved INLINE (sidebar removed); Now/Next/Later
roadmap added; legacy tab wired to the rebuilt, firm-dependent diagnostic;
provenance footer on every tab.
"""
from __future__ import annotations
import streamlit as st
import plotly.graph_objects as go
import html
from engine.legacy_diagnostic import run_diagnostic, LegacyInputs
from engine.competitive import compute_competitive_advantage_score
from engine.math_engine import (compute_execution_risk, payback_months,
                                IMPACT_THRESHOLD, FEASIBILITY_THRESHOLD)
from storage.audit import ENGINE_VERSION, CORPUS_VERSION

# Levers whose value is genuinely unlocked only by a modern data platform.
PLATFORM_GATED_LEVERS = {"lever_2", "lever_7", "lever_8", "lever_11", "lever_13"}


def render_dashboard() -> None:
    if not st.session_state.get("thesis_generated"):
        st.warning("Please complete the intake form first.")
        return

    _scenario_bar()

    plan = st.session_state.thesis_plan or []
    answers = st.session_state.discovery_answers or {}
    company = html.escape(st.session_state.company_name) if st.session_state.company_name else "The Firm"

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Executive Summary", "Prioritization Matrix", "Legacy Deprecation",
        "Risk & Competitiveness", "Assumptions Appendix",
    ])
    with tab1:
        _render_kpi_header(plan, answers, company)
        _roadmap(plan)
        _tab_memo()
        _footer()
    with tab2:
        _tab_matrix(plan)
        _footer()
    with tab3:
        _tab_deprecation(answers, plan)
        _footer()
    with tab4:
        _tab_risk_competitive(plan, answers)
        _footer()
    with tab5:
        _tab_assumptions()
        _footer()


# ── Inline scenario toggle (replaces the sidebar radio) ─────────────────────

def _scenario_bar() -> None:
    st.html('<div class="hz-scenario-lbl">Execution scenario</div>')
    c1, c2, c3, _ = st.columns([1, 1, 1, 4])
    current = st.session_state.get("current_scenario", "base")
    labels = {"conservative": "Conservative", "base": "Base", "aggressive": "Aggressive"}
    cols = {"conservative": c1, "base": c2, "aggressive": c3}
    for key, col in cols.items():
        with col:
            is_active = current == key
            if st.button(labels[key], key=f"sc_{key}", use_container_width=True,
                         type="primary" if is_active else "secondary"):
                if key != current:
                    st.session_state.current_scenario = key
                    from engine.math_engine import build_investment_plan
                    st.session_state.thesis_plan = build_investment_plan(
                        st.session_state.discovery_answers, st.session_state.budget_usd_m,
                        st.session_state.primary_goals, scenario=key)
                    st.rerun()
    if st.button("↺ Restart analysis", key="restart", type="secondary"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


# ── KPI header ──────────────────────────────────────────────────────────────

def _render_kpi_header(plan, answers, company):
    approved = [p for p in plan if p.get("budget_approved")]
    total_anv = sum(p["anv"] for p in approved) / 1e6
    total_cost = sum(p["impl_cost"] for p in approved) / 1e6
    exec_risk = compute_execution_risk(answers)
    risk_adj = total_anv * (1.0 - exec_risk)
    pb = payback_months(total_cost * 1e6, total_anv * 1e6)
    bets = sum(1 for p in approved if p["quadrant"] == "Strategic Bets")
    quick = sum(1 for p in approved if p["quadrant"] == "Quick Wins / Fill-ins")
    aum = answers.get("S1_AUM", 50)
    pb_str = f"{pb:.0f}mo" if pb < 900 else "n/a"

    st.html(f"""
    <div style="margin-bottom:var(--sp-4);">
        <div style="font-family:var(--font-head); font-size:26px; color:var(--black); line-height:1.2;">
            AI Investment Roadmap: <span style="color:var(--pwc-orange);">{company}</span>
        </div>
        <div style="font-size:14px; color:var(--g500); margin-top:var(--sp-1);">
            ${aum}B AUM · {len(plan)} levers scored · scenario: {st.session_state.get('current_scenario','base')}
        </div>
    </div>
    <div class="hz-kpi-row">
        <div class="hz-kpi-tile hz-kpi-hero">
            <div class="hz-kpi-lbl">Risk-Adjusted Annual Net Value</div>
            <div class="hz-kpi-num">${risk_adj:.1f}M</div>
            <div style="font-size:11px; color:var(--pwc-orange); border-top:1px solid var(--pwc-orange); margin-top:8px; padding-top:4px;">
                Raw ANV: ${total_anv:.1f}M · exec risk {exec_risk*100:.0f}%
            </div>
        </div>
        <div class="hz-kpi-tile"><div class="hz-kpi-lbl">Strategic Bets (funded)</div><div class="hz-kpi-num">{bets}</div></div>
        <div class="hz-kpi-tile"><div class="hz-kpi-lbl">Quick Wins (funded)</div><div class="hz-kpi-num">{quick}</div></div>
        <div class="hz-kpi-tile"><div class="hz-kpi-lbl">Portfolio Payback</div><div class="hz-kpi-num">{pb_str}</div></div>
    </div>
    """)


# ── Now / Next / Later roadmap ──────────────────────────────────────────────

def _roadmap(plan):
    funded = [p for p in plan if p.get("budget_approved")]
    now = [p for p in funded if p["quadrant"] == "Strategic Bets"]
    nxt = [p for p in funded if p["quadrant"] == "Quick Wins / Fill-ins"]
    later = [p for p in plan if p["quadrant"] == "Park (Data-Blocked)"]

    def col(items, cls, head, subtitle):
        if items:
            body = "".join(f'<div class="hz-road-item">{html.escape(p["name"])} · ${p["anv_m"]:.1f}M</div>' for p in items[:5])
        else:
            body = '<div class="hz-road-empty">None in this horizon.</div>'
        return f'<div class="hz-road-col {cls}"><div class="hz-road-h">{head}</div><div style="font-size:11px;color:var(--g500);margin-bottom:8px;">{subtitle}</div>{body}</div>'

    st.html('<div class="hz-report-h2">Phased Roadmap</div>')
    st.html('<div class="hz-roadmap">'
            + col(now, "now", "Now (0–6 mo)", "High impact, ready to build")
            + col(nxt, "next", "Next (6–18 mo)", "Fast, momentum-building")
            + col(later, "later", "Later (data-blocked)", "High value, fix the foundation first")
            + '</div>')


# ── Matrix ──────────────────────────────────────────────────────────────────

def _tab_matrix(plan: list[dict]) -> None:
    st.html('<div class="hz-report-h2">AI Use Case Prioritization Matrix</div>')
    st.html('<p class="hz-p">Bubble height is <strong>Business Impact</strong> — computed per firm from value-pool size, strategic-goal fit, and urgency. Width is <strong>Feasibility</strong> (data readiness, legacy constraints). Bubble area is annual net value; outlined bubbles are unfunded within budget.</p>')

    ti, tf = IMPACT_THRESHOLD, FEASIBILITY_THRESHOLD
    top5_ids = {p["id"] for p in sorted(plan, key=lambda x: x["anv"], reverse=True)[:5]}

    fig = go.Figure()
    fig.add_shape(type="rect", x0=tf, y0=ti, x1=105, y1=105,
                  fillcolor="rgba(208,74,2,0.07)", line=dict(width=0), layer="below")
    fig.add_hline(y=ti, line_dash="dash", line_color="#DEDEDE", line_width=1)
    fig.add_vline(x=tf, line_dash="dash", line_color="#DEDEDE", line_width=1)

    for p in plan:
        funded = p.get("budget_approved", False)
        negative = p["anv_m"] < 0
        area = max(10, abs(p["anv_m"]) * 3)
        size = area ** 0.5 * 3
        if negative:
            marker = dict(size=size, color="rgba(0,0,0,0)", line=dict(color="#E0301E", width=2))
        elif funded:
            marker = dict(size=size, color="#D04A02", line=dict(color="white", width=1))
        else:
            marker = dict(size=size, color="rgba(0,0,0,0)", line=dict(color="#D04A02", width=1.5))

        label = p["name"].split("&")[0].split("(")[0].strip()
        mode = "markers+text" if p["id"] in top5_ids else "markers"
        tag = " (unfunded)" if not funded else ""
        tag += " · value-destructive" if negative else ""
        fig.add_trace(go.Scatter(
            x=[p["feasibility"]], y=[p["impact"]], mode=mode,
            text=[label], textposition="top center",
            textfont=dict(size=11, color="#2D2D2D", family="Arial"),
            marker=marker, name=p["name"], showlegend=False,
            hovertemplate=(f"<b>{p['name']}</b>{tag}<br>Impact {p['impact']}/100 · "
                           f"Feasibility {p['feasibility']}/100<br>ANV ${p['anv_m']:.1f}M/yr · "
                           f"Payback {p['payback']:.0f}mo<extra>{p['quadrant']}</extra>"),
        ))

    fig.update_layout(
        annotations=[dict(x=tf + 2, y=103, text="Strategic bets", font=dict(color="#D04A02", size=11, family="Arial"), showarrow=False, xanchor="left")],
        xaxis=dict(range=[0, 105], showgrid=False, zeroline=False, tickfont=dict(size=11, color="#7D7D7D"), title=dict(text="Feasibility →", font=dict(color="#7D7D7D"))),
        yaxis=dict(range=[0, 105], showgrid=False, zeroline=False, tickfont=dict(size=11, color="#7D7D7D"), title=dict(text="Business Impact →", font=dict(color="#7D7D7D"))),
        height=500, margin=dict(l=40, r=40, t=20, b=40),
        plot_bgcolor="white", paper_bgcolor="white", font=dict(family="Arial"),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.html('<div class="hz-report-h2">Full Lever Scorecard</div>')
    rows = ""
    for p in plan:
        funded = p.get("budget_approved", False)
        tr_cls = "" if funded else "unfunded"
        tag = "" if funded else '<span class="hz-chip median" style="margin-left:8px;">UNFUNDED</span>'
        if p["anv_m"] < 0:
            val = f"<span class='hz-status-breach'>${p['anv_m']:.1f}M</span>"
            pb = "n/a — negative ANV"
            warn = '<span class="hz-status-breach" style="font-size:11px; margin-left:8px;">△ value-destructive</span>'
        else:
            val = f"${p['anv_m']:.1f}M"
            pb = f"{p['payback']:.0f} mo"
            warn = ""
        rows += (f'<tr class="{tr_cls}"><td><strong>{html.escape(p["name"])}</strong>{warn}{tag}</td>'
                 f'<td>{p["priority"]}</td><td>{p["quadrant"]}</td>'
                 f'<td class="num">{val}</td><td class="num">{pb}</td>'
                 f'<td class="num">{p["impact"]}/100</td><td class="num">{p["feasibility"]}/100</td></tr>')
    st.html(f"""
    <table class="hz-table-wrap"><thead><tr>
        <th>AI Use Case</th><th>Priority</th><th>Quadrant</th>
        <th style="text-align:right;">ANV / yr</th><th style="text-align:right;">Payback</th>
        <th style="text-align:right;">Impact</th><th style="text-align:right;">Feasibility</th>
    </tr></thead><tbody>{rows}</tbody></table>
    """)


# ── Legacy deprecation (independent engine) ─────────────────────────────────

def _tab_deprecation(answers: dict, plan: list[dict]) -> None:
    st.html('<div class="hz-report-h2">Legacy System Deprecation Diagnostic</div>')
    st.html('<p class="hz-p">This diagnostic is independent of the matrix: it asks whether the legacy stack should be killed, modernized, or held, and whether retiring it can help fund the AI programme.</p>')

    unlocked_anv_m = sum(p["anv"] for p in plan if p.get("id") in PLATFORM_GATED_LEVERS
                         and p["anv"] > 0) / 1e6

    default_rebuild = answers.get("S5_MAINTENANCE_COST", 6.5) * 3.5
    rebuild_capex = st.slider("Rebuild capex ($M) — supply the client's figure if known",
                              1.0, 200.0, float(default_rebuild), 0.5)

    inputs = LegacyInputs(
        maintenance_cost_m=answers.get("S5_MAINTENANCE_COST", 6.5),
        biz_value_m=answers.get("S5_BIZ_VALUE", 20.0),
        silo_count=answers.get("S1_SILO", 5.0),
        architecture=answers.get("S1_ARCH", "Hybrid — partial cloud"),
        api_maturity=answers.get("S1_ERP", "On-prem with API layer"),
        data_ownership=0, lineage=0, dq_sla=0, reg_trace=0, change_mgmt=0,
        unlocked_anv_m=unlocked_anv_m,
        rebuild_cost_m=rebuild_capex,
        governance_score=answers.get("S5_GOVERNANCE_SCORE", 50.0),
    )
    result = run_diagnostic(inputs)
    pillars = result["pillars"]

    col1, col2 = st.columns([1, 1])
    with col1:
        vcls = {"KILL & REBUILD": "kill", "REBUILD-BLOCKED": "blocked",
                "MODERNIZE": "modernize", "HOLD & OPTIMIZE": "hold"}.get(result["verdict"], "modernize")
        st.html(f"""
        <div class="hz-verdict {vcls}">
            <div class="hz-verdict-title">{result['verdict']}</div>
            <div class="hz-verdict-body"><strong>Pattern:</strong> {result['pattern']}<br><br>{result['rationale']}</div>
        </div>
        """)
    with col2:
        def bs(s, invert=False):
            good = s < 40 if invert else s > 70
            watch = 40 <= s <= 70
            if good:
                return "<span class='hz-status-ok'>● Healthy</span>"
            if watch:
                return "<span class='hz-status-watch'>● Watch</span>"
            return "<span class='hz-status-breach'>● Toxic</span>" if not invert else "<span class='hz-status-breach'>● Breach</span>"
        st.html(f"""
        <table class="hz-table-wrap">
            <thead><tr><th>Diagnostic Pillar</th><th style="text-align:right;">Score</th><th>Status</th></tr></thead>
            <tbody>
                <tr><td>Tech Debt (toxicity)</td><td class="num">{pillars['tech_debt_score']}/100</td><td>{bs(pillars['tech_debt_score'], invert=True)}</td></tr>
                <tr><td>Data Fragmentation</td><td class="num">{pillars['fragmentation_score']}/100</td><td>{bs(pillars['fragmentation_score'], invert=True)}</td></tr>
                <tr><td>Governance Readiness</td><td class="num">{pillars['governance_readiness']}/100</td><td>{bs(pillars['governance_readiness'])}</td></tr>
                <tr><td><strong>Deprecation Score</strong></td><td class="num"><strong>{result['deprecation_score']}/100</strong></td><td></td></tr>
            </tbody>
        </table>
        """)

    sf = result["self_funding"]
    st.html('<div class="hz-report-h2" style="margin-top:2rem;">Self-Funding Horizon</div>')
    pb = f"{sf['payback_months']} months" if sf["payback_months"] else "Does not pay back"
    gap = "Fully funded in year one" if sf["first_year_funding_gap_m"] <= 0 else f"${sf['first_year_funding_gap_m']}M"
    est = " (estimated at 3.5× maintenance)" if sf["rebuild_cost_estimated"] else ""
    st.html(f"""
    <table class="hz-table-wrap">
        <thead><tr><th>Metric</th><th style="text-align:right;">Value</th></tr></thead>
        <tbody>
            <tr><td>Legacy annual savings (retained after new run-cost)</td><td class="num">${sf['legacy_annual_savings_m']}M</td></tr>
            <tr><td>Unlocked AI value (platform-gated levers)</td><td class="num">${sf['unlocked_anv_m']}M</td></tr>
            <tr><td><strong>Total annual value</strong></td><td class="num"><strong>${sf['total_annual_value_m']}M</strong></td></tr>
            <tr><td>Rebuild capex{est}</td><td class="num">${sf['rebuild_cost_m']}M</td></tr>
            <tr><td>First-year funding gap</td><td class="num">{gap}</td></tr>
            <tr><td><strong>Payback</strong></td><td class="num"><strong>{pb}</strong></td></tr>
        </tbody>
    </table>
    """)


# ── Memo ────────────────────────────────────────────────────────────────────

def _tab_memo() -> None:
    summary = st.session_state.get("thesis_summary", "")
    if not summary:
        st.info("Complete the intake form to generate the strategic memo.")
        return
    rid = st.session_state.get("last_run_id", "not logged")
    st.html(f"""
    <div style="max-width:800px;">
        <div style="font-family:var(--font-head); font-size:26px; color:var(--black); margin:var(--sp-6) 0;">Executive Summary</div>
        {summary}
        <div style="margin-top:var(--sp-6); font-size:11px; color:var(--g500); border-top:1px solid var(--g200); padding-top:var(--sp-2);">
            Narrative generated by Gemini and grounded in the computed plan. Review for accuracy. · Run ID: {rid}
        </div>
    </div>
    """)


# ── Risk & competitiveness ──────────────────────────────────────────────────

def _tab_risk_competitive(plan: list[dict], answers: dict) -> None:
    st.html('<div class="hz-report-h2">Competitive Positioning</div>')
    comp = compute_competitive_advantage_score(plan, answers)
    c = comp["overall_score"]
    col1, col2 = st.columns([1, 2])
    with col1:
        st.html(f"""
        <div class="hz-bullet-wrap" style="margin-top:var(--sp-4);">
            <div class="hz-bullet-lbl-row"><span class="hz-bullet-lbl">Defensibility Index</span><span class="hz-bullet-val">{c}/100</span></div>
            <div class="hz-bullet-track">
                <div class="hz-bullet-thresh" style="left:40%;"></div>
                <div class="hz-bullet-thresh" style="left:70%;"></div>
                <div class="hz-bullet-fill" style="width:{c}%;"></div>
            </div>
        </div>
        """)
    with col2:
        if c >= 70:
            st.html('<div class="hz-callout win"><div class="hz-callout-title">Market-leading advantage</div><div class="hz-callout-desc">The funded plan leverages highly defensible assets. Competitors need 18–24 months to reach parity on these levers.</div></div>')
        else:
            st.html('<div class="hz-callout park"><div class="hz-callout-title">Catch-up posture</div><div class="hz-callout-desc">The plan is weighted toward foundational modernization. Necessary, but not yet a distinctive moat against tier-1 incumbents.</div></div>')
        adv = "".join(f"<li><strong>{a.name}:</strong> {a.mmil_advantage} (<em>parity: {a.time_to_parity}</em>)</li>" for a in comp["advantages"])
        if adv:
            st.html(f"<ul style='font-size:13px; color:var(--g700);'>{adv}</ul>")

    st.html('<div class="hz-report-h2" style="margin-top:32px;">Regulatory Compliance Constraints</div>')
    reg_rows = ""
    for p in plan:
        rs = p.get("reg_status", {})
        if not rs:
            continue
        lvl = rs.get("risk_level", "green")
        txt = {"green": "<span class='hz-status-ok'>● Compliant</span>",
               "yellow": "<span class='hz-status-watch'>● Requires mitigation</span>",
               "red": "<span class='hz-status-breach'>● High risk</span>"}.get(lvl, "")
        cons = "<br>".join(f"• {c.name} ({c.authority})" for c in rs.get("constraints", [])) or "Standard IT hygiene"
        mit = "<br>".join(f"• {m}" for m in rs.get("mitigations", [])) or "None required"
        reg_rows += f"<tr><td><strong>{html.escape(p['name'])}</strong></td><td>{txt}</td><td>{cons}</td><td>{mit}</td></tr>"
    st.html(f"""
    <table class="hz-table-wrap"><thead><tr>
        <th>Investment Lever</th><th>Risk Profile</th><th>Key Constraints</th><th>Required Mitigations</th>
    </tr></thead><tbody>{reg_rows}</tbody></table>
    """)


# ── Assumptions appendix ────────────────────────────────────────────────────

def _tab_assumptions() -> None:
    st.html('<div class="hz-report-h2">Model Assumptions & Constants</div>')
    st.html('<p class="hz-p">All calculations derive from explicit, auditable constants in <code>config/value_pools.py</code>. Impact is computed per firm (value-pool × goal-fit × urgency); feasibility from architecture, silos, and governance. No hidden scaling factors.</p>')
    from config.value_pools import CONSTANTS
    rows = "".join(f"<tr><td><strong>{k}</strong></td><td class='num'>{v}</td></tr>" for k, v in CONSTANTS.items())
    st.html(f'<table class="hz-table-wrap"><thead><tr><th>Constant</th><th style="text-align:right;">Value</th></tr></thead><tbody>{rows}</tbody></table>')

    st.html('<div class="hz-report-h2" style="margin-top:32px;">Lever Benchmarks</div>')
    from config.value_pools import BFSI_LEVERS
    brows = "".join(f"<tr><td><strong>{html.escape(l['name'])}</strong></td><td>{html.escape(l.get('benchmark',''))}</td></tr>" for l in BFSI_LEVERS)
    st.html(f'<table class="hz-table-wrap"><thead><tr><th>Lever</th><th>Benchmark source</th></tr></thead><tbody>{brows}</tbody></table>')


def _footer() -> None:
    rid = st.session_state.get("last_run_id", "—")
    sc = st.session_state.get("current_scenario", "base")
    st.html(f'<div class="hz-footer"><span>Run {rid} · Engine v{ENGINE_VERSION} · Corpus v{CORPUS_VERSION}</span><span>Scenario: {sc}</span></div>')
