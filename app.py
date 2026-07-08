"""
app.py
Entry point for the AI Investment Engine.

Phase 0  Landing page (welcome, overview)
Phase 1  Unified intake form (company, KPIs, tech stack, discovery, budget)
Phase 3  Full AI investment prioritisation dashboard (full-width)

Run with: .venv/bin/streamlit run app.py --server.port 8502
"""

import streamlit as st

# Must be the first Streamlit call
st.set_page_config(
    page_title="AI Investment Engine — BFSI",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "AI Investment Engine — BFSI C-Suite Edition",
    },
)

from ui.theme import inject_theme, render_header
from ui.landing import render_landing_page
from ui.sidebar import (
    init_session_state,
    render_sidebar_branding,
    render_intake_wizard,
)
from ui.dashboard import render_dashboard
from storage.audit import init_db

def main() -> None:
    # Inject CSS theme first (must precede all rendering)
    inject_theme()

    # Initialize all session state keys
    init_session_state()

    # Initialize the audit database
    init_db()

    # Render the persistent top header bar and sidebar branding
    render_header()
    render_sidebar_branding()

    phase = st.session_state.app_phase

    if phase == 0:
        # Phase 0: Landing page (full-width, no columns)
        render_landing_page()
    elif phase == 1:
        # Phase 1: Full-width unified intake form
        render_intake_wizard()
    else:
        # Phase 3: Full-width AI investment prioritisation dashboard
        render_dashboard()


if __name__ == "__main__":
    main()
