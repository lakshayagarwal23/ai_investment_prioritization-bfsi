"""
ui/prefill_review.py — "Here's what we found" review step (PwC Horizon v6).

Renders AFTER company selection, BEFORE section pages. Turns prefill from a
mute banner into an auditable, client-ready checkpoint:

    Found (n)      — value, source, quote; editable; keep or discard
    Not found (m)  — listed honestly, with the queries that were run
    Backend status — which retrieval tier ran, how long, how many sources

Wiring (2 lines in ui/sidebar.py):
    from ui.prefill_review import render_prefill_review
    # in render_intake_wizard(): insert a page between company (0) and S1:
    #   if page == 1: render_prefill_review(); return   (shift later pages by +1)
"""
from __future__ import annotations
import html
import streamlit as st
from config.questions import QUESTIONS

_Q_BY_ID = {q["id"]: q for q in QUESTIONS}


def render_prefill_review() -> None:
    prov = st.session_state.get("discovery_provenance", {}) or {}
    log = st.session_state.get("prefill_log", {}) or {}
    company = html.escape(st.session_state.get("company_name", "the firm"))

    st.html(f"""
    <div class="hz-q-group-intro">Review pre-filled data (Step 2 of 8)</div>
    <div style="font-size:14px; color:var(--g700); margin-bottom:var(--sp-4);">
        We searched public sources for <strong>{company}</strong>. Confirm or correct
        what was found. Nothing below is estimated; every value carries its source.
    </div>
    """)

    # ── Backend status strip ────────────────────────────────────────────────
    backend = log.get("backend") or "no retrieval ran (missing API key)"
    n_src = len(set(log.get("sources_seen", [])))
    dur = log.get("duration_s", 0)
    st.html(f"""
    <div style="display:flex; gap:var(--sp-6); font-size:11.5px; color:var(--g500);
                border:1px solid var(--g200); border-radius:2px; padding:8px 14px; margin-bottom:var(--sp-5);">
        <span><strong style="color:var(--g700);">Backend</strong> · {html.escape(str(backend))}</span>
        <span><strong style="color:var(--g700);">Sources reviewed</strong> · {n_src}</span>
        <span><strong style="color:var(--g700);">Time</strong> · {dur}s</span>
    </div>
    """)

    found = {k: v for k, v in prov.items() if isinstance(v, dict) and k in _Q_BY_ID}
    missing = [f for f in log.get("fields_missing", []) if f in _Q_BY_ID]

    # ── Found fields: value + source + keep/discard ─────────────────────────
    st.html(f'<div class="hz-report-h2">Found from public sources ({len(found)})</div>')
    if not found:
        st.html('<p class="hz-p" style="color:var(--g500);">Nothing could be verified from public sources for this firm. All fields will be entered manually or use peer medians, clearly chipped as such.</p>')
    answers = st.session_state.discovery_answers
    for fid, p in found.items():
        q = _Q_BY_ID[fid]
        conf = p.get("confidence", "Low")
        chip = {"High": ("auto", "VERIFIED · TIER A/B"), "Med": ("verify", "VERIFY · PRESS"),
                "Low": ("verify", "VERIFY · WEAK SOURCE")}.get(conf, ("verify", "VERIFY"))
        src = html.escape(str(p.get("source_url", "")))[:90]
        quote = html.escape(str(p.get("quote", "")))[:180]
        with st.container(border=True):
            st.html(f"""
            <div class="hz-q-label-row">
                <span class="hz-q-label">{html.escape(q['question'])}</span>
                <span class="hz-chip {chip[0]}">{chip[1]}</span>
            </div>
            <div style="font-family:var(--font-head); font-size:22px; color:var(--black); margin:4px 0;">{html.escape(str(p.get('value','')))}</div>
            <div style="font-size:11px; color:var(--g500);">Source: <a href="{src}" target="_blank" style="color:var(--pwc-orange);">{src}</a><br><em>"{quote}"</em></div>
            """)
            keep = st.toggle("Use this value", value=True, key=f"keep_{fid}")
            if not keep:
                answers.pop(fid, None)
                st.session_state.discovery_provenance.pop(fid, None)

    # ── Not found: honest, with the queries run ─────────────────────────────
    if missing:
        st.html(f'<div class="hz-report-h2">Not found in public sources ({len(missing)})</div>')
        items = "".join(
            f'<div class="hz-road-item">{html.escape(_Q_BY_ID[f]["question"])} '
            f'<span style="color:var(--g500);">You will enter this in the next steps'
            f'{" (internal metric, rarely public)" if f in ("S1_ARCH","S1_ERP") else ""}</span></div>'
            for f in missing)
        st.html(items)

    st.write("")
    c1, _, c2 = st.columns([1.5, 3, 1.5])
    with c1:
        if st.button("Back", use_container_width=True):
            st.session_state.wizard_page -= 1
            st.rerun()
    with c2:
        if st.button("Confirm & continue", type="primary", use_container_width=True):
            st.session_state.wizard_page += 1
            st.rerun()
