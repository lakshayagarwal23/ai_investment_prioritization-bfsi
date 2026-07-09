"""
app.py — Entry point for the AI Investment Engine (PwC Horizon, v5).

Phase 0  Landing page
Phase 1  Single-column intake wizard (no sidebar)
Phase 2  Full-width prioritisation dashboard

Run with: streamlit run app.py
"""

import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st

st.set_page_config(
    page_title="AI Investment Engine — BFSI",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",   # sidebar removed in v5
    menu_items={"Get Help": None, "Report a bug": None,
                "About": "AI Investment Engine — BFSI"},
)

from ui.theme import inject_theme, render_header
from ui.landing import render_landing_page
from ui.sidebar import init_session_state, render_intake_wizard
from ui.dashboard import render_dashboard
from storage.audit import init_db


def main() -> None:
    inject_theme()
    init_session_state()
    init_db()

    firm = st.session_state.get("company_name") or "New engagement"
    sector = st.session_state.get("target_sector", "BFSI")
    run_id = st.session_state.get("last_run_id")
    run_label = f"run {run_id}" if run_id else "run —"
    render_header(firm_name=firm, sector=sector, run_id=run_label)

    phase = st.session_state.app_phase
    if phase == 0:
        render_landing_page()
    elif phase == 1:
        render_intake_wizard()
    else:
        render_dashboard()


if __name__ == "__main__":
    main()
