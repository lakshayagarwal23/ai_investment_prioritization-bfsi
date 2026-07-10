"""
ui/dashboard.py — BFSI AI Investment results dashboard (PwC Horizon v5).
"""
from __future__ import annotations
import streamlit as st
import plotly.graph_objects as go
import html
from engine.competitive import compute_competitive_advantage_score
from engine.math_engine import (compute_execution_risk, payback_months,
                                IMPACT_THRESHOLD, FEASIBILITY_THRESHOLD)
from storage.audit import ENGINE_VERSION, CORPUS_VERSION
from config.value_pools import PLATFORM_GATED_LEVERS

def render_dashboard() -> None:
    if not st.session_state.get("thesis_generated"):
        st.warning("Please complete the intake form first.")
        return

    _foundation_flash()
    _scenario_bar()

    plan = st.session_state.thesis_plan or []
    answers = st.session_state.discovery_answers or {}
    company = html.escape(st.session_state.company_name) if st.session_state.company_name else "The Firm"

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "The Recommendation", "The Portfolio", "The Foundation",
        "Risks & Compliance", "Appendix",
    ])
    with tab1:
        _tab_recommendation(plan, answers, company)
    with tab2:
        _tab_portfolio(plan)
    with tab3:
        _tab_foundation(plan, answers)
    with tab4:
        _tab_risk_competitive(plan, answers)
    with tab5:
        _tab_assumptions()

# ── One-time confirmation after a Foundation decision ───────────────────────
# st.tabs resets to the first tab on rerun, so without this banner the user
# gets silently teleported with no feedback — the #1 confusion in testing.

def _foundation_flash() -> None:
    flash = st.session_state.pop("foundation_flash", None)
    if not flash:
        return
    plan = st.session_state.get("thesis_plan") or []
    if flash == "funded":
        fnd = next((p for p in plan if p["id"] == "lever_0_foundation"), None)
        capex = f"${fnd['impl_cost']/1e6:.1f}M" if fnd else "The rebuild capital"
        st.html(f"""
        <div style="background:var(--orange-tint); border:1px solid var(--pwc-orange);
                    border-radius:4px; padding:14px 18px; font-size:13px; color:var(--g700); margin-bottom:16px;">
            <strong>Your decision has been applied: modernization is now in the plan.</strong>
            {capex} of the budget is committed to the rebuild, previously blocked use cases are active,
            and every number below has been recomputed. You can revisit the decision on
            <strong>The Foundation</strong> tab.
        </div>""")
    else:
        st.html("""
        <div style="background:var(--grey-tint); border:1px solid var(--g300);
                    border-radius:4px; padding:14px 18px; font-size:13px; color:var(--g700); margin-bottom:16px;">
            <strong>Your decision has been applied: modernization stays out of the plan.</strong>
            No rebuild spend was added. Use cases blocked by the legacy estate remain parked.
            You can revisit the decision on <strong>The Foundation</strong> tab.
        </div>""")


# ── Inline scenario toggle (replaces the sidebar radio) ─────────────────────

def _scenario_bar() -> None:
    decision = st.session_state.get("foundation_decision")
    status = {True: ('var(--pwc-orange)', 'Legacy modernization: in the plan'),
              False: ('var(--g500)', 'Legacy modernization: not in the plan'),
              None: ('var(--g500)', 'Legacy modernization: decision pending on The Foundation tab')}[decision]
    st.html(f'<div class="hz-scenario-lbl" style="display:flex; justify-content:space-between;">'
            f'<span>Execution scenario</span>'
            f'<span style="color:{status[0]}; font-size:11px; font-weight:600;">{status[1]}</span></div>')
    c1, c2, c3, _ = st.columns([2, 2, 2, 4])
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
                        st.session_state.primary_goals, scenario=key,
                        foundation_decision=st.session_state.get("foundation_decision", False))
                    st.rerun()
    if st.button("↺ Restart analysis", key="restart", type="secondary"):
        st.session_state.show_restart_confirm = True

    if st.session_state.get("show_restart_confirm"):
        st.warning("Are you sure you want to restart? All data will be lost.")
        rc1, rc2 = st.columns(2)
        if rc1.button("Yes, Restart"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
        if rc2.button("Cancel"):
            st.session_state.show_restart_confirm = False
            st.rerun()

# ── Act 1: The Recommendation ────────────────────────────────────────────────
def _tab_recommendation(plan, answers, company):
    approved = [p for p in plan if p.get("budget_approved")]
    total_anv = sum(p["anv"] for p in approved) / 1e6
    total_cost = sum(p["impl_cost"] for p in approved) / 1e6
    exec_risk = compute_execution_risk(answers)
    risk_adj = total_anv * (1.0 - exec_risk)
    # Payback on the risk-adjusted cashflow — consistent with the hero tile
    pb = payback_months(total_cost * 1e6, risk_adj * 1e6)
    pb_str = f"{pb:.0f}" if pb < 900 else "n/a"

    budget_m = float(st.session_state.get("budget_usd_m", 100.0))
    st.html(f"""
    <div style="font-family: var(--font-head); font-size: 22px; color: var(--g900); margin-bottom: 16px; line-height: 1.4;">
        Based on {company}'s operational footprint, we recommend a focused AI investment program prioritizing your strategic goals. A ${total_cost:.1f}M commitment will unlock ${risk_adj:.1f}M in risk-adjusted annual net value, paying for itself in {pb_str} months.
    </div>
    <div style="font-size:13px; color:var(--g500); margin-bottom: 32px;">
        Budget position: ${total_cost:.1f}M committed of your ${budget_m:.0f}M envelope,
        ${max(0.0, budget_m - total_cost):.1f}M held uncommitted. The full breakdown is on The Foundation tab, section 4.
    </div>
    """)

    _render_kpi_header(plan, answers, company)
    
    st.html('<div class="hz-report-h2" style="margin-top: 32px;">Executive Asks</div>')
    now = [p for p in approved if p["quadrant"] == "Strategic Bets"]
    nxt = [p for p in approved if p["quadrant"] == "Quick Wins / Fill-ins"]
    now_capex = sum(p["impl_cost"] for p in now) / 1e6
    nxt_capex = sum(p["impl_cost"] for p in nxt) / 1e6
    
    # 3 Decision Asks
    st.html(f'''
    <div style="display:flex; gap:16px; margin-bottom: 32px;">
      <div style="flex:1; border:1px solid #E0E0E0; border-top: 4px solid #D04A02; padding: 16px; border-radius: 4px;">
        <div style="font-family: var(--font-head); font-size: 16px; margin-bottom: 8px;">1. Fund Now (0-6 mo)</div>
        <div style="font-size: 14px; color: var(--g700);">Commit ${now_capex:.1f}M to Strategic Bets</div>
      </div>
      <div style="flex:1; border:1px solid #E0E0E0; border-top: 4px solid #EB8C00; padding: 16px; border-radius: 4px;">
        <div style="font-family: var(--font-head); font-size: 16px; margin-bottom: 8px;">2. Fund Next (6-18 mo)</div>
        <div style="font-size: 14px; color: var(--g700);">Approve ${nxt_capex:.1f}M for Quick Wins</div>
      </div>
      <div style="flex:1; border:1px solid #E0E0E0; border-top: 4px solid #7D7D7D; padding: 16px; border-radius: 4px;">
        <div style="font-family: var(--font-head); font-size: 16px; margin-bottom: 8px;">3. Change Management</div>
        <div style="font-size: 14px; color: var(--g700);">Align business units to adopt new processes</div>
      </div>
    </div>
    ''')
    
    _roadmap(plan)


def _render_kpi_header(plan, answers, company):
    approved = [p for p in plan if p.get("budget_approved")]
    total_anv = sum(p["anv"] for p in approved) / 1e6
    total_cost = sum(p["impl_cost"] for p in approved) / 1e6
    exec_risk = compute_execution_risk(answers)
    risk_adj = total_anv * (1.0 - exec_risk)
    pb = payback_months(total_cost * 1e6, risk_adj * 1e6)
    bets = sum(1 for p in approved if p["quadrant"] == "Strategic Bets")
    quick = sum(1 for p in approved if p["quadrant"] == "Quick Wins / Fill-ins")
    pb_str = f"{pb:.0f}mo" if pb < 900 else "n/a"

    st.html(f"""
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

    st.html('<div class="hz-report-h2" style="margin-top: 32px;">Phased Roadmap</div>')
    st.html('<div class="hz-roadmap">'
            + col(now, "now", "Now (0–6 mo)", "High impact, ready to build")
            + col(nxt, "next", "Next (6–18 mo)", "Fast, momentum-building")
            + col(later, "later", "Later (data-blocked)", "High value, fix the foundation first")
            + '</div>')


# ── Act 2: The Portfolio ──────────────────────────────────────────────────────
def _tab_portfolio(plan: list[dict]) -> None:
    st.html('<div class="hz-report-h2">AI Use Case Prioritization Matrix</div>')
    st.html('<p class="hz-p" style="font-size:13px; color:var(--g700);">'
            'Each circle is one AI use case, positioned by how much it is worth to you (vertical) '
            'and how ready your firm is to deliver it (horizontal). Bigger circles carry more annual value. '
            'Solid circles are funded within your budget; outlined circles are not.</p>')

    ti, tf = IMPACT_THRESHOLD, FEASIBILITY_THRESHOLD
    funded_ids = {p["id"] for p in plan if p.get("budget_approved")}

    fig = go.Figure()
    fig.add_shape(type="rect", x0=tf, y0=ti, x1=105, y1=105,
                  fillcolor="rgba(208,74,2,0.07)", line=dict(width=0), layer="below")
    fig.add_hline(y=ti, line_color="#DEDEDE", line_width=1)
    fig.add_vline(x=tf, line_color="#DEDEDE", line_width=1)

    brand_color = "#D04A02"
    red_color = "#E0301E"
    grey_color = "#7D7D7D"

    # Collision-checked label placement: funded levers are direct-labeled.
    # Each label tries positions in order and takes the first that clears
    # every bubble and every label already placed (axis units, ~10 px/unit).
    def bubble_r(p):
        size = min(48.0, 16.0 + (max(0.0, p["anv_m"]) ** 0.5) * 8.0)
        return size / 20.0

    def label_box(p, slot, label):
        w = max(6.0, len(label) * 0.68)
        h = 3.2
        pad = 0.8
        cx, cy, r = p["feasibility"], p["impact"], bubble_r(p)
        if slot == "top center":
            return (cx - w / 2, cx + w / 2, cy + r + pad, cy + r + pad + h)
        if slot == "bottom center":
            return (cx - w / 2, cx + w / 2, cy - r - pad - h, cy - r - pad)
        if slot == "top right":
            return (cx + r * 0.7, cx + r * 0.7 + w, cy + r * 0.6, cy + r * 0.6 + h)
        if slot == "bottom right":
            return (cx + r * 0.7, cx + r * 0.7 + w, cy - r * 0.6 - h, cy - r * 0.6)
        if slot == "middle right":
            return (cx + r + pad, cx + r + pad + w, cy - h / 2, cy + h / 2)
        return (cx - r - pad - w, cx - r - pad, cy - h / 2, cy + h / 2)  # middle left

    def boxes_overlap(a, b):
        return a[0] < b[1] and b[0] < a[1] and a[2] < b[3] and b[2] < a[3]

    all_bubble_boxes = []
    for p in plan:
        r = bubble_r(p)
        all_bubble_boxes.append((p["id"], (p["feasibility"] - r, p["feasibility"] + r,
                                           p["impact"] - r, p["impact"] + r)))

    slots = ["top center", "bottom center", "top right", "bottom right",
             "middle right", "middle left"]
    def overlap_area(a, b):
        w = min(a[1], b[1]) - max(a[0], b[0])
        h = min(a[3], b[3]) - max(a[2], b[2])
        return w * h if (w > 0 and h > 0) else 0.0

    labeled = sorted((p for p in plan if p["id"] in funded_ids),
                     key=lambda p: (-p["impact"], p["feasibility"]))
    label_pos, placed_boxes = {}, []
    for p in labeled:
        label = p.get("short_name") or p["name"]
        chosen, best_cost = slots[0], float("inf")
        for slot in slots:
            box = label_box(p, slot, label)
            cost = sum(overlap_area(box, b) for b in placed_boxes)
            cost += sum(overlap_area(box, b) for pid, b in all_bubble_boxes if pid != p["id"])
            if not (0 <= box[0] and box[1] <= 105 and 0 <= box[2] and box[3] <= 105):
                cost += 50.0  # off-plot penalty
            if cost == 0.0:
                chosen = slot
                break
            if cost < best_cost:
                chosen, best_cost = slot, cost
        label_pos[p["id"]] = chosen
        placed_boxes.append(label_box(p, chosen, label))

    for p in plan:
        funded = p.get("budget_approved", False)
        negative = p["anv_m"] < 0
        # Readable sizing: 16px floor, ~48px at the largest lever
        size = min(48.0, 16.0 + (max(0.0, p["anv_m"]) ** 0.5) * 8.0)

        if p["quadrant"] in ("Park (Data-Blocked)", "De-prioritize"):
            base_color = grey_color
        else:
            base_color = brand_color

        if negative:
            marker = dict(size=size, color="rgba(0,0,0,0)", line=dict(color=red_color, width=2))
        elif funded:
            marker = dict(size=size, color=base_color, line=dict(color="white", width=2))
        else:
            marker = dict(size=size, color="rgba(0,0,0,0)", line=dict(color=base_color, width=1.5))

        label = p.get("short_name") or p["name"]
        # Direct-label the funded plan; unfunded names live in the hover and table
        mode = "markers+text" if p["id"] in funded_ids else "markers"
        status = "Funded in this plan" if funded else "Not funded in this plan"
        if negative:
            status = "Loses money at current inputs"
        pb_txt = f"{p['payback']:.0f} months" if 0 < p["payback"] < 900 else "n/a"
        fig.add_trace(go.Scatter(
            x=[p["feasibility"]], y=[p["impact"]], mode=mode,
            text=[label], textposition=label_pos.get(p["id"], "top center"),
            textfont=dict(size=11, color="#2D2D2D", family="Arial"),
            marker=marker, name=p["name"], showlegend=False,
            hovertemplate=(f"<b>{p['name']}</b><br>{status}<br>"
                           f"Value ${p['anv_m']:.1f}M per year · Pays back in {pb_txt}<br>"
                           f"Impact {p['impact']}/100 · Readiness {p['feasibility']}/100"
                           f"<extra></extra>"),
        ))

    def corner(x, y, text, color, xanchor):
        return dict(x=x, y=y, text=text, showarrow=False, xanchor=xanchor,
                    font=dict(size=11, family="Arial", color=color))

    fig.update_layout(
        annotations=[
            corner(104, 104, "STRATEGIC BETS · fund first", "#D04A02", "right"),
            corner(104, 2, "QUICK WINS · fast, lower value", "#7D7D7D", "right"),
            corner(1, 104, "BLOCKED · fix the data foundation first", "#7D7D7D", "left"),
            corner(1, 2, "LOWER PRIORITY", "#BDBDBD", "left"),
        ],
        xaxis=dict(range=[0, 105], showgrid=False, zeroline=False,
                   tickfont=dict(size=11, color="#7D7D7D"),
                   title=dict(text="Readiness to deliver", font=dict(color="#7D7D7D", size=12))),
        yaxis=dict(range=[0, 105], showgrid=False, zeroline=False,
                   tickfont=dict(size=11, color="#7D7D7D"),
                   title=dict(text="Value to the business", font=dict(color="#7D7D7D", size=12))),
        height=640, margin=dict(l=40, r=40, t=20, b=40),
        plot_bgcolor="white", paper_bgcolor="white", font=dict(family="Arial"),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.html("""
    <div style="display:flex; align-items:center; justify-content:center; gap:16px; margin-top:-8px; margin-bottom:16px; font-size:12px; color:var(--g500);">
        <span><span style="display:inline-block; width:10px; height:10px; border-radius:50%; background-color:#D04A02; vertical-align:middle; margin-right:5px;"></span>Funded in this plan</span>
        <span><span style="display:inline-block; width:10px; height:10px; border-radius:50%; border:1.5px solid #D04A02; vertical-align:middle; margin-right:5px;"></span>Not funded</span>
        <span><span style="display:inline-block; width:10px; height:10px; border-radius:50%; border:2px solid #E0301E; vertical-align:middle; margin-right:5px;"></span>Loses money</span>
        <span>Circle size = annual value ($M per year)</span>
    </div>
    """)

    st.html('<div class="hz-report-h2" style="display:flex; justify-content:space-between; align-items:flex-end;"><span>Full Lever Scorecard</span></div>')
    
    import pandas as pd
    df = pd.DataFrame(plan)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇ Download CSV",
        data=csv,
        file_name='use_case_scorecard.csv',
        mime='text/csv',
    )

    rows = ""
    for p in plan:
        funded = p.get("budget_approved", False)
        tr_cls = "" if funded else "unfunded"
        tag = "" if funded else '<span class="hz-chip median" style="margin-left:8px;">UNFUNDED</span>'
        warn = ""
        if p.get("warning") == "COMPUTE_ERROR":
            val, pb, roi = "n/a", "n/a", "n/a"
            warn = '<span class="hz-status-breach" style="font-size:11px; margin-left:8px;">△ could not be computed</span>'
        elif p["anv_m"] < 0:
            val = f"<span class='hz-status-breach'>${p['anv_m']:.1f}M</span>"
            pb, roi = "n/a (negative value)", "n/a"
            warn = '<span class="hz-status-breach" style="font-size:11px; margin-left:8px;">△ value-destructive</span>'
        else:
            val = f"${p['anv_m']:.1f}M"
            pb = f"{p['payback']:.0f} mo" if p["payback"] < 900 else "n/a"
            roi = f"{p['roi']:.0f}%"
            if p.get("warning") == "REG_CAPPED":
                warn = '<span class="hz-status-watch" style="font-size:11px; margin-left:8px;">△ automation capped pending compliance mitigations</span>'

        dot_color = brand_color if (p["quadrant"] not in ["Park (Data-Blocked)", "De-prioritize"]) else grey_color
        q_dot = f'<span style="display:inline-block; width:10px; height:10px; border-radius:50%; background-color:{dot_color}; margin-right:8px;"></span>'

        rows += (f'<tr class="{tr_cls}"><td><strong>{html.escape(p["name"])}</strong>{warn}{tag}</td>'
                 f'<td>{p["priority"]}</td><td>{q_dot}{p["quadrant"]}</td>'
                 f'<td class="num">{val}</td><td class="num">{pb}</td><td class="num">{roi}</td>'
                 f'<td class="num">{p["impact"]}/100</td><td class="num">{p["feasibility"]}/100</td></tr>')
    st.html(f"""
    <table class="hz-table-wrap"><thead><tr>
        <th>AI Use Case</th><th>Priority</th><th>Quadrant</th>
        <th style="text-align:right;">ANV / yr</th><th style="text-align:right;">Payback</th>
        <th style="text-align:right;">Risk-adj ROI</th>
        <th style="text-align:right;">Impact</th><th style="text-align:right;">Feasibility</th>
    </tr></thead><tbody>{rows}</tbody></table>
    """)


# ── Act 3: The Foundation ─────────────────────────────────────────────────────
def _tab_foundation(plan, answers):
    # Basically the same as ui/foundation.py but as a tab
    from ui.foundation import render_foundation_decision
    render_foundation_decision()

# ── Act 4: Risk & Competitiveness ───────────────────────────────────────────
def _tab_risk_competitive(plan: list[dict], answers: dict) -> None:
    st.html('<div class="hz-report-h2">Competitive Positioning</div>')
    comp = compute_competitive_advantage_score(plan, answers)
    c = comp["overall_score"]
    
    st.html(f'<p class="hz-p"><b>Summary:</b> {"Market-leading advantage" if c >= 70 else "Catch-up posture based on foundational modernization."}</p>')
    
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
        adv = "".join(
            f"<li><strong>{html.escape(a.name)}:</strong> the sector norm is still "
            f"{html.escape(a.market_norm.lower())} <em>(competitors need {a.time_to_parity} to catch up)</em></li>"
            for a in comp["advantages"])
        if adv:
            st.html(f"<ul style='font-size:13px; color:var(--g700);'>{adv}</ul>")
        comps = ", ".join(comp.get("primary_competitors", []))
        if comps:
            st.html(f'<p style="font-size:12px; color:var(--g500);">Benchmark competitor set ({html.escape(st.session_state.get("target_sector", "BFSI"))}): {html.escape(comps)}</p>')

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


# ── Act 5: Assumptions Appendix ───────────────────────────────────────────────
def _tab_assumptions() -> None:
    _tab_memo()
    st.html('<div class="hz-report-h2">Model Assumptions & Constants</div>')
    st.html('<p class="hz-p">All calculations derive from explicit, auditable constants in <code>config/value_pools.py</code>. Impact is computed per firm (value-pool × goal-fit × urgency); feasibility from architecture, silos, and governance. No hidden scaling factors.</p>')
    from config.value_pools import CONSTANTS
    rows = "".join(f"<tr><td><strong>{k}</strong></td><td class='num'>{v}</td></tr>" for k, v in CONSTANTS.items())
    st.html(f'<table class="hz-table-wrap"><thead><tr><th>Constant</th><th style="text-align:right;">Value</th></tr></thead><tbody>{rows}</tbody></table>')

    st.html('<div class="hz-report-h2" style="margin-top:32px;">Lever Benchmarks</div>')
    from config.value_pools import BFSI_LEVERS
    brows = "".join(f"<tr><td><strong>{html.escape(l['name'])}</strong></td><td>{html.escape(l.get('benchmark',''))}</td></tr>" for l in BFSI_LEVERS)
    st.html(f'<table class="hz-table-wrap"><thead><tr><th>Lever</th><th>Benchmark source</th></tr></thead><tbody>{brows}</tbody></table>')


def _tab_memo() -> None:
    summary = st.session_state.get("thesis_summary", "")
    if not summary:
        st.info("Complete the intake form to generate the strategic memo.")
        return
    rid = st.session_state.get("last_run_id", "not logged")
    st.html(f"""
    <div style="max-width:800px; margin-bottom: 32px;">
        <div style="font-family:var(--font-head); font-size:26px; color:var(--black); margin:var(--sp-6) 0;">Executive Summary Memo</div>
        {summary}
        <div style="margin-top:var(--sp-6); font-size:11px; color:var(--g500); border-top:1px solid var(--g200); padding-top:var(--sp-2);">
            Narrative generated by Gemini and grounded in the computed plan. Review for accuracy. · Run ID: {rid}
        </div>
    </div>
    """)


