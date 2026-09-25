/** Atmospheric SVG scenes (factory / warehouse / distribution / cold store) used as card backdrops. */
export type SceneKind = "factory" | "warehouse" | "dist" | "cold";

export const sceneFor = (sectorOrType: string): SceneKind =>
  /manufact|industrial/i.test(sectorOrType) ? "factory" : /transport|storage|warehouse/i.test(sectorOrType) ? "warehouse" : /wholesale|distrib/i.test(sectorOrType) ? "dist" : "cold";

const PALETTE: Record<SceneKind, { sky: [string, string]; glow: string; ground: string }> = {
  factory: { sky: ["#2b2a3a", "#0a0f16"], glow: "#f5b84a", ground: "#0c1218" },
  warehouse: { sky: ["#13303b", "#0a0f16"], glow: "#7fe0ea", ground: "#0b1117" },
  dist: { sky: ["#241f3f", "#0a0f16"], glow: "#8b7cf6", ground: "#0b1017" },
  cold: { sky: ["#10263f", "#0a0f16"], glow: "#4f8df7", ground: "#0a1119" },
};

export default function Scene({ kind, className }: { kind: SceneKind; className?: string }) {
  const p = PALETTE[kind];
  const id = `sky-${kind}`;
  return (
    <svg className={className} viewBox="0 0 400 200" preserveAspectRatio="xMidYMid slice" aria-hidden style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={p.sky[0]} /><stop offset="1" stopColor={p.sky[1]} /></linearGradient>
        <radialGradient id={`${id}-g`} cx="0.5" cy="0.5" r="0.5"><stop offset="0" stopColor={p.glow} stopOpacity=".55" /><stop offset="1" stopColor={p.glow} stopOpacity="0" /></radialGradient>
      </defs>
      <rect width="400" height="200" fill={`url(#${id})`} />
      <ellipse cx={kind === "factory" ? 300 : 110} cy="70" rx="150" ry="70" fill={`url(#${id}-g)`} />
      {/* stars / dust */}
      {[30, 80, 140, 210, 260, 330, 370].map((x, i) => <circle key={x} cx={x} cy={20 + (i * 13) % 50} r=".8" fill="#fff" opacity=".45" />)}
      <g fill="#141d27" stroke="rgba(255,255,255,.16)" strokeWidth=".8">
        {kind === "factory" && (<>
          <rect x="40" y="110" width="120" height="70" /><rect x="170" y="125" width="90" height="55" /><rect x="270" y="100" width="60" height="80" />
          <rect x="60" y="60" width="10" height="55" /><rect x="90" y="70" width="10" height="45" /><rect x="290" y="55" width="12" height="50" />
          <path d="M170 125 l22 -18 l23 18 l22 -18 l23 18" fill="none" />
          <circle cx="65" cy="52" r="6" fill="rgba(255,255,255,.06)" stroke="none" /><circle cx="296" cy="46" r="7" fill="rgba(255,255,255,.05)" stroke="none" />
        </>)}
        {kind === "warehouse" && (<>
          <path d="M30 180 V120 Q30 95 60 95 H220 Q250 95 250 120 V180 Z" /><rect x="262" y="130" width="110" height="50" />
          <rect x="60" y="140" width="30" height="40" fill="rgba(127,224,234,.10)" stroke="none" /><rect x="110" y="140" width="30" height="40" fill="rgba(127,224,234,.08)" stroke="none" /><rect x="160" y="140" width="30" height="40" fill="rgba(127,224,234,.10)" stroke="none" />
          <path d="M40 120 H240" stroke="rgba(255,255,255,.12)" />
        </>)}
        {kind === "dist" && (<>
          <rect x="20" y="120" width="200" height="60" /><rect x="240" y="135" width="140" height="45" />
          {[40, 80, 120, 160].map((x) => <rect key={x} x={x} y="150" width="24" height="30" fill="rgba(139,124,246,.14)" stroke="none" />)}
          <rect x="250" y="120" width="40" height="15" rx="2" /><rect x="300" y="120" width="40" height="15" rx="2" />
          <path d="M0 185 H400" stroke="rgba(139,124,246,.35)" strokeWidth="1" />
        </>)}
        {kind === "cold" && (<>
          <rect x="60" y="105" width="170" height="75" /><rect x="250" y="125" width="100" height="55" />
          <rect x="70" y="95" width="150" height="10" fill="rgba(79,141,247,.25)" stroke="none" />
          {[90, 130, 170].map((x) => <rect key={x} x={x} y="125" width="22" height="55" fill="rgba(79,141,247,.12)" stroke="none" />)}
          <circle cx="300" cy="115" r="9" fill="rgba(79,141,247,.2)" stroke="none" />
        </>)}
      </g>
      <rect x="0" y="180" width="400" height="20" fill={p.ground} />
      <path d="M0 180 H400" stroke={p.glow} strokeOpacity=".35" strokeWidth=".8" />
    </svg>
  );
}
