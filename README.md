# AI Investment Prioritisation Engine — BFSI

A client-facing diagnostic that turns ~15 minutes of executive input into a
board-ready AI investment plan for financial-services firms: a prioritised,
budget-constrained portfolio of AI use cases, a verdict on the legacy estate
with a bottom-up modernization cost, an India-specific regulatory overlay,
and an executive memo — with **every number on screen traceable to an input
or a declared constant**.

Built for PwC-style advisory engagements in Indian BFSI (mutual funds /
asset management, life & general insurance, diversified financial services).

> **Full handover documentation:** [`docs/HANDOVER.md`](docs/HANDOVER.md) —
> the product story, every formula, every assumption, the UI system, and the
> reasoning behind each design decision, written for tech, business, and
> non-technical readers.

---

## Quick start

```bash
# 1. Clone and enter
git clone https://github.com/lakshayagarwal23/ai_investment_prioritization-bfsi.git
cd ai_investment_prioritization-bfsi

# 2. Create a virtualenv and install
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. (Optional but recommended) enable the AI features
cp .env.template .env          # then paste your Google AI Studio key
# GEMINI_API_KEY="..."         # powers web prefill + the executive memo
# Without a key the app runs fully — prefill is skipped honestly and the
# memo shows a clear configuration notice instead of pretending.

# 4. Run
streamlit run app.py           # opens on http://localhost:8501
```

**Tests** (28 invariants — every one encodes a defect class that actually
shipped once):

```bash
python -m pytest tests/ -q
```

## What the user experiences

1. **Landing** — what the diagnostic is and what you receive.
2. **Intake wizard (8 steps)** — firm, sector, goals; a *prefill review*
   step where facts found in public sources (with quotes and URLs) are
   confirmed or discarded; then ~16 operational questions, each stating why
   it is asked; finally the budget.
3. **The report** — five tabs, each answering exactly one question:

   | Tab | The question it answers |
   |---|---|
   | What should we fund? | The decision card: invest $X now, value/yr after risk discount, break-even, drivers, risks, confidence — then the phased sequence |
   | Which use cases, and why? | The prioritisation matrix (value × readiness) and the full scorecard |
   | Can our systems support it? | The legacy-estate diagnostic (TCO framework), modernization business case, budget position, and the fund/defer decision |
   | What could stop us? | Competitive positioning + IRDAI/RBI/SEBI compliance table |
   | How was this computed? | The memo, every model constant, every benchmark source |

   Two global controls recompute everything live: **execution scenario**
   (conservative / base / aggressive realisation haircuts) and **AI model
   stack** (frontier / balanced / cost-optimized — a real capability-vs-run-cost
   trade-off).

## Architecture at a glance

```
app.py                     entry point; phase routing (landing → wizard → report)
├── config/
│   ├── questions.py       the intake questionnaire (single source of truth)
│   └── value_pools.py     14 lever specs, goal taxonomy, all model CONSTANTS,
│                          run costs, AI stacks, cost-basis text
├── engine/                pure Python, deterministic, no Streamlit imports
│   ├── math_engine.py     lever valuation, scoring, budget allocation
│   ├── legacy_diagnostic.py  TCO deprecation score + bottom-up rebuild cost
│   ├── regulatory.py      IRDAI / RBI / SEBI constraint checks
│   └── competitive.py     sector-aware defensibility scoring
├── llm/
│   ├── search_client.py   grounded web prefill (search → structured extract)
│   └── openai_client.py   executive memo generation (Gemini, plan-grounded)
├── ui/                    Streamlit presentation layer only — never computes
│   ├── theme.py           design system (PwC Horizon), header, all CSS
│   ├── landing.py  sidebar.py  prefill_review.py  dashboard.py  foundation.py
├── storage/audit.py       SQLite run log (inputs + plan + versions per run)
└── tests/test_invariants.py   28 invariants
```

**Design contract:** the engine computes, the UI renders. Every lever is
priced only from questions actually asked (or derivations declared in
`CONSTANTS`); every goal string, gated lever, and cost basis has exactly one
definition; anything that fails computes loudly, never as a silent zero.

## Deployment

`render.yaml` is a ready Render blueprint (Python 3.12.9, free plan).
Set `GEMINI_API_KEY` in the service's environment. Any platform that can run
`streamlit run app.py` works the same way; secrets are read from the
environment (a `.env` file is optional, for local dev only).

## Honest limitations

- Benchmarks and cost scopes are calibrated judgment with cited sources —
  not client data. In an engagement they are replaced by rate cards and
  scoped quotes (the UI says this wherever such a number appears).
- Streamlit caps the interaction polish; the engine is cleanly separated so
  a React/Next.js front end can replace `ui/` without touching the model.
- Single-session, no authentication — a pilot tool, not a multi-tenant product.

See [`docs/HANDOVER.md`](docs/HANDOVER.md) §12 for the full roadmap.
