"""
app.py — Entry point for the AI Investment Engine (PwC Horizon, v5).

Phase 0  Landing page
Phase 1  Single-column intake wizard (no sidebar)
Phase 2  Full-width prioritisation dashboard

Run with: streamlit run app.py
"""

import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # In production (Streamlit Cloud / HF Spaces), secrets are injected natively via the platform
    pass

import streamlit as st

st.set_page_config(
    page_title="AI Investment Engine — BFSI",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",   # sidebar removed in v5
    menu_items={"Get Help": None, "Report a bug": None,
                "About": "AI Investment Engine — BFSI"},
)

from observability import setup_observability
from ui.theme import inject_theme, render_header
from ui.landing import render_landing_page
from ui.sidebar import init_session_state, render_intake_wizard
from ui.dashboard import render_dashboard
from storage.audit import init_db

setup_observability()


def _access_gate() -> bool:
    """Optional shared-secret gate for hosted deployments.

    The app ingests confidential client financials, so a world-readable URL
    is not acceptable. Set APP_PASSWORD in the environment to require it;
    unset (local dev) the gate is disabled. This is an interim control:
    production access is SSO (see docs/PRODUCTION_READINESS.md 3.2).
    """
    import hmac
    required = os.environ.get("APP_PASSWORD", "")
    if not required:
        return True
    if st.session_state.get("_access_ok"):
        return True
    st.markdown("### This engagement tool is access-restricted")
    supplied = st.text_input("Access code", type="password",
                             help="Provided by the engagement team")
    if supplied:
        if hmac.compare_digest(supplied, required):
            st.session_state._access_ok = True
            st.rerun()
        else:
            st.error("That access code is not valid.")
    return False


def main() -> None:
    if not _access_gate():
        return
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
