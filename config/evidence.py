"""
config/evidence.py

Single source of truth for peer evidence tied to each use case.

ALL entries are currently labelled "illustrative — unverified" because the
underlying AR citations have not been page-verified by a human researcher.
The `cited()` helper enforces this gate: until `verified=True` is set, no
bare claim of fact is shown to the client.

[HUMAN] To promote an entry: confirm the figure against the actual annual
report / Capital Markets Day slide, set `verified=True`, fill in
`source_locator` (e.g. "AR2024 p.47"), and remove the VERIFY tag.
"""

from __future__ import annotations

CORPUS_VERSION = "0.1.0-unverified"

# ---------------------------------------------------------------------------
# Evidence map  — keyed by the exact use-case name in USE_CASE_LIBRARY
# ---------------------------------------------------------------------------
# Schema per entry:
#   value        : str   — the stated metric (e.g. "10–20% inventory reduction")
#   verified     : bool  — True only after human page-verification
#   source_title : str   — Short citation (e.g. "Unilever AR2024")
#   source_url   : str   — URL to the public document
#   source_locator: str  — Page / section reference ("p.X" until verified)
#   as_of        : str   — Year of the disclosure
# ---------------------------------------------------------------------------

_UNVERIFIED = "illustrative — unverified"

# ---------------------------------------------------------------------------
# Alias map for company-name matching (source_title → company names).
# Used to detect when a citation would be self-referencing.
# ---------------------------------------------------------------------------
_SOURCE_ALIASES: dict[str, list[str]] = {
    "Nestlé":    ["nestle", "nestlé", "nestle s.a."],
    "P&G":       ["procter", "p&g", "procter & gamble", "procter and gamble"],
    "Unilever":  ["unilever", "hindustan unilever", "hul"],
    "Coca-Cola": ["coca-cola", "coca cola", "the coca-cola company"],
    "Reckitt":   ["reckitt", "reckitt benckiser"],
    "Mondelez":  ["mondelez", "mondelēz", "mondelez international"],
    "Colgate":   ["colgate", "colgate-palmolive"],
    "ITC":       ["itc"],
    "Marico":    ["marico"],
    "Dabur":     ["dabur"],
}

_ENTRIES: dict[str, dict] = {
    "Trade Promotion Optimization": {
        "value": "Peers report 80–180bps gross-margin expansion from trade-promo AI",
        "verified": False,
        "sources": [
            {"source_title": "Nestlé AR2024", "source_url": "https://www.nestle.com/investors/annual-report", "source_locator": "p.X — VERIFY", "as_of": "2024", "company_key": "Nestlé"},
            {"source_title": "Colgate-Palmolive AR2024", "source_url": "https://investor.colgatepalmolive.com/", "source_locator": "p.X — VERIFY", "as_of": "2024", "company_key": "Colgate"},
            {"source_title": "P&G AR2024", "source_url": "https://pginvestor.com/financial-reporting/annual-reports", "source_locator": "p.X — VERIFY", "as_of": "2024", "company_key": "P&G"},
        ],
    },
    "Sales Copilot / Next-Best-Action": {
        "value": "Peers report 5–10% uplift in field-sales conversion from AI-assisted recommendations",
        "verified": False,
        "sources": [
            {"source_title": "Unilever Capital Markets Day 2024", "source_url": "https://www.unilever.com/investors/", "source_locator": "slide X — VERIFY", "as_of": "2024", "company_key": "Unilever"},
            {"source_title": "P&G Capital Markets Day 2024", "source_url": "https://pginvestor.com/", "source_locator": "slide X — VERIFY", "as_of": "2024", "company_key": "P&G"},
        ],
    },
    "Demand Sensing & Forecasting": {
        "value": "Peers report 10–20% inventory reduction from AI demand sensing",
        "verified": False,
        "sources": [
            {"source_title": "Unilever AR2024", "source_url": "https://www.unilever.com/investors/annual-report", "source_locator": "p.X — VERIFY", "as_of": "2024", "company_key": "Unilever"},
            {"source_title": "P&G AR2024", "source_url": "https://pginvestor.com/financial-reporting/annual-reports", "source_locator": "p.X — VERIFY", "as_of": "2024", "company_key": "P&G"},
        ],
    },
    "Consumer Personalization Engine": {
        "value": "Peers report 6–12% revenue uplift from personalized digital engagement",
        "verified": False,
        "sources": [
            {"source_title": "P&G AR2024", "source_url": "https://pginvestor.com/financial-reporting/annual-reports", "source_locator": "p.X — VERIFY", "as_of": "2024", "company_key": "P&G"},
            {"source_title": "Unilever AR2024", "source_url": "https://www.unilever.com/investors/annual-report", "source_locator": "p.X — VERIFY", "as_of": "2024", "company_key": "Unilever"},
        ],
    },
    "Procurement AI & Supplier Intelligence": {
        "value": "Peers report 80–180bps gross-margin expansion from procurement AI",
        "verified": False,
        "sources": [
            {"source_title": "P&G AR2024", "source_url": "https://pginvestor.com/financial-reporting/annual-reports", "source_locator": "p.X — VERIFY", "as_of": "2024", "company_key": "P&G"},
            {"source_title": "Reckitt AR2024", "source_url": "https://www.reckitt.com/investors/", "source_locator": "p.X — VERIFY", "as_of": "2024", "company_key": "Reckitt"},
        ],
    },
    "Manufacturing Yield Optimization": {
        "value": "Peers report 1–3% yield improvement from AI quality controls",
        "verified": False,
        "sources": [
            {"source_title": "Coca-Cola AR2024", "source_url": "https://www.coca-colacompany.com/investors", "source_locator": "p.X — VERIFY", "as_of": "2024", "company_key": "Coca-Cola"},
            {"source_title": "Nestlé AR2024", "source_url": "https://www.nestle.com/investors/annual-report", "source_locator": "p.X — VERIFY", "as_of": "2024", "company_key": "Nestlé"},
        ],
    },
    "Logistics Route & Cost Optimization": {
        "value": "Peers report 5–10% logistics cost reduction from AI routing",
        "verified": False,
        "sources": [
            {"source_title": "Reckitt AR2024", "source_url": "https://www.reckitt.com/investors/", "source_locator": "p.X — VERIFY", "as_of": "2024", "company_key": "Reckitt"},
            {"source_title": "Mondelez AR2024", "source_url": "https://ir.mondelezinternational.com/", "source_locator": "p.X — VERIFY", "as_of": "2024", "company_key": "Mondelez"},
        ],
    },
    "Predictive Maintenance AI": {
        "value": "Peers report 10–25% reduction in unplanned downtime from predictive maintenance",
        "verified": False,
        "sources": [
            {"source_title": "Mondelez AR2024", "source_url": "https://ir.mondelezinternational.com/", "source_locator": "p.X — VERIFY", "as_of": "2024", "company_key": "Mondelez"},
            {"source_title": "Coca-Cola AR2024", "source_url": "https://www.coca-colacompany.com/investors", "source_locator": "p.X — VERIFY", "as_of": "2024", "company_key": "Coca-Cola"},
        ],
    },
    "Enterprise Knowledge Search": {
        "value": "Peers report 15–30% reduction in time-to-information for enterprise knowledge retrieval",
        "verified": False,
        "sources": [
            {"source_title": "Gartner Enterprise AI Survey 2024", "source_url": "https://www.gartner.com", "source_locator": "p.X — VERIFY", "as_of": "2024", "company_key": None},
        ],
    },
    "Invoice & PO Extraction": {
        "value": "Peers report 60–80% reduction in manual invoice-processing time via AI extraction",
        "verified": False,
        "sources": [
            {"source_title": "Gartner Intelligent Automation Report 2024", "source_url": "https://www.gartner.com", "source_locator": "p.X — VERIFY", "as_of": "2024", "company_key": None},
        ],
    },
    "Field Sales Productivity Platform": {
        "value": "Peers report 10–20% improvement in calls-per-day from AI-assisted field tools",
        "verified": False,
        "sources": [
            {"source_title": "Hindustan Unilever Limited AR2024", "source_url": "https://www.hul.co.in/investor-relations/", "source_locator": "p.X — VERIFY", "as_of": "2024", "company_key": "Unilever"},
            {"source_title": "P&G AR2024", "source_url": "https://pginvestor.com/financial-reporting/annual-reports", "source_locator": "p.X — VERIFY", "as_of": "2024", "company_key": "P&G"},
        ],
    },
    "Meeting & Document Intelligence": {
        "value": "Peers report 1–2 hours/week productivity saving per knowledge worker from AI meeting tools",
        "verified": False,
        "sources": [
            {"source_title": "Microsoft Work Trend Index 2024", "source_url": "https://www.microsoft.com/en-us/worklab/work-trend-index", "source_locator": "p.X — VERIFY", "as_of": "2024", "company_key": None},
        ],
    },
}


def _is_self_source(company_key: str | None, target_company: str) -> bool:
    """Check if a source's company_key refers to the same entity as the target."""
    if not company_key or not target_company:
        return False
    t = target_company.lower()
    aliases = _SOURCE_ALIASES.get(company_key, [])
    return any(al in t for al in aliases)


def get_evidence(use_case: str, target_company: str = "") -> str:
    """Return the evidence string for a use case, avoiding self-citations.

    If the primary source matches the target company, fall back to the
    next available source. This prevents e.g. citing "Nestlé AR2024"
    when the report is being generated FOR Nestlé.
    """
    entry = _ENTRIES.get(use_case)
    if not entry:
        return ""

    sources = entry.get("sources", [])
    # Pick the first source that is NOT the target company
    chosen = None
    for src in sources:
        if not _is_self_source(src.get("company_key"), target_company):
            chosen = src
            break
    # If all sources match (unlikely), just use the first one
    if not chosen:
        chosen = sources[0] if sources else None
    if not chosen:
        return ""

    if not entry.get("verified", False):
        return f"{entry['value']} [{chosen['source_title']} — {_UNVERIFIED}]"
    return f"{entry['value']} [{chosen['source_title']}, {chosen['source_locator']}]"


# Legacy static dict — kept for backward compatibility but prefer get_evidence()
USE_CASE_EVIDENCE: dict[str, str] = {
    name: get_evidence(name, "")
    for name in _ENTRIES
}


def cited(metric: dict) -> tuple[str | None, str]:
    """Return (value_str, citation_str) for a structured metric entry.

    If not verified, value is None and citation is the illustrative label.
    This function gates every figure behind human verification.
    """
    if not metric or not metric.get("verified"):
        return None, _UNVERIFIED
    return (
        str(metric["value"]),
        f'{metric["source_title"]} ({metric["source_locator"]})',
    )

