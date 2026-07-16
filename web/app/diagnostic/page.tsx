"use client";

/**
 * The intake, as a guided multi-step wizard. One decision per step, a
 * progress stepper, Back/Continue with validation. Sector selection gates
 * which questions appear (same rule the engine uses). The final step posts
 * to the engine API and routes to the report.
 */
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  computeReport,
  fetchConfig,
  fetchPrefill,
  type Config,
  type PrefillField,
  type Question,
} from "@/lib/api";

const SECTION_META: Record<string, { title: string; blurb: string }> = {
  S1: {
    title: "Technology & data",
    blurb: "Your data estate sets the ceiling on what AI can reach and how fast.",
  },
  S2: {
    title: "Front office",
    blurb: "How efficiently the front office runs today sizes the revenue-facing levers.",
  },
  S3: {
    title: "Middle & back office",
    blurb: "Post-trade and claims operations are the fastest, highest-certainty payback.",
  },
  S4: {
    title: "Risk & compliance",
    blurb: "Regulatory friction and false positives are a silent tax on growth.",
  },
  S5: {
    title: "Legacy & delivery",
    blurb: "The health of the estate and the firm's ability to deliver drive the risk view.",
  },
};

export default function DiagnosticPage() {
  const router = useRouter();
  const [cfg, setCfg] = useState<Config | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [step, setStep] = useState(0);

  const [company, setCompany] = useState("");
  const [sector, setSector] = useState("");
  const [goals, setGoals] = useState<string[]>([]);
  const [budget, setBudget] = useState(100);
  const [answers, setAnswers] = useState<Record<string, number | string>>({});
  const [existingIds, setExistingIds] = useState<string[]>([]);
  const [provenance, setProvenance] = useState<Record<string, PrefillField>>({});
  const [searching, setSearching] = useState(false);
  const [searchNote, setSearchNote] = useState<string | null>(null);

  useEffect(() => {
    fetchConfig()
      .then((c) => {
        setCfg(c);
        setSector(c.sectors[0]);

        const defaults: Record<string, number | string> = {};
        for (const q of c.questions) {
          if (q.default !== undefined) defaults[q.id] = q.default;
        }
        setAnswers(defaults);
      })
      .catch((err) => {
        console.error(err);
        setError(err instanceof Error ? err.message : JSON.stringify(err));
      });
  }, []);

  const sectionSteps = useMemo(() => {
    if (!cfg) return [];
    const present = new Set(
      cfg.questions
        .filter((q) => !q.visible_when?.sector || q.visible_when.sector.includes(sector))
        .map((q) => q.section),
    );
    return ["S1", "S2", "S3", "S4", "S5"].filter((s) => present.has(s));
  }, [cfg, sector]);

  // Step model: 0 = firm profile, 1 = current AI landscape, then one per section.
  const steps = useMemo(
    () => ["Firm profile", "Current AI", ...sectionSteps.map((s) => SECTION_META[s].title)],
    [sectionSteps],
  );
  const lastStep = steps.length - 1;

  const stepQuestions = useMemo(() => {
    if (!cfg || step < 2) return [];
    const sid = sectionSteps[step - 2];
    return cfg.questions.filter(
      (q) =>
        q.section === sid &&
        (!q.visible_when?.sector || q.visible_when.sector.includes(sector)),
    );
  }, [cfg, step, sectionSteps, sector]);

  async function runPrefill() {
    if (!company.trim()) {
      setError("Name the firm first, then search public sources for it.");
      return;
    }
    setError(null);
    setSearching(true);
    setSearchNote(null);
    try {
      const p = await fetchPrefill(company.trim());
      if (!p.searched) {
        setSearchNote(
          "No retrieval ran: the engine API has no GEMINI_API_KEY configured. All fields stay manual.",
        );
      } else {
        const found = Object.keys(p.fields);
        if (p.company_name) setCompany(p.company_name);
        if (found.length) {
          setAnswers((a) => {
            const nextA = { ...a };
            for (const [fid, f] of Object.entries(p.fields)) {
              const n = Number(f.value);
              nextA[fid] = Number.isFinite(n) ? n : f.value;
            }
            return nextA;
          });
          setProvenance(p.fields);
          setSearchNote(
            `Found ${found.length} field(s) from public sources in ${p.duration_s.toFixed(0)}s — each is marked with its source in the sections ahead. Nothing was estimated.`,
          );
        } else {
          setSearchNote(
            `Searched public sources in ${p.duration_s.toFixed(0)}s and verified nothing for this firm — all fields stay manual. That is the honest outcome, not a failure.`,
          );
        }
      }
    } catch (e) {
      setSearchNote(`Search failed: ${String(e)}`);
    } finally {
      setSearching(false);
    }
  }

  function next() {
    if (step === 0 && !company.trim()) {
      setError("Please name the firm — the report is addressed to it.");
      return;
    }
    setError(null);
    if (step < lastStep) {
      setStep(step + 1);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } else {
      submit();
    }
  }

  async function submit() {
    setBusy(true);
    try {
      const report = await computeReport({
        answers,
        company_name: company.trim(),
        target_sector: sector,
        budget_usd_m: budget,
        primary_goals: goals,
        scenario: "base",
        ai_stack: "Balanced",
        foundation_decision: false,
        existing_lever_ids: existingIds,
      });
      sessionStorage.setItem("hz_report", JSON.stringify(report));
      router.push(`/report/decision?run=${report.run_id}`);
    } catch (e) {
      setError(String(e));
      setBusy(false);
    }
  }

  if (!cfg)
    return (
      <div className="mx-auto max-w-3xl px-6 py-24 text-center text-g500">
        {error ?? "Loading the diagnostic…"}
      </div>
    );

  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      {/* Stepper */}
      <div className="sticky top-[60px] z-30 -mx-6 mb-8 border-b border-g200 bg-white/95 px-6 py-3 backdrop-blur">
        <div className="flex items-center gap-1 overflow-x-auto">
          {steps.map((label, i) => (
            <button
              key={label}
              onClick={() => i < step && setStep(i)}
              disabled={i > step}
              className={`flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-1 text-[11.5px] font-semibold transition-colors ${
                i === step
                  ? "bg-flame text-white"
                  : i < step
                    ? "text-flame hover:bg-flame/10"
                    : "text-g300"
              }`}
            >
              <span
                className={`flex h-4 w-4 items-center justify-center rounded-full text-[9px] ${
                  i < step ? "bg-flame text-white" : i === step ? "bg-white/25" : "bg-g100"
                }`}
              >
                {i < step ? "✓" : i + 1}
              </span>
              {label}
            </button>
          ))}
        </div>
        <div className="mt-2 h-1 w-full rounded bg-g100">
          <div
            className="h-full rounded bg-flame transition-all"
            style={{ width: `${(step / lastStep) * 100}%` }}
          />
        </div>
      </div>

      {error && (
        <div className="mb-6 rounded-md border border-maroon bg-maroon/5 px-4 py-3 text-[13px] text-maroon">
          {error}
        </div>
      )}

      {/* Step 0: Firm profile */}
      {step === 0 && (
        <section className="fade-step">
          <p className="eyebrow">Step 1</p>
          <h1 className="display mt-2 text-4xl">Tell us about the firm</h1>
          <p className="mt-2 text-[13.5px] text-g500">
            Name the firm and set the frame. We can pull public facts to save
            you typing — every value arrives with its source.
          </p>

          <div className="card mt-6 p-6">
            <label className="block text-[13px] font-semibold text-black">
              Firm name
              <div className="mt-1.5 flex gap-2">
                <input
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  placeholder="e.g. HDFC Asset Management"
                  className="w-full rounded-md border border-g300 px-3 py-2 text-sm text-black outline-none focus:border-flame"
                />
                <button
                  onClick={runPrefill}
                  disabled={searching}
                  className="shrink-0 rounded-md border border-flame px-4 py-2 text-[13px] font-semibold text-flame transition-colors hover:bg-flame hover:text-white disabled:opacity-50"
                >
                  {searching ? "Searching…" : "Search public sources"}
                </button>
              </div>
            </label>
            {searchNote && (
              <p className="mt-3 rounded-md border border-flame/40 bg-flame/5 px-3 py-2 text-[12.5px]">
                {searchNote}
              </p>
            )}

            <p className="mt-5 text-[13px] font-semibold text-black">Sector</p>
            <p className="text-xs text-g500">
              Determines which questions you are asked and which use cases are scored.
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              {cfg.sectors.map((s) => (
                <button
                  key={s}
                  onClick={() => setSector(s)}
                  className={`rounded-md border px-3.5 py-2 text-[13px] transition-colors ${
                    sector === s
                      ? "border-flame bg-flame text-white"
                      : "border-g300 text-g700 hover:border-black"
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>

            <p className="mt-5 text-[13px] font-semibold text-black">
              Strategic goals <span className="font-normal text-g500">(optional)</span>
            </p>
            <p className="text-xs text-g500">
              Use cases serving a selected goal reach full impact; off-goal ones
              are dampened, never hidden.
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              {cfg.goals.map((g) => (
                <button
                  key={g}
                  onClick={() =>
                    setGoals((prev) =>
                      prev.includes(g) ? prev.filter((x) => x !== g) : [...prev, g],
                    )
                  }
                  className={`rounded-md border px-3.5 py-2 text-[13px] transition-colors ${
                    goals.includes(g)
                      ? "border-flame bg-flame/10 text-flame"
                      : "border-g300 text-g700 hover:border-black"
                  }`}
                >
                  {g}
                </button>
              ))}
            </div>

            <label className="mt-5 block text-[13px] font-semibold text-black">
              Transformation budget:{" "}
              <span className="display text-lg">${budget}M</span>
              <input
                type="range"
                min={10}
                max={500}
                step={5}
                value={budget}
                onChange={(e) => setBudget(Number(e.target.value))}
                className="mt-2 w-full accent-flame"
              />
            </label>
          </div>
        </section>
      )}

      {/* Step 1: Current AI landscape */}
      {step === 1 && (
        <section className="fade-step">
          <p className="eyebrow">Step 2</p>
          <h1 className="display mt-2 text-4xl">Your current AI landscape</h1>
          <p className="mt-2 text-[13.5px] text-g500">
            Select every capability that is <b>already live in production</b> at
            the firm. Anything selected is excluded from the investment ask and
            shown as covered — this tool never recommends what you already run.
          </p>
          <div className="card mt-6 p-6">
            <div className="flex flex-wrap gap-2">
              {cfg.levers
                .filter((l) => l.sectors.includes("all") || l.sectors.includes(sector))
                .map((l) => (
                  <button
                    key={l.id}
                    onClick={() =>
                      setExistingIds((prev) =>
                        prev.includes(l.id)
                          ? prev.filter((x) => x !== l.id)
                          : [...prev, l.id],
                      )
                    }
                    className={`rounded-md border px-3 py-1.5 text-[12.5px] transition-colors ${
                      existingIds.includes(l.id)
                        ? "border-flame bg-flame/10 font-semibold text-flame"
                        : "border-g300 text-g700 hover:border-black"
                    }`}
                  >
                    {existingIds.includes(l.id) ? "✓ " : ""}
                    {l.short_name}
                  </button>
                ))}
            </div>
            <p className="mt-3 text-[12px] text-g500">
              {existingIds.length === 0
                ? "None selected — the report will assume a greenfield AI estate."
                : `${existingIds.length} capability(ies) will be marked as already covered and excluded from the ask.`}
            </p>
          </div>
        </section>
      )}

      {/* Steps 2+: question sections */}
      {step >= 2 && (
        <section className="fade-step">
          <p className="eyebrow">Step {step + 1}</p>
          <h1 className="display mt-2 text-4xl">
            {SECTION_META[sectionSteps[step - 2]].title}
          </h1>
          <p className="mt-2 text-[13.5px] text-g500">
            {SECTION_META[sectionSteps[step - 2]].blurb} Peer-median defaults are
            pre-filled — correct the ones you know.
          </p>
          <div className="card mt-6 p-6">
            <div className="space-y-6">
              {stepQuestions.map((q) => (
                <QuestionField
                  key={q.id}
                  q={q}
                  value={answers[q.id]}
                  provenance={provenance[q.id]}
                  onChange={(v) => setAnswers((a) => ({ ...a, [q.id]: v }))}
                />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Navigation */}
      <div className="mt-8 flex items-center justify-between">
        <button
          onClick={() => {
            setStep(Math.max(0, step - 1));
            window.scrollTo({ top: 0, behavior: "smooth" });
          }}
          disabled={step === 0 || busy}
          className="rounded-md border border-g300 px-5 py-2.5 text-[13px] font-semibold text-g700 transition-colors hover:border-black disabled:opacity-40"
        >
          Back
        </button>
        <span className="text-[12px] text-g500">
          {step + 1} of {steps.length}
        </span>
        <button
          onClick={next}
          disabled={busy}
          className="rounded-md bg-flame px-6 py-2.5 text-[13px] font-semibold text-white transition-colors hover:bg-flame-dark disabled:opacity-60"
        >
          {busy
            ? "Computing the plan…"
            : step === lastStep
              ? "Generate the investment plan"
              : "Continue"}
        </button>
      </div>
      {step === lastStep && (
        <p className="mt-2 text-center text-[11.5px] text-g500">
          Deterministic: the same answers always produce the same plan.
        </p>
      )}
    </div>
  );
}

function QuestionField({
  q,
  value,
  provenance,
  onChange,
}: {
  q: Question;
  value: number | string | undefined;
  provenance?: PrefillField;
  onChange: (v: number | string) => void;
}) {
  const [exact, setExact] = useState(false);
  return (
    <div className="border-t border-g100 pt-4 first:border-t-0 first:pt-0">
      <p className="text-[13px] font-semibold text-black">
        {q.question}
        {provenance && (
          <span
            className={`ml-2 rounded px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide ${
              provenance.confidence === "High"
                ? "bg-flame/10 text-flame"
                : "bg-tangerine/15 text-[#9a6200]"
            }`}
          >
            Pre-filled ·{" "}
            {provenance.confidence === "High" ? "verified source" : "please verify"}
          </span>
        )}
      </p>
      {q.help && <p className="mt-0.5 text-xs text-g500">{q.help}</p>}
      {provenance && (
        <p className="mt-1 text-[11.5px] text-g500">
          Source:{" "}
          <a
            href={provenance.source_url}
            target="_blank"
            rel="noreferrer"
            className="text-flame underline"
          >
            {new URL(provenance.source_url).hostname}
          </a>{" "}
          — &ldquo;{provenance.quote.slice(0, 140)}&rdquo;
        </p>
      )}

      {q.type === "categorical" && (
        <div className="mt-2 flex flex-wrap gap-2">
          {q.options?.map((opt) => (
            <button
              key={opt}
              onClick={() => onChange(opt)}
              className={`rounded-md border px-3 py-1.5 text-[12.5px] transition-colors ${
                value === opt
                  ? "border-flame bg-flame text-white"
                  : "border-g300 text-g700 hover:border-black"
              }`}
            >
              {opt}
            </button>
          ))}
        </div>
      )}

      {q.type === "percentage" && q.bands && !exact && (
        <div className="mt-2">
          <div className="flex flex-wrap gap-2">
            {q.bands.map(([label, v]) => (
              <button
                key={label}
                onClick={() => onChange(v)}
                className={`rounded-md border px-3 py-1.5 text-[12.5px] transition-colors ${
                  Number(value) === v
                    ? "border-flame bg-flame text-white"
                    : "border-g300 text-g700 hover:border-black"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
          <button
            onClick={() => setExact(true)}
            className="mt-1.5 text-[11.5px] text-g500 underline hover:text-flame"
          >
            I know the exact figure
          </button>
        </div>
      )}

      {q.type === "percentage" && (!q.bands || exact) && (
        <div className="mt-2 flex items-center gap-4">
          <input
            type="range"
            min={0}
            max={100}
            value={Number(value ?? 50)}
            onChange={(e) => onChange(Number(e.target.value))}
            className="flex-1 accent-flame"
          />
          <span className="display w-14 text-right text-lg">
            {Number(value ?? 50)}%
          </span>
          {q.bands && (
            <button
              onClick={() => setExact(false)}
              className="text-[11.5px] text-g500 underline hover:text-flame"
            >
              back to ranges
            </button>
          )}
        </div>
      )}

      {q.type === "numeric" && (
        <input
          type="number"
          min={0}
          step="any"
          value={value ?? ""}
          onChange={(e) => onChange(e.target.value === "" ? 0 : Number(e.target.value))}
          className="mt-2 w-48 rounded-md border border-g300 px-3 py-2 text-sm text-black outline-none focus:border-flame"
        />
      )}
    </div>
  );
}
