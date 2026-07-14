"""
api/schemas.py — the typed contract between the engine and any front end.

Every request is validated here (never trust a client), and every response
is shaped here so the web app renders data, not guesses. The engine itself
stays untouched: this layer only validates in and serialises out.
"""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator


Scenario = Literal["conservative", "base", "aggressive"]
AiStack = Literal["Frontier", "Balanced", "Cost-optimized"]


class ReportRequest(BaseModel):
    answers: dict[str, Any] = Field(default_factory=dict)
    company_name: str = Field(default="New engagement", max_length=120)
    target_sector: str = "Mutual Funds / Asset Management"
    budget_usd_m: float = Field(default=100.0, gt=0, le=10_000)
    primary_goals: list[str] = Field(default_factory=list)
    scenario: Scenario = "base"
    ai_stack: AiStack = "Balanced"
    foundation_decision: bool = False
    existing_lever_ids: list[str] = Field(default_factory=list)

    @field_validator("existing_lever_ids")
    @classmethod
    def levers_must_exist(cls, v: list[str]) -> list[str]:
        from config.value_pools import BFSI_LEVERS
        known = {spec["id"] for spec in BFSI_LEVERS}
        unknown = [x for x in v if x not in known]
        if unknown:
            raise ValueError(f"unknown lever ids: {unknown}")
        return v

    @field_validator("primary_goals")
    @classmethod
    def goals_must_exist(cls, v: list[str]) -> list[str]:
        from config.value_pools import GOALS
        unknown = [g for g in v if g not in GOALS]
        if unknown:
            raise ValueError(f"unknown goals: {unknown}")
        return v

    @field_validator("target_sector")
    @classmethod
    def sector_must_exist(cls, v: str) -> str:
        from config.value_pools import SECTOR_MF, SECTOR_INS, SECTOR_DIV
        if v not in (SECTOR_MF, SECTOR_INS, SECTOR_DIV):
            raise ValueError(f"unknown sector: {v}")
        return v


class LeverOut(BaseModel):
    id: str
    name: str
    short_name: str
    rank: Optional[int]              # explicit priority order among funded levers
    quadrant: str
    quadrant_label: str
    anv_m: float
    impl_cost_m: float
    run_cost_m: float                # annual running cost (stack-adjusted)
    payback_months: Optional[float]
    impact: int
    feasibility: int
    priority: str
    budget_approved: bool
    already_implemented: bool
    warning: Optional[str]
    reg_risk: str
    reg_mitigations: list[str]
    cost_basis: str
    benchmark: str
    rationale: str                   # deterministic, citation-backed why


class PortfolioSummary(BaseModel):
    company_name: str
    budget_m: float
    committed_m: float
    uncommitted_m: float
    total_anv_m: float
    risk_adjusted_anv_m: float
    exec_risk_pct: int
    confidence_pct: int
    payback_months: Optional[float]
    funded_count: int
    blocked_anv_m: float
    already_covered_count: int
    funded_run_cost_m: float         # annual running costs already deducted


class RebuildComponent(BaseModel):
    component: str
    amount_m: float
    basis: str


class DiagnosticOut(BaseModel):
    verdict: str
    verdict_action: str
    deprecation_score: int
    score_math: str
    pillars: dict[str, int]
    pillar_explain: dict[str, str]
    tco: dict[str, Any]
    self_funding: dict[str, Any]
    rebuild_breakdown: list[RebuildComponent]
    guardrails: list[str]
    recommend_funding: bool


class ReportResponse(BaseModel):
    run_id: str
    engine_version: str
    assumptions_hash: str
    summary: PortfolioSummary
    levers: list[LeverOut]
    diagnostic: DiagnosticOut
    scenario: Scenario
    ai_stack: AiStack
    foundation_decision: bool
    request: ReportRequest  # echoed so any report is self-describing


class MemoResponse(BaseModel):
    generated: bool          # False = deterministic fallback (no key / failure)
    paragraphs: list[str]
    grounded_on: list[str]


class LeverInfo(BaseModel):
    id: str
    name: str
    short_name: str
    sectors: list[str]


class ConfigResponse(BaseModel):
    sectors: list[str]
    goals: list[str]
    scenarios: list[str]
    ai_stacks: dict[str, dict[str, Any]]
    questions: list[dict[str, Any]]
    levers: list[LeverInfo]
    engine_version: str


class PrefillRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=120)


class PrefillResponse(BaseModel):
    company_name: Optional[str] = None   # official name, when a source states it
    fields: dict[str, dict[str, Any]]    # question id -> {value, source_url, quote, confidence}
    searched: bool                       # False when no retrieval could run (no key)
    duration_s: float = 0.0
