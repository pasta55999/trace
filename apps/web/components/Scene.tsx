/** Light, editorial SVG scenes (factory / warehouse / distribution / cold store) used as card backdrops and thumbnails. */
export type SceneKind = "factory" | "warehouse" | "dist" | "cold";

export const sceneFor = (sectorOrType: string): SceneKind =>
  /manufact|industrial/i.test(sectorOrType) ? "factory" : /transport|storage|warehouse/i.test(sectorOrType) ? "warehouse" : /wholesale|distrib/i.test(sectorOrType) ? "dist" : "cold";

const P: Record<SceneKind, { sky: [string, string]; bld: string; bld2: string; accent: string; ground: string }> = {
  factory: { sky: ["#f3ecdf", "#e6d9c3"], bld: "#b9a98f", bld2: "#d9cdb6", accent: "#d99a2b", ground: "#e9dfcb" },
  warehouse: { sky: ["#e6f0f2", "#cfe1e6"], bld: "#98b1b7", bld2: "#c6d8dc", accent: "#3f8c92", ground: "#d9e6e9" },
  dist: { sky: ["#ecebf4", "#d9d8ea"], bld: "#a2a3c2", bld2: "#cfcfe3", accent: "#7d7fc4", ground: "#e2e1ee" },
  cold: { sky: ["#e8f0f8", "#d3e2f1"], bld: "#97b0cc", bld2: "#c6d7e8", accent: "#3b7dd8", ground: "#dce7f3" },
};

export default function Scene({ kind, style }: { kind: SceneKind; style?: React.CSSProperties }) {
  const p = P[kind];
  const id = `sc-${kind}`;
  return (
    <svg viewBox="0 0 400 200" preserveAspectRatio="xMidYMid slice" aria-hidden style={{ position: "absolute", inset: 0, width: "100%", height: "100%", ...style }}>
      <defs><linearGradient id={id} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={p.sky[0]} /><stop offset="1" stopColor={p.sky[1]} /></linearGradient></defs>
      <rect width="400" height="200" fill={`url(#${id})`} />
      <circle cx="320" cy="50" r="26" fill="#fff" opacity=".55" />
      <g fill={p.bld2}>
        {kind === "factory" && (<><rect x="30" y="112" width="120" height="70" /><rect x="160" y="126" width="100" height="56" /><rect x="272" y="104" width="70" height="78" /><rect x="52" y="60" width="10" height="54" /><rect x="84" y="72" width="10" height="42" /><rect x="292" y="58" width="12" height="48" /></>)}
        {kind === "warehouse" && (<><path d="M24 182 V122 Q24 96 56 96 H226 Q258 96 258 122 V182 Z" /><rect x="272" y="132" width="106" height="50" /></>)}
        {kind === "dist" && (<><rect x="16" y="120" width="210" height="62" /><rect x="244" y="136" width="140" height="46" /><rect x="254" y="120" width="42" height="16" rx="3" /><rect x="304" y="120" width="42" height="16" rx="3" /></>)}
        {kind === "cold" && (<><rect x="56" y="104" width="176" height="78" /><rect x="252" y="126" width="104" height="56" /><rect x="66" y="94" width="156" height="10" fill={p.accent} opacity=".45" /></>)}
      </g>
      <g fill={p.bld} opacity=".9">
        {kind === "factory" && (<><rect x="40" y="130" width="100" height="52" /><path d="M160 126 l25 -20 l25 20 l25 -20 l25 20 V140 H160 Z" /></>)}
        {kind === "warehouse" && (<><rect x="56" y="140" width="34" height="42" /><rect x="112" y="140" width="34" height="42" /><rect x="168" y="140" width="34" height="42" /><path d="M34 122 H248" stroke={p.bld} strokeWidth="3" /></>)}
        {kind === "dist" && (<>{[36, 80, 124, 168].map((x) => <rect key={x} x={x} y="150" width="26" height="32" />)}</>)}
        {kind === "cold" && (<>{[86, 128, 170].map((x) => <rect key={x} x={x} y="126" width="24" height="56" />)}</>)}
      </g>
      <rect x="0" y="182" width="400" height="18" fill={p.ground} />
      <path d="M0 182 H400" stroke={p.accent} strokeOpacity=".5" strokeWidth="1.2" />
    </svg>
  );
}
