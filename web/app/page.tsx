import Link from "next/link";

const DELIVERABLES = [
  {
    n: "01",
    title: "A prioritised, funded portfolio",
    desc: "Every AI use case scored on value and readiness, ranked against your budget",
  },
  {
    n: "02",
    title: "A verdict on your legacy estate",
    desc: "Keep, modernize in phases, or replace, with a bottom-up cost estimate and break-even",
  },
  {
    n: "03",
    title: "A compliance-checked roadmap",
    desc: "Each use case screened against Indian regulatory constraints before it is funded",
  },
];

const STEPS = [
  {
    n: "01",
    title: "Answer 16 questions",
    desc: "Your scale, operations, compliance posture and legacy footprint — each question states why it is asked.",
  },
  {
    n: "02",
    title: "The engine computes",
    desc: "Deterministic financial models size each use case from your answers, haircut them for realism, and screen them against regulation.",
  },
  {
    n: "03",
    title: "Decide with evidence",
    desc: "A funded portfolio, a legacy verdict with break-even, and every assumption on the table.",
  },
];

export default function Landing() {
  return (
    <>
      <section className="border-b-[3px] border-flame bg-[radial-gradient(circle_at_80%_50%,#201a15_0%,#111111_100%)] text-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-12 px-6 py-16 lg:flex-row lg:items-center">
          <div className="max-w-xl flex-1">
            <span className="inline-block rounded-full border border-flame bg-flame/10 px-3 py-1 text-[11px] font-bold uppercase tracking-widest text-flame">
              BFSI · AI Investment Diagnostic
            </span>
            <h1 className="display mt-5 text-5xl leading-[1.1] !text-white">
              Where should your
              <br />
              next AI dollar go?
            </h1>
            <p className="mt-4 max-w-lg text-[15px] leading-relaxed text-g300">
              A 15-minute diagnostic that turns your operating data into a
              board-ready AI investment plan: prioritised, budget-constrained,
              and traceable down to every constant in the model.
            </p>
            <div className="mt-7 flex flex-wrap gap-2">
              {["14 value levers", "3 execution scenarios", "IRDAI / RBI / SEBI overlay", "Fully auditable math"].map(
                (b) => (
                  <span
                    key={b}
                    className="rounded-full border border-[#333] bg-[#1e1e1e] px-3 py-1.5 text-[11px] text-g300"
                  >
                    {b}
                  </span>
                ),
              )}
            </div>
            <Link
              href="/diagnostic"
              className="mt-9 inline-block rounded-md bg-flame px-8 py-3 text-sm font-semibold text-white transition-colors hover:bg-flame-dark"
            >
              Begin the diagnostic
            </Link>
            <p className="mt-2 text-[11.5px] text-g500">
              About 15 minutes · No data leaves the session without your say
            </p>
          </div>

          <div className="w-full max-w-md rounded-lg border border-[#2a2a2a] bg-[#161616] p-5 shadow-2xl">
            <p className="border-b border-[#333] pb-3 text-[10px] font-bold uppercase tracking-widest text-g300">
              What you receive
            </p>
            {DELIVERABLES.map((d, i) => (
              <div
                key={d.n}
                className={`flex gap-3 py-3.5 ${i < 2 ? "border-b border-[#262626]" : ""}`}
              >
                <span className="display min-w-6 text-[15px] !text-flame">{d.n}</span>
                <div>
                  <p className="text-[13.5px] font-bold text-white">{d.title}</p>
                  <p className="mt-0.5 text-xs leading-relaxed text-g300">{d.desc}</p>
                </div>
              </div>
            ))}
            <p className="border-t border-[#333] pt-3 text-[10.5px] text-g500">
              Every number traces back to your answers. Nothing is estimated
              silently.
            </p>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-16">
        <div className="text-center">
          <p className="eyebrow">How it works</p>
          <h2 className="display mt-2 text-3xl">
            From intake to board-ready plan in one session
          </h2>
        </div>
        <div className="mt-9 grid gap-6 md:grid-cols-3">
          {STEPS.map((s) => (
            <div key={s.n} className="card card-hover p-6">
              <p className="display text-3xl !text-flame opacity-35">{s.n}</p>
              <p className="mt-3 text-[15px] font-bold text-black">{s.title}</p>
              <p className="mt-1.5 text-[13px] leading-relaxed">{s.desc}</p>
            </div>
          ))}
        </div>
        <div className="mt-14 flex items-center justify-between border-t border-g200 pt-4">
          <span className="display text-[22px] font-bold !text-flame">pwc</span>
          <span className="text-[11px] text-g500">
            Deterministic math · Sourced benchmarks · Narrative grounded in the
            computed plan
          </span>
        </div>
      </section>
    </>
  );
}
