"""
config/value_pools.py

Value-type classification for the portfolio view (Framework 2) and
named-quadrant decision matrix (Framework 1).

HONEST CONSTRAINT: the value-type mapping and the impact/feasibility midlines
are calibrated judgement, not validated constants — they live here so they are
tunable. Two genuinely ambiguous mappings are documented below.
"""

# ─────────────────────────────────────────────────────────────────────────────
# VALUE TYPES (mutually exclusive per use case for maths; secondary is footnote only)
# ─────────────────────────────────────────────────────────────────────────────
REVENUE      = "Revenue generation"
OPPROFIT     = "Operating-profit enhancement"
PRODUCTIVITY = "Productivity & scaling"

# Primary mapping: use-case name (matching USE_CASE_LIBRARY) → single value type.
# Ambiguous mappings flagged with comments.
VALUE_TYPE: dict[str, str] = {
    # Revenue Growth pillar
    "Trade Promotion Optimization":         OPPROFIT,
    "Sales Copilot / Next-Best-Action":     REVENUE,
    "Demand Sensing & Forecasting":         OPPROFIT,        # AMBIGUOUS: secondary = REVENUE (demand sensing improves revenue forecasting, but primary value is inventory/margin)
    "Consumer Personalization Engine":      REVENUE,
    # Margin Recovery pillar
    "Procurement AI & Supplier Intelligence": OPPROFIT,
    "Manufacturing Yield Optimization":     OPPROFIT,
    "Logistics Route & Cost Optimization":  OPPROFIT,
    "Predictive Maintenance AI":            OPPROFIT,
    # Enterprise Productivity pillar
    "Enterprise Knowledge Search":          PRODUCTIVITY,
    "Invoice & PO Extraction":              PRODUCTIVITY,
    "Field Sales Productivity Platform":    REVENUE,          # AMBIGUOUS: secondary = PRODUCTIVITY (field tool, but primary value is sales conversion)
    "Meeting & Document Intelligence":      PRODUCTIVITY,
}

# Secondary tags — used ONLY for footnotes/narrative, NEVER for maths.
SECONDARY: dict[str, str] = {
    "Demand Sensing & Forecasting":      REVENUE,
    "Field Sales Productivity Platform":  PRODUCTIVITY,
}

# Which value types each objective (pillar) maps to — for the alignment check.
MANDATE_VALUE_TYPES: dict[str, set[str]] = {
    "Revenue Growth":            {REVENUE},
    "Margin Recovery":           {OPPROFIT},
    "Enterprise Productivity":   {PRODUCTIVITY},
}

# Colours per value type (used in charts, chips, and stacked bar).
COLORS: dict[str, str] = {
    REVENUE:      "#3B6D11",   # forest green
    OPPROFIT:     "#185FA5",   # deep blue
    PRODUCTIVITY: "#BA7517",   # warm amber
}

# Short label for accessibility (colour-blind / B&W safe).
SHORT_LABEL: dict[str, str] = {
    REVENUE:      "R",
    OPPROFIT:     "O",
    PRODUCTIVITY: "P",
}

# Human-readable short names for display
DISPLAY_NAME: dict[str, str] = {
    REVENUE:      "Revenue",
    OPPROFIT:     "Operating profit",
    PRODUCTIVITY: "Productivity",
}

# ─────────────────────────────────────────────────────────────────────────────
# QUADRANT CONFIGURATION (Framework 1 — named-quadrant decision matrix)
# ─────────────────────────────────────────────────────────────────────────────
IMPACT_MID  = 70    # midline for impact axis
FEAS_MID    = 55    # midline for feasibility axis

# (high_impact, high_feas) → (quadrant_name, quadrant_action)
QUADRANT: dict[tuple[bool, bool], tuple[str, str]] = {
    (True,  True):  ("Prime candidates", "High value and ready"),
    (True,  False): ("Strategic bets",   "High value, blocked by readiness"),
    (False, True):  ("Tactical add-ons", "Lower value but easy to deploy"),
    (False, False): ("Marginal",         "Low value and high effort"),
}


def classify_quadrant(impact: float, feasibility: float) -> tuple[str, str]:
    """Return (quadrant_name, quadrant_action) for a use case."""
    return QUADRANT[(impact >= IMPACT_MID, feasibility >= FEAS_MID)]
