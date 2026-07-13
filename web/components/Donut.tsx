"use client";

/**
 * Budget-position donut, native SVG. Segments: AI use cases (flame),
 * modernization (maroon, when in plan), uncommitted (neutral). Center
 * hero states the committed total — the number the section exists for.
 */
export default function Donut({
  leversM,
  modernM,
  uncommittedM,
  budgetM,
}: {
  leversM: number;
  modernM: number;
  uncommittedM: number;
  budgetM: number;
}) {
  const committed = leversM + modernM;
  const R = 74;
  const CIRC = 2 * Math.PI * R;
  const total = Math.max(0.0001, leversM + modernM + uncommittedM);

  const segments = [
    { label: "AI use cases", value: leversM, color: "#d04a02" },
    ...(modernM > 0 ? [{ label: "Modernization", value: modernM, color: "#a32020" }] : []),
    { label: "Uncommitted", value: uncommittedM, color: "#dedede" },
  ];

  let offset = 0;
  const arcs = segments.map((s) => {
    const frac = s.value / total;
    const arc = { ...s, dash: frac * CIRC, offset };
    offset += frac * CIRC;
    return arc;
  });

  return (
    <div className="flex items-center gap-8">
      <svg viewBox="0 0 200 200" className="h-56 w-56 shrink-0">
        {arcs.map((a) => (
          <circle key={a.label} cx="100" cy="100" r={R} fill="none"
            stroke={a.color} strokeWidth="30"
            strokeDasharray={`${Math.max(0, a.dash - 2)} ${CIRC - Math.max(0, a.dash - 2)}`}
            strokeDashoffset={-a.offset}
            transform="rotate(-90 100 100)" />
        ))}
        <text x="100" y="97" textAnchor="middle" fontSize="26"
          fontFamily="Georgia, serif" fill="#000">
          ${committed.toFixed(1)}M
        </text>
        <text x="100" y="115" textAnchor="middle" fontSize="10.5" fill="#7d7d7d">
          committed of ${budgetM.toFixed(0)}M
        </text>
      </svg>
      <div className="space-y-2">
        {arcs.map((a) => (
          <div key={a.label} className="flex items-center gap-2.5 text-[13px]">
            <span className="h-3 w-3 rounded-sm" style={{ background: a.color }} />
            <span className="text-g700">{a.label}</span>
            <span className="font-semibold text-black">${a.value.toFixed(1)}M</span>
          </div>
        ))}
        <p className="max-w-[220px] pt-1 text-[11.5px] leading-relaxed text-g500">
          Capital is committed only where a use case clears the bar. The
          uncommitted balance is held, not spent.
        </p>
      </div>
    </div>
  );
}
