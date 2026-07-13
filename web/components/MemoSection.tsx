"use client";

/**
 * The executive memo: generated on demand (LLM spend is a user choice,
 * never a side effect), grounded in the computed plan, and honest about
 * whether the narrative came from the model or the deterministic fallback.
 */
import { useEffect, useState } from "react";
import { API_URL, type ReportRequest } from "@/lib/api";

interface Memo {
  generated: boolean;
  paragraphs: string[];
  grounded_on: string[];
}

export default function MemoSection({ request }: { request: ReportRequest }) {
  const [memo, setMemo] = useState<Memo | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cacheKey = "hz_memo_" + JSON.stringify([request.company_name, request.scenario, request.ai_stack, request.foundation_decision]);

  useEffect(() => {
    const cached = sessionStorage.getItem(cacheKey);
    setMemo(cached ? JSON.parse(cached) : null);
  }, [cacheKey]);

  async function generate() {
    setBusy(true);
    setError(null);
    try {
      const r = await fetch(`${API_URL}/api/memo`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      });
      if (!r.ok) throw new Error(`memo failed: ${r.status}`);
      const m: Memo = await r.json();
      sessionStorage.setItem(cacheKey, JSON.stringify(m));
      setMemo(m);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card mt-4 p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-[15px] font-bold text-black">The executive memo</p>
          <p className="mt-0.5 text-xs text-g500">
            Three narrative paragraphs grounded in this plan&apos;s strategic
            bets. Generated only when you ask.
          </p>
        </div>
        <button
          onClick={generate}
          disabled={busy}
          className="shrink-0 rounded-md border border-flame px-4 py-2 text-[13px] font-semibold text-flame transition-colors hover:bg-flame hover:text-white disabled:opacity-50"
        >
          {busy ? "Writing…" : memo ? "Regenerate" : "Generate the memo"}
        </button>
      </div>

      {error && <p className="mt-3 text-[13px] text-maroon">{error}</p>}

      {memo && (
        <div className="mt-4 border-t border-g100 pt-4">
          {memo.paragraphs.map((p, i) => (
            <p key={i} className="mt-3 max-w-3xl text-sm leading-relaxed first:mt-0">
              {p}
            </p>
          ))}
          <p className="mt-4 text-[11px] text-g500">
            {memo.generated
              ? "Narrative by Gemini, grounded in the computed plan — review before sharing."
              : "Deterministic fallback narrative (no AI key configured or the model was unavailable)."}
            {" "}Grounded on: {memo.grounded_on.join(", ")}.
          </p>
        </div>
      )}
    </div>
  );
}
