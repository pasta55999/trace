/**
 * trace wordmark — thin monoline geometric letterforms drawn as paths (no font dependency),
 * with the distinctive long crossbar running from the "t" across the top of the "r".
 */
export default function Logo({ size = 28, color = "currentColor", glow = false }: { size?: number; color?: string; glow?: boolean }) {
  const h = size, w = size * 2.85;
  return (
    <svg width={w} height={h} viewBox="0 0 285 100" fill="none" stroke={color} strokeWidth="5.5" strokeLinecap="round" strokeLinejoin="round" aria-label="trace" role="img" style={glow ? { filter: "drop-shadow(0 0 10px rgba(127,224,234,.45))" } : undefined}>
      {/* t : stem with a soft foot, long crossbar */}
      <path d="M24 16 V64 Q24 78 40 78" />
      <path d="M8 36 H92" />
      {/* r */}
      <path d="M76 78 V46" />
      <path d="M76 58 Q78 44 96 44" />
      {/* a */}
      <circle cx="128" cy="61" r="17" />
      <path d="M145 44 V78" />
      {/* c */}
      <path d="M196 50 A17 17 0 1 0 196 72" />
      {/* e */}
      <path d="M212 61 H246 A17 17 0 1 0 241 73" />
    </svg>
  );
}
