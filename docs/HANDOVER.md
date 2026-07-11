# Handover Documentation — AI Investment Prioritisation Engine (BFSI)

**Audience:** anyone inheriting this system — engineers, consultants,
product owners, and non-technical stakeholders. Read §1–§3 for the story,
§4–§9 for the model and math, §10–§11 for the code and UI, §12 for what to
do next. A glossary for non-technical readers is at the end.

**State at handover:** engine version 5.1.0 · 28/28 tests passing ·
deployed via Render blueprint · repository
`github.com/lakshayagarwal23/ai_investment_prioritization-bfsi`.

---

## 1. What this product is, in one paragraph

A consultant sits with a BFSI executive (or the executive self-serves) and
answers ~16 questions about the firm: its scale, how manual its operations
are, its compliance friction, and the cost and health of its legacy
systems. The engine then produces a defensible answer to one question —
**"where should our next AI dollar go?"** — as a funded portfolio of AI use
cases, a keep/modernize/replace verdict on the legacy estate, a regulatory
risk overlay, and an executive memo. The product's core bet is **trust
through traceability**: every number on screen can be traced to an answer
the user gave or a constant the appendix declares. Nothing is estimated
silently.

## 2. Who it serves and the three audiences of every screen

| Persona | What they need | Where they get it |
|---|---|---|
| CEO / Board member | One decision with consequences | The decision card on tab 1 |
| CFO | Where every dollar goes and returns | Budget itemization (tab 3 §4), scorecard (tab 2), reconciliation lines |
| CIO / CTO | Whether the estate can deliver | Legacy diagnostic (tab 3), readiness scores, regulatory constraints |
| Consultant | Defensibility under challenge | Formulas shown verbatim, appendix constants, benchmark citations, audit log |

Design rule that governs everything: **each tab answers exactly one
executive question** (the tab labels are literally those questions), and
detail appears only on request (expanders), never by default.

## 3. The user journey

```
Phase 0  Landing        what this is, what you receive, one CTA
Phase 1  Intake wizard  8 steps:
         1  Firm, sector, strategic goals (validated: cannot proceed nameless)
         2  Prefill review — facts found in public sources, each with source
            URL + verbatim quote + confidence chip; user keeps or discards
         3-7  Five question sections (Technology, Front office, Middle/back
            office, Risk & compliance, Legacy & governance). Sector gates
            which questions appear (insurers get claims/underwriting volume
            questions; asset managers do not)
         8  Budget envelope
Phase 2+ The report     five question-tabs (see README table) with two live
         controls: execution scenario and AI model stack. The Foundation tab
         contains the one decision the user must make (fund or defer
         modernization); everything recomputes on any change, always with a
         confirmation banner stating before → after.
```

Wizard behaviors worth knowing: pages advance with an explicit `st.rerun()`
(a stale-frame bug once made the UI lag one click behind the state); the
company step blocks empty submission; prefill is skipped entirely (with an
honest notice) when no API key is present, because retrieval without
extraction would waste the user's time for guaranteed nothing.

## 4. The questionnaire (config/questions.py)

Single source of truth for what is asked. Every question carries: `id`
(e.g. `S3_STP`), `section`, plain-English `question` and `help` (why we
ask), `type` (numeric / percentage / categorical), `default` (the peer
median), and optional `visible_when` sector gating.

**The contract that keeps the product honest** (enforced by tests):

1. Every lever's `value_driver.answer_key` must be a question that exists —
   no lever may be priced from a phantom input.
2. Goal strings offered to the user are imported from `config/value_pools.py
   GOALS` — the questionnaire and the lever library can never drift apart
   (this exact drift once silently crippled the default path: every lever
   was treated as off-goal and no Strategic Bets could ever appear).

The ~16 questions (13 for asset managers; +3 volume questions for
insurers): AUM/premiums, data architecture, core-system age, keep-the-lights-on
share, silo count, digital-application share, (insurance: annual
applications, onboarding days, annual claims), straight-through-processing
rate, ops headcount, AML false-positive rate, months per regulatory change,
legacy maintenance cost, legacy business value, governance maturity.
**Every one of them feeds the engine somewhere** — a question that changes
nothing is not allowed to exist.

## 5. The lever library (config/value_pools.py)

Fourteen AI use cases ("levers"), each a declarative spec:

| id | Lever (short name) | Sectors | Build cost* | Defensibility |
|---|---|---|---|---|
| 1 | Trade Reconciliation | MF, Div | $1.0M | medium |
| 2 | Smart Execution | MF, Div | $1.2M | low |
| 3 | Research Coverage | MF, Div | $0.8M | medium |
| 4 | Sales Coverage | all | $1.5M | medium |
| 5 | Onboarding & KYC | all | $0.9M | medium |
| 6 | Reg Reporting | all | $1.1M | low |
| 7 | NAV Oversight | MF, Div | $0.8M | low |
| 8 | Personalization | all | $1.8M | high |
| 9 | Golden Source | all | $2.5M | high |
| 10 | Corporate Actions | MF, Div | $0.6M | low |
| 11 | Underwriting | Ins, Div | $2.5M | medium |
| 12 | Claims & Fraud | Ins, Div | $1.8M | medium |
| 13 | Customer 360 | all | $2.5M | high |
| 14 | Digital Onboarding | Ins, Div | $1.2M | high |

\* peer-median scope, before the firm-size multiplier (§6.4). Each cost has
a `COST_BASIS` sentence stating what it covers (licence, integrations,
build team), shown wherever the cost is itemized.

Other spec fields: `value_driver` (which answered question scales this
lever's impact, and whether bigger answers mean a bigger pool — `scale` —
or less headroom — `gap`), `goal_alignment` (drawn only from `GOALS`),
`benchmark` (the cited source for the automation claims),
`base_impact` / `base_feasibility` (the seeds the dynamic models modulate).

`PLATFORM_GATED_LEVERS` = {2, 7, 8, 9, 11, 13}: levers that cannot ship on a
broken data foundation. Golden Source (9) is in the set because it *is*
foundation work — funding the foundation unblocks it by definition.

`CONSTANTS` is the assumptions register: every loaded FTE cost
(India-blended), every derivation multiplier, ramp curve, haircut, risk
bound, cost-scaling clamp, and stack multiplier. It renders verbatim in the
report appendix — a partner can defend any number because every number is
on the table.

## 6. The engine (engine/math_engine.py) — how a plan is computed

Pure, deterministic Python (same answers → identical plan, tested). No
Streamlit imports. `build_investment_plan(answers, budget, goals, scenario,
foundation_decision, ai_stack)` returns a list of scored lever dicts.

### 6.1 Per-lever annual value (ANV — shown to clients only as "annual value")

Each lever has a formula reading **only asked questions or declared
derivations**. The recurring shapes:

- **FTE savings with benefit attribution.** The ops headcount pool is split
  once — reconciliation 20%, claims 40%, onboarding 15%, compliance 25%
  (sums to 100%) — so no two levers can claim the same person's savings.
  Savings = pool share × loaded cost × automation share.
- **Volume economics.** e.g. claims × STP-uplift × per-claim handling cost;
  applications × conversion uplift × policy margin ($700 premium × 25%
  new-business margin); AUM × turnover × basis-points saved on the
  *non-electronic* share only.
- **Derived internals, never phantom inputs.** Underwriter bench =
  applications ÷ 2,500; in-force book = applications × 7; MF folios =
  AUM($B) × 12,000; AML alerts = ops FTE × 120; recon breaks scale with
  (1 − STP). All multipliers live in `CONSTANTS`.
- Each formula ends minus the lever's **run cost** (`RUN_COSTS`) — model
  licences and inference at the Balanced stack.

### 6.2 Scenario haircut and the AI-stack trade-off

- **Scenario** multiplies value by the benefits-realisation haircut:
  conservative 50%, base 60%, aggressive 75% (the McKinsey-convention
  answer to "modelled value never fully lands").
- **AI stack** is a two-sided trade-off applied as
  `gross × capability_x − run_cost × run_x`:
  Frontier (+6% capture, +30% run cost), Balanced (reference),
  Cost-optimized (−7% capture, −25% run cost). Neither option strictly
  dominates — big value pools justify premium models; small ones net more
  on a cheap stack. A test reconstructs this arithmetic exactly.

### 6.3 Impact, readiness, quadrant

- **Impact (0–100)** = 55% value-pool score (the firm's answer on the
  lever's `value_driver`, normalised to the peer median, capped at 1.6×)
  + 45% urgency (P0→100 … P3→25), then × goal fit (off-goal levers dampen
  to 25%, never hidden — GE-McKinsey style).
- **Readiness / feasibility (0–100)** starts from the lever's base and
  moves with the firm's architecture, core-system age, silo count, KTLO
  share, and governance (each modifier a few points, all in code).
- **Quadrant** from thresholds (impact 65, readiness 60): Strategic bet /
  Quick win / Blocked / Lower priority. If the foundation is funded, gated
  levers get their readiness lifted above the threshold — modernization
  removes exactly that constraint, so position, quadrant, and funding stay
  one story.

### 6.4 Costs, regulation, funding

- **Build cost** = spec cost × firm-size multiplier
  `√(AUM/50 × opsFTE/400)` clamped 0.7–1.5 (integration surface grows with
  scale). When ≠ 1.0 the cost-basis line says so.
- **Regulatory cap:** a red compliance status halves the lever's value until
  mitigations land, with a visible warning — regulation feeds the math, it
  doesn't just print badges.
- **Budget allocation** is greedy by (goal fit, value): only positive-value
  Strategic bets / Quick wins consume capital; blocked, lower-priority,
  negative-value, or compute-errored levers never do. Uncommitted budget is
  *held*, not spent — the report says why.
- **Payback** uses a 3-year ramp (25% / 60% / 100% of steady value), so
  nothing ever pays back implausibly fast.
- **Execution risk** = (1 − governance/100) × 0.5, clamped 5–45%. Applied
  once, at portfolio level, always labelled ("after a 25% risk discount");
  its complement is shown as "plan confidence".

## 7. The legacy diagnostic (engine/legacy_diagnostic.py)

Follows the standard decommissioning framework (TCO analysis → technical
health → modern alternatives → retirement strategy). Everything it returns
carries its own arithmetic (`score_math`, per-pillar explanations) — the UI
renders those verbatim.

- **Three pillars → one score:** tech-debt interest (maintenance ÷ business
  value, weight 40%), fragmentation (silos × architecture × integration
  modifiers, 35%), governance gap (100 − maturity, 25%).
- **Verdicts:** <40 KEEP AND OPTIMIZE · 40–70 MODERNIZE IN PHASES · ≥70
  REPLACE THE CORE · ≥70 with governance <50 → FIX GOVERNANCE FIRST (you
  cannot safely migrate data you cannot trace). Each verdict ships a
  plain-English action and retirement safeguards (statutory data archival,
  dependency mapping, phased cutover, certified decommissioning).
- **Rebuild cost is built bottom-up,** not a flat multiple: core rebuild
  (maintenance × complexity 1.2–2.5× by core age and architecture), data
  migration ($0.35M/silo × data-quality 1.0–1.5×), integration rewiring
  ($0.15M/silo), parallel-run testing (15%), training (8%), contingency
  (15%) — presented as a ±20% range with a line-by-line driver table. A
  client-provided quote overrides the model.
- **The decision** (fund/defer) is a stage-gate with a computed
  recommendation: fund only when the verdict calls for intervention AND the
  spend breaks even within 4 years — extended to 6 only by a *material*
  unlock (≥$1M/yr and ≥5% of the rebuild). This rule exists because the
  system once recommended a $21M spend that unlocked $0.0M — never again.
- "Blocked AI value" counts **only** levers currently parked by the
  foundation, computed from a baseline plan without it — never value
  already funded.

## 8. Regulatory & competitive modules

**Regulatory (engine/regulatory.py):** six India constraints (IRDAI claims
timelines, underwriting explainability, RBI data localization, grievance
redressal, solvency, SEBI algo accountability) mapped to the levers they
bite. Risk level from *asked* inputs: red is reserved for a genuine blocker
(governance <35 — audit trails can't be evidenced); cloud estates with
mid governance get yellow with a named residency action. Red halves the
lever's value in the engine (§6.4).

**Competitive (engine/competitive.py):** defensibility score from the
levers actually funded (high 30 / medium 15 / low 5 points + base 20),
sector-specific competitor sets, and moat statements derived from the lever
library. No client hardcoding — this module once said "Mahindra's rural
footprint" to every firm on earth; that class of defect is banned.

## 9. LLM features (llm/) — deliberately fenced

The financial model is 100% deterministic. LLMs do exactly two jobs:

1. **Prefill** (`search_client.py`): two-step pattern — a Gemini call with
   Google-Search grounding gathers cited facts (AUM, claims volume, policy
   volume, tech-stack signals), then a second structured-output call
   extracts them with source URL + verbatim quote + confidence. Absolute
   rule: a field with no supporting source is omitted, never estimated.
   Range guards reject nonsense. Without a key, no retrieval runs at all.
2. **The memo** (`openai_client.py`): Gemini writes three narrative
   paragraphs grounded in the computed plan (top bets passed in; financial
   claims and invented technologies forbidden by prompt). Everything else in
   the memo is assembled from the plan itself. Failures degrade to a clear
   fallback; the firm name is HTML-escaped (it once was an XSS vector).

## 10. Code map & conventions

```
app.py                 phase router; loads .env if present (optional)
config/questions.py    intake definition (§4)
config/value_pools.py  lever specs, GOALS, PLATFORM_GATED_LEVERS, COST_BASIS,
                       RUN_COSTS, AI_STACKS, CONSTANTS (§5)
engine/*.py            all computation (§6–§8); no Streamlit
llm/*.py               prefill + memo (§9)
ui/theme.py            all CSS (design tokens → components), dark header
ui/landing.py          phase 0
ui/sidebar.py          wizard (init_session_state, stepper, pages, nav)
ui/prefill_review.py   the "here's what we found" checkpoint
ui/dashboard.py        the five report tabs, controls, matrix, scorecard
ui/foundation.py       the legacy decision page (verdict → TCO → business
                       case → budget donut → decision → safeguards)
storage/audit.py       SQLite run log; ENGINE_VERSION lives here — bump it
                       on ANY formula change
tests/test_invariants.py  the contract (see below)
```

Conventions that matter:

- **The UI never computes.** If a screen needs a number, the engine returns
  it. The one exception is display aggregation (sums for reconciliation
  lines), which must visibly tie back to engine output.
- **No client-facing jargon.** ANV, ROI, "Park (Data-Blocked)" are banned
  from screens (tests enforce no em dashes and no "strangler" in report
  copy; plain-language names are mapped at render time).
- **Feedback for every state change.** Scenario, stack, and foundation
  changes flash a banner stating before → after, because tabs reset on
  rerun and silent recomputes read as broken buttons.
- **Session state keys:** `app_phase`, `wizard_page`, `discovery_answers`,
  `discovery_provenance`, `thesis_plan`, `thesis_generated`,
  `current_scenario`, `ai_stack`, `foundation_decision`, `budget_usd_m`,
  `primary_goals`, plus one-shot flash keys.
- **Streamlit quirks encoded in comments:** element containers whose only
  content is out-of-flow get hidden (the fixed header needs its container
  forced visible); sticky can't work inside `st.html` (wrapper is exactly
  the element's height); Plotly annotations drop inline-styled spans (use
  separate annotations).

## 11. Design system & verification

**PwC Horizon theme** (`ui/theme.py`): Georgia for display numbers and
headlines, Inter for everything else; PwC flame palette (orange #D04A02 on
white, greys #2D2D2D→#F2F2F2); 8pt spacing grid; flat surfaces, 2/4px
radii; restrained hover micro-interactions (tiles lift 2px). Charts follow
the dataviz rules: the budget donut's palette passed a colorblind-safety
validator; the matrix direct-labels only funded levers with a
collision-checked placer; corner labels state what each quadrant means.

**Verification philosophy — the part that actually kept quality up:**

1. `tests/test_invariants.py` (28): each test encodes a defect class that
   actually shipped once — goal-taxonomy drift, phantom inputs, CFO-implausible
   economics (portfolio ROI band, lever concentration cap, payback bounds),
   negative-value levers consuming budget, fake-dynamic regulatory output,
   silent stack toggles, unexplained diagnostic scores, em dashes in copy.
   If one fails, a client-facing lie is back.
2. **Look at the pixels.** DOM assertions pass while the page is broken
   (the black header shipped invisible for a day). Playwright is installed:
   screenshot `localhost:8501`, read the image, then claim it works.
   A seeded harness (`streamlit run` a small script that pre-populates
   session state) renders the dashboard without clicking through the wizard.

## 12. Known limitations & the roadmap that was already agreed

- **Calibrated judgment, not client data.** Benchmarks, cost scopes, stack
  multipliers, and the size curve are sourced/reasoned constants. The next
  maturity step is loading them from engagement benchmarks and rate cards.
- **Streamlit ceiling.** CSS delivers ~80% of the premium feel; page
  transitions, drill-down side panels, and command-palette navigation need
  a real front end. The agreed V2: keep `engine/` (unchanged, tested),
  serve it via FastAPI, rebuild `ui/` in Next.js/React.
- **Planned next features, in priority order:** natural-language
  exploration of the plan ("why?", "what if my budget halves?") grounded in
  the computed plan via the existing Gemini key; per-use-case drill-down
  cards (why recommended, evidence, sensitivity); a sensitivity tornado for
  the five assumptions that most move the answer; PPTX/board-pack export.
- Single-session, no auth/RBAC, SQLite audit log beside the code — right
  for a pilot, not for multi-tenant production.
- `config/evidence.py` and `config/peer_corpus.py` are unwired roadmap
  assets (an evidence-citation gate and peer benchmark data): wire them or
  delete them.

## 13. Operations

- **Run locally:** `streamlit run app.py`. Python 3.12+ (Render pins
  3.12.9; local dev has run on 3.14).
- **Deploy:** push to `main`; Render builds from the blueprint
  (`render.yaml`). Set `GEMINI_API_KEY` in the Render dashboard (it is
  `sync: false` — never committed). **Requirements pin streamlit 1.39.0 for
  Render compatibility.**
- **Secrets:** only `GEMINI_API_KEY`. Local: `.env` (gitignored;
  `.env.template` shows the shape). Never commit a real key — a key was
  once leaked in this repo's history and had to be revoked; treat it as the
  cautionary tale it is.
- **Audit trail:** every generated report writes a row to `audit.db`
  (inputs, plan, engine + corpus versions, run id shown in the header).
  The DB is gitignored — it contains client inputs.
- **On any formula change:** bump `ENGINE_VERSION` in `storage/audit.py`,
  and add/adjust the invariant that would have caught the change's failure
  mode.

## Glossary (for non-technical readers)

| Term on screen | Meaning |
|---|---|
| Use case / lever | One specific way to apply AI (e.g. automating client onboarding) |
| Annual value | What a use case saves + earns per year once running, after the realisation haircut |
| Build cost | The one-off cost to implement a use case |
| Earns it back in | Months until cumulative value equals the build cost (value ramps up over 3 years) |
| Risk discount / plan confidence | A deduction for delivery slippage, driven by your governance maturity; confidence is its complement |
| Value score | How much this use case is worth to *your* firm (your volumes vs peer median, urgency, goal fit) — 0–100 |
| Readiness | How able your systems and data are to deliver it — 0–100 |
| Strategic bet / Quick win / Blocked / Lower priority | Fund first / fast momentum / valuable but the data foundation can't support it yet / doesn't earn a place |
| Legacy estate | The firm's ageing core systems |
| Cost-to-value ratio | Annual maintenance ÷ business value the estate still delivers; above 100% it costs more than it earns |
| Modernization | Replacing/renovating the legacy estate; "in phases" = one function at a time behind a modern access layer |
| Self-funding horizon | Months until modernization pays for itself from stopped maintenance + unlocked AI value |
| Execution scenario | How conservatively we count modelled value: 50% / 60% / 75% of it |
| AI model stack | Which class of AI models runs the program: premium hosted (Frontier), a mix (Balanced), or open-source-led (Cost-optimized) |
| Peer median | The typical mid-size firm we calibrate defaults against ($50B AUM, 400 ops staff) |
