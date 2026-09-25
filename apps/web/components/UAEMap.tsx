"use client";
/** Simplified UAE outline (lon 51.4–56.6, lat 22.4–26.4) with projected asset markers. Illustrative geometry. */
const LON = [51.3, 57.0], LAT = [22.4, 26.4];
const W = 640, H = 495; // aspect ≈ (Δlon·cos 24.4°)/Δlat
export const project = (lon: number, lat: number): [number, number] => [((lon - LON[0]) / (LON[1] - LON[0])) * W, H - ((lat - LAT[0]) / (LAT[1] - LAT[0])) * H];

// coastline runs SW->NE along the Gulf, Musandam tip at the top right, east coast down to Fujairah, then the desert border.
const UAE: [number, number][] = [
  [51.58, 24.25], [51.9, 24.05], [52.3, 24.15], [52.7, 24.15], [53.1, 24.1], [53.5, 24.15], [53.9, 24.2], [54.2, 24.35], [54.45, 24.5],
  [54.7, 24.75], [55.0, 24.95], [55.3, 25.28], [55.5, 25.45], [55.7, 25.65], [55.9, 25.85], [56.02, 26.06], [56.12, 26.0], [56.2, 25.75], [56.3, 25.55],
  [56.36, 25.3], [56.35, 25.0], [56.2, 24.9], [56.0, 24.85], [55.82, 24.6], [55.8, 24.2], [55.6, 23.95], [55.6, 23.4], [55.4, 22.9],
  [55.1, 22.65], [54.5, 22.7], [53.5, 22.75], [52.6, 22.95], [52.0, 23.1], [51.6, 23.7],
];
const LABELS: { n: string; lon: number; lat: number }[] = [{ n: "Abu Dhabi", lon: 54.37, lat: 24.45 }, { n: "Dubai", lon: 55.27, lat: 25.2 }, { n: "Al Ain", lon: 55.75, lat: 24.2 }, { n: "Fujairah", lon: 56.33, lat: 25.12 }];

export interface Marker { id: string; lon: number | null; lat: number | null; level: "high" | "medium" | "low" | "unknown"; label?: string; district?: string | null }
const DISTRICT_FALLBACK: Record<string, [number, number]> = { "D-JAI": [55.03, 24.98], "D-AQ3": [55.24, 25.135], "D-DIFC": [55.28, 25.21] };
const COLOR = { high: "var(--red)", medium: "var(--amber)", low: "var(--sage)", unknown: "var(--faint)" };

export default function UAEMap({ markers, onSelect }: { markers: Marker[]; onSelect?: (id: string) => void }) {
  const path = UAE.map(([lo, la], i) => `${i ? "L" : "M"}${project(lo, la).map((v) => v.toFixed(1)).join(",")}`).join(" ") + " Z";
  return (
    <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="UAE exposure map">
      <defs>
        <linearGradient id="land" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#f6f3ea" /><stop offset="1" stopColor="#ece6d6" /></linearGradient>
        <filter id="soft"><feGaussianBlur stdDeviation="1.2" /></filter>
        <pattern id="dots" width="10" height="10" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".7" fill="#c7d3d8" /></pattern>
      </defs>
      <rect width={W} height={H} fill="url(#dots)" opacity=".7" />
      <path d={path} fill="#d7e2e6" filter="url(#soft)" transform="translate(0,3)" opacity=".8" />
      <path d={path} fill="url(#land)" stroke="#c8c1ad" strokeWidth="1.2" />
      {LABELS.map((l) => { const [x, y] = project(l.lon, l.lat); return <text key={l.n} x={x + 8} y={y - 6} fontSize="11" fill="#5b6a63" fontWeight="500">{l.n}</text>; })}
      {markers.map((m, i) => {
        const pos = m.lon !== null && m.lat !== null ? project(m.lon, m.lat) : m.district && DISTRICT_FALLBACK[m.district] ? project(...DISTRICT_FALLBACK[m.district]) : null;
        if (!pos) return null;
        const jitter = (i % 3) * 4 - 4;
        return (
          <g key={m.id} transform={`translate(${pos[0] + jitter},${pos[1] + jitter})`} style={{ cursor: onSelect ? "pointer" : "default" }} onClick={() => onSelect?.(m.id)}>
            {m.level === "high" && <circle r="12" fill={COLOR.high} opacity=".18"><animate attributeName="r" values="8;16;8" dur="2.8s" repeatCount="indefinite" /></circle>}
            <circle r="5.5" fill={COLOR[m.level]} stroke="#fff" strokeWidth="2" strokeDasharray={m.level === "unknown" ? "2 2" : undefined} />
            <title>{m.label ?? m.id}</title>
          </g>
        );
      })}
    </svg>
  );
}
