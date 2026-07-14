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
  fetchPrefill,
  type Config,
  type PrefillField,
  type Question,
} from "@/lib/api";
// eslint-disable-next-line @typescript-eslint/no-unused-vars


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
  const [existingIds, setExistingIds] = useState<string[]>([]);
  const [provenance, setProvenance] = useState<Record<string, PrefillField>>({});
  const [searching, setSearching] = useState(false);
  const [searchNote, setSearchNote] = useState<string | null>(null);

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
        setSearchNote("No retrieval ran: the engine API has no GEMINI_API_KEY configured. All fields stay manual.");
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
            `Found ${found.length} field(s) from public sources in ${p.duration_s.toFixed(0)}s — each is marked below with its source. Everything else stays manual; nothing was estimated.`,
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
        existing_lever_ids: existingIds,
      });
      sessionStorage.setItem("hz_report", JSON.stringify(report));
      router.push(`/report?run=${report.run_id}`);
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
          <span className="mt-1 block text-[11.5px] font-normal text-g500">
            Pulls verifiable facts (AUM, volumes) from filings and regulator
            data — every value arrives with its source and a quote.
          </span>
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

      {/* Current AI landscape: what is already live is never re-recommended */}
      <section className="card mt-6 p-6">
        <h2 className="display text-xl">Your current AI landscape</h2>
        <p className="mt-1 text-xs text-g500">
          Select every capability that is <b>already live in production</b> at
          the firm. Anything you select is excluded from the investment ask and
          shown as covered — this tool never recommends what you already run.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
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
                {existingIds.includes(l.id) ? "✓ " : ""}{l.short_name}
              </button>
            ))}
        </div>
        {existingIds.length > 0 && (
          <p className="mt-2 text-[12px] text-g500">
            {existingIds.length} capability(ies) will be marked as already
            covered in the report.
          </p>
        )}
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
                provenance={provenance[q.id]}
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
            Pre-filled · {provenance.confidence === "High" ? "verified source" : "please verify"}
          </span>
        )}
      </p>
      {q.help && <p className="mt-0.5 text-xs text-g500">{q.help}</p>}
      {provenance && (
        <p className="mt-1 text-[11.5px] text-g500">
          Source:{" "}
          <a href={provenance.source_url} target="_blank" rel="noreferrer"
            className="text-flame underline">
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
          value={Number(value ?? 0)}
          onChange={(e) => onChange(Number(e.target.value))}
          className="mt-2 w-48 rounded-md border border-g300 px-3 py-2 text-sm text-black outline-none focus:border-flame"
        />
      )}
    </div>
  );
}
