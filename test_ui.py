import sys
import streamlit as st
from ui.sidebar import _advance_company, _generate

class DummySession:
    def __init__(self):
        self.d = {}
    def get(self, k, default=None): return self.d.get(k, default)
    def __getattr__(self, k): return self.d.get(k)
    def __setattr__(self, k, v):
        if k == 'd': super().__setattr__(k, v)
        else: self.d[k] = v

st.session_state = DummySession()
st.session_state.wizard_page = 0
st.session_state.discovery_answers = {}

try:
    _advance_company("ICICI Bank", "", ["Cost"], "Bank")
    print("advance_company OK. page:", st.session_state.wizard_page)
except Exception as e:
    print("Error in advance_company:", e)

st.session_state.budget_usd_m = 100
try:
    _generate(100)
    print("generate OK")
except Exception as e:
    print("Error in generate:", e)

