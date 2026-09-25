"use client";
import { compactNum } from "@/lib/i18n";

/** Horizontal-ish bar chart with optional low/high range whiskers. Pure SVG, no dependencies. */
export function BarChart({ rows, height = 170 }: { rows: { label: string; value: number | null; low?: number; high?: number; color?: string }[]; height?: number }) {
  const max = Math.max(1, ...rows.map((r) => r.high ?? r.value ?? 0));
  const w = 100 / Math.max(rows.length, 1);
  return (
    <svg viewBox="0 0 100 60" preserveAspectRatio="none" className="sparkline" style={{ height }}>
      {[0.25, 0.5, 0.75, 1].map((g) => <line key={g} x1="0" x2="100" y1={55 - g * 50} y2={55 - g * 50} stroke="rgba(255,255,255,.06)" strokeWidth=".3" />)}
      {rows.map((r, i) => {
        const x = i * w + w * 0.2, bw = w * 0.6;
        if (r.value === null) return <g key={i}><rect x={x} y={5} width={bw} height={50} fill="rgba(255,255,255,.04)" stroke="rgba(255,255,255,.15)" strokeDasharray="1 1" strokeWidth=".3" /><text x={x + bw / 2} y={32} fontSize="3" fill="#8a97a8" textAnchor="middle">?</text></g>;
        const h = (r.value / max) * 50;
        return (
          <g key={i}>
            <rect x={x} y={55 - h} width={bw} height={h} rx=".8" fill={r.color ?? "url(#g)"} />
            {r.low !== undefined && r.high !== undefined && r.low !== r.high && (
              <line x1={x + bw / 2} x2={x + bw / 2} y1={55 - (r.high / max) * 50} y2={55 - (r.low / max) * 50} stroke="#e6ebf1" strokeWidth=".5" />
            )}
          </g>
        );
      })}
      <defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#2fb9c9" /><stop offset="1" stopColor="#1b4f6b" /></linearGradient></defs>
    </svg>
  );
}

export function BarLabels({ rows }: { rows: { label: string; value: number | null }[] }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: `repeat(${rows.length}, 1fr)`, textAlign: "center", fontSize: 11, color: "var(--muted)" }}>
      {rows.map((r) => <div key={r.label}><div className="num" style={{ color: "var(--ink-2)" }}>{r.value === null ? "—" : compactNum(r.value)}</div>{r.label}</div>)}
    </div>
  );
}

/** Two-line comparison (baseline vs protected) drawn across scenario stages. */
export function LineCompare({ a, b, labels }: { a: number[]; b: number[]; labels: string[] }) {
  const max = Math.max(1, ...a, ...b);
  const pts = (arr: number[]) => arr.map((v, i) => `${(i / Math.max(arr.length - 1, 1)) * 100},${55 - (v / max) * 48}`).join(" ");
  return (
    <div>
      <svg viewBox="0 0 100 60" preserveAspectRatio="none" className="sparkline">
        {[0.25, 0.5, 0.75, 1].map((g) => <line key={g} x1="0" x2="100" y1={55 - g * 48} y2={55 - g * 48} stroke="rgba(255,255,255,.06)" strokeWidth=".3" />)}
        <polyline points={pts(a)} fill="none" stroke="#ff6b6b" strokeWidth="1" vectorEffect="non-scaling-stroke" />
        <polyline points={pts(b)} fill="none" stroke="#2fb9c9" strokeWidth="1" vectorEffect="non-scaling-stroke" />
        {a.map((v, i) => <circle key={`a${i}`} cx={(i / Math.max(a.length - 1, 1)) * 100} cy={55 - (v / max) * 48} r="1" fill="#ff6b6b" />)}
        {b.map((v, i) => <circle key={`b${i}`} cx={(i / Math.max(b.length - 1, 1)) * 100} cy={55 - (v / max) * 48} r="1" fill="#2fb9c9" />)}
      </svg>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--muted)" }}>{labels.map((l) => <span key={l}>{l}</span>)}</div>
    </div>
  );
}
