"""
api/main.py — FastAPI service around the untouched deterministic engine.

This is the product backbone described in docs/PRODUCTION_READINESS.md
Phase 1: stateless, horizontally scalable, typed at the boundary. The
Streamlit app keeps working unchanged; this serves the Next.js front end
(and anything else) the exact same numbers.

Run:  uvicorn api.main:app --reload --port 8000
Auth: set API_TOKEN to require `Authorization: Bearer <token>`; unset for
      local dev. (Interim control — SSO replaces this in production.)
"""
from __future__ import annotations

import hmac
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # production injects env vars natively

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (ConfigResponse, DiagnosticOut, LeverOut, MemoResponse,
                         PortfolioSummary, RebuildComponent, ReportRequest,
                         ReportResponse)
from observability import get_logger, setup_observability

setup_observability()
_log = get_logger("horizon.api")

QUADRANT_LABELS = {
    "Strategic Bets": "Strategic bet",
    "Quick Wins / Fill-ins": "Quick win",
    "Park (Data-Blocked)": "Blocked",
    "De-prioritize": "Lower priority",
}

app = FastAPI(
    title="AI Investment Prioritisation Engine",
    version="1.0.0",
    docs_url="/api/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


async def require_token(request: Request) -> None:
    required = os.environ.get("API_TOKEN", "")
    if not required:
        return
    supplied = request.headers.get("Authorization", "")
    if not (supplied.startswith("Bearer ")
            and hmac.compare_digest(supplied[7:], required)):
        raise HTTPException(status_code=401, detail="invalid or missing bearer token")


@app.get("/health")
async def health() -> dict:
    from storage.audit import ENGINE_VERSION
    return {"status": "ok", "engine_version": ENGINE_VERSION}


@app.get("/api/config", response_model=ConfigResponse,
         dependencies=[Depends(require_token)])
async def get_config() -> ConfigResponse:
    from config.questions import QUESTIONS
    from config.value_pools import (AI_STACKS, GOALS, SECTOR_DIV, SECTOR_INS,
                                    SECTOR_MF)
    from storage.audit import ENGINE_VERSION
    return ConfigResponse(
        sectors=[SECTOR_MF, SECTOR_INS, SECTOR_DIV],
        goals=list(GOALS),
        scenarios=["conservative", "base", "aggressive"],
        ai_stacks=AI_STACKS,
        questions=QUESTIONS,
        engine_version=ENGINE_VERSION,
    )


def _compute_response(req: ReportRequest,
                      existing_run_id: str | None = None) -> ReportResponse:
    """The whole report: plan + portfolio summary + legacy diagnostic.
    Logs a new audit row unless reconstructing an existing run by id."""
    from config.value_pools import PLATFORM_GATED_LEVERS
    from engine.legacy_diagnostic import LegacyInputs, run_diagnostic
    from engine.math_engine import (build_investment_plan,
                                    compute_execution_risk, payback_months)
    from storage.audit import ENGINE_VERSION, assumptions_hash, log_run

    answers = dict(req.answers)
    answers["target_sector"] = req.target_sector

    plan = build_investment_plan(
        answers, req.budget_usd_m, req.primary_goals,
        scenario=req.scenario, foundation_decision=req.foundation_decision,
        ai_stack=req.ai_stack)

    # Diagnostic uses the honest baseline (without the foundation) for
    # blocked value, mirroring the Streamlit foundation page.
    baseline = plan if not req.foundation_decision else build_investment_plan(
        answers, req.budget_usd_m, req.primary_goals,
        scenario=req.scenario, foundation_decision=False, ai_stack=req.ai_stack)
    blocked = [p for p in baseline
               if p["id"] in PLATFORM_GATED_LEVERS
               and p["quadrant"] == "Park (Data-Blocked)" and p["anv"] > 0]
    unlocked_anv_m = sum(p["anv"] for p in blocked) / 1e6

    def _num(key: str, default: float) -> float:
        try:
            return float(answers.get(key, default))
        except (TypeError, ValueError):
            return default

    diag = run_diagnostic(LegacyInputs(
        maintenance_cost_m=_num("S5_MAINTENANCE_COST", 6.5),
        biz_value_m=_num("S5_BIZ_VALUE", 20.0),
        silo_count=_num("S1_SILO", 5.0),
        architecture=str(answers.get("S1_ARCH", "Hybrid — partial cloud")),
        api_maturity=str(answers.get("S1_ERP", "On-prem with API layer")),
        data_ownership=0, lineage=0, dq_sla=0, reg_trace=0, change_mgmt=0,
        unlocked_anv_m=unlocked_anv_m,
        governance_score=_num("S5_GOVERNANCE_SCORE", 50.0),
    ))

    approved = [p for p in plan if p.get("budget_approved")]
    total_cost_m = sum(p["impl_cost"] for p in approved) / 1e6
    total_anv_m = sum(p["anv"] for p in approved) / 1e6
    exec_risk = compute_execution_risk(answers)
    risk_adj_m = total_anv_m * (1.0 - exec_risk)
    pb = payback_months(total_cost_m * 1e6, risk_adj_m * 1e6)
    blocked_anv_m = sum(p["anv"] for p in plan
                        if p["quadrant"] == "Park (Data-Blocked)" and p["anv"] > 0) / 1e6

    summary = PortfolioSummary(
        company_name=req.company_name,
        budget_m=req.budget_usd_m,
        committed_m=round(total_cost_m, 2),
        uncommitted_m=round(max(0.0, req.budget_usd_m - total_cost_m), 2),
        total_anv_m=round(total_anv_m, 2),
        risk_adjusted_anv_m=round(risk_adj_m, 2),
        exec_risk_pct=round(exec_risk * 100),
        confidence_pct=round((1 - exec_risk) * 100),
        payback_months=round(pb, 1) if pb < 900 else None,
        funded_count=len(approved),
        blocked_anv_m=round(blocked_anv_m, 2),
    )

    levers = [LeverOut(
        id=p["id"], name=p["name"], short_name=p.get("short_name", p["name"]),
        quadrant=p["quadrant"],
        quadrant_label=QUADRANT_LABELS.get(p["quadrant"], p["quadrant"]),
        anv_m=round(p["anv"] / 1e6, 2),
        impl_cost_m=round(p["impl_cost"] / 1e6, 2),
        payback_months=p["payback"] if p["payback"] < 900 else None,
        impact=p["impact"], feasibility=p["feasibility"], priority=p["priority"],
        budget_approved=p["budget_approved"], warning=p.get("warning"),
        reg_risk=p["reg_status"].get("risk_level", "green"),
        reg_mitigations=list(p["reg_status"].get("mitigations", [])),
        cost_basis=p.get("cost_basis", ""),
    ) for p in plan]

    est = diag.get("rebuild_estimate") or {"breakdown": []}
    diagnostic = DiagnosticOut(
        verdict=diag["verdict"], verdict_action=diag["verdict_action"],
        deprecation_score=diag["deprecation_score"], score_math=diag["score_math"],
        pillars=diag["pillars"], pillar_explain=diag["pillar_explain"],
        tco=diag["tco"], self_funding=diag["self_funding"],
        rebuild_breakdown=[RebuildComponent(**c) for c in est["breakdown"]],
        guardrails=diag["guardrails"], recommend_funding=diag["recommend_funding"],
    )

    if existing_run_id is None:
        # The request is stored with the run so any report is rebuildable
        # from its URL alone (deterministic engine + stored inputs + knobs).
        run_id = log_run(company=req.company_name, inputs=answers, plan=plan,
                         payload={"summary": summary.model_dump(),
                                  "request": req.model_dump()},
                         mode="api")
        _log.info("report computed", extra={"run_id": run_id,
                                            "company": req.company_name,
                                            "event": "api_report"})
    else:
        run_id = existing_run_id

    return ReportResponse(
        run_id=run_id, engine_version=ENGINE_VERSION,
        assumptions_hash=assumptions_hash(),
        summary=summary, levers=levers, diagnostic=diagnostic,
        scenario=req.scenario, ai_stack=req.ai_stack,
        foundation_decision=req.foundation_decision,
        request=req,
    )


@app.post("/api/report", response_model=ReportResponse,
          dependencies=[Depends(require_token)])
async def compute_report(req: ReportRequest) -> ReportResponse:
    return _compute_response(req)


@app.get("/api/runs", dependencies=[Depends(require_token)])
async def get_runs(limit: int = 25) -> list[dict]:
    """The engagements list: recent runs, newest first."""
    from storage.audit import list_runs
    return list_runs(min(max(1, limit), 100))


@app.get("/api/runs/{run_id}", response_model=ReportResponse,
         dependencies=[Depends(require_token)])
async def get_run(run_id: str) -> ReportResponse:
    """Rebuild a past report from the audit trail: stored inputs + stored
    knobs through the deterministic engine. Reports are URLs, not sessions."""
    from storage.audit import fetch_run
    row = fetch_run(run_id)
    if not row:
        raise HTTPException(status_code=404, detail="run not found")
    stored = (row.get("payload") or {}).get("request")
    if not stored:
        raise HTTPException(status_code=409,
                            detail="run predates report-by-URL; generate a new report")
    return _compute_response(ReportRequest(**stored), existing_run_id=run_id)


@app.post("/api/memo", response_model=MemoResponse,
          dependencies=[Depends(require_token)])
async def compute_memo(req: ReportRequest) -> MemoResponse:
    """Narrative memo grounded in the computed plan. Generated on demand
    (never automatically) so LLM spend is a user choice, not a side effect."""
    from engine.math_engine import build_investment_plan
    from llm.openai_client import generate_memo_paragraphs

    answers = dict(req.answers)
    answers["target_sector"] = req.target_sector
    plan = build_investment_plan(
        answers, req.budget_usd_m, req.primary_goals,
        scenario=req.scenario, foundation_decision=req.foundation_decision,
        ai_stack=req.ai_stack)
    result = generate_memo_paragraphs(req.company_name, plan, req.target_sector)
    _log.info("memo computed", extra={"company": req.company_name,
                                      "event": "api_memo",
                                      "provider": "gemini" if result["generated"] else "fallback"})
    return MemoResponse(**result)
