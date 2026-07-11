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
    _plan_flash()
    _scenario_bar()

    plan = st.session_state.thesis_plan or []
    answers = st.session_state.discovery_answers or {}
    company = html.escape(st.session_state.company_name) if st.session_state.company_name else "The Firm"

    # Each tab answers exactly one executive question.
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "What should we fund?", "Which use cases, and why?", "Can our systems support it?",
        "What could stop us?", "How was this computed?",
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

def _plan_value(plan) -> float:
    return sum(p["anv"] for p in (plan or []) if p.get("budget_approved")) / 1e6


def _recompute_plan(change_label: str) -> None:
    """Recompute the plan and record what the change did, so the user gets
    explicit before/after feedback instead of a silent refresh."""
    from engine.math_engine import build_investment_plan
    before = _plan_value(st.session_state.get("thesis_plan"))
    st.session_state.thesis_plan = build_investment_plan(
        st.session_state.discovery_answers, st.session_state.budget_usd_m,
        st.session_state.primary_goals,
        scenario=st.session_state.get("current_scenario", "base"),
        foundation_decision=st.session_state.get("foundation_decision", False),
        ai_stack=st.session_state.get("ai_stack", "Balanced"))
    after = _plan_value(st.session_state.thesis_plan)
    direction = "up" if after > before else ("down" if after < before else "unchanged at")
    delta = abs(after - before)
    if direction == "unchanged at":
        effect = f"plan value unchanged at ${after:.1f}M per year"
    else:
        effect = f"plan value {direction} ${delta:.1f}M, from ${before:.1f}M to ${after:.1f}M per year"
    st.session_state.plan_flash = f"{change_label}: {effect}. Every figure below has been recomputed."


def _plan_flash() -> None:
    msg = st.session_state.pop("plan_flash", None)
    if msg:
        st.html(f'<div style="background:var(--orange-tint); border:1px solid var(--pwc-orange); '
                f'border-radius:4px; padding:12px 16px; font-size:13px; color:var(--g700); '
                f'margin-bottom:16px;"><strong>✓</strong> {msg}</div>')


def _scenario_bar() -> None:
    decision = st.session_state.get("foundation_decision")
    status = {True: ('var(--pwc-orange)', 'Legacy modernization: in the plan'),
              False: ('var(--g500)', 'Legacy modernization: not in the plan'),
              None: ('var(--g500)', 'Legacy modernization: decision pending on The Foundation tab')}[decision]
    st.html(f'<div class="hz-scenario-lbl" style="display:flex; justify-content:space-between;">'
            f'<span>Execution scenario &nbsp;·&nbsp; AI model stack</span>'
            f'<span style="color:{status[0]}; font-size:11px; font-weight:600;">{status[1]}</span></div>')
    c1, c2, c3, gap, s1, s2, s3, gap2, r1 = st.columns(
        [1.4, 1.1, 1.4, 0.4, 1.3, 1.3, 1.7, 0.9, 1.3])

    current = st.session_state.get("current_scenario", "base")
    labels = {"conservative": "Conservative", "base": "Base", "aggressive": "Aggressive"}
    for key, col in {"conservative": c1, "base": c2, "aggressive": c3}.items():
        with col:
            if st.button(labels[key], key=f"sc_{key}", use_container_width=True,
                         type="primary" if current == key else "secondary",
                         help="How much of the modelled value we bank: 50% / 60% / 75%"):
                if key != current:
                    st.session_state.current_scenario = key
                    _recompute_plan(f"Scenario set to {labels[key]}")
                    st.rerun()

    from config.value_pools import AI_STACKS
    stack = st.session_state.get("ai_stack", "Balanced")
    stack_effect = {"Frontier": "Run costs +30%, automation capture +6%",
                    "Balanced": "The cost and capability reference point",
                    "Cost-optimized": "Run costs -25%, automation capture -7%"}
    for key, col in {"Frontier": s1, "Balanced": s2, "Cost-optimized": s3}.items():
        with col:
            if st.button(key, key=f"stk_{key}", use_container_width=True,
                         type="primary" if stack == key else "secondary",
                         help=f"{AI_STACKS[key]['desc']} {stack_effect[key]}."):
                if key != stack:
                    st.session_state.ai_stack = key
                    _recompute_plan(f"AI stack set to {key}")
                    st.rerun()

    with r1:
        if st.button("↺ Restart", key="restart", type="secondary", use_container_width=True,
                     help="Discard this engagement and start a new diagnostic"):
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

# ── Tab 1: What should we fund? (one question, one answer, one action) ───────
def _tab_recommendation(plan, answers, company):
    approved = [p for p in plan if p.get("budget_approved")]
    total_anv = sum(p["anv"] for p in approved) / 1e6
    total_cost = sum(p["impl_cost"] for p in approved) / 1e6
    exec_risk = compute_execution_risk(answers)
    risk_adj = total_anv * (1.0 - exec_risk)
    confidence = int(round((1.0 - exec_risk) * 100))
    pb = payback_months(total_cost * 1e6, risk_adj * 1e6)
    pb_str = f"{pb:.0f} months" if pb < 900 else "beyond the horizon"
    budget_m = float(st.session_state.get("budget_usd_m", 100.0))

    drivers = sorted(approved, key=lambda p: -p["anv"])[:3]
    driver_html = "".join(
        f'<span class="hz-driver-chip">{html.escape(p.get("short_name") or p["name"])}'
        f'<span class="hz-driver-val">returns ${p["anv_m"]:.1f}M/yr</span></span>'
        for p in drivers)

    risks = []
    if "monolith" in str(answers.get("S1_ERP", "")).lower():
        risks.append("Legacy core system")
    if float(answers.get("S1_SILO", 5) or 5) >= 5:
        risks.append("Fragmented data estate")
    if float(answers.get("S5_GOVERNANCE_SCORE", 50) or 50) < 60:
        risks.append("Governance maturity")
    if any(p["reg_status"].get("risk_level") == "yellow" for p in approved):
        risks.append("Compliance mitigations required")
    risks = risks[:3] or ["No structural risks flagged"]
    risk_html = "".join(f'<span class="hz-risk-chip">{html.escape(r)}</span>' for r in risks)

    st.html(f"""
    <div class="hz-decision-card">
        <div class="hz-decision-eyebrow">Recommendation for {company}</div>
        <div class="hz-decision-headline">Invest ${total_cost:.1f}M of your ${budget_m:.0f}M budget now.</div>
        <div class="hz-decision-sub">
            That ${total_cost:.1f}M is a one-off build cost. In return, the funded plan creates
            <strong>${risk_adj:.1f}M of value every year</strong> after a {exec_risk*100:.0f}% risk
            discount, earning the money back in <strong>{pb_str}</strong>.
            The remaining ${max(0.0, budget_m - total_cost):.1f}M stays uncommitted, because
            spending it on weaker cases would destroy value.
        </div>
        <div class="hz-decision-row">
            <div class="hz-decision-block">
                <div class="hz-decision-lbl">Largest value drivers</div>{driver_html}
            </div>
            <div class="hz-decision-block">
                <div class="hz-decision-lbl">What could get in the way</div>{risk_html}
            </div>
            <div class="hz-decision-block" style="min-width:150px;">
                <div class="hz-decision-lbl">Plan confidence</div>
                <div style="font-family:var(--font-head); font-size:30px; color:var(--black);">{confidence}%</div>
                <div style="font-size:11px; color:var(--g500);">driven by your governance maturity</div>
            </div>
        </div>
    </div>
    """)

    with st.expander("How these headline numbers are built"):
        st.html(f"""
        <table class="hz-table-wrap">
          <tbody>
            <tr><td>Value created per year (before risk discount)</td><td class="num">${total_anv:.1f}M</td>
                <td style="font-size:12px; color:var(--g500);">Sum of every funded use case's annual value; each one is itemized on the next tab</td></tr>
            <tr><td>Risk discount</td><td class="num">{exec_risk*100:.0f}%</td>
                <td style="font-size:12px; color:var(--g500);">From your governance maturity score: weaker governance means more delivery slippage</td></tr>
            <tr style="background:var(--g100);"><td><strong>Value created per year (after discount)</strong></td>
                <td class="num"><strong>${risk_adj:.1f}M</strong></td><td></td></tr>
            <tr><td>Money in</td><td class="num">${total_cost:.1f}M</td>
                <td style="font-size:12px; color:var(--g500);">Every dollar itemized on the systems tab, section 4</td></tr>
            <tr style="border-top:2px solid var(--g300);"><td><strong>Earns back its cost in</strong></td>
                <td class="num"><strong>{pb_str}</strong></td>
                <td style="font-size:12px; color:var(--g500);">Value ramps over 3 years (25% / 60% / 100%), so early months earn less</td></tr>
          </tbody>
        </table>
        """)

    now = [p for p in approved if p["quadrant"] == "Strategic Bets"]
    nxt = [p for p in approved if p["quadrant"] == "Quick Wins / Fill-ins"]
    now_capex = sum(p["impl_cost"] for p in now) / 1e6
    nxt_capex = sum(p["impl_cost"] for p in nxt) / 1e6

    st.html('<div class="hz-report-h2" style="margin-top: 32px;">The three asks of your leadership team</div>')
    st.html(f'''
    <div style="display:flex; gap:16px; margin-bottom: 32px;">
      <div class="hz-ask-card" style="border-top-color:#D04A02;">
        <div class="hz-ask-title">1. Fund now (0 to 6 months)</div>
        <div class="hz-ask-desc">Commit ${now_capex:.1f}M to the {len(now)} highest-value, ready-to-build use cases</div>
      </div>
      <div class="hz-ask-card" style="border-top-color:#EB8C00;">
        <div class="hz-ask-title">2. Fund next (6 to 18 months)</div>
        <div class="hz-ask-desc">Approve ${nxt_capex:.1f}M for {len(nxt)} fast, momentum-building use cases</div>
      </div>
      <div class="hz-ask-card" style="border-top-color:#7D7D7D;">
        <div class="hz-ask-title">3. Sponsor the change</div>
        <div class="hz-ask-desc">Name business owners for each use case; value lands only if teams adopt the new way of working</div>
      </div>
    </div>
    ''')

    _roadmap(plan)


def _roadmap(plan):
    funded = [p for p in plan if p.get("budget_approved")]
    now = [p for p in funded if p["quadrant"] == "Strategic Bets"]
    nxt = [p for p in funded if p["quadrant"] == "Quick Wins / Fill-ins"]
    later = [p for p in plan if p["quadrant"] == "Park (Data-Blocked)"]

    def item(p, locked=False):
        if locked:
            money = f'Worth ${p["anv_m"]:.1f}M per year, locked until the foundation is fixed'
        else:
            money = (f'Costs ${p["impl_cost"]/1e6:.1f}M to build &nbsp;·&nbsp; '
                     f'returns ${p["anv_m"]:.1f}M per year')
        return (f'<div class="hz-road-item">{html.escape(p["name"])}'
                f'<div style="font-size:11.5px; color:var(--g500); font-weight:400; margin-top:2px;">'
                f'{money}</div></div>')

    def col(items, cls, head, subtitle, locked=False):
        body = "".join(item(p, locked) for p in items) if items \
            else '<div class="hz-road-empty">None in this horizon.</div>'
        return (f'<div class="hz-road-col {cls}"><div class="hz-road-h">{head}</div>'
                f'<div style="font-size:11px;color:var(--g500);margin-bottom:8px;">{subtitle}</div>{body}</div>')

    st.html('<div class="hz-report-h2" style="margin-top: 32px;">The sequence</div>')
    st.html('<div class="hz-roadmap">'
            + col(now, "now", "Now (0-6 mo)", "High value, ready to build")
            + col(nxt, "next", "Next (6-18 mo)", "Fast, momentum-building")
            + col(later, "later", "Later (blocked)", "High value, needs the data foundation first", locked=True)
            + '</div>')

    # Reconcile the sequence back to the headline, so the two can never
    # appear to disagree: build costs sum to the committed figure; the
    # per-year figures are returns, not spend.
    total_build = sum(p["impl_cost"] for p in funded) / 1e6
    total_value = sum(p["anv"] for p in funded) / 1e6
    st.html(f'<div style="font-size:12.5px; color:var(--g500); margin-top:-8px;">'
            f'Adds up: the build costs above total <strong style="color:var(--g700);">${total_build:.1f}M</strong>, '
            f'the same figure as the headline commitment. Together they return '
            f'<strong style="color:var(--g700);">${total_value:.1f}M per year</strong> before the risk discount.</div>')


# ── Act 2: The Portfolio ──────────────────────────────────────────────────────
def _tab_portfolio(plan: list[dict]) -> None:
    n_funded = sum(1 for p in plan if p.get("budget_approved"))
    blocked_m = sum(p["anv"] for p in plan
                    if p["quadrant"] == "Park (Data-Blocked)" and p["anv"] > 0) / 1e6
    if blocked_m > 0.05:
        headline = (f"{n_funded} use cases are worth funding now; "
                    f"${blocked_m:.1f}M per year sits blocked behind the data foundation")
    else:
        headline = f"{n_funded} of {len(plan)} use cases earn a place in the funded plan"
    st.html(f'<div class="hz-report-h2">{headline}</div>')
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

    quadrant_display = {
        "Strategic Bets": "Strategic bet",
        "Quick Wins / Fill-ins": "Quick win",
        "Park (Data-Blocked)": "Blocked",
        "De-prioritize": "Lower priority",
    }
    st.html("""
    <div style="display:flex; gap:20px; font-size:12px; color:var(--g500); margin-bottom:8px; flex-wrap:wrap;">
        <span><strong style="color:var(--g700);">Strategic bet</strong> · high value and ready to build; fund first</span>
        <span><strong style="color:var(--g700);">Quick win</strong> · smaller value, fast to deliver; builds momentum</span>
        <span><strong style="color:var(--g700);">Blocked</strong> · valuable but your data foundation cannot support it yet</span>
        <span><strong style="color:var(--g700);">Lower priority</strong> · does not earn a place in this plan</span>
    </div>
    """)

    rows = ""
    for p in plan:
        funded = p.get("budget_approved", False)
        tr_cls = "" if funded else "unfunded"
        tag = "" if funded else '<span class="hz-chip median" style="margin-left:8px;">NOT FUNDED</span>'
        warn = ""
        if p.get("warning") == "COMPUTE_ERROR":
            val, pb = "n/a", "n/a"
            warn = '<span class="hz-status-breach" style="font-size:11px; margin-left:8px;">could not be computed</span>'
        elif p["anv_m"] < 0:
            val = f"<span class='hz-status-breach'>${p['anv_m']:.1f}M</span>"
            pb = "n/a (loses money)"
            warn = '<span class="hz-status-breach" style="font-size:11px; margin-left:8px;">loses money at current inputs</span>'
        else:
            val = f"${p['anv_m']:.1f}M"
            pb = f"{p['payback']:.0f} mo" if p["payback"] < 900 else "n/a"
            if p.get("warning") == "REG_CAPPED":
                warn = ('<span class="hz-status-watch" style="font-size:11px; margin-left:8px;">'
                        'value halved until compliance gaps close</span>')

        dot_color = brand_color if (p["quadrant"] not in ["Park (Data-Blocked)", "De-prioritize"]) else grey_color
        q_dot = f'<span style="display:inline-block; width:10px; height:10px; border-radius:50%; background-color:{dot_color}; margin-right:8px;"></span>'

        rows += (f'<tr class="{tr_cls}"><td><strong>{html.escape(p["name"])}</strong>{warn}{tag}</td>'
                 f'<td>{q_dot}{quadrant_display.get(p["quadrant"], p["quadrant"])}</td>'
                 f'<td class="num">${p["impl_cost"]/1e6:.1f}M</td>'
                 f'<td class="num">{val}</td><td class="num">{pb}</td>'
                 f'<td class="num">{p["impact"]}/100</td><td class="num">{p["feasibility"]}/100</td></tr>')
    st.html(f"""
    <table class="hz-table-wrap"><thead><tr>
        <th>AI use case</th><th>Category</th>
        <th style="text-align:right;">Build cost</th>
        <th style="text-align:right;">Annual value</th><th style="text-align:right;">Earns it back in</th>
        <th style="text-align:right;">Value score</th><th style="text-align:right;">Readiness</th>
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


