# Enterprise Review — AI Investment Prioritisation Platform (BFSI Edition)

**Review basis:** full read of every source file in `task1_ai_investment_engine_6.zip`, plus empirical execution of the engine and import chain. Every finding below was verified by running the code, not inferred. Findings cite the file and, where relevant, the exact line of evidence.

**Review stance:** as instructed — brutal, evidence-first, incorporating the manager's three mandatory feedback directions (fewer questions, dynamic flow, AI prefill) throughout. No ML-model recommendations; all remedies are deterministic rules, LLM reasoning, RAG, or agentic workflows.

---

## 1. Executive summary

The platform has a genuinely differentiated core thesis — *pair a deterministic, auditable financial engine with LLM narrative, and gate AI investment on legacy-stack health* — and several pieces of real engineering maturity exist in embryo (an audit log with engine versioning in `storage/audit.py`, an evidence gate in `config/evidence.py` that refuses to show unverified citations, sector-conditional questions). That thesis is exactly what Palantir/QuantumBlack-class products do, and it is the right one.

The current build, however, is **not deployable, not demonstrable, and not defensible**. Specifically:

1. **The app does not run.** `ui/dashboard.py` imports `calculate_deprecation_score` from `engine/legacy_diagnostic.py`; no such function exists (the module exports `deprecation_score` / `run_diagnostic`). `app.py` imports `ui.dashboard` at startup, so the entire application crashes with an `ImportError` before rendering a single pixel. Verified by import test.
2. **The numbers would be laughed out of a CFO's office.** On questionnaire defaults with a $100M budget, the engine reports **$204M/yr of ANV on $24M of spend — an 856% portfolio ROI — with paybacks as short as 0.4 months.** A single lever (Life Underwriting Automation) claims $84M/yr. No Fortune 100 finance function will accept a tool whose default output is 8.5x return with two-week paybacks; it destroys the credibility of every other screen.
3. **The centerpiece visual is fake-dynamic.** The Impact × Feasibility matrix positions are hardcoded per lever in `config/value_pools.py` (`base_impact`, `base_feasibility`). Verified: radically different governance/silo answers produce **identical** matrix positions. Only bubble size changes. The product's hero output does not respond to the diagnostic it just made the user complete.
4. **A live OpenAI API key is committed in `.env` and shipped inside the zip.** This is a credential leak. Revoke it today. Meanwhile the code reads `GEMINI_API_KEY`, which is absent — so **both** LLM features (prefill, memo) silently fail in the shipped configuration, while the UI displays a banner asserting "Data Pre-filled via Web Search." The product currently *lies to the user* about what it did.
5. **Identity crisis throughout.** The landing page advertises "GPT-4o Intelligence" (it uses Gemini), shows fabricated KPIs ("185% Portfolio ROI"), the competitive tab hardcodes one client (MMIL / Mahindra Manulife, "Mahindra's rural footprint") for *every* firm analysed, the repo contains an FMCG PDF, FMCG evidence corpus, a stale test suite for a completely different engine API, a zip inside the zip, a committed 815KB `audit.db`, `.venv`, and `__pycache__` directories.

**Verdict: strong concept, correct architecture instincts, pre-alpha execution.** Two focused sprints could produce a credible demo; the roadmap is in §12.

---

## 2. Product understanding

**What it is.** A Streamlit wizard (7 steps, 37–48 questions depending on sector) feeding a deterministic lever-valuation engine (`engine/math_engine.py`, 14 BFSI levers), a legacy-deprecation diagnostic, a regulatory constraint checker (IRDAI/RBI/SEBI), a competitive positioning module, and a Gemini-generated strategic memo, rendered in a 4-tab dashboard with a budget-constrained prioritisation matrix.

**Who it serves.** Consultants running AI-investment diagnostics for Indian BFSI clients; ultimately CIO/CFO/CDO audiences.

**Differentiation that is real and worth protecting:**
- Deterministic ANV math + LLM narrative separation (auditable numbers, generated prose).
- Legacy deprecation as a *gate* on AI investment ("kill-to-fund") — few competitors frame this.
- India-specific regulatory layer (IRDAI claims timelines, RBI data localisation) — genuinely rare.
- Run-level audit logging with engine/corpus versioning — the seed of enterprise reproducibility.

**What prevents adoption today:** the five failures in §1, plus everything in §5–§9.

---

## 3. Showstoppers (fix before anything else)

| # | Defect | Evidence | Impact | Fix |
|---|--------|----------|--------|-----|
| S1 | App crashes on launch | `ui/dashboard.py` line 8 imports `calculate_deprecation_score`; function absent from `engine/legacy_diagnostic.py`. Verified `ImportError`. | Product is un-demonstrable | Call `run_diagnostic(LegacyInputs(...))` and consume its dict; delete the duplicated inline math in `_tab_deprecation` |
| S2 | Live API key committed | `.env` contains a real `sk-proj-…` OpenAI key, inside a zip that has now been shared | Credential compromise; SOC2 instant-fail | **Revoke the key now.** Add `.env` to `.gitignore` (the template exists; the real file was still committed), scrub git history (`git filter-repo`), load secrets via `st.secrets` |
| S3 | Wrong env var → all LLM features dead | `llm/search_client.py` and `llm/openai_client.py` read `GEMINI_API_KEY`; `.env` defines only `OPENAI_API_KEY` | Prefill returns `{}`; memo falls back to canned paragraph — silently | Standardise on one var; **fail loudly** in the UI when the key is absent instead of pretending |
| S4 | UI asserts prefill happened when it didn't | `ui/sidebar.py` `_page_section` renders "Data Pre-filled via Web Search" unconditionally | Fabricated provenance — trust-destroying in front of a client | Render the banner only when `extract_company_data` returned non-empty; show *which fields* were filled, each with a source citation |
| S5 | Implausible economics | Verified run: $204M ANV on $24M spend; lever_11 = $84M/yr, payback 0.4 months | CFO credibility = zero | See §6 remediation: conservative defaults, ramp curves, benefit haircuts, scenario bands |
| S6 | Static prioritisation matrix | `base_impact`/`base_feasibility` are constants in `value_pools.py`; verified invariant to answers | The diagnostic doesn't diagnose | Compute feasibility per firm: start from the base and apply deterministic modifiers from S1 architecture, silo count, governance, unstructured-data readiness (rules, not ML) |
| S7 | Sector filter applies to questions but not levers | `calculate_investment_plan` iterates `BFSI_LEVERS` wholesale | A pure insurer gets "Fund Accounting & NAV Oversight" and "Trade Reconciliation" recommendations built from **default** values for questions they were never asked | Add `sectors` metadata to each lever mirroring `questions.py`; filter before scoring |
| S8 | Two contradictory deprecation models in one product | Dashboard recomputes fragmentation as `silos * 15` and tech debt as `ratio * 100`; `engine/legacy_diagnostic.py` uses anchored bands and a 3-factor fragmentation blend | Same inputs → different scores depending on which code path; indefensible under audit | One source of truth: the engine module. The dashboard renders, never computes |

---

## 4. Engineering review

**Repo hygiene.** Committed: `.venv/` (thousands of files), `__pycache__/`, `audit.db` (815KB of run data — client inputs are being committed to source control, itself a data-governance violation), `core_investment_engine_backend.zip` (a zip *inside* the repo), two large PDFs, `last_message.txt`, `debug_test.py`, `claude_engine.patch`, orphaned `build_framework.py`. `requirements.txt` is unpinned (`streamlit`, `pandas`, …) — non-reproducible builds. Fix: proper `.gitignore`, pin versions (`streamlit==1.41.*` style), move sample PDFs out of the repo.

**Dead and misleading code.**
- `tests/test_invariants.py` tests a *previous product's API* (`build_investment_plan(100, ["Revenue Growth"], discovery_answers=…)`, `complexity_score`, OpenAI mocking). Every test fails on import. A failing-by-construction test suite is worse than none: it trains the team to ignore red. Rewrite against the real API — the invariants themselves (determinism, no-silent-financials, archetype postures) are excellent ideas worth keeping.
- `generate_company_intelligence` returns a hardcoded stub.
- `math_engine.py` comment says "Explicit exception handling (no silent masking)" directly above `except Exception: anv = 0.0` — which is precisely silent masking. A lever that errors should surface as "could not be computed," not appear as a $0 lever ranked at the bottom.
- `goal_weights` are all `1.0`, so goal alignment degenerates to "count of matching goals" — the dict is decoration.
- `speed_score` is computed and never used for anything visible.
- `risk_adjusted_roi` is computed, stored, and shown nowhere in the dashboard table.
- `payback_months` returns a `999.0` sentinel that would render as "999 mo" in an executive table.
- `search_client.py` extracts `S1_EMPLOYEES` — a key that **no question uses**. Half of the prefill payload is thrown away.

**Input validation.** `st.number_input` has no `min_value`: negative AUM, negative FTEs, negative claims volumes are all accepted and flow straight into ANV math. `S5_BIZ_VALUE = 0` is guarded only by the dashboard's `max(biz_val, 0.01)` — the engine module handles it properly; the dashboard path (pre-crash) would produce a 65,000% tech-debt ratio.

**Security.**
- **XSS:** the custom firm name from `st.text_input` is interpolated raw into `st.html(f"…{st.session_state.company_name}…")` in at least four places. Entering `<img src=x onerror=…>` as a firm name executes script. Escape all user strings (`html.escape`) before `st.html`.
- No authentication, no roles, no session isolation beyond Streamlit defaults; `audit.db` is a world-readable SQLite file beside the code.
- `storage/audit.py` exists but **is never called** for actual runs — `init_db()` runs, `log_run()` is orphaned. The audit trail is a facade.

**State management.** `_search_completed` is read via `getattr(st.session_state, …)` (works, but inconsistent with the dict-style everywhere else); wizard answers are mutated in place during render, which mostly works in Streamlit but makes back-navigation state drift easy to introduce.

---

## 5. Business-logic review — lever by lever

The shared backbone (`ANV = savings + incremental revenue − run cost`, risk-adjusted ROI, payback) is sound. The per-lever instantiations are where credibility dies. Recurring defect classes, with the worst offenders:

**(a) Benefits invented from constants, not inputs.**
- `lever_2_execution`: ANV = AUM × 1.5 turnover × 3.5bps − run cost. Nothing about the *firm's* execution comes in except AUM; the questionnaire's `S2_ELECTRONIC_FLOW` (which exists precisely to size the non-electronic addressable flow) is ignored. On defaults it emits $25.6M/yr — for an insurer who does no trading.
- `lever_4_distribution`: `sales_fte = 20.0` hardcoded; each freed FTE magically raises $500M of new AUM.
- `lever_7_nav`: every input hardcoded; `S3_NAV_EXCEPTIONS` (asked in the questionnaire!) unused.
- `lever_13_cdp`: total customers = `rural customers × 5` — a fabricated multiplier on an unrelated field.
- `lever_14`: `speed_savings = target_rural * (50-2) * 50 / 50` — dimensionally meaningless arithmetic that no one can explain to a partner.

**(b) Double counting.** `lever_1` (trade recon) and `lever_12` (claims) both harvest STP-uplift savings from the same `S3_STP` baseline; `lever_5` and `lever_14` both claim onboarding FTE savings; `lever_8` and `lever_13` both claim retention uplift on overlapping books. Portfolio ANV sums all of them. An enterprise engine needs a **benefit-attribution matrix**: each value pool (an FTE pool, a churn pool, an error-cost pool) can be claimed once, with explicit splits.

**(c) No ramp, no probability, no haircut.** Every lever delivers 100% of steady-state value from month one at 65–95% automation rates. Standard consulting practice: year-1 ramp (25/60/100%), adoption probability, and a benefits-realisation haircut (McKinsey convention: 50–70% of modelled value). This alone brings the $204M headline into the defensible $60–90M band.

**(d) Questionnaire inputs collected and never used.** Verified unused in any computation: `S1_ARCH`, `S1_API_GATEWAY`, `S1_UNSTRUCTURED_DATA`, `S1_LATENCY`, `S1_ERP`, `S1_HRMS`, `S1_KTLO` (engine; dashboard-only), `S2_ELECTRONIC_FLOW`, `S2_QUOTE_TO_BIND_DAYS`, `S2_FNOL_DIGITAL_PCT`, `S3_NAV_EXCEPTIONS`, `S3_CLAIMS_FRAUD_FLAG_PCT`, `S3_REINS_BORDEREAUX_VOL`, `S4_REG_MONTHS`, `S4_UNSERVED`, `S4_VERNACULAR_SUPPORT`, `S4_AGENTIC_READINESS`, `S4_LAPSE_RATE`, `S4_TELEMATICS_MATURITY`, `S5_DATA_STEWARDSHIP`. That is **20 of 48 questions (42%) whose answers change nothing.** This is the single most important fact for the manager's Feedback 1: the questionnaire is not "too long" in the abstract — it is padded with questions the engine ignores. Either wire them in (S1 fields → feasibility modifiers; S4_LAPSE_RATE → a persistency lever; S2_FNOL_DIGITAL_PCT → claims lever penetration) or cut them.

**(e) Insurance levers with fantasy parameters.** `lever_11`: 50% volume uplift from underwriting automation, $50K average premium per application (defaults imply a book writing $2.5B of new premium annually), plus a lapse-savings term computed on *applications* rather than in-force policies. `lever_12`: fraud prevention = 2% of all claims × $5K × 50% regardless of the firm's actual `S3_CLAIMS_FRAUD_FLAG_PCT` answer.

**Remediation pattern (deterministic, per the constraint):** every lever becomes a declarative spec — inputs (question IDs), value-pool formula, penetration %, ramp curve, run cost, benchmark citation, sector list, and *feasibility modifiers* keyed to S1/S5 answers. The engine becomes a generic evaluator over specs. This also makes the lever library extensible to new sectors (FMCG, healthcare) without touching engine code — directly serving Feedback 2.

---

## 6. Output & dashboard review

- **KPI header:** "↑ 25–35% cost reduction potential" is a static string shown regardless of results. Fastest-payback tile can show the 999 sentinel. "Total ANV" sums double-counted, un-ramped benefits (§5). Add: total investment, *risk-adjusted* ANV, payback of the funded portfolio, and a confidence band — not four flavours of optimism.
- **Matrix:** static positions (S6). Also: negative-ANV bubbles get `max(12, anv*3)` so a value-destructive lever renders the same size as a modest positive one; unfunded levers at 0.3 opacity with 10px labels are illegible in a boardroom projector test.
- **Deprecation tab:** contradicts the engine module (S8); "Kill-to-Fund" callout hardcodes 60% savings while the engine uses 50%; the self-funding horizon — the best number in the whole product — is computed in `legacy_diagnostic.py` and **never displayed**. The verdict card is good copy; keep it, feed it real numbers.
- **Memo tab:** the Gemini prompt hard-requires "Indian BFSI landscape, UPI, Account Aggregator" even if the firm is global; instructs "make it sound like cutting-edge research from a 2026 industry report" — i.e., instructs the model to *simulate* authority. Replace with grounded generation: pass the actual scores and verified evidence entries, forbid claims not present in the payload, and render the run_id + engine version under the memo for auditability.
- **Risk & Competitiveness tab:** hardcoded to one client's story (MMIL, Mahindra rural footprint, named competitors LIC/HDFC Life) for every user. Either generalise (competitor set and moat statements derived from sector + selected levers) or remove until it can be client-specific. The regulatory table, by contrast, is genuinely strong — extend it to per-lever automation caps that *feed back into the ANV math* (a constraint with `impact_on_automation=0.5` should halve the automation rate used, not just print a badge).
- **Missing outputs executives actually ask for:** phased roadmap on a timeline (Now/Next/Later), ROI waterfall (baseline → savings − run costs − rebuild), scenario toggle (conservative/base/aggressive — the scenario parameter already exists in lever functions and is never exposed), sensitivity tornado on the 5 most influential assumptions, one-click board pack export (PDF/PPTX). The strongest missing artifact is an **assumptions appendix**: every constant in the engine, printed, with its benchmark source. Consultants cannot defend numbers they cannot see.

---

## 7. UX review

- **48 questions, 7 steps, no save/resume, no "skip — use peer median" affordance.** An executive abandons at step 3. Target: ≤12 manual questions (see §10).
- The wizard back button loses nothing (good), but a browser refresh loses everything (session state only). Persist drafts keyed on run_id.
- Percentage sliders force false precision ("Data lineage coverage: 35%") — executives don't know these to the point. Use 4-band choices (None / Partial / Majority / Comprehensive) mapped to numeric midpoints; keep the numeric field as an "I know the exact figure" override.
- Landing page fabricates KPIs (185% ROI) and misstates the model ("GPT-4o"). Both must go.
- No empty states, no error states (an LLM failure shows a canned paragraph with no indication), no loading skeletons beyond spinners, no accessibility pass (contrast of 10px grey-on-white labels fails WCAG AA).
- Trust indicators are absent where they matter most: nothing on any screen says *why* a number is what it is. Every figure should be hoverable → formula + inputs + benchmark source. The `evidence.py` gate was built for exactly this and is unused by the UI.

---

## 8. Enterprise readiness

Currently: no auth/RBAC, no tenant isolation, secrets in repo, XSS, unpinned deps, dead tests, no CI, no monitoring, client data committed in `audit.db`, no deletion/retention policy (GDPR/DPDP fail), single-file SQLite beside code. Streamlit itself is a prototype substrate: fine for the pilot phase, but the V3 target (multi-user, approvals, exports, versioned engagements) needs a proper backend (FastAPI + Postgres) with Streamlit or a React front end as a client. Honest sequencing in §12 — do *not* attempt SOC2 theatre now; do revoke the key, escape HTML, pin deps, and start logging runs for real, because those cost hours, not months.

---

## 9. Consulting review (would McKinsey/PwC/Deloitte use it?)

As-is: no. A partner's checklist it fails: numbers not defensible (§5), no assumptions register, no evidence citations surfaced, no scenario bands, no client-ready export, one client's competitive story hardcoded, memo generated with an instruction to *sound* authoritative rather than *be* grounded. What partners would expect and the platform is closest to delivering: the deprecation gate (unique), the regulatory overlay (unique for India), the audit/reproducibility spine (rare). Lean into those three; they are the moat. The artifacts to add, in order: assumptions appendix → scenario bands → phased roadmap → PPTX export → benchmarking ("your STP of 65% vs peer median 78%" — `peer_corpus.py` exists and is barely used).

---

## 10. Feedback 1 — Questionnaire redesign (48 → ~12 asked)

Disposition of every current question. Principle: **a question earns its place only if (a) the engine uses it, (b) the executive knows it, and (c) it cannot be inferred.**

**KEEP — manual, high-signal, engine-critical (9):**
`S1_SILO`, `S1_KTLO`, `S3_STP`, `S3_FTE_RECON`, `S4_AML_FALSE_POS`, `S5_MAINTENANCE_COST`, `S5_BIZ_VALUE`, budget, primary goals. These are internal, decision-dense, and executives can answer them (or bring an ops lead).

**KEEP — but convert to 4-band categorical (5):** `S5_DATA_OWNERSHIP`, `S5_LINEAGE`, `S5_DQ_SLA`, `S5_REGULATORY_TRACE`, `S5_CHANGE_MGMT`. Merge presentation into one "governance readiness" card with five band-selectors; also drop `S5_DATA_STEWARDSHIP` entirely (fully redundant with the five pillars — currently unused anyway).

**INFER via prefill, user validates (10):** `S1_AUM` (annual report / screener), `S1_ARCH`, `S1_API_GATEWAY`, `S1_ERP` (tech-stack signals: job postings, engineering blogs, vendor case studies — medium confidence, always shown for confirmation), `S2_ANNUAL_UNDERWRITING_APPS`, `S3_ANNUAL_CLAIMS`, `S4_LAPSE_RATE` (IRDAI public disclosures / embedded-value reports for Indian insurers — high confidence), `S2_ANALYST_COUNT`, `S2_NAMES_COVERED` (fund factsheets — medium), `S4_RURAL_CUSTOMERS` (investor presentations — low, validate).

**DERIVE from other answers — never ask (6):** `S1_UNSTRUCTURED_DATA` (from ERP + architecture), `S1_LATENCY` (from architecture), `S4_AGENTIC_READINESS` (this is an *output* of the diagnostic, not an input — asking the user to self-assess the thing the tool exists to assess is circular), `S2_ADMIN_PCT`, `S3_ANNUAL_BREAKS`, `S3_CLAIMS_PROCESSOR_FTE` (peer-median defaults scaled by AUM/claims volume, editable in an "advanced" drawer).

**MERGE (4→2):** `S2_QUOTE_TO_BIND_DAYS` + `S4_ONBOARD_DAYS` → one sector-worded "issuance/onboarding turnaround" question; `S2_UNDERWRITER_FTE` + `S4_ONBOARD_FTE` → one "manual processing FTE" question with sub-splits defaulted.

**DROP (12):** `S1_HRMS` (feeds nothing an executive cares about; change-management band covers it), `S2_PARSING_HOURS` (peer median suffices), `S2_SHORTFALL_BPS`, `S3_FAIL_EVENTS`, `S3_NAV_EXCEPTIONS`, `S3_CA_VOLUME` (all: engine ignores or hardcodes; niche sub-sector precision that defaults handle), `S2_ELECTRONIC_FLOW` (fold into STP), `S2_FNOL_DIGITAL_PCT`, `S3_CLAIMS_FRAUD_FLAG_PCT`, `S3_REINS_BORDEREAUX_VOL` (keep only if the corresponding lever formulas are wired to them; today they are not), `S4_REG_MONTHS`, `S4_UNSERVED`/`S4_VERNACULAR_SUPPORT`/`S4_TELEMATICS_MATURITY` (interesting colour, zero computation — resurrect if/when a lever consumes them).

**Net result:** ~9 mandatory manual answers + 1 governance card + validation of ~8 prefilled fields ≈ a 6–8 minute intake, from ~25 minutes today.

---

## 11. Feedback 2 — Dynamic question flow (decision tree)

The `sectors` key in `questions.py` is the right primitive; extend it into a 3-level tree, all deterministic:

**Level 0 — Firm profile (always):** company, country, sector, sub-model flags. Sub-model flags are yes/no gates the current design lacks: *Do you trade on your own book?* (gates S2 execution & recon levers), *Do you have a unit-linked/variable book?* (gates NAV lever), *Do you write motor/P&C?* (gates telematics), *Do you cede to reinsurers?* (gates bordereaux).
**Level 1 — Sector branch:** the existing S1–S5 sections, filtered by sector **and** sub-model flags. A pure life insurer with no ULIP book sees zero capital-markets questions (today `S3_NAV_EXCEPTIONS` shows for all insurers with a "skip if" note in help text — the tree should skip it, not the user).
**Level 2 — Answer-conditional follow-ups:** ask `S5_MAINTENANCE_COST`/`S5_BIZ_VALUE` detail *only if* `S1_KTLO > 65%` or `S1_ERP = legacy monolith` (otherwise the deprecation verdict is Hold and the detail is wasted time); ask fraud-flag detail only if claims volume > threshold; ask governance pillars individually only if the one-line governance band answer is "Partial" or worse.
**Implementation:** add `visible_when: {question_id: predicate}` to each question dict; the wizard evaluates predicates against `discovery_answers` on each render. ~30 lines of code, no framework change. Crucially, **levers must carry the same gates** (fixes S7): the tree that hides a question also hides its lever.

---

## 12. Feedback 3 — AI prefill architecture

Current state: one Gemini-with-Google-Search call extracting 2 fields (one of which no question uses), no citations, no confidence, silently failing, with a UI that claims success regardless. Target architecture (all LLM/RAG/rules — no ML):

1. **Entity resolution.** Input: name, industry, country, website, optional ticker. One grounded search → canonical name, listed/unlisted, regulator (IRDAI/SEBI/RBI), sub-sector. Cache by canonical name (30-day TTL).
2. **Document retrieval, tiered by reliability:** Tier A (regulatory filings, annual reports, IRDAI/AMFI public disclosures — India-specific gold mine: solvency ratios, persistency/lapse, claims settlement ratios, AUM are *published*), Tier B (investor presentations, earnings transcripts), Tier C (press, LinkedIn, job postings — tech-stack inference only).
3. **Field extraction with provenance.** Per questionnaire field: extraction prompt returns `{value, source_url, quote_span, as_of, confidence}`. A value with no quotable source is discarded — this is the same gate `evidence.py` already encodes; reuse it.
4. **Confidence routing:** High (Tier A, exact figure) → auto-fill, green chip with citation, editable. Medium (Tier B/C or derived) → pre-filled but flagged "please verify," amber chip. Low/absent → question asked manually, or peer-median default with a grey "industry median" chip. The three chip states replace today's blanket false banner and directly implement the manager's high/medium/low workflow.
5. **Hallucination prevention:** temperature 0, JSON-schema-validated output (pydantic is already a dependency — use it), numeric range guards (AUM within [0.1, 5000] $B; percentages [0,100]), source-quote required, and a rule that prefill may *never* overwrite a value the user has manually edited.
6. **Cost/failure handling:** cache per company; batch fields per document rather than per-field calls; on any failure, degrade to manual with an honest notice — never a fake success banner.
7. **Audit:** every prefilled value logs `{field, value, source, confidence, model, timestamp}` into the run row — turning prefill from a liability into an enterprise feature ("every number traceable to a public source").

---

## 13. Top prioritized improvements

P0 = blocks any demo; P1 = blocks a credible client pilot; P2 = blocks enterprise sale. Effort: S <1 day, M ≤1 week, L multi-week.

| # | P | Improvement | Effort |
|---|---|------------|--------|
| 1 | P0 | Revoke the leaked OpenAI key; scrub git history; move secrets to `st.secrets` | S |
| 2 | P0 | Fix the `calculate_deprecation_score` import crash by consuming `run_diagnostic` | S |
| 3 | P0 | Standardise the LLM env var; surface missing-key state honestly in UI | S |
| 4 | P0 | Remove the unconditional "pre-filled via web search" banner; show per-field chips | S |
| 5 | P0 | Escape all user strings before `st.html` (XSS) | S |
| 6 | P0 | Delete `.venv`, `__pycache__`, `audit.db`, inner zip from repo; pin `requirements.txt` | S |
| 7 | P0 | Remove fabricated landing KPIs and "GPT-4o" claim | S |
| 8 | P1 | Single deprecation source of truth; render engine outputs incl. self-funding horizon | M |
| 9 | P1 | Sector + sub-model gating of levers (fixes insurer-gets-NAV-lever) | M |
| 10 | P1 | Benefit haircut + 3-year ramp + adoption probability on every lever | M |
| 11 | P1 | Benefit-attribution matrix to kill double counting | M |
| 12 | P1 | Dynamic feasibility: base score ± deterministic modifiers from S1/S5 answers | M |
| 13 | P1 | Wire the 20 unused questions into formulas or cut them (per §10) | M |
| 14 | P1 | Rewrite lever_11/13/14 economics with defensible parameters and citations | M |
| 15 | P1 | Expose the existing conservative/base/aggressive scenarios as a UI toggle | S |
| 16 | P1 | Questionnaire reduction to ~12 asked questions (per §10) | M |
| 17 | P1 | `visible_when` predicate engine for the decision tree (per §11) | M |
| 18 | P1 | Prefill v2: tiered retrieval, per-field provenance, confidence routing (per §12) | L |
| 19 | P1 | Assumptions appendix screen: every constant, value, and benchmark source | M |
| 20 | P1 | Actually call `log_run()`; show run_id + engine version on the dashboard | S |
| 21 | P1 | Rewrite tests against the real API; add engine golden-file tests; CI | M |
| 22 | P1 | Input validation: min/max on all numerics; guard `S5_BIZ_VALUE=0` in one place | S |
| 23 | P1 | Grounded memo: pass scores + verified evidence; forbid unsupported claims; drop "sound like 2026 research" | M |
| 24 | P1 | Generalise or remove the MMIL-hardcoded competitive tab | M |
| 25 | P1 | Surface `risk_adjusted_roi` and fix the 999-payback sentinel display | S |
| 26 | P2 | Regulatory constraints feed automation caps into ANV math | M |
| 27 | P2 | Peer benchmarking panel from `peer_corpus.py` ("you vs peer median") | M |
| 28 | P2 | ROI waterfall + phased Now/Next/Later roadmap visual | M |
| 29 | P2 | Sensitivity tornado on top-5 assumptions | M |
| 30 | P2 | PPTX/PDF board-pack export (python-pptx over deterministic templates) | L |
| 31 | P2 | Save/resume engagements; multi-run comparison per client | L |
| 32 | P2 | Declarative lever-spec format → multi-industry libraries (FMCG next, reusing your existing FMCG corpus) | L |
| 33 | P2 | AuthN/RBAC, tenant isolation, Postgres, retention policy (DPDP/GDPR) | L |
| 34 | P2 | Human-in-the-loop verification workflow for `evidence.py` (the gate exists; build the review queue) | M |
| 35 | P2 | Monitoring: LLM failure rates, prefill hit rates, run analytics | M |

---

## 14. Final scorecard

| Dimension | Score /10 | One-line justification |
|---|---|---|
| Business value (concept) | 8 | Deprecation-gated AI investment + India regulatory overlay is a real wedge |
| Business logic (as built) | 2 | 856% default ROI, double counting, 42% of inputs unused |
| Engineering | 2 | App doesn't launch; leaked key; dead tests; committed venv/db |
| UX | 4 | Coherent visual language; but 48 questions, false banners, fake landing KPIs |
| AI workflow | 3 | Right pattern (deterministic + LLM), wrong execution (ungrounded, silently failing) |
| Consulting quality | 3 | No assumptions register, no citations surfaced, no export |
| Enterprise readiness | 1 | No auth, no isolation, secrets in repo |
| Innovation | 7 | Kill-to-fund, evidence gate, audit spine — keep these |

**Final verdict:** the strategy is right and rarer than the team may realise; the execution is pre-alpha. Fix the seven P0 items this week (all are under a day each), spend two sprints on P1 — economics credibility and the manager's three feedbacks — and this becomes a demoable, defensible consulting asset. Ship nothing to a client before items 1–14 are done.
