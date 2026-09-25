/** The trace wordmark: thin geometric letters with a hairline running through the "t" crossbar. */
export default function Logo({ size = 28, color = "currentColor" }: { size?: number; color?: string }) {
  const w = size * 3.1;
  return (
    <svg width={w} height={size} viewBox="0 0 310 100" fill="none" aria-label="trace" role="img">
      <text x="2" y="78" fontFamily="'Segoe UI Light','Helvetica Neue',Inter,Arial,sans-serif" fontWeight="200" fontSize="92" letterSpacing="6" fill={color}>trace</text>
      <line x1="0" y1="38" x2="88" y2="38" stroke={color} strokeWidth="2.2" strokeLinecap="round" />
    </svg>
  );
}
