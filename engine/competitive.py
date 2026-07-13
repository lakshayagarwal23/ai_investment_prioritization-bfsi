"""
engine/competitive.py

Sector-aware competitive positioning.
Derives the firm's defensibility from the levers it is actually funding —
no client-specific hardcoding. Defensibility per lever is declared in
config/value_pools.py; competitor sets come from the selected sector.
"""
from dataclasses import dataclass
from config.value_pools import BFSI_LEVERS, SECTOR_MF, SECTOR_INS, SECTOR_DIV


@dataclass
class CompetitiveAdvantage:
    name: str
    capability: str          # what the funded lever gives the firm
    market_norm: str         # what the sector still does today
    advantage: str
    time_to_parity: str
    defensibility: str


_SECTOR_COMPETITORS = {
    SECTOR_MF:  ["SBI MF", "ICICI Prudential AMC", "HDFC AMC", "Nippon India MF"],
    SECTOR_INS: ["LIC", "HDFC Life", "ICICI Prudential Life", "SBI Life"],
    SECTOR_DIV: ["Bajaj Finserv", "Kotak Mahindra", "ICICI Group", "SBI Group"],
}

# Market-norm and parity framing per defensibility class
_PARITY = {"high": "18-24 months", "medium": "12-18 months", "low": "6-12 months"}

_MARKET_NORMS = {
    "lever_1":  "Manual break-resolution queues; T+2 exception backlogs",
    "lever_2":  "Voice/chat execution with manual order handling",
    "lever_5":  "45-60 day onboarding with manual KYC review",
    "lever_8":  "Quarterly batch statements; no individualized servicing",
    "lever_9":  "Fragmented data estates reconciled by hand",
    "lever_11": "3-7 day manual underwriting",
    "lever_12": "10-15 day claims cycles with sampled fraud review",
    "lever_13": "Siloed product books; no unified customer view",
    "lever_14": "Branch-led onboarding with high application dropout",
}

_LEVERS_BY_ID = {spec["id"]: spec for spec in BFSI_LEVERS}


def compute_competitive_advantage_score(plan: list[dict], answers: dict) -> dict:
    """0-100 defensibility score from the levers the plan actually executes.
    High-defensibility funded levers score 30, medium 15, low 5."""
    points = {"high": 30, "medium": 15, "low": 5}
    score = 20  # base: having a sequenced, budget-constrained roadmap at all
    advantages = []

    for p in plan:
        lever = _LEVERS_BY_ID.get(p["id"])
        if not lever:
            continue
        executing = p.get("budget_approved") and p["quadrant"] in (
            "Strategic Bets", "Quick Wins / Fill-ins")
        if not executing:
            continue
        defensibility = lever.get("defensibility", "low")
        score += points[defensibility]
        if defensibility in ("high", "medium") and p["id"] in _MARKET_NORMS:
            advantages.append(CompetitiveAdvantage(
                name=lever["name"],
                capability=lever.get("benchmark", ""),
                market_norm=_MARKET_NORMS[p["id"]],
                advantage=f"Funded now while the sector norm remains: {_MARKET_NORMS[p['id']].lower()}",
                time_to_parity=_PARITY[defensibility],
                defensibility=defensibility,
            ))

    sector = answers.get("target_sector", SECTOR_MF)
    return {
        "overall_score": min(100, score),
        "advantages": advantages[:4],
        "primary_competitors": _SECTOR_COMPETITORS.get(sector, _SECTOR_COMPETITORS[SECTOR_DIV]),
    }
