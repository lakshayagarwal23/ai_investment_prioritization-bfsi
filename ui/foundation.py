"""
ui/foundation.py — The Foundation Decision (legacy modernization, TCO framework).

Page contract (client-facing):
  1. Cost vs value      what the estate costs against what it delivers
  2. The score          three pillars with the arithmetic shown verbatim
  3. The business case  what funding modernization changes, in dollars
  4. Budget position    where the total budget stands, as a donut + table
  5. The decision       two options, consequences listed, one recommended
  6. Safeguards         verdict-specific transition checklist

Every number displays the inputs and formula that produced it. "Blocked AI
value" counts ONLY levers currently parked by the foundation, never value
already funded. Typography: headings via .hz-report-h2, body 13px, captions
12px, all colors from theme tokens.
"""
import html
import streamlit as st
import plotly.graph_objects as go

from engine.legacy_diagnostic import run_diagnostic, LegacyInputs
from config.value_pools import PLATFORM_GATED_LEVERS

_BODY = 'font-size:13px; color:var(--g700); line-height:1.6;'
_CAPTION = 'font-size:12px; color:var(--g500); line-height:1.5;'


def _apply_decision(fund: bool) -> None:
    """Record the decision, recompute the portfolio, and set a one-time
    confirmation banner (tabs reset to The Recommendation on rerun)."""
    from engine.math_engine import build_investment_plan
    st.session_state.foundation_decision = fund
    st.session_state.thesis_plan = build_investment_plan(
        answers=st.session_state.discovery_answers,
        budget_usd_m=st.session_state.budget_usd_m,
        primary_goals=st.session_state.primary_goals,
        scenario=st.session_state.get("current_scenario", "base"),
        foundation_decision=fund,
    )
    st.session_state.foundation_flash = "funded" if fund else "deferred"
    st.rerun()


def _budget_position() -> dict:
    """Reconcile the committed capital in the CURRENT plan against the budget."""
    plan = st.session_state.get("thesis_plan") or []
    budget_m = float(st.session_state.get("budget_usd_m", 100.0))
    levers_m = sum(p["impl_cost"] for p in plan
                   if p.get("budget_approved") and p["id"] != "lever_0_foundation") / 1e6
    modern_m = sum(p["impl_cost"] for p in plan
                   if p.get("budget_approved") and p["id"] == "lever_0_foundation") / 1e6
    remaining_m = max(0.0, budget_m - levers_m - modern_m)
    return {"budget_m": budget_m, "levers_m": levers_m,
            "modern_m": modern_m, "remaining_m": remaining_m}


def _budget_donut(pos: dict) -> go.Figure:
    labels, values, colors = ["AI use cases"], [pos["levers_m"]], ["#D04A02"]
    if pos["modern_m"] > 0:
        labels.append("Modernization")
        values.append(pos["modern_m"])
        colors.append("#A32020")
    labels.append("Uncommitted")
    values.append(pos["remaining_m"])
    colors.append("#DEDEDE")

    committed = pos["levers_m"] + pos["modern_m"]
    fig = go.Figure(go.Pie(
        labels=labels, values=values, sort=False, direction="clockwise",
        hole=0.62,
        marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
        texttemplate="%{label}<br>$%{value:.1f}M",
        textposition="outside",
        textfont=dict(size=12, color="#464646", family="Arial"),
        hovertemplate="<b>%{label}</b><br>$%{value:.1f}M · %{percent:.0%} of budget<extra></extra>",
    ))
    fig.update_layout(
        showlegend=False,
        height=290,
        margin=dict(l=10, r=10, t=28, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        # Two plain annotations: Plotly silently drops inline-styled spans
        annotations=[
            dict(text=f"${committed:.1f}M", showarrow=False, x=0.5, y=0.56,
                 font=dict(size=26, color="#000000", family="Georgia")),
            dict(text=f"committed of ${pos['budget_m']:.0f}M", showarrow=False, x=0.5, y=0.40,
                 font=dict(size=11, color="#7D7D7D", family="Arial")),
        ],
    )
    return fig


def render_foundation_decision() -> None:
    answers = st.session_state.get("discovery_answers", {})

    # Baseline plan WITHOUT the foundation, so "blocked" numbers are honest
    # regardless of the decision already taken.
    from engine.math_engine import build_investment_plan
    baseline = build_investment_plan(
        answers=answers,
        budget_usd_m=st.session_state.get("budget_usd_m", 100.0),
        primary_goals=st.session_state.get("primary_goals", []),
        scenario=st.session_state.get("current_scenario", "base"),
        foundation_decision=False,
    )
    blocked = [p for p in baseline
               if p["id"] in PLATFORM_GATED_LEVERS
               and p["quadrant"] == "Park (Data-Blocked)" and p["anv"] > 0]
    unlocked_anv_m = sum(p["anv"] for p in blocked) / 1e6

    inputs = LegacyInputs(
        maintenance_cost_m=float(answers.get("S5_MAINTENANCE_COST", 6.5)),
        biz_value_m=float(answers.get("S5_BIZ_VALUE", 20.0)),
        silo_count=float(answers.get("S1_SILO", 5.0)),
        architecture=str(answers.get("S1_ARCH", "Hybrid — partial cloud")),
        api_maturity=str(answers.get("S1_ERP", "On-prem with API layer")),
        data_ownership=0, lineage=0, dq_sla=0, reg_trace=0, change_mgmt=0,
        unlocked_anv_m=unlocked_anv_m,
        rebuild_cost_m=None,
        governance_score=float(answers.get("S5_GOVERNANCE_SCORE", 50.0)),
    )
    res = run_diagnostic(inputs)
    sf, tco, pillars = res["self_funding"], res["tco"], res["pillars"]

    # ── Current decision status ──────────────────────────────────────────────
    decision = st.session_state.get("foundation_decision")
    if decision is True:
        st.html(f'<div style="background:var(--orange-tint); border:1px solid var(--pwc-orange); '
                f'border-radius:4px; padding:12px 16px; {_BODY} margin-bottom:24px;">'
                f'<strong>Modernization is included in your investment plan.</strong> '
                f'The rebuild capital is committed and previously blocked use cases are active. '
                f'You can change this in section 5 below.</div>')
    elif decision is False:
        st.html(f'<div style="background:var(--grey-tint); border:1px solid var(--g300); '
                f'border-radius:4px; padding:12px 16px; {_BODY} margin-bottom:24px;">'
                f'<strong>Modernization is not included in your investment plan.</strong> '
                f'Blocked use cases stay parked. You can change this in section 5 below.</div>')
    else:
        st.html(f'<div style="background:var(--yellow-tint); border:1px solid var(--pwc-yellow); '
                f'border-radius:4px; padding:12px 16px; {_BODY} margin-bottom:24px;">'
                f'<strong>One decision is pending on this page.</strong> '
                f'Review the evidence below, then choose in section 5 whether legacy '
                f'modernization goes into your investment plan.</div>')

    # ── Verdict ──────────────────────────────────────────────────────────────
    st.html(f"""
    <div class="hz-verdict {res['verdict_css']}">
        <div class="hz-verdict-title">Our verdict on your legacy estate: {html.escape(res['verdict'])}
            <span style="font-family:var(--font-body); font-size:12px; color:var(--g500); margin-left:12px;">
                score {res['deprecation_score']} of 100</span>
        </div>
        <div class="hz-verdict-body">{html.escape(res['verdict_action'])}</div>
    </div>
    """)

    # ── 1. Cost vs value ─────────────────────────────────────────────────────
    st.html('<div class="hz-report-h2">1. What the estate costs vs. what it delivers</div>')
    ratio = tco["ratio_pct"]
    ratio_txt = f"{ratio}%" if ratio is not None else "not computable (no stated value)"
    band_cls = {"healthy": "hz-status-ok", "watch": "hz-status-watch",
                "critical": "hz-status-breach", "value-negative": "hz-status-breach"}[tco["band"]]
    security_row = ""
    if tco["security_flag"]:
        security_row = ('<tr><td>Security and audit exposure</td>'
                        '<td class="num"><span class="hz-status-watch">Elevated</span></td>'
                        f'<td style="{_CAPTION}">Ageing on-premise components are harder to patch '
                        'and harder to evidence in a regulatory audit</td></tr>')
    st.html(f"""
    <table class="hz-table-wrap">
      <thead><tr><th>Measure</th><th style="text-align:right;">Value</th><th>What it means</th></tr></thead>
      <tbody>
        <tr><td>Annual maintenance cost</td><td class="num">${tco['annual_maintenance_m']}M</td>
            <td style="{_CAPTION}">Your answer in the intake: what you spend keeping the estate alive</td></tr>
        <tr><td>Business value it delivers</td><td class="num">${tco['business_value_m']}M</td>
            <td style="{_CAPTION}">Your answer in the intake: what the estate still earns each year</td></tr>
        <tr style="background:var(--g100);"><td><strong>Cost-to-value ratio</strong></td>
            <td class="num"><span class="{band_cls}">{ratio_txt}</span></td>
            <td style="{_BODY}">{html.escape(tco['verdict'])}</td></tr>
        {security_row}
      </tbody>
    </table>
    <div style="{_CAPTION} margin-top:-12px; margin-bottom:8px;">
      Reading the ratio: below 25% is healthy. 25 to 50% needs watching. 50 to 100% is critical.
      Above 100% the estate costs more than it earns.
    </div>
    """)

    # ── 2. The score, arithmetic shown ───────────────────────────────────────
    st.html('<div class="hz-report-h2">2. How we scored it</div>')
    st.html(f'<div style="{_BODY} margin-bottom:12px;">Three factors, weighted. '
            'Each shows the exact inputs behind it. Nothing else feeds the score.</div>')
    pe = res["pillar_explain"]
    gov_gap = 100 - pillars["governance_readiness"]

    def meter(label, score, explain):
        return f"""
        <div class="hz-bullet-wrap">
            <div class="hz-bullet-lbl-row">
                <span class="hz-bullet-lbl">{html.escape(label)}</span>
                <span class="hz-bullet-val" style="font-size:20px;">{score}/100</span>
            </div>
            <div class="hz-bullet-track">
                <div class="hz-bullet-thresh" style="left:40%;"></div>
                <div class="hz-bullet-thresh" style="left:70%;"></div>
                <div class="hz-bullet-fill" style="width:{max(0, min(100, score))}%;"></div>
            </div>
            <div style="{_CAPTION} margin-top:4px;">{html.escape(explain)}</div>
        </div>"""

    c1, c2, c3 = st.columns(3)
    with c1:
        st.html(meter("Cost of technical debt (40%)", pillars["tech_debt_score"], pe["tech_debt"]))
    with c2:
        st.html(meter("Data fragmentation (35%)", pillars["fragmentation_score"], pe["fragmentation"]))
    with c3:
        st.html(meter("Governance gap (25%)", gov_gap, pe["governance"]))

    st.html(f"""
    <div style="background:var(--g100); border-radius:4px; padding:12px 16px; margin:8px 0 8px;
                font-family:monospace; font-size:12.5px; color:var(--g700);">
        {html.escape(res['score_math'])}
    </div>
    <div style="{_CAPTION} margin-bottom:16px;">
        Verdict bands: below 40 keep and optimize. 40 to 70 modernize in phases. 70 and above replace the core.
    </div>
    """)

    # ── 3. The business case for funding ─────────────────────────────────────
    st.html('<div class="hz-report-h2">3. What funding modernization would do</div>')
    pb = f"{sf['payback_months']} months" if sf["payback_months"] else "does not pay back on current numbers"
    st.html(f"""
    <table class="hz-table-wrap">
      <tbody>
        <tr><td>One-off modernization cost</td><td class="num">${sf['rebuild_cost_m']}M</td>
            <td style="{_CAPTION}">Estimated at 3.5x your annual maintenance, a standard planning heuristic. Refined during scoping</td></tr>
        <tr><td>Maintenance you stop paying</td><td class="num">${sf['legacy_annual_savings_m']}M per year</td>
            <td style="{_CAPTION}">65% of today's maintenance ends; 35% carries over to run the new platform</td></tr>
        <tr><td>AI value currently blocked</td><td class="num">${sf['unlocked_anv_m']}M per year</td>
            <td style="{_CAPTION}">Value of use cases parked because the current estate cannot support them</td></tr>
        <tr style="background:var(--g100);"><td><strong>Total annual value if funded</strong></td>
            <td class="num"><strong>${sf['total_annual_value_m']}M per year</strong></td><td></td></tr>
        <tr style="border-top:2px solid var(--g300);"><td><strong>Pays for itself in</strong></td>
            <td class="num"><strong>{pb}</strong></td>
            <td style="{_CAPTION}">One-off cost divided by the monthly value above</td></tr>
      </tbody>
    </table>
    """)
    if blocked:
        rows = "".join(f'<div class="hz-road-item">{html.escape(p["name"])} · '
                       f'${p["anv_m"]:.1f}M per year, currently parked</div>' for p in blocked)
        st.html(f'<div style="{_BODY} font-weight:600; margin-bottom:8px;">The blocked use cases:</div>{rows}')
    else:
        st.html(f'<div style="{_CAPTION}">No use case in your current plan is blocked by the estate, '
                'so this decision is purely about cost and risk, not about unlocking AI value.</div>')

    # ── 4. Budget position (current plan) ────────────────────────────────────
    st.html('<div class="hz-report-h2">4. Where your budget stands</div>')
    pos = _budget_position()
    col_chart, col_table = st.columns([1, 1.2])
    with col_chart:
        st.plotly_chart(_budget_donut(pos), use_container_width=True,
                        config={"displayModeBar": False})
    with col_table:
        modern_row = (f'<tr><td>Committed to modernization</td>'
                      f'<td class="num">${pos["modern_m"]:.1f}M</td></tr>') if pos["modern_m"] > 0 else \
                     (f'<tr><td>Committed to modernization</td>'
                      f'<td class="num" style="color:var(--g500);">$0.0M (not in plan)</td></tr>')
        st.html(f"""
        <table class="hz-table-wrap" style="margin-top:24px;">
          <tbody>
            <tr><td>Total transformation budget</td><td class="num">${pos['budget_m']:.0f}M</td></tr>
            <tr><td>Committed to AI use cases</td><td class="num">${pos['levers_m']:.1f}M</td></tr>
            {modern_row}
            <tr style="border-top:2px solid var(--g300);"><td><strong>Uncommitted</strong></td>
                <td class="num"><strong>${pos['remaining_m']:.1f}M</strong></td></tr>
          </tbody>
        </table>
        <div style="{_CAPTION}">This reflects the plan as it stands. It updates the moment
        you change the decision below or switch scenario.</div>
        """)

    # ── 5. The decision ──────────────────────────────────────────────────────
    st.html('<div class="hz-report-h2">5. Your decision</div>')
    st.html(f'<div style="{_BODY} margin-bottom:12px;">One question: does legacy modernization '
            'go into your investment plan? Your choice reshapes The Recommendation and '
            'The Portfolio tabs, and you can change it at any time.</div>')

    recommend_fund = res["recommend_funding"] and sf["payback_months"] is not None
    rec_a = ' <span class="hz-chip auto">RECOMMENDED</span>' if recommend_fund else ""
    rec_b = "" if recommend_fund else ' <span class="hz-chip auto">RECOMMENDED</span>'

    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            st.html(f"""
            <div style="font-family:var(--font-head); font-size:18px; color:var(--black); margin-bottom:8px;">
                Option A. Include modernization{rec_a}</div>
            <ul style="{_BODY} padding-left:18px; margin:0 0 12px;">
                <li>Commits ${sf['rebuild_cost_m']}M of the budget to the rebuild</li>
                <li>Stops ${sf['legacy_annual_savings_m']}M per year of maintenance spend</li>
                <li>Activates {len(blocked)} parked use case(s) worth ${unlocked_anv_m:.1f}M per year</li>
            </ul>
            """)
            if st.button("Include modernization in the plan", key="fund_foundation", type="primary",
                         use_container_width=True, disabled=(decision is True)):
                _apply_decision(True)
    with col_b:
        with st.container(border=True):
            st.html(f"""
            <div style="font-family:var(--font-head); font-size:18px; color:var(--black); margin-bottom:8px;">
                Option B. Defer it{rec_b}</div>
            <ul style="{_BODY} padding-left:18px; margin:0 0 12px;">
                <li>No rebuild spend now. Budget stays on fast-payback use cases</li>
                <li>{len(blocked)} use case(s) stay parked; ${unlocked_anv_m:.1f}M per year stays locked</li>
                <li>The ${tco['annual_maintenance_m']}M per year maintenance bill continues</li>
            </ul>
            """)
            if st.button("Keep it out of the plan for now", key="defer_foundation",
                         use_container_width=True, disabled=(decision is False)):
                _apply_decision(False)

    # ── 6. Safeguards ────────────────────────────────────────────────────────
    st.html('<div class="hz-report-h2">6. If you proceed: transition safeguards</div>')
    items = "".join(f'<div class="hz-road-item">{html.escape(g)}</div>' for g in res["guardrails"])
    st.html(items)
