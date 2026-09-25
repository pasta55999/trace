/** Editorial skyline illustration: hazy dawn sky, Gulf water, a soft Dubai-like silhouette with palms. Pure SVG. */
export default function Skyline({ style }: { style?: React.CSSProperties }) {
  return (
    <svg viewBox="0 0 400 600" preserveAspectRatio="xMidYMax slice" aria-hidden style={{ position: "absolute", inset: 0, width: "100%", height: "100%", ...style }}>
      <defs>
        <linearGradient id="sk-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#e9eef1" /><stop offset=".55" stopColor="#d9e6ea" /><stop offset="1" stopColor="#bfd6dc" /></linearGradient>
        <linearGradient id="sk-sea" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#8fbfc9" /><stop offset="1" stopColor="#3f8c92" /></linearGradient>
        <linearGradient id="sk-bld" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#b9c6c9" /><stop offset="1" stopColor="#8fa1a5" /></linearGradient>
        <linearGradient id="sk-fog" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#fff" stopOpacity="0" /><stop offset="1" stopColor="#fff" stopOpacity=".55" /></linearGradient>
        <radialGradient id="sk-sun" cx=".5" cy=".5" r=".5"><stop offset="0" stopColor="#fff3d6" stopOpacity=".9" /><stop offset="1" stopColor="#fff3d6" stopOpacity="0" /></radialGradient>
      </defs>
      <rect width="400" height="600" fill="url(#sk-sky)" />
      <circle cx="300" cy="150" r="120" fill="url(#sk-sun)" />
      <g fill="url(#sk-bld)" opacity=".9">
        {/* distant towers */}
        <rect x="20" y="330" width="26" height="130" /><rect x="52" y="300" width="18" height="160" /><rect x="76" y="345" width="30" height="115" />
        <rect x="120" y="280" width="22" height="180" /><rect x="150" y="320" width="34" height="140" /><rect x="192" y="290" width="20" height="170" />
        <rect x="250" y="335" width="28" height="125" /><rect x="286" y="310" width="20" height="150" /><rect x="312" y="350" width="40" height="110" /><rect x="360" y="325" width="24" height="135" />
        {/* the tall spire */}
        <path d="M222 460 V250 l4 -60 l4 -80 l4 80 l4 60 V460 Z" />
        <path d="M212 460 V300 h8 V460 Z M242 460 V300 h8 V460 Z" opacity=".8" />
        {/* sail tower */}
        <path d="M100 460 V360 Q100 300 140 285 V460 Z" opacity=".85" />
      </g>
      <rect x="0" y="420" width="400" height="60" fill="url(#sk-fog)" />
      {/* sea */}
      <rect x="0" y="455" width="400" height="145" fill="url(#sk-sea)" />
      <g stroke="#fff" strokeOpacity=".35" strokeWidth="1.2" fill="none">
        <path d="M0 480 Q40 474 80 480 T160 480 T240 480 T320 480 T400 480" /><path d="M0 505 Q50 499 100 505 T200 505 T300 505 T400 505" opacity=".6" /><path d="M0 535 Q60 529 120 535 T240 535 T360 535 T480 535" opacity=".4" />
      </g>
      {/* palms */}
      <g fill="none" stroke="#2a4a3f" strokeWidth="3" strokeLinecap="round">
        <path d="M42 600 Q40 560 44 515" />
        <path d="M44 515 q-28 -6 -44 12 M44 515 q-18 -22 -40 -20 M44 515 q4 -30 -10 -44 M44 515 q14 -28 34 -30 M44 515 q26 -10 46 6 M44 515 q24 6 34 26" strokeWidth="2.4" />
        <path d="M364 600 Q362 570 366 540" />
        <path d="M366 540 q-24 -4 -38 10 M366 540 q-14 -20 -34 -18 M366 540 q2 -26 -10 -38 M366 540 q12 -24 30 -26 M366 540 q22 -8 40 6 M366 540 q20 6 28 22" strokeWidth="2.2" />
      </g>
      <rect width="400" height="600" fill="url(#sk-fog)" opacity=".25" />
    </svg>
  );
}
