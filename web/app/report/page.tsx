"use client";

/**
 * The report. One scrolling narrative with a sticky section nav — each
 * section answers exactly one executive question. Scenario, AI-stack and
 * the foundation decision re-compute live against the engine API, always
 * with explicit before/after feedback.
 */
import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  computeReport,
  fetchRun,
  type AiStack,
  type Lever,
  type Report,
  type Scenario,
} from "@/lib/api";
import Matrix from "@/components/Matrix";
import Donut from "@/components/Donut";
import MemoSection from "@/components/MemoSection";

const NAV = [
  ["decision", "What should we fund?"],
  ["portfolio", "Which use cases?"],
  ["foundation", "Can our systems support it?"],
  ["compliance", "What could stop us?"],
  ["method", "How was this computed?"],
] as const;

const STACK_NOTES: Record<AiStack, string> = {
  Frontier: "Premium hosted models: +6% automation capture, +30% run cost",
  Balanced: "The cost and capability reference point",
  "Cost-optimized": "Open-source-led: -25% run cost, -7% automation capture",
};

export default function ReportPage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-3xl px-6 py-24 text-center text-g500">
          Loading the report…
        </div>
      }
    >
      <ReportInner />
    </Suspense>
  );
}

function ReportInner() {
  const router = useRouter();
  const runParam = useSearchParams().get("run");
  const [report, setReport] = useState<Report | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [flash, setFlash] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [openWhy, setOpenWhy] = useState<string | null>(null);

  // Reports are URLs: prefer the fresh session copy when it matches the
  // run id, otherwise rebuild the report from the audit trail by id.
  useEffect(() => {
    const cached = sessionStorage.getItem("hz_report");
    if (cached) {
      const r: Report = JSON.parse(cached);
      if (!runParam || r.run_id === runParam) {
        setReport(r);
        return;
      }
    }
    if (runParam) {
      fetchRun(runParam)
        .then((r) => {
          sessionStorage.setItem("hz_report", JSON.stringify(r));
          setReport(r);
        })
        .catch(() => setNotFound(true));
    }
  }, [runParam]);

  const base = report ? report.request : null;

  async function recompute(
    changes: Partial<Pick<Report, "scenario" | "ai_stack" | "foundation_decision">>,
    label: string,
  ) {
    if (!report || !base) return;
    setBusy(true);
    const before = report.summary.risk_adjusted_anv_m;
    try {
      const next = await computeReport({
        ...base,
        scenario: changes.scenario ?? report.scenario,
        ai_stack: changes.ai_stack ?? report.ai_stack,
        foundation_decision:
          changes.foundation_decision ?? report.foundation_decision,
      });
      sessionStorage.setItem("hz_report", JSON.stringify(next));
      setReport(next);
      router.replace(`/report?run=${next.run_id}`, { scroll: false });
      const after = next.summary.risk_adjusted_anv_m;
      const dir =
        after > before ? "up" : after < before ? "down" : "unchanged at";
      setFlash(
        dir === "unchanged at"
          ? `${label}: plan value unchanged at $${after.toFixed(1)}M per year.`
          : `${label}: plan value ${dir} $${Math.abs(after - before).toFixed(1)}M, from $${before.toFixed(1)}M to $${after.toFixed(1)}M per year. Every figure has been recomputed.`,
      );
    } finally {
      setBusy(false);
    }
  }

  if (!report)
    return (
      <div className="mx-auto max-w-3xl px-6 py-24 text-center text-g500">
        {notFound
          ? "That report id was not found (it may have been erased under retention policy). "
          : "No report in this session. "}{" "}
        <Link href="/diagnostic" className="text-flame underline">
          Run the diagnostic
        </Link>{" "}
        to generate one.
      </div>
    );

  const s = report.summary;
  const d = report.diagnostic;
  const funded = report.levers.filter((l) => l.budget_approved);
  const now = funded.filter((l) => l.quadrant === "Strategic Bets");
  const next = funded.filter((l) => l.quadrant === "Quick Wins / Fill-ins");
  const later = report.levers.filter(
    (l) => l.quadrant === "Park (Data-Blocked)" && !l.already_implemented,
  );
  const covered = report.levers.filter((l) => l.already_implemented);
  const orderedLevers = [...report.levers].sort((a, b) => {
    const ra = a.rank ?? (a.already_implemented ? 900 : 500 - a.anv_m);
    const rb = b.rank ?? (b.already_implemented ? 900 : 500 - b.anv_m);
    return ra - rb;
  });
  const drivers = [...funded].sort((a, b) => b.anv_m - a.anv_m).slice(0, 3);
  const modernM =
    funded.find((l) => l.id === "lever_0_foundation")?.impl_cost_m ?? 0;

  return (
    <div className="mx-auto max-w-6xl px-6 pb-24">
      {busy && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-white/60 backdrop-blur-[2px]">
          <div className="card flex items-center gap-3 px-6 py-4 shadow-lg">
            <span className="spinner" />
            <span className="text-sm font-semibold text-black">Recomputing the plan…</span>
          </div>
        </div>
      )}
      {/* Sticky section nav + controls */}
      <div className="sticky top-[60px] z-40 -mx-6 border-b border-g200 bg-white/95 px-6 py-3 backdrop-blur">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <nav className="flex flex-wrap gap-1">
            {NAV.map(([id, label]) => (
              <a
                key={id}
                href={`#${id}`}
                className="rounded px-2.5 py-1.5 text-[12.5px] font-semibold text-g500 transition-colors hover:bg-g100 hover:text-black"
              >
                {label}
              </a>
            ))}
          </nav>
          <div className="flex items-center gap-2">
            <Segmented
              value={report.scenario}
              options={["conservative", "base", "aggressive"] as Scenario[]}
              labels={{ conservative: "Conservative", base: "Base", aggressive: "Aggressive" }}
              disabled={busy}
              onSelect={(v) => recompute({ scenario: v }, `Scenario set to ${v}`)}
            />
            <Segmented
              value={report.ai_stack}
              options={["Frontier", "Balanced", "Cost-optimized"] as AiStack[]}
              labels={{ Frontier: "Frontier", Balanced: "Balanced", "Cost-optimized": "Cost-opt." }}
              titles={STACK_NOTES}
              disabled={busy}
              onSelect={(v) => recompute({ ai_stack: v }, `AI stack set to ${v}`)}
            />
          </div>
        </div>
      </div>

      {flash && (
        <div className="mt-4 rounded-md border border-flame bg-flame/5 px-4 py-3 text-[13px]">
          <strong>✓</strong> {flash}
        </div>
      )}

      {/* 1 · Decision */}
      <section id="decision" className="scroll-mt-32 pt-10">
        <div className="card border-t-4 !border-t-flame p-8 shadow-sm">
          <p className="eyebrow">Recommendation for {s.company_name}</p>
          <h1 className="display mt-2 text-4xl">
            Invest ${s.committed_m.toFixed(1)}M of your ${s.budget_m.toFixed(0)}M
            budget now.
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed">
            That ${s.committed_m.toFixed(1)}M is a one-off build cost. In
            return, the funded plan creates{" "}
            <strong className="text-black">
              ${s.risk_adjusted_anv_m.toFixed(1)}M of value every year
            </strong>{" "}
            after a {s.exec_risk_pct}% risk discount, earning the money back in{" "}
            <strong className="text-black">
              {s.payback_months ? `${Math.round(s.payback_months)} months` : "beyond the horizon"}
            </strong>
            . The remaining ${s.uncommitted_m.toFixed(1)}M stays uncommitted,
            because spending it on weaker cases would destroy value.
            {s.already_covered_count > 0 && (
              <>
                {" "}
                <strong className="text-black">
                  {s.already_covered_count} capability
                  {s.already_covered_count > 1 ? "ies" : "y"} you already run
                </strong>{" "}
                {s.already_covered_count > 1 ? "were" : "was"} excluded from
                this ask rather than re-recommended.
              </>
            )}
          </p>
          <div className="mt-7 grid gap-8 md:grid-cols-3">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-wider text-g500">
                Largest value drivers
              </p>
              {drivers.map((l) => (
                <div
                  key={l.id}
                  className="mt-1.5 flex items-center justify-between rounded border-l-[3px] border-flame bg-flame/5 px-3 py-2 text-[13px] text-black"
                >
                  {l.short_name}
                  <span className="text-xs text-g700">
                    returns ${l.anv_m.toFixed(1)}M/yr
                  </span>
                </div>
              ))}
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-wider text-g500">
                What could get in the way
              </p>
              {[
                d.tco.security_flag ? "Ageing on-premise estate" : null,
                d.pillars.fragmentation_score >= 50 ? "Fragmented data estate" : null,
                d.pillars.governance_readiness < 60 ? "Governance maturity" : null,
                funded.some((l) => l.reg_risk !== "green")
                  ? "Compliance mitigations required"
                  : null,
              ]
                .filter(Boolean)
                .slice(0, 3)
                .map((r) => (
                  <div
                    key={r}
                    className="mt-1.5 rounded border-l-[3px] border-g300 bg-g100 px-3 py-2 text-[13px]"
                  >
                    {r}
                  </div>
                ))}
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-wider text-g500">
                Plan confidence
              </p>
              <p className="display mt-1 text-4xl">{s.confidence_pct}%</p>
              <p className="text-[11px] text-g500">
                driven by your governance maturity
              </p>
            </div>
          </div>
        </div>

        <details className="mt-4">
          <summary>How these headline numbers are built</summary>
          <div className="px-4 pb-4">
            <table className="hz-table">
              <tbody>
                <Row k="Value created per year (before risk discount)" v={`$${s.total_anv_m.toFixed(1)}M`} note="Sum of every funded use case's annual value, itemized below" />
                <Row k="Risk discount" v={`${s.exec_risk_pct}%`} note="From your governance maturity: weaker governance means more delivery slippage" />
                <Row k="Value created per year (after discount)" v={`$${s.risk_adjusted_anv_m.toFixed(1)}M`} strong />
                <Row k="Annual running costs (already deducted)" v={`$${s.funded_run_cost_m.toFixed(1)}M/yr`} note="Model licences, inference and hosting for the funded plan; every value above is net of these" />
                <Row k="Money in (one-off)" v={`$${s.committed_m.toFixed(1)}M`} note="Every dollar itemized in the foundation section" />
                <Row k="Earns back its cost in" v={s.payback_months ? `${Math.round(s.payback_months)} months` : "n/a"} note="Value ramps over 3 years (25% / 60% / 100%)" strong />
              </tbody>
            </table>
          </div>
        </details>

        {/* Sequence */}
        <h2 className="display mt-10 text-2xl">The sequence</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <RoadCol title="Now (0-6 mo)" subtitle="High value, ready to build" accent="border-flame" items={now} />
          <RoadCol title="Next (6-18 mo)" subtitle="Fast, momentum-building" accent="border-tangerine" items={next} />
          <RoadCol title="Later (blocked)" subtitle="Needs the data foundation first" accent="border-g300" items={later} locked />
        </div>
        <p className="mt-3 text-[12.5px] text-g500">
          Adds up: the build costs above total{" "}
          <strong className="text-g700">${s.committed_m.toFixed(1)}M</strong>,
          the same figure as the headline commitment. Together they return{" "}
          <strong className="text-g700">${s.total_anv_m.toFixed(1)}M per year</strong>{" "}
          before the risk discount.
        </p>
      </section>

      {/* 2 · Portfolio */}
      <section id="portfolio" className="scroll-mt-32 pt-14">
        <h2 className="display text-2xl">
          {s.funded_count} use cases earn a place in the funded plan
          {s.blocked_anv_m > 0.05 &&
            `; $${s.blocked_anv_m.toFixed(1)}M/yr sits blocked behind the data foundation`}
        </h2>
        {covered.length > 0 && (
          <p className="mt-2 rounded-md border border-g200 bg-g100/60 px-3 py-2 text-[12.5px]">
            <b className="text-g700">Already in place at the firm (excluded from the ask):</b>{" "}
            {covered.map((l) => l.name).join(" · ")}
          </p>
        )}
        <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-xs text-g500">
          <span><b className="text-g700">Strategic bet</b> · high value and ready; fund first</span>
          <span><b className="text-g700">Quick win</b> · smaller value, fast to deliver</span>
          <span><b className="text-g700">Blocked</b> · valuable but the data foundation cannot support it yet</span>
          <span><b className="text-g700">Lower priority</b> · does not earn a place</span>
        </div>
        <div className="mt-5">
          <Matrix levers={report.levers} />
        </div>
        <div className="card mt-4 overflow-x-auto">
          <table className="hz-table">
            <thead>
              <tr>
                <th className="w-14">Priority</th>
                <th>AI use case</th>
                <th>Category</th>
                <th className="num">Build cost</th>
                <th className="num">Running cost / yr</th>
                <th className="num">Annual value</th>
                <th className="num">Earns it back in</th>
                <th className="num">Readiness</th>
                <th className="w-10"></th>
              </tr>
            </thead>
            <tbody>
              {orderedLevers.map((l) => (
                <ScorecardRow
                  key={l.id}
                  l={l}
                  open={openWhy === l.id}
                  onToggle={() => setOpenWhy(openWhy === l.id ? null : l.id)}
                />
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-[12px] text-g500">
          Every value is net of its annual running cost. Click{" "}
          <b className="text-g700">Why?</b> on any row for the drivers behind
          its rank and the industry benchmark it rests on.
        </p>
      </section>

      {/* 3 · Foundation */}
      <section id="foundation" className="scroll-mt-32 pt-14">
        <h2 className="display text-2xl">
          Our verdict on your legacy estate: {d.verdict}
          <span className="ml-3 align-middle text-xs font-normal text-g500">
            score {d.deprecation_score} of 100
          </span>
        </h2>
        <p className="mt-2 max-w-3xl text-sm leading-relaxed">{d.verdict_action}</p>

        <div className="mt-5 grid gap-4 md:grid-cols-3">
          {(
            [
              ["Cost of technical debt (40%)", d.pillars.tech_debt_score, d.pillar_explain.tech_debt],
              ["Data fragmentation (35%)", d.pillars.fragmentation_score, d.pillar_explain.fragmentation],
              ["Governance gap (25%)", 100 - d.pillars.governance_readiness, d.pillar_explain.governance],
            ] as const
          ).map(([label, score, why]) => (
            <div key={label} className="card p-4">
              <div className="flex items-baseline justify-between">
                <p className="text-[13px] font-semibold text-black">{label}</p>
                <p className="display text-xl">{score}/100</p>
              </div>
              <div className="mt-2 h-2.5 rounded bg-g100">
                <div
                  className="h-full rounded bg-black"
                  style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
                />
              </div>
              <p className="mt-2 text-xs leading-relaxed text-g500">{why}</p>
            </div>
          ))}
        </div>
        <p className="mt-3 rounded bg-g100 px-4 py-2.5 font-mono text-[12px] text-g700">
          {d.score_math}
        </p>

        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <div className="card p-5">
            <p className="text-[13px] font-bold text-black">The money story</p>
            <table className="hz-table mt-2">
              <tbody>
                <Row k="One-off modernization cost" v={`$${d.self_funding.rebuild_cost_m.toFixed(1)}M`} note="Built bottom-up; breakdown below" />
                <Row k="Maintenance you stop paying" v={`$${d.self_funding.legacy_annual_savings_m.toFixed(1)}M/yr`} />
                <Row k="AI value currently blocked" v={`$${d.self_funding.unlocked_anv_m.toFixed(1)}M/yr`} />
                <Row k="Pays for itself in" v={d.self_funding.payback_months ? `${d.self_funding.payback_months} months` : "does not pay back"} strong />
              </tbody>
            </table>
          </div>
          <div className="card flex flex-col justify-between p-5">
            <div>
              <p className="text-[13px] font-bold text-black">
                The decision: does modernization go into the plan?
              </p>
              <p className="mt-1.5 text-[13px] leading-relaxed">
                Our recommendation is to{" "}
                <strong className="text-black">
                  {d.recommend_funding && d.self_funding.payback_months
                    ? "include modernization"
                    : "defer modernization"}
                </strong>
                . Currently:{" "}
                <strong className="text-black">
                  {report.foundation_decision ? "in the plan" : "not in the plan"}
                </strong>
                .
              </p>
            </div>
            <button
              disabled={busy}
              onClick={() =>
                recompute(
                  { foundation_decision: !report.foundation_decision },
                  report.foundation_decision
                    ? "Modernization taken out of the plan"
                    : "Modernization added to the plan",
                )
              }
              className="mt-4 rounded-md border border-flame px-4 py-2.5 text-[13px] font-semibold text-flame transition-colors hover:bg-flame hover:text-white disabled:opacity-50"
            >
              {report.foundation_decision
                ? "Take modernization out of the plan"
                : "Put modernization into the plan"}
            </button>
          </div>
        </div>

        <div className="card mt-4 p-5">
          <p className="text-[13px] font-bold text-black">
            Where your budget stands: ${s.committed_m.toFixed(1)}M of ${s.budget_m.toFixed(0)}M committed
          </p>
          <div className="mt-3">
            <Donut
              leversM={s.committed_m - modernM}
              modernM={modernM}
              uncommittedM={s.uncommitted_m}
              budgetM={s.budget_m}
            />
          </div>
        </div>

        <details className="mt-4">
          <summary>
            How the ${d.self_funding.rebuild_cost_m.toFixed(1)}M modernization
            estimate is built, line by line
          </summary>
          <div className="px-4 pb-4">
            <table className="hz-table">
              <thead>
                <tr>
                  <th>Component</th>
                  <th className="num">Estimate</th>
                  <th>What drives it</th>
                </tr>
              </thead>
              <tbody>
                {d.rebuild_breakdown.map((c) => (
                  <tr key={c.component}>
                    <td className="text-black">{c.component}</td>
                    <td className="num">${c.amount_m.toFixed(1)}M</td>
                    <td className="text-xs text-g500">{c.basis}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      </section>

      {/* 4 · Compliance */}
      <section id="compliance" className="scroll-mt-32 pt-14">
        <h2 className="display text-2xl">What could stop us</h2>
        <div className="card mt-4 overflow-x-auto">
          <table className="hz-table">
            <thead>
              <tr>
                <th>Use case</th>
                <th>Risk profile</th>
                <th>Required actions</th>
              </tr>
            </thead>
            <tbody>
              {report.levers.map((l) => (
                <tr key={l.id}>
                  <td className="font-semibold text-black">{l.name}</td>
                  <td>
                    {l.reg_risk === "green" && <span className="text-g900">● Compliant</span>}
                    {l.reg_risk === "yellow" && <span className="text-tangerine">● Requires mitigation</span>}
                    {l.reg_risk === "red" && <span className="text-maroon">● High risk</span>}
                  </td>
                  <td className="text-xs">
                    {l.reg_mitigations.length
                      ? l.reg_mitigations.map((m) => <div key={m}>• {m}</div>)
                      : "Standard IT hygiene"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* 5 · Method */}
      <section id="method" className="scroll-mt-32 pt-14">
        <h2 className="display text-2xl">How this was computed</h2>
        <p className="mt-2 max-w-3xl text-sm leading-relaxed">
          Every number is deterministic: your answers, a declared assumption
          set, no hidden scaling. This run is logged for reproducibility.
        </p>
        <div className="mt-4 flex flex-wrap gap-2 text-[11.5px]">
          <span className="rounded-full border border-g200 px-3 py-1.5">Run ID · {report.run_id}</span>
          <span className="rounded-full border border-g200 px-3 py-1.5">Engine · {report.engine_version}</span>
          <span className="rounded-full border border-g200 px-3 py-1.5">Assumptions fingerprint · {report.assumptions_hash}</span>
          <span className="rounded-full border border-g200 px-3 py-1.5">Scenario · {report.scenario}</span>
          <span className="rounded-full border border-g200 px-3 py-1.5">AI stack · {report.ai_stack}</span>
        </div>
        <div className="card mt-5 p-5">
          <p className="text-[14px] font-bold text-black">How the ranking works</p>
          <ol className="mt-2 max-w-3xl list-decimal space-y-1.5 pl-5 text-[13px] leading-relaxed">
            <li>
              <b className="text-black">Each use case is valued from your answers</b>: your
              volumes and rates against peer medians, through published automation
              benchmarks (BCG 2026, PwC 2025, EY 2026, Jersey Finance 2025, IVP,
              Coalition Greenwich 2026, Oliver Wyman 2026 — the exact citation sits
              on every row&apos;s <i>Why?</i>).
            </li>
            <li>
              <b className="text-black">Value is haircut for realism</b>: only 50–75% of
              modelled value is counted (your scenario), consistent with standard
              benefits-realisation practice, and each value is net of its annual
              running cost.
            </li>
            <li>
              <b className="text-black">Use cases are ordered</b> by fit to your stated
              goals first, then by annual value — and funded in that order while
              budget remains. That allocation order is the priority number shown.
            </li>
            <li>
              <b className="text-black">Discipline rules</b>: nothing blocked by your data
              foundation, already live at the firm, loss-making, or non-compliant
              without mitigation can consume budget.
            </li>
          </ol>
          <p className="mt-2 text-[11.5px] text-g500">
            Every constant behind these steps is in the assumptions register below;
            benchmark scopes are replaced by scoped vendor quotes in an engagement.
          </p>
        </div>

        {base && (
          <MemoSection
            request={{
              ...base,
              scenario: report.scenario,
              ai_stack: report.ai_stack,
              foundation_decision: report.foundation_decision,
            }}
          />
        )}

        <details className="mt-4">
          <summary>What each build cost covers</summary>
          <div className="px-4 pb-4">
            <table className="hz-table">
              <tbody>
                {report.levers.map((l) => (
                  <tr key={l.id}>
                    <td className="text-black">{l.name}</td>
                    <td className="num">${l.impl_cost_m.toFixed(1)}M</td>
                    <td className="text-xs text-g500">{l.cost_basis}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      </section>
    </div>
  );
}

function Row({
  k,
  v,
  note,
  strong,
}: {
  k: string;
  v: string;
  note?: string;
  strong?: boolean;
}) {
  return (
    <tr className={strong ? "bg-g100/60" : ""}>
      <td className={strong ? "font-semibold text-black" : ""}>{k}</td>
      <td className={`num ${strong ? "font-semibold" : ""}`}>{v}</td>
      <td className="text-xs text-g500">{note ?? ""}</td>
    </tr>
  );
}

function RoadCol({
  title,
  subtitle,
  accent,
  items,
  locked,
}: {
  title: string;
  subtitle: string;
  accent: string;
  items: Lever[];
  locked?: boolean;
}) {
  return (
    <div className="card p-4">
      <p className={`border-b-2 ${accent} pb-2 text-[11px] font-bold uppercase tracking-wider text-black`}>
        {title}
      </p>
      <p className="mt-1.5 text-[11px] text-g500">{subtitle}</p>
      <div className="mt-2 space-y-2">
        {items.length === 0 && (
          <p className="text-xs italic text-g500">None in this horizon.</p>
        )}
        {items.map((l) => (
          <div
            key={l.id}
            className="flex items-start gap-2.5 rounded border-l-[3px] border-flame/60 bg-g100 px-3 py-2"
          >
            {l.rank != null && (
              <span className="display mt-0.5 min-w-7 text-xl leading-none !text-flame">
                #{l.rank}
              </span>
            )}
            <div>
              <p className="text-[13px] font-medium text-black">{l.name}</p>
              <p className="text-[11.5px] text-g500">
                {locked
                  ? `Worth $${l.anv_m.toFixed(1)}M per year, locked until the foundation is fixed`
                  : `Costs $${l.impl_cost_m.toFixed(1)}M to build · returns $${l.anv_m.toFixed(1)}M per year`}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Segmented<T extends string>({
  value,
  options,
  labels,
  titles,
  disabled,
  onSelect,
}: {
  value: T;
  options: T[];
  labels: Record<T, string>;
  titles?: Record<T, string>;
  disabled?: boolean;
  onSelect: (v: T) => void;
}) {
  return (
    <div className="flex overflow-hidden rounded-md border border-g300">
      {options.map((opt) => (
        <button
          key={opt}
          title={titles?.[opt]}
          disabled={disabled}
          onClick={() => opt !== value && onSelect(opt)}
          className={`px-3 py-1.5 text-[12px] font-semibold transition-colors disabled:opacity-50 ${
            value === opt ? "bg-flame text-white" : "bg-white text-g700 hover:bg-g100"
          }`}
        >
          {labels[opt]}
        </button>
      ))}
    </div>
  );
}


function ScorecardRow({
  l,
  open,
  onToggle,
}: {
  l: Lever;
  open: boolean;
  onToggle: () => void;
}) {
  const dim = !l.budget_approved && !l.already_implemented;
  return (
    <>
      <tr className={dim ? "opacity-50" : ""}>
        <td>
          {l.rank != null ? (
            <span className="display text-xl !text-flame">#{l.rank}</span>
          ) : l.already_implemented ? (
            <span className="text-[11px] font-bold uppercase text-g500">Live</span>
          ) : (
            <span className="text-g300">—</span>
          )}
        </td>
        <td className="font-semibold text-black">
          {l.name}
          {l.already_implemented && (
            <span className="ml-2 rounded bg-flame/10 px-1.5 py-0.5 text-[10px] font-bold uppercase text-flame">
              Already live
            </span>
          )}
          {dim && (
            <span className="ml-2 rounded bg-g100 px-1.5 py-0.5 text-[10px] font-bold text-g500">
              NOT FUNDED
            </span>
          )}
          {l.warning === "REG_CAPPED" && (
            <span className="ml-2 text-[11px] font-normal text-tangerine">
              value halved until compliance gaps close
            </span>
          )}
        </td>
        <td>
          <span
            className={`mr-2 inline-block h-2.5 w-2.5 rounded-full ${
              l.already_implemented
                ? "bg-flame/40"
                : ["Blocked", "Lower priority"].includes(l.quadrant_label)
                  ? "bg-g300"
                  : "bg-flame"
            }`}
          />
          {l.quadrant_label}
        </td>
        <td className="num">
          {l.already_implemented ? "—" : `$${l.impl_cost_m.toFixed(1)}M`}
        </td>
        <td className="num">
          {l.already_implemented ? "in run-rate" : `$${l.run_cost_m.toFixed(1)}M`}
        </td>
        <td className="num">
          {l.already_implemented ? "—" : `$${l.anv_m.toFixed(1)}M`}
        </td>
        <td className="num">
          {l.already_implemented
            ? "—"
            : l.payback_months
              ? `${Math.round(l.payback_months)} mo`
              : "n/a"}
        </td>
        <td className="num">{l.feasibility}/100</td>
        <td>
          <button
            onClick={onToggle}
            className={`rounded border px-2 py-0.5 text-[11px] font-semibold transition-colors ${
              open
                ? "border-flame bg-flame text-white"
                : "border-g300 text-g500 hover:border-flame hover:text-flame"
            }`}
          >
            Why?
          </button>
        </td>
      </tr>
      {open && (
        <tr>
          <td colSpan={9} className="!border-l-2 !border-l-flame bg-flame/[0.03]">
            <p className="max-w-4xl py-1 text-[12.5px] leading-relaxed text-g700">
              {l.rationale}
            </p>
          </td>
        </tr>
      )}
    </>
  );
}
