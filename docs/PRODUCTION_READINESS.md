# Production-Readiness Assessment — AI Investment Prioritisation Engine

**Scope:** what it takes to move this system from its current state (a
polished single-session pilot/demonstrator) to full-scale production — a
multi-user, client-facing product operated under a firm's brand, with
client data flowing through it. Each gap states *why it matters*, not just
that it exists.

**Assessed at:** engine 5.1.0, commit `cd2e506`, 28/28 invariants passing.

---

## 1. Executive summary

The system's **analytical core is production-grade in design**: a
deterministic, fully-tested engine cleanly separated from the UI, an
assumptions register, versioned audit logging, and explainability as a
contract. What surrounds that core is **pilot-grade by construction**:
single-session Streamlit, no authentication, file-based storage, no
monitoring, no CI, and LLM calls without operational guardrails.

The honest one-line verdict: **the model is ready for clients in the room;
the platform is not ready for clients on the internet.**

| Dimension | Readiness | Blocking for production? |
|---|---|---|
| Analytical engine & explainability | ● ● ● ● ○ strong | No |
| Test discipline (invariants) | ● ● ● ● ○ strong | No |
| Frontend architecture | ● ● ○ ○ ○ pilot | Yes, for premium multi-user product |
| Security & access control | ● ○ ○ ○ ○ absent | **Yes** |
| Data persistence & privacy | ● ○ ○ ○ ○ pilot | **Yes** |
| LLM operations & safety | ● ● ○ ○ ○ partial | **Yes** |
| Reliability / observability / CI-CD | ● ○ ○ ○ ○ absent | **Yes** |
| Model governance (assumptions lifecycle) | ● ● ○ ○ ○ partial | Yes, for a Big-4 context |
| Product completeness (engagements, exports) | ● ● ○ ○ ○ partial | Yes, commercially |

---

## 2. What is already production-shaped (protect these)

1. **Engine/UI separation.** `engine/` imports no Streamlit and is pure and
   deterministic. This is the single most valuable property in the
   codebase: it means the entire V2 platform can be built around the
   existing model with zero rework of the math.
2. **The invariant test suite.** 28 tests, each encoding a defect class
   that actually shipped once (goal-taxonomy drift, phantom inputs,
   implausible economics, silent regulatory output, budget indiscipline).
   This is a regression fence most prototypes never have.
3. **Traceability as a product feature.** Assumptions register, cost-basis
   lines, score arithmetic on screen, per-run audit rows with engine
   version. This is exactly what an enterprise risk function will ask for —
   it needs operationalising (see §5), not inventing.
4. **Honest degradation.** No API key → no fake prefill; compute failure →
   visible "could not be computed", never a silent zero.

---

## 3. Gap analysis

### 3.1 Architecture & scalability — the Streamlit ceiling

**Current:** one Python process renders UI and computes; all state lives in
`st.session_state` (lost on refresh); every interaction reruns the script
top-to-bottom; the whole app shares one event loop.

**Why it blocks production:**
- **No horizontal scale.** Session state is process-local; a load balancer
  breaks the app unless sessions are sticky, and even then one heavy rerun
  degrades every user on the process.
- **No state durability.** A browser refresh mid-wizard destroys 15 minutes
  of executive input — unacceptable for paying clients.
- **Interaction ceiling.** Page transitions, drill-down panels,真 multi-tab
  state are not achievable; we already hit this wall (documented Streamlit
  quirks in HANDOVER §10).

**Required:**
- Split into **FastAPI service** (wraps `engine/`, stateless, horizontally
  scalable) + **Next.js/React front end**. The engine needs an API schema
  (Pydantic models for answers/plan — pydantic is already a dependency).
- Server-side engagement state in Postgres (see §3.3), so any device can
  resume any engagement.
- Effort: the engine wrap is days; the front end is the bulk (4–8 weeks for
  parity with the current five tabs, done properly with a design system).

### 3.2 Security & access control — currently absent by design

**Current:** no authentication, no authorisation, no tenant model; anyone
with the URL sees the app; `audit.db` sits beside the code readable by the
process; the only secret is handled correctly (env var, never committed —
after one historical leak that was revoked).

**Why it blocks production:** the product ingests **confidential client
financials** (maintenance spend, headcounts, budgets). Without identity and
isolation there is no lawful or contractual basis to run it for real firms.

**Required:**
- **SSO** (OIDC/SAML — for a PwC context, Azure AD) + role model
  (consultant, engagement lead, client-viewer, admin).
- **Tenant isolation** at the data layer: every row keyed by engagement +
  tenant; row-level checks in the API, not the UI.
- **Transport & headers:** TLS everywhere (Render provides), CSP, secure
  cookies, CSRF on state-changing endpoints once there's an API.
- **Input hardening carried over:** the XSS-escaping discipline already in
  the UI must become API-side validation (Pydantic) so no client can be
  trusted.
- **Dependency & secret hygiene:** Dependabot/`pip-audit` in CI; secret
  scanning on the repo (a leak already happened once in this project's
  history — the control should be automated, not remembered).
- **Pen test** before any external client faces it.

### 3.3 Data persistence & privacy — SQLite is the pilot talking

**Current:** `audit.db` (SQLite, gitignored) stores full client inputs and
plans per run; no encryption at rest beyond the disk's; no retention or
deletion capability; no backup story; wizard state is session-only.

**Why it blocks production:**
- **India DPDP Act / client contracts** require deletion on request,
  retention limits, and knowing where data lives. A single SQLite file with
  no schema for tenancy or deletion cannot satisfy that.
- SQLite serialises writers — fine for one consultant, not for a fleet.

**Required:**
- **Postgres** with a real schema: tenants, users, engagements, runs
  (inputs JSONB, plan JSONB, engine_version), decisions. The current
  `log_run` columns map over almost 1:1.
- Encryption at rest, automated backups + restore drill, PITR.
- **Retention & deletion:** per-tenant retention policy, hard-delete
  endpoint, and an access log of who viewed which engagement (the audit
  trail must cover reads, not only writes).
- Draft persistence: wizard answers saved server-side per engagement
  (resume on any device) — also fixes the refresh-loses-everything defect.

### 3.4 LLM operations & safety — fenced, but not operated

**Current:** two well-fenced uses (grounded prefill; plan-grounded memo).
No quotas, no cost tracking, no timeouts/retries policy, no output
moderation, and — the sharpest edge — **the prefill pipeline feeds
web-retrieved text into an extraction prompt**, and its Tier-2/3 fallback
fetches arbitrary URLs surfaced by search.

**Why it blocks production:**
- **Prompt injection via retrieved pages:** a hostile or SEO-spam page
  about a client firm could instruct the extractor. The structured-output
  schema + "omit if unsourced" rule limits blast radius (values must carry
  a URL + quote and pass range guards), but the failure mode ("plausible
  wrong number with a real-looking citation") lands in front of a client
  who then clicks "keep".
- **SSRF surface:** `_fetch_page` will GET URLs from search results.
  In a VPC this must not be able to reach internal addresses.
- **Cost & availability:** every wizard run may spend LLM tokens with no
  budget alarms; Gemini outage currently degrades gracefully in UX but
  invisibly to operators.

**Required:**
- Allowlist/denylist + IP-range blocking for outbound fetches (deny
  RFC-1918, metadata endpoints); fetch through a proxy with logging.
- Treat retrieved text as untrusted: keep the extraction model tool-less
  (already true), add source-domain tiering (regulator/exchange domains
  auto-High, everything else capped at Med), and require **two independent
  sources for High confidence** on numeric prefills.
- Per-tenant LLM budgets, request timeouts, retry policy, and cost
  dashboards; cache prefill results per firm per day (a per-process dict
  cache exists; it must move to Redis/DB with TTL).
- Vendor posture: DPA with Google, region pinning for inference if client
  contracts demand India residency, and a documented "what leaves the
  boundary" data-flow (today: firm name + retrieved public text + computed
  plan summaries; **no client questionnaire financials are sent to the LLM
  for prefill, and the memo sends plan-derived aggregates** — write this
  down formally, clients will ask).

### 3.5 Reliability, observability, CI/CD — nothing exists yet

**Current:** manual `pytest` locally; deploy = push to `main`, Render
builds; no health checks beyond the platform default; no logs beyond
stdout; no error tracking; no staging; local dev on Streamlit 1.41 vs
production pin 1.39 (a real drift that already bit once).

**Required (why obvious):**
- **CI (GitHub Actions):** pytest + ruff/format + `pip-audit` on every PR;
  the invariant suite is fast (<1s) so there is no excuse for red main.
- **Environments:** dev → staging → prod, with staging seeded by the
  existing harness; pin one Python/Streamlit version across all of them.
- **Observability:** structured logs (run_id as correlation id — it already
  exists), Sentry for exceptions, metrics (runs/day, LLM spend, p95 compute
  time), uptime alerting.
- **Release discipline:** the "bump ENGINE_VERSION on formula change" rule
  should be enforced by a CI check (formula files changed ⇒ version bumped
  ⇒ CHANGELOG entry), because plans must be reproducible per version — an
  auditor will ask "which engine produced this number for this client".

### 3.6 Model governance — the Big-4-specific gap

**Current:** constants are visible and cited, but they are **calibrated
judgment**, maintained by editing Python. There is no owner, review cycle,
or client-level override workflow.

**Why it matters:** in a professional-services context this tool produces
numbers partners defend to boards. That makes it a *model* in the
model-risk-management sense, and it will need: an owner for the assumption
set, a documented refresh cadence for benchmarks (they cite 2025–26
sources that will age), sign-off on changes, and reproducibility (engine
version + constants snapshot per run — the audit row already stores the
version; it should store the constants hash too).

**Required:**
- Move `CONSTANTS`/lever specs to versioned data (DB or YAML) with an
  editorial workflow; per-engagement overrides (e.g. a real vendor quote
  replacing a cost scope) stored on the engagement, not by editing global
  config — the diagnostic already supports a client-provided rebuild cost,
  which is the pattern to generalise.
- A calibration backlog: replace judgment constants with engagement
  benchmarks as they accumulate (the intended flywheel).

### 3.7 Product completeness — what "full scale" commercially implies

Missing capabilities that clients/consultants will ask for in week one:

- **Engagements as first-class objects:** create, name, resume, duplicate,
  compare two runs of the same client (pre/post-workshop).
- **Exports:** board-pack PPTX/PDF of the five tabs — the artifact
  partners actually circulate. (Highest-value single feature on the list.)
- **Collaboration:** share a read-only client view; comments per section.
- **What-if exploration:** the agreed roadmap items — natural-language
  Q&A grounded in the computed plan, per-use-case drill-downs, sensitivity
  tornado. These deepen trust and are cheap relative to the platform work.
- **Accessibility & i18n:** WCAG AA pass (contrast is mostly there; needs a
  proper audit), keyboard navigation; currency/locale if used outside India.

### 3.8 Testing gaps (beyond the invariants)

- **UI E2E in CI:** Playwright is already used ad hoc; codify the seeded
  harness + screenshot flows into CI with visual snapshots (the invisible-
  header incident is the argument: DOM green, pixels broken).
- **Load/perf:** engine compute is trivially fast; the risks are LLM
  latency in the wizard and Streamlit/py process saturation — load-test the
  API once it exists, and set an SLO (e.g. p95 plan compute < 500ms,
  wizard prefill < 20s with progress).
- **Security tests:** authz matrix tests per role/tenant; SSRF/injection
  suites for the retrieval pipeline.

---

## 4. Phased plan (what to do, in what order, and why this order)

**Phase 0 — Harden the pilot (1–2 weeks, no architecture change).**
CI with tests+lint+pip-audit; pin runtime versions everywhere; Sentry +
structured logging; secret scanning; SSRF guards + retrieval domain
tiering; LLM timeouts/budget alarm; password-gate or IP-allowlist the
Render app so it stops being world-readable. *Why first:* cheap, removes
the worst exposures while the platform is built.

**Phase 1 — The platform (6–10 weeks).**
FastAPI service around the untouched engine (Pydantic schemas, tenancy,
authn via SSO); Postgres with engagements/runs/retention; Next.js front end
to parity with the five tabs + wizard, including draft persistence and the
premium interaction layer Streamlit cannot deliver. Streamlit app remains
as the internal/staging harness. *Why:* every remaining gap (scale, auth,
durability, UX ceiling) resolves through this one move; the engine
separation makes it a bounded rewrite of the presentation layer only.

**Phase 2 — Enterprise & commercial (4–8 weeks, parallelisable).**
PPTX/PDF export; engagement compare; NL exploration + sensitivity tornado;
model-governance workflow (versioned assumptions, overrides, constants
hash per run); pen test; DPDP compliance review + retention automation;
WCAG audit. *Why:* these convert a working platform into a sellable one.

**Team shape:** 1 full-stack (Next.js/FastAPI) + 1 backend/infra + the
existing engine owner part-time + design support in Phase 1; add a security
review externally. Total to production: roughly **3–4 months** calendar
with that team, dominated by Phase 1 front-end work.

---

## 5. Risk register (top 6)

| # | Risk | Likelihood | Impact | Mitigation (section) |
|---|---|---|---|---|
| 1 | Client data exposure (no auth, file DB) | High if externally shared today | Severe — contractual/regulatory | §3.2, §3.3; Phase 0 gate access now |
| 2 | Prompt-injected/wrong prefill accepted by user | Medium | High — wrong numbers with citations | §3.4 two-source rule, domain tiering |
| 3 | Assumptions age silently (2025–26 benchmarks) | Certain over time | Medium — credibility erosion | §3.6 ownership + refresh cadence |
| 4 | Version drift (local 1.41 vs prod 1.39) ships an env-specific bug | Medium | Medium | §3.5 pin + CI on the prod version |
| 5 | Engine change without version bump breaks reproducibility | Medium | High in audit context | §3.5 CI enforcement |
| 6 | LLM vendor outage/cost spike mid-engagement | Low/Medium | Medium — degraded UX, surprise bills | §3.4 budgets, timeouts, cached prefill |

---

## 6. Bottom line

Nothing here says "rebuild." The deterministic engine, the invariant
discipline, and the traceability contract are exactly what a production
system needs at its core — they are the hard part, and they are done. The
work to full scale is **wrapping that core in a real platform**: identity,
tenancy, durable storage, an API, a front end without Streamlit's
ceiling, operational guardrails on the LLM edges, and a governance loop for
the assumptions. Phase 0 is a week of hygiene that should start
immediately; Phase 1 is the decisive investment; Phase 2 makes it a
product people pay for.
