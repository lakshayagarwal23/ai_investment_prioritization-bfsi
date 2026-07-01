"""
docs/build_framework.py

Generates two framework diagrams for the AI Investment Engine:

  1. framework_exec.{png,svg}  — one-page executive view (for the manager).
  2. framework.{png,svg}       — full variable-level framework, showing
                                  every intake input, every engine modifier,
                                  every synthesis step and every report section.

Outputs land in the same directory.  Re-run after any engine change to keep
the framework documentation in sync with the implementation.

Layout strategy
---------------
Top-to-bottom flow with each "layer" of the architecture rendered as one
horizontal band.  Orthogonal edge routing + explicit same-rank groups stop
Graphviz from producing spaghetti.  Colour tokens match ui/theme.py so the
slide matches the product.
"""

from graphviz import Digraph
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ─── Brand palette (mirrors ui/theme.py) ────────────────────────────────────
BRAND, BRAND_DEEP = "#D04A02", "#A63A01"
INK_900, INK_700, INK_500, INK_300, INK_150, INK_50 = (
    "#11161C", "#2E353D", "#6B7480", "#C6CCD3", "#EDF0F3", "#FAFBFC"
)
GREEN, AMBER, RED, BLUE, VIOLET = "#1B9C6B", "#E8A317", "#D0342C", "#1F6FEB", "#6C5CE7"

# (fill, border, font, cluster-bg, cluster-border)
TINT = {
    "intake": ("#FFF1E6", BRAND,   INK_900, "#FFF7EE", BRAND),
    "parse":  ("#F4F6F8", INK_500, INK_900, "#FAFBFC", INK_300),
    "score":  ("#FFF7DF", AMBER,   INK_900, "#FFFBEE", AMBER),
    "lever":  ("#E6F6EE", GREEN,   INK_900, "#F1FBF6", GREEN),
    "syn":    ("#EAF1FF", BLUE,    INK_900, "#F3F7FF", BLUE),
    "llm":    ("#F2EEFC", VIOLET,  INK_900, "#F8F6FE", VIOLET),
    "out":    (INK_900,   BRAND,   "#FFFFFF", INK_700, BRAND),
}
FONT = "Helvetica"


def _node(g, nid, label, tint_key, shape="box", width="2.0"):
    fill, border, fg, *_ = TINT[tint_key]
    g.node(
        nid, label, shape=shape, style="filled,rounded",
        fillcolor=fill, color=border, fontcolor=fg,
        fontname=FONT, fontsize="10",
        width=width, height="0.55", margin="0.10,0.06",
        penwidth="1.3",
    )


def _cluster(parent, cid, label, tint_key):
    _, _, _, cbg, cbr = TINT[tint_key]
    fc = "white" if tint_key == "out" else INK_700
    c = parent.subgraph(name=f"cluster_{cid}")
    return c, cbg, cbr, fc


def _style_root(g, rankdir="TB", nodesep="0.22", ranksep="0.55"):
    g.attr(
        rankdir=rankdir, splines="ortho",
        nodesep=nodesep, ranksep=ranksep,
        bgcolor="white", fontname=FONT, pad="0.4", newrank="true",
    )
    g.attr("node", fontname=FONT, fontsize="10")
    g.attr("edge", fontname=FONT, fontsize="9", color=INK_300,
           arrowsize="0.65", penwidth="1.0")


# ═══════════════════════════════════════════════════════════════════════════
# 1. EXECUTIVE ONE-PAGER  (for the manager) — 4 columns, LR
# ═══════════════════════════════════════════════════════════════════════════
def build_executive() -> Digraph:
    g = Digraph("framework_exec", format="png")
    _style_root(g, rankdir="LR", nodesep="0.30", ranksep="0.95")
    g.attr(label=(
        "AI Investment Engine — Decision Framework\n"
        "PwC FMCG / CPG Strategic Capital Allocation"
    ), labelloc="t", labeljust="l", fontsize="18", fontcolor=INK_900)

    with g.subgraph(name="cluster_in") as c:
        _, _, _, cbg, cbr = TINT["intake"]
        c.attr(label="1 · INTAKE\nClient Discovery (16 inputs)",
               style="rounded,filled", fillcolor=cbg, color=cbr,
               fontcolor=BRAND_DEEP, fontname=FONT, fontsize="12", penwidth="1.4")
        _node(c, "I1", "Strategic Mandate (Q1.1–Q1.5)", "intake")
        _node(c, "I2", "Operational Baselines (Q2.1–Q2.4)", "intake")
        _node(c, "I3", "Data & Infrastructure (Q3.1–Q3.3)", "intake")
        _node(c, "I4", "Execution & Governance (Q4.1–Q4.3)", "intake")
        _node(c, "I5", "Investment Scope (Budget · Timeline)", "intake")

    with g.subgraph(name="cluster_en") as c:
        _, _, _, cbg, cbr = TINT["syn"]
        c.attr(label="2 · DETERMINISTIC ENGINE\nmath_engine.py — rules-based, traceable",
               style="rounded,filled", fillcolor=cbg, color=cbr,
               fontcolor=BLUE, fontname=FONT, fontsize="12", penwidth="1.4")
        _node(c, "E1", "Complexity Score   (Q3.1·Q3.2·Q2.1)", "score", width="2.6")
        _node(c, "E2", "Risk Score   (Q4.1·Q1.4·Q3.3)", "score", width="2.6")
        _node(c, "E3", "Cost Overlays\nSI inflation (Q4.3) · Compliance (Q4.2)", "score", width="2.6")
        _node(c, "E4", "Value at Stake\nbaseline × peer-evidenced band", "lever", width="2.6")
        _node(c, "E5", "Realisation Factor\nmax(0.45, 1 − 0.35·R − 0.20·C)", "syn", width="2.6")
        _node(c, "E6", "Phased Allocation\nFoundation → Scale → Expand", "syn", width="2.6")
        _node(c, "E7", "Financials\nROI · NPV · Payback · Confidence", "syn", width="2.6")

    with g.subgraph(name="cluster_ll") as c:
        _, _, _, cbg, cbr = TINT["llm"]
        c.attr(label="3 · NARRATIVE LAYER\nGPT-4o, grounded",
               style="rounded,filled", fillcolor=cbg, color=cbr,
               fontcolor="#3D3187", fontname=FONT, fontsize="12", penwidth="1.4")
        _node(c, "L1", "GPT-4o thesis + benchmarks", "llm", width="2.4")
        _node(c, "L2", "_ground_decision()\noverrides headline with engine", "llm", width="2.4")
        _node(c, "L3", "_reconcile_with_engine()\nblocks contradictions", "llm", width="2.4")

    with g.subgraph(name="cluster_op") as c:
        _, _, _, cbg, cbr = TINT["out"]
        c.attr(label="4 · BOARD-READY REPORT\n10 interactive sections, PDF export",
               style="rounded,filled", fillcolor=cbg, color=cbr,
               fontcolor="white", fontname=FONT, fontsize="12", penwidth="1.4")
        for nid, lbl in [
            ("O1", "Capital Allocation Decision"),
            ("O2", "Investment Roadmap (phases · gates)"),
            ("O3", "Strategic AI Investment Prioritisation"),
            ("O4", "Use-Case Prioritisation Matrix"),
            ("O5", "Investment Ledger + value-at-stake"),
            ("O6", "Capital Allocation by Phase"),
            ("O7", "AI Maturity Assessment"),
            ("O8", "Competitive Benchmarking"),
            ("O9", "Risk Heat Map"),
            ("O10", "Scenario Financial Model"),
        ]:
            _node(c, nid, lbl, "out", width="2.4")

    # Cross-lane wires (kept sparse for legibility)
    for s in ("I1", "I2", "I3", "I4", "I5"):
        g.edge(s, "E1", color=INK_300)
        g.edge(s, "E4", color=INK_300)
    g.edge("E1", "E5"); g.edge("E2", "E5"); g.edge("E4", "E5")
    g.edge("E1", "E6"); g.edge("E3", "E6"); g.edge("E5", "E6")
    g.edge("E5", "E7"); g.edge("E6", "E7")

    for s in ("E6", "E7", "E4"):
        g.edge(s, "L1", color=VIOLET, style="dashed")
    g.edge("L1", "L2", color=VIOLET); g.edge("L2", "L3", color=VIOLET)
    g.edge("E7", "L2", color=BRAND, penwidth="1.8", label="anchors numbers",
           fontcolor=BRAND_DEEP)
    g.edge("E6", "L3", color=BRAND, penwidth="1.8")

    g.edge("L3", "O1"); g.edge("L3", "O3"); g.edge("L3", "O8"); g.edge("L3", "O9")
    g.edge("E6", "O2", color=BRAND); g.edge("E6", "O5", color=BRAND)
    g.edge("E6", "O6", color=BRAND)
    g.edge("E7", "O1", color=BLUE); g.edge("E7", "O4", color=BLUE)
    g.edge("E7", "O10", color=BLUE); g.edge("E1", "O7", color=BLUE)
    g.edge("E4", "O5", color=GREEN)

    return g


# ═══════════════════════════════════════════════════════════════════════════
# 2. DETAILED VARIABLE-LEVEL FRAMEWORK  — TB rows, ortho splines
# ═══════════════════════════════════════════════════════════════════════════
def build_detailed() -> Digraph:
    g = Digraph("framework", format="png")
    _style_root(g, rankdir="TB", nodesep="0.18", ranksep="0.85")
    g.attr(label=(
        "AI Investment Engine — Variable-Level Framework\n"
        "Every input → every transformation → every output.   "
        "Solid arrow = primary flow.   Dashed = modifier influence."
    ), labelloc="t", labeljust="l", fontsize="16", fontcolor=INK_900)

    # ── ROW 1: INTAKE ─────────────────────────────────────────────────────
    with g.subgraph(name="cluster_in") as c:
        _, _, _, cbg, cbr = TINT["intake"]
        c.attr(label="1 · INTAKE  —  Client Discovery   (config/questions.py)",
               style="rounded,filled", fillcolor=cbg, color=cbr,
               fontcolor=BRAND_DEEP, fontname=FONT, fontsize="13", penwidth="1.4")
        intake_ids = [
            ("Q11", "Q1.1  Strategic objectives\n(multi-select)"),
            ("Q12", "Q1.2  Baseline + target\n(USD M, %, category)"),
            ("Q13", "Q1.3  Max payback\n(months)"),
            ("Q14", "Q1.4  Executive sponsor"),
            ("Q15", "Q1.5  Inter-dependencies\n(free text)"),
            ("Q21", "Q2.1  SKU count"),
            ("Q22", "Q2.2  Warehouses / DCs"),
            ("Q23", "Q2.3  Trade-promo ROI\n+ forecast error"),
            ("Q24", "Q2.4  OOS frequency"),
            ("Q31", "Q3.1  ERP architecture"),
            ("Q32", "Q3.2  Cloud maturity"),
            ("Q33", "Q3.3  Data freshness\n+ accuracy"),
            ("Q41", "Q4.1  KPI / adoption\nalignment"),
            ("Q42", "Q4.2  Compliance regime"),
            ("Q43", "Q4.3  Build model\n(SI / Hybrid / Internal)"),
            ("SC",  "Investment scope\nBudget · Timeline · Company"),
        ]
        for nid, lbl in intake_ids:
            _node(c, nid, lbl, "intake", width="1.95")
        # Force them onto one rank.
        c.attr(rank="same")

    # ── ROW 2: PARSE ──────────────────────────────────────────────────────
    with g.subgraph(name="cluster_pa") as c:
        _, _, _, cbg, cbr = TINT["parse"]
        c.attr(label="2 · PARSE & CLASSIFY  —  hardened extraction",
               style="rounded,filled", fillcolor=cbg, color=cbr,
               fontcolor=INK_700, fontname=FONT, fontsize="13", penwidth="1.4")
        _node(c, "PM", "_parse_money_usd()\nMONEY_RE: requires $ or unit", "parse", width="2.5")
        _node(c, "PP", "_parse_pct()\nextracts target %", "parse", width="2.5")
        _node(c, "PL", "_parse_payback_limit_months()", "parse", width="2.5")
        _node(c, "PC", "Categorical → enum\n(ERP · Cloud · SKU · Sponsor · OOS · …)", "parse", width="2.8")
        c.attr(rank="same")

    # ── ROW 3: MODIFIERS / SCORES ─────────────────────────────────────────
    with g.subgraph(name="cluster_md") as c:
        _, _, _, cbg, cbr = TINT["score"]
        c.attr(label="3 · MODIFIERS  —  scores & cost overlays   "
                     "(config/peer_corpus.model_assumptions)",
               style="rounded,filled", fillcolor=cbg, color=cbr,
               fontcolor="#8A6300", fontname=FONT, fontsize="13", penwidth="1.4")
        _node(c, "CX",  "Complexity score  C ∈ [0,1]\n0.35·ERP + 0.30·Cloud + 0.20·SKU", "score", width="3.0")
        _node(c, "RK",  "Risk score  R ∈ [0,1]\n0.35·Adoption + 0.25·Sponsor + 0.25·Data", "score", width="3.0")
        _node(c, "SI",  "SI cost inflation\nexternal 35% · hybrid 15% · internal 0", "score", width="3.0")
        _node(c, "CM",  "Compliance foundation uplift\nstrict 8% · moderate 4% · minimal 0", "score", width="3.0")
        _node(c, "OOS", "OOS recovery rate\nrarely 0 → constantly 1.5% of revenue", "score", width="3.0")
        _node(c, "PYL", "Payback limit\n(board patience)", "score", width="2.2")
        c.attr(rank="same")

    # ── ROW 4: VALUE LEVERS ───────────────────────────────────────────────
    with g.subgraph(name="cluster_lv") as c:
        _, _, _, cbg, cbr = TINT["lever"]
        c.attr(label="4 · VALUE LEVERS  —  evidence-banded   (EVIDENCE table + peer corpus)",
               style="rounded,filled", fillcolor=cbg, color=cbr,
               fontcolor="#0E6D4A", fontname=FONT, fontsize="13", penwidth="1.4")
        _node(c, "EV", "EVIDENCE\nP&G · Unilever · Nestlé · Coca-Cola ·\n"
                       "Mondelez · Reckitt · Colgate · Danone ·\nMarico · ITC", "lever", width="2.6")
        _node(c, "L1", "Revenue Uplift\n= revenue × 1.5–4.0%", "lever", width="2.2")
        _node(c, "L2", "Lost-Sales Recovery\n= revenue × OOS rate", "lever", width="2.2")
        _node(c, "L3", "Working-Capital Release\n= rev × 12% × 10–20% × 12% carry", "lever", width="2.6")
        _node(c, "L4", "Margin Expansion\n= cost-base × 80–180 bps", "lever", width="2.2")
        _node(c, "L5", "Opex Efficiency\n= addressable × 3–8%", "lever", width="2.2")
        _node(c, "L6", "CX Uplift (NPS / CSAT)\nstrategic, non-dollarised", "lever", width="2.2")
        c.attr(rank="same")

    # ── ROW 5: SYNTHESIS ──────────────────────────────────────────────────
    with g.subgraph(name="cluster_sy") as c:
        _, _, _, cbg, cbr = TINT["syn"]
        c.attr(label="5 · SYNTHESIS  —  realisation, allocation, finance",
               style="rounded,filled", fillcolor=cbg, color=cbr,
               fontcolor=BLUE, fontname=FONT, fontsize="13", penwidth="1.4")
        # Sub-row a: aggregates
        _node(c, "VAS", "Σ Value at stake (midpoint)", "syn", width="2.4")
        _node(c, "RF",  "Realisation factor\nmax(0.45, 1 − 0.35·R − 0.20·C)", "syn", width="2.4")
        _node(c, "FP",  "Foundation %\nmin(55%, 20% + 20%·C + Compliance)", "syn", width="2.4")
        _node(c, "TPC", "Total programme cost\n= Budget × (1 + SI inflation)", "syn", width="2.4")
        _node(c, "MAT", "AI maturity 0–100\n= f(complexity, data)", "syn", width="2.4")
        # Sub-row b: derived numbers
        _node(c, "RAV", "Realisable annual value\n= VAS × Realisation", "syn", width="2.4")
        _node(c, "FU",  "Foundation USD\n= Budget × Foundation %", "syn", width="2.4")
        _node(c, "DU",  "Deployable USD\n= Budget − Foundation", "syn", width="2.4")
        _node(c, "RAMP","Value ramp\nYear 1/2/3 = 0.40 / 0.75 / 1.00", "syn", width="2.4")
        _node(c, "SM",  "Scoring matrix\nuse cases × Impact·Feas·Speed·Fit", "syn", width="2.6")
        # Sub-row c: financial outputs
        _node(c, "DCF", "DCF @ 12%", "syn", width="1.6")
        _node(c, "NPV", "NPV (USD M)", "syn", width="1.6")
        _node(c, "ROI", "3-yr ROI %", "syn", width="1.6")
        _node(c, "PAY", "Payback months\n+ complexity penalty", "syn", width="2.0")
        _node(c, "CB",  "Confidence band\n20 + 25R + 15C + data + payback + compliance", "syn", width="3.4")
        _node(c, "PHS", "Phases\nP1 = Foundation · P2 = Deployable×60% · P3 = ×40%", "syn", width="3.4")

    # ── ROW 6: NARRATIVE LAYER ────────────────────────────────────────────
    with g.subgraph(name="cluster_ll") as c:
        _, _, _, cbg, cbr = TINT["llm"]
        c.attr(label="6 · NARRATIVE LAYER  —  GPT-4o, grounded   (llm/openai_client.py)",
               style="rounded,filled", fillcolor=cbg, color=cbr,
               fontcolor="#3D3187", fontname=FONT, fontsize="13", penwidth="1.4")
        _node(c, "PR",  "Prompt assembly\nSystem + engine facts + answers", "llm", width="2.8")
        _node(c, "GEN", "GPT-4o payload\nthesis · benchmarks · risks", "llm", width="2.6")
        _node(c, "GRD", "_ground_decision()\noverrides headline with engine Phase 1", "llm", width="3.2")
        _node(c, "REC", "_reconcile_with_engine()\nforces AMBER if no baseline", "llm", width="3.0")
        c.attr(rank="same")

    # ── ROW 7: REPORT ─────────────────────────────────────────────────────
    with g.subgraph(name="cluster_op") as c:
        _, _, _, cbg, cbr = TINT["out"]
        c.attr(label="7 · BOARD-READY REPORT  —  ui/dashboard.py",
               style="rounded,filled", fillcolor=cbg, color=cbr,
               fontcolor="white", fontname=FONT, fontsize="13", penwidth="1.4")
        for nid, lbl in [
            ("O1", "Decision Banner"),
            ("O2", "Investment Roadmap"),
            ("O3", "Strategic Thesis"),
            ("O4", "Use-Case Prioritisation"),
            ("O5", "Investment Ledger"),
            ("O6", "Capital Allocation Chart"),
            ("O7", "AI Maturity"),
            ("O8", "Competitive Benchmarking"),
            ("O9", "Risk Heat Map"),
            ("O10", "Scenario Model"),
        ]:
            _node(c, nid, lbl, "out", width="2.0")
        c.attr(rank="same")

    # ════════════════════════════════════════════════════════════════════════
    # EDGES — kept sparse and one-directional so ortho routing stays clean.
    # Solid = primary flow.  Dashed = modifier influence.
    # ════════════════════════════════════════════════════════════════════════

    # INTAKE → PARSE
    g.edge("Q12", "PM"); g.edge("Q23", "PM"); g.edge("Q12", "PP"); g.edge("Q13", "PL")
    for q in ("Q11","Q21","Q22","Q24","Q31","Q32","Q33","Q41","Q42","Q43","Q14"):
        g.edge(q, "PC")

    # PARSE / INTAKE → MODIFIERS
    for q in ("Q31","Q32","Q21"): g.edge(q, "CX", color=AMBER, style="dashed")
    for q in ("Q41","Q14","Q33"): g.edge(q, "RK", color=AMBER, style="dashed")
    g.edge("Q43", "SI",  color=AMBER, style="dashed")
    g.edge("Q42", "CM",  color=AMBER, style="dashed")
    g.edge("Q24", "OOS", color=AMBER, style="dashed")
    g.edge("PL",  "PYL", color=AMBER)

    # INTAKE / EVIDENCE → LEVERS
    for lv in ("L1", "L3", "L4", "L5", "L6"): g.edge("Q12", lv, color=GREEN)
    g.edge("OOS", "L2", color=GREEN)
    for lv in ("L1", "L3", "L4", "L5"):       g.edge("EV", lv, color=GREEN, style="dashed")

    # LEVERS → SYNTHESIS
    for lv in ("L1", "L2", "L3", "L4", "L5"): g.edge(lv, "VAS", color=BLUE)

    # MODIFIERS → SYNTHESIS
    g.edge("RK", "RF", color=BLUE); g.edge("CX", "RF", color=BLUE)
    g.edge("CX", "FP", color=BLUE); g.edge("CM", "FP", color=BLUE)
    g.edge("SI", "TPC", color=BLUE)
    g.edge("CX", "MAT", color=BLUE)

    # Within SYNTHESIS
    g.edge("VAS", "RAV"); g.edge("RF", "RAV")
    g.edge("FP", "FU"); g.edge("FU", "DU")
    g.edge("RAV", "RAMP"); g.edge("RAMP", "DCF")
    g.edge("DCF", "NPV"); g.edge("DCF", "ROI"); g.edge("TPC", "ROI")
    g.edge("RAV", "PAY"); g.edge("TPC", "PAY"); g.edge("CX", "PAY", color=BLUE)
    g.edge("RK", "CB", color=BLUE); g.edge("CX", "CB", color=BLUE)
    g.edge("Q33", "CB", color=AMBER, style="dashed")
    g.edge("PYL", "CB", color=AMBER, style="dashed")
    g.edge("Q42", "CB", color=AMBER, style="dashed")
    g.edge("FU", "PHS"); g.edge("DU", "PHS")
    g.edge("Q11", "SM", color=AMBER, style="dashed")

    # Scope → synthesis (Budget feeds three places)
    g.edge("SC", "FU"); g.edge("SC", "DU"); g.edge("SC", "TPC")

    # SYNTHESIS → NARRATIVE
    for s in ("PHS","ROI","NPV","PAY","CB","SM","MAT"):
        g.edge(s, "PR", color=VIOLET, style="dashed")
    g.edge("Q11","PR", color=VIOLET, style="dashed")
    g.edge("Q15","PR", color=VIOLET, style="dashed")
    g.edge("PR","GEN", color=VIOLET); g.edge("GEN","GRD", color=VIOLET); g.edge("GRD","REC", color=VIOLET)
    g.edge("PHS","GRD", color=BRAND, penwidth="1.6", label=" anchor ", fontcolor=BRAND_DEEP)
    g.edge("PHS","REC", color=BRAND, penwidth="1.6")

    # NARRATIVE / ENGINE → REPORT
    g.edge("REC","O1"); g.edge("REC","O3"); g.edge("REC","O8"); g.edge("REC","O9")
    g.edge("PHS","O2", color=BRAND, penwidth="1.4")
    g.edge("PHS","O5", color=BRAND); g.edge("PHS","O6", color=BRAND)
    g.edge("EV","O8", color=GREEN, style="dashed"); g.edge("EV","O5", color=GREEN, style="dashed")
    g.edge("SM","O4", color=BLUE); g.edge("MAT","O7", color=BLUE)
    g.edge("ROI","O10", color=BLUE); g.edge("NPV","O10", color=BLUE); g.edge("PAY","O10", color=BLUE)
    g.edge("CB","O1", color=BLUE, style="dashed", label="confidence", fontcolor=INK_500)

    return g


# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    exec_g = build_executive()
    full_g = build_detailed()

    exec_g.attr(dpi="200")
    full_g.attr(dpi="160")

    exec_g.render(filename="framework_exec", directory=str(HERE), format="png", cleanup=False)
    exec_g.render(filename="framework_exec", directory=str(HERE), format="svg", cleanup=False)
    full_g.render(filename="framework",      directory=str(HERE), format="png", cleanup=False)
    full_g.render(filename="framework",      directory=str(HERE), format="svg", cleanup=False)

    print("Wrote:")
    for name in ("framework_exec.png","framework_exec.svg","framework.png","framework.svg"):
        p = HERE / name
        if p.exists():
            print(f"  {p}  ({p.stat().st_size//1024} KB)")


if __name__ == "__main__":
    main()
