"use client";

/**
 * The prioritisation matrix as native SVG: value (y) × readiness (x),
 * bubble area = annual value, solid = funded. Direct labels use the same
 * collision-checked greedy placement as the pilot, ported to TS.
 */
import { useState } from "react";
import type { Lever } from "@/lib/api";

const W = 1000;
const H = 620;
const PAD = { l: 56, r: 24, t: 28, b: 46 };
const TI = 65; // impact threshold
const TF = 60; // feasibility threshold

type Slot = "top" | "bottom" | "bottomRight" | "topRight" | "right" | "left";
const SLOTS: Slot[] = ["top", "bottom", "bottomRight", "topRight", "right", "left"];

const sx = (v: number) => PAD.l + (v / 105) * (W - PAD.l - PAD.r);
const sy = (v: number) => H - PAD.b - (v / 105) * (H - PAD.t - PAD.b);
const rOf = (l: Lever) => Math.min(24, 8 + Math.sqrt(Math.max(0, l.anv_m)) * 4);

interface Box { x0: number; x1: number; y0: number; y1: number }
const overlaps = (a: Box, b: Box) =>
  a.x0 < b.x1 && b.x0 < a.x1 && a.y0 < b.y1 && b.y0 < a.y1;

function labelBox(l: Lever, slot: Slot): Box {
  const cx = sx(l.feasibility);
  const cy = sy(l.impact);
  const r = rOf(l);
  const w = Math.max(50, l.short_name.length * 6.6);
  const h = 14;
  const pad = 5;
  switch (slot) {
    case "top": return { x0: cx - w / 2, x1: cx + w / 2, y0: cy - r - pad - h, y1: cy - r - pad };
    case "bottom": return { x0: cx - w / 2, x1: cx + w / 2, y0: cy + r + pad, y1: cy + r + pad + h };
    case "topRight": return { x0: cx + r * 0.7, x1: cx + r * 0.7 + w, y0: cy - r - h, y1: cy - r };
    case "bottomRight": return { x0: cx + r * 0.7, x1: cx + r * 0.7 + w, y0: cy + r, y1: cy + r + h };
    case "right": return { x0: cx + r + pad, x1: cx + r + pad + w, y0: cy - h / 2, y1: cy + h / 2 };
    case "left": return { x0: cx - r - pad - w, x1: cx - r - pad, y0: cy - h / 2, y1: cy + h / 2 };
  }
}

function placeLabels(levers: Lever[]): Map<string, Box> {
  const funded = levers
    .filter((l) => l.budget_approved)
    .sort((a, b) => b.impact - a.impact || a.feasibility - b.feasibility);
  const bubbles: Box[] = levers.map((l) => {
    const cx = sx(l.feasibility), cy = sy(l.impact), r = rOf(l);
    return { x0: cx - r, x1: cx + r, y0: cy - r, y1: cy + r };
  });
  const placed = new Map<string, Box>();
  const area = (a: Box, b: Box) =>
    Math.max(0, Math.min(a.x1, b.x1) - Math.max(a.x0, b.x0)) *
    Math.max(0, Math.min(a.y1, b.y1) - Math.max(a.y0, b.y0));

  for (const l of funded) {
    let best: Box | null = null;
    let bestCost = Infinity;
    for (const slot of SLOTS) {
      const box = labelBox(l, slot);
      let cost = 0;
      for (const b of placed.values()) cost += area(box, b);
      levers.forEach((o, i) => {
        if (o.id !== l.id) cost += area(box, bubbles[i]);
      });
      if (box.x0 < PAD.l || box.x1 > W - PAD.r || box.y0 < PAD.t || box.y1 > H - PAD.b)
        cost += 5000;
      if (cost === 0) { best = box; break; }
      if (cost < bestCost) { bestCost = cost; best = box; }
    }
    if (best) placed.set(l.id, best);
  }
  return placed;
}

export default function Matrix({ levers }: { levers: Lever[] }) {
  const [hover, setHover] = useState<Lever | null>(null);
  const labels = placeLabels(levers);

  return (
    <div className="card relative overflow-hidden">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full">
        {/* Strategic-bets quadrant tint */}
        <rect x={sx(TF)} y={PAD.t} width={sx(105) - sx(TF)} height={sy(TI) - PAD.t}
          fill="rgba(208,74,2,0.06)" />
        <line x1={PAD.l} x2={W - PAD.r} y1={sy(TI)} y2={sy(TI)} stroke="#dedede" />
        <line x1={sx(TF)} x2={sx(TF)} y1={PAD.t} y2={H - PAD.b} stroke="#dedede" />

        {/* Corner guidance */}
        <text x={W - PAD.r - 6} y={PAD.t + 14} textAnchor="end" fontSize="11" fontWeight="600" fill="#d04a02">STRATEGIC BETS · fund first</text>
        <text x={W - PAD.r - 6} y={H - PAD.b - 8} textAnchor="end" fontSize="11" fontWeight="600" fill="#7d7d7d">QUICK WINS · fast, lower value</text>
        <text x={PAD.l + 6} y={PAD.t + 14} fontSize="11" fontWeight="600" fill="#7d7d7d">BLOCKED · fix the data foundation first</text>
        <text x={PAD.l + 6} y={H - PAD.b - 8} fontSize="11" fontWeight="600" fill="#bdbdbd">LOWER PRIORITY</text>

        {/* Axes */}
        <text x={(PAD.l + W - PAD.r) / 2} y={H - 10} textAnchor="middle" fontSize="12" fill="#7d7d7d">Readiness to deliver →</text>
        <text x={16} y={(PAD.t + H - PAD.b) / 2} fontSize="12" fill="#7d7d7d"
          transform={`rotate(-90 16 ${(PAD.t + H - PAD.b) / 2})`} textAnchor="middle">Value to the business →</text>

        {/* Bubbles */}
        {levers.map((l) => {
          const cx = sx(l.feasibility), cy = sy(l.impact), r = rOf(l);
          const grey = ["Blocked", "Lower priority"].includes(l.quadrant_label);
          const color = grey ? "#7d7d7d" : "#d04a02";
          return (
            <circle key={l.id} cx={cx} cy={cy} r={r}
              fill={l.budget_approved ? color : "transparent"}
              stroke={l.budget_approved ? "#fff" : color}
              strokeWidth={l.budget_approved ? 2 : 1.5}
              opacity={hover && hover.id !== l.id ? 0.35 : 1}
              style={{ transition: "opacity 140ms", cursor: "pointer" }}
              onMouseEnter={() => setHover(l)}
              onMouseLeave={() => setHover(null)} />
          );
        })}

        {/* Collision-placed labels for the funded plan */}
        {levers.filter((l) => labels.has(l.id)).map((l) => {
          const b = labels.get(l.id)!;
          return (
            <text key={`lb-${l.id}`} x={(b.x0 + b.x1) / 2} y={b.y1 - 3}
              textAnchor="middle" fontSize="11.5" fontWeight="500" fill="#2d2d2d">
              {l.short_name}
            </text>
          );
        })}
      </svg>

      {/* Hover detail card */}
      {hover && (
        <div className="pointer-events-none absolute right-4 top-4 w-64 rounded-md border border-g200 bg-white p-3 shadow-lg">
          <p className="text-[13px] font-bold text-black">{hover.name}</p>
          <p className="text-xs text-g500">
            {hover.budget_approved ? "Funded in this plan" : "Not funded in this plan"}
          </p>
          <p className="mt-1 text-xs">
            Value ${hover.anv_m.toFixed(1)}M/yr · Build ${hover.impl_cost_m.toFixed(1)}M
            {hover.payback_months ? ` · Pays back in ${Math.round(hover.payback_months)} mo` : ""}
          </p>
          <p className="text-xs text-g500">
            Value score {hover.impact}/100 · Readiness {hover.feasibility}/100
          </p>
        </div>
      )}

      <div className="flex flex-wrap items-center justify-center gap-5 border-t border-g100 py-2.5 text-xs text-g500">
        <span><span className="mr-1.5 inline-block h-2.5 w-2.5 rounded-full bg-flame align-middle" />Funded in this plan</span>
        <span><span className="mr-1.5 inline-block h-2.5 w-2.5 rounded-full border-[1.5px] border-flame align-middle" />Not funded</span>
        <span>Circle size = annual value ($M per year)</span>
      </div>
    </div>
  );
}
