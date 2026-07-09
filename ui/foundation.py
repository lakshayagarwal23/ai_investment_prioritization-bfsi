"""
ui/foundation.py — The Foundation Decision Interstitial (Phase 2).

Acts as a stage-gate before the dashboard. Forces the client to make a decision
about their legacy architecture, which then parameters the portfolio.
"""
import streamlit as st
import html
from engine.legacy_diagnostic import run_diagnostic, LegacyInputs

PLATFORM_GATED_LEVERS = {"lever_2", "lever_7", "lever_8", "lever_11", "lever_13"}

def render_foundation_decision() -> None:
    answers = st.session_state.get("discovery_answers", {})
    plan = st.session_state.get("thesis_plan", [])
    
    # Calculate the diagnostic
    unlocked_anv_m = sum(p["anv"] for p in plan if p.get("id") in PLATFORM_GATED_LEVERS and p["anv"] > 0) / 1e6
    maintenance_cost = answers.get("S5_MAINTENANCE_COST", 6.5)
    
    inputs = LegacyInputs(
        maintenance_cost_m=maintenance_cost,
        biz_value_m=answers.get("S5_BIZ_VALUE", 20.0),
        silo_count=answers.get("S1_SILO", 5.0),
        architecture=answers.get("S1_ARCH", "Hybrid — partial cloud"),
        api_maturity=answers.get("S1_ERP", "On-prem with API layer"),
        data_ownership=0, lineage=0, dq_sla=0, reg_trace=0, change_mgmt=0,
        unlocked_anv_m=unlocked_anv_m,
        rebuild_cost_m=None, # Will auto-estimate
        governance_score=answers.get("S5_GOVERNANCE_SCORE", 50.0),
    )
    result = run_diagnostic(inputs)
    sf = result["self_funding"]
    pillars = result["pillars"]
    
    payback_text = f"a rebuild would pay for itself in {round(sf['payback_months'])} months" if sf["payback_months"] else "a rebuild does not currently pay for itself"
    blocked_count = len([p for p in plan if p.get("id") in PLATFORM_GATED_LEVERS])
    total_levers = len(plan) if plan else 11
    
    # ── Boardroom-grade UI ──
    st.html("<div style='height: 40px;'></div>") # Spacer
    st.html(f"""
    <div style="max-width: 900px; margin: 0 auto;">
        <span class="hz-hero-pill-orange" style="margin-bottom: 24px; display: inline-block;">THE FOUNDATION DECISION</span>
        
        <h1 style="font-family: var(--font-head); font-size: 36px; color: var(--black); line-height: 1.2; margin-bottom: 32px;">
            Your core systems cost ${maintenance_cost}M/yr to keep alive and block {blocked_count} of your {total_levers} AI opportunities.<br>
            <span style="color: var(--g500); font-size: 28px;">We recommend an incremental modernization; {payback_text}.</span>
        </h1>
    </div>
    """)
    
    col1, col2 = st.columns([1.2, 1])
    
    with col1:
        st.html("""<div class="hz-report-h2" style="margin-bottom: 16px;">The Evidence</div>""")
        silos = inputs.silo_count
        arch = html.escape(str(inputs.architecture))
        api = html.escape(str(inputs.api_maturity))
        st.html(f"""
        <div style="background: white; border: 1px solid var(--g200); border-radius: 4px; padding: 24px; margin-bottom: 32px;">
            <ul style="margin: 0; padding-left: 20px; color: var(--g700); line-height: 1.8; font-size: 15px;">
                <li><strong>You told us:</strong> {silos} systems hold the same customer record &rarr; your data is fragmented ({pillars['fragmentation_score']}/100).</li>
                <li><strong>You told us:</strong> your architecture is "{arch}" &rarr; cloud readiness is heavily constrained.</li>
                <li><strong>You told us:</strong> your API maturity is "{api}" &rarr; real-time AI agents will struggle to execute actions.</li>
            </ul>
        </div>
        """)
        
        st.html("""<div class="hz-report-h2" style="margin-bottom: 16px;">The Money Story</div>""")
        pb = f"{sf['payback_months']} months" if sf["payback_months"] else "Does not pay back"
        gap = "Fully funded in year one" if sf["first_year_funding_gap_m"] <= 0 else f"${sf['first_year_funding_gap_m']}M"
        st.html(f"""
        <table class="hz-table-wrap" style="width: 100%; margin-bottom: 32px;">
            <tbody>
                <tr><td>Legacy annual savings (what you stop paying)</td><td class="num">${sf['legacy_annual_savings_m']}M</td></tr>
                <tr><td>Unlocked AI value (what gets unlocked)</td><td class="num">${sf['unlocked_anv_m']}M</td></tr>
                <tr style="background: #f8f8f8;"><td><strong>Total annual value</strong></td><td class="num"><strong>${sf['total_annual_value_m']}M</strong></td></tr>
                <tr><td>Rebuild capex (estimated)</td><td class="num">${sf['rebuild_cost_m']}M</td></tr>
                <tr style="border-top: 2px solid var(--g300);"><td><strong>Payback</strong></td><td class="num"><strong>{pb}</strong></td></tr>
            </tbody>
        </table>
        """)
        
    with col2:
        st.html("""
        <div style="background: var(--pwc-orange); color: white; padding: 32px; border-radius: 4px; display: flex; flex-direction: column; justify-content: center; margin-bottom: 24px;">
            <h2 style="font-family: var(--font-head); font-size: 24px; margin-top: 0; margin-bottom: 24px;">Executive Decision Required</h2>
            <p style="font-size: 15px; line-height: 1.5; margin-bottom: 0; opacity: 0.9;">
                Choose how to proceed. Your decision will parameterize the final AI portfolio dashboard.
            </p>
        </div>
        """)
        
        st.markdown("**Include modernization in the plan**<br><span style='font-size: 13px; color: var(--g600);'>*Rebuild capex enters the budget as a funded item; platform-gated levers move from Later to Next.*</span>", unsafe_allow_html=True)
        if st.button("Fund the Foundation", type="primary", use_container_width=True):
            st.session_state.foundation_decision = True
            from engine.math_engine import build_investment_plan
            st.session_state.thesis_plan = build_investment_plan(
                answers=st.session_state.discovery_answers,
                budget_usd_m=st.session_state.budget_usd_m,
                primary_goals=st.session_state.primary_goals,
                scenario=st.session_state.current_scenario,
                foundation_decision=True
            )
            st.session_state.app_phase = 3
            st.rerun()
            
        st.write("")
        st.write("")
            
        st.markdown(f"**Proceed without it**<br><span style='font-size: 13px; color: var(--g600);'>*Gated levers stay parked. ${sf['unlocked_anv_m']}M/yr of value remains locked.*</span>", unsafe_allow_html=True)
        if st.button("Defer Modernization", use_container_width=True):
            st.session_state.foundation_decision = False
            from engine.math_engine import build_investment_plan
            st.session_state.thesis_plan = build_investment_plan(
                answers=st.session_state.discovery_answers,
                budget_usd_m=st.session_state.budget_usd_m,
                primary_goals=st.session_state.primary_goals,
                scenario=st.session_state.current_scenario,
                foundation_decision=False
            )
            st.session_state.app_phase = 3
            st.rerun()
