"use client";

/**
 * The intake: one scrollable, sectioned form. Every question shows why it
 * is asked; sector selection gates which questions appear (same rule the
 * engine uses). Submit posts to the engine API and routes to the report.
 */
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  computeReport,
  fetchConfig,
  type Config,
  type Question,
} from "@/lib/api";

const SECTION_TITLES: Record<string, string> = {
  S1: "Technology & data",
  S2: "Front office",
  S3: "Middle & back office",
  S4: "Risk & compliance",
  S5: "Legacy systems & governance",
};

export default function DiagnosticPage() {
  const router = useRouter();
  const [cfg, setCfg] = useState<Config | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [company, setCompany] = useState("");
  const [sector, setSector] = useState("");
  const [goals, setGoals] = useState<string[]>([]);
  const [budget, setBudget] = useState(100);
  const [answers, setAnswers] = useState<Record<string, number | string>>({});

  useEffect(() => {
    fetchConfig()
      .then((c) => {
        setCfg(c);
        setSector(c.sectors[0]);
        const defaults: Record<string, number | string> = {};
        for (const q of c.questions)
          if (q.default !== undefined) defaults[q.id] = q.default;
        setAnswers(defaults);
      })
      .catch(() =>
        setError(
          "Could not reach the engine API. Start it with: uvicorn api.main:app --port 8000",
        ),
      );
  }, []);

  const visible = useMemo(() => {
    if (!cfg) return [];
    return cfg.questions.filter((q) => {
      const cond = q.visible_when?.sector;
      return !cond || cond.includes(sector);
    });
  }, [cfg, sector]);

  const sections = useMemo(() => {
    const by: Record<string, Question[]> = {};
    for (const q of visible) (by[q.section] ??= []).push(q);
    return by;
  }, [visible]);

  async function submit() {
    if (!company.trim()) {
      setError("Please name the firm — the report is addressed to it.");
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }
    setError(null);
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
      });
      sessionStorage.setItem("hz_report", JSON.stringify(report));
      sessionStorage.setItem(
        "hz_request",
        JSON.stringify({
          answers,
          company_name: company.trim(),
          target_sector: sector,
          budget_usd_m: budget,
          primary_goals: goals,
        }),
      );
      router.push("/report");
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
    <div className="mx-auto max-w-3xl px-6 py-12">
      <p className="eyebrow">The diagnostic</p>
      <h1 className="display mt-2 text-4xl">Tell us about the firm</h1>
      <p className="mt-2 text-[13.5px] text-g500">
        Sixteen questions, each stating why it is asked. Peer-median defaults
        are pre-filled — correct the ones you know.
      </p>

      {error && (
        <div className="mt-6 rounded-md border border-maroon bg-maroon/5 px-4 py-3 text-[13px] text-maroon">
          {error}
        </div>
      )}

      {/* Firm profile */}
      <section className="card mt-8 p-6">
        <h2 className="display text-xl">Firm profile</h2>
        <label className="mt-4 block text-[13px] font-semibold text-black">
          Firm name
          <input
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            placeholder="e.g. HDFC Asset Management"
            className="mt-1.5 w-full rounded-md border border-g300 px-3 py-2 text-sm text-black outline-none focus:border-flame"
          />
        </label>

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
          Use cases serving a selected goal reach full impact; off-goal ones are
          dampened, never hidden.
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
          Transformation budget: <span className="display text-lg">${budget}M</span>
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
      </section>

      {/* Question sections */}
      {Object.entries(sections).map(([sid, qs]) => (
        <section key={sid} className="card mt-6 p-6">
          <h2 className="display text-xl">{SECTION_TITLES[sid] ?? sid}</h2>
          <div className="mt-2 space-y-6">
            {qs.map((q) => (
              <QuestionField
                key={q.id}
                q={q}
                value={answers[q.id]}
                onChange={(v) => setAnswers((a) => ({ ...a, [q.id]: v }))}
              />
            ))}
          </div>
        </section>
      ))}

      <button
        onClick={submit}
        disabled={busy}
        className="mt-8 w-full rounded-md bg-flame px-8 py-3.5 text-sm font-semibold text-white transition-colors hover:bg-flame-dark disabled:opacity-60"
      >
        {busy ? "Computing the plan…" : "Generate the investment plan"}
      </button>
      <p className="mt-2 pb-12 text-center text-[11.5px] text-g500">
        Deterministic: the same answers always produce the same plan.
      </p>
    </div>
  );
}

function QuestionField({
  q,
  value,
  onChange,
}: {
  q: Question;
  value: number | string | undefined;
  onChange: (v: number | string) => void;
}) {
  return (
    <div className="border-t border-g100 pt-4 first:border-t-0 first:pt-0">
      <p className="text-[13px] font-semibold text-black">{q.question}</p>
      {q.help && <p className="mt-0.5 text-xs text-g500">{q.help}</p>}

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

      {q.type === "percentage" && (
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
        </div>
      )}

      {q.type === "numeric" && (
        <input
          type="number"
          min={0}
          value={Number(value ?? 0)}
          onChange={(e) => onChange(Number(e.target.value))}
          className="mt-2 w-48 rounded-md border border-g300 px-3 py-2 text-sm text-black outline-none focus:border-flame"
        />
      )}
    </div>
  );
}
