"use client";

/**
 * The engagements list: every generated report, rebuildable by URL from
 * the audit trail. This is what makes reports durable product objects
 * instead of browser sessions.
 */
import { useEffect, useState } from "react";
import Link from "next/link";
import { listRuns, type RunListItem } from "@/lib/api";

export default function EngagementsPage() {
  const [runs, setRuns] = useState<RunListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listRuns().then(setRuns).catch((e) => setError(String(e)));
  }, []);

  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <p className="eyebrow">Engagements</p>
      <h1 className="display mt-2 text-4xl">Every report, rebuildable</h1>
      <p className="mt-2 max-w-2xl text-[13.5px] text-g500">
        Each run is stored with its exact inputs and settings; opening one
        rebuilds the report deterministically through the current engine.
      </p>

      {error && <p className="mt-6 text-[13px] text-maroon">{error}</p>}
      {!runs && !error && <p className="mt-6 text-g500">Loading…</p>}

      {runs && runs.length === 0 && (
        <p className="mt-6 text-g500">
          No engagements yet.{" "}
          <Link href="/diagnostic" className="text-flame underline">
            Run the first diagnostic.
          </Link>
        </p>
      )}

      {runs && runs.length > 0 && (
        <div className="card mt-6 overflow-x-auto">
          <table className="hz-table">
            <thead>
              <tr>
                <th>Firm</th>
                <th>Generated</th>
                <th>Source</th>
                <th>Run</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr key={r.run_id}>
                  <td>
                    <Link
                      href={`/report?run=${r.run_id}`}
                      className="font-semibold text-black hover:text-flame"
                    >
                      {r.company || "Unnamed engagement"}
                    </Link>
                  </td>
                  <td className="text-g500">
                    {new Date(r.ts).toLocaleString()}
                  </td>
                  <td className="text-g500">{r.mode}</td>
                  <td className="font-mono text-xs text-g500">{r.run_id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
