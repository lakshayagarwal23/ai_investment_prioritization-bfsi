"""
engine/competitive.py
MMIL-Specific Competitive Positioning Engine
Calculates differentiation advantage vs. LIC, HDFC Life, etc. based on AI lever selection.
"""
from dataclasses import dataclass

@dataclass
class CompetitiveLever:
    name: str
    mmil_capability: str
    competitor_capability: str
    mmil_advantage: str
    time_to_parity: str
    defensibility: str

MMIL_COMPETITIVE_LEVERS = {
    "lever_11": CompetitiveLever(
        name="Underwriting Automation (MAUDE)",
        mmil_capability="2-minute underwriting (Manulife MAUDE)",
        competitor_capability="3-7 day manual underwriting",
        mmil_advantage="Speed (3-7x faster), accuracy (fewer errors), volume (2x capacity)",
        time_to_parity="18-24 months",
        defensibility="medium",
    ),
    "lever_14": CompetitiveLever(
        name="Rural Digital Onboarding",
        mmil_capability="Offline-first app, biometric KYC, 1-2 day onboarding",
        competitor_capability="Manual KYC, 45-60 day onboarding",
        mmil_advantage="Mahindra's rural footprint, lower dropout rates, faster revenue",
        time_to_parity="12-18 months",
        defensibility="high",
    ),
    "lever_13": CompetitiveLever(
        name="Customer Data Platform (CDP)",
        mmil_capability="Unified 360-degree customer view (life + wealth + MF)",
        competitor_capability="Siloed data (insurance vs. wealth vs. MF)",
        mmil_advantage="Cross-sell, retention, personalization",
        time_to_parity="12-24 months",
        defensibility="medium",
    ),
}

def compute_competitive_advantage_score(plan: list[dict], answers: dict) -> dict:
    """
    Computes a 0-100 competitiveness score based on which defensive/offensive
    levers are currently prioritized in the strategic investment plan.
    """
    score = 0
    advantages = []
    
    # We assign points if highly defensible levers are present in the recommended plan (e.g., Strategic Bets)
    for p in plan:
        lid = p["id"]
        if lid in MMIL_COMPETITIVE_LEVERS:
            comp_lever = MMIL_COMPETITIVE_LEVERS[lid]
            advantages.append(comp_lever)
            
            # Add to score if it's being executed (Strategic Bet or Quick Win)
            if p["quadrant"] in ["Strategic Bets", "Quick Wins / Fill-ins"]:
                points = 30 if comp_lever.defensibility == "high" else 15
                score += points
                
    # Normalize score
    final_score = min(100, max(0, score + 20)) # Base score of 20 just for having a roadmap
    
    return {
        "overall_score": final_score,
        "advantages": advantages,
        "primary_competitors": ["LIC", "HDFC Life", "ICICI Prudential", "Bajaj Allianz"]
    }
