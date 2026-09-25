"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import Logo from "@/components/Logo";
import { useI18n } from "@/lib/i18n";

const REPO = "https://github.com/pasta55999/trace";
const SCREENS = [
  { path: "/dashboard", label: "Home" }, { path: "/portfolio", label: "Portfolio" }, { path: "/risk", label: "Risk analysis" },
  { path: "/agents", label: "AI agents" }, { path: "/reports", label: "Reports" },
];

const FEATURES = [
  { g: "◫", h: "Bring your portfolio", p: "Loan book, collateral register, Arabic and English valuation PDFs, insurance schedules. Agents read them, extract fields, and quarantine anything that looks like an instruction." },
  { g: "◎", h: "It never guesses a location", p: "A corporate HQ is never used as a factory site. Below its confidence threshold, the agent asks — listing the candidates — instead of inventing coordinates." },
  { g: "≋", h: "Hazard meets balance sheet", p: "Flood depth × building vulnerability × replacement value, then business interruption, insurance terms and collateral sensitivity — kept in separate columns, never summed." },
  { g: "?", h: "It asks the one question that matters", p: "“Are the switchboards in the basement?” The evidence-gap agent ranks unknowns by how much they move the number and asks only that." },
  { g: "◔", h: "Unknown is never low", p: "No flood layer at building level? The result says unknown, with the reason. No event-frequency model? Expected annual loss and NPV say unknown, too." },
  { g: "✦", h: "It evolves — inside a fence", p: "Every human correction becomes a hypothesis. Agents propose new versions of themselves, a verifier rejects the dangerous ones on an adversarial suite, the best is promoted with rollback. Engines and hazard data are off-limits: proposal only." },
];

const STACK = ["Python · deterministic engines", "FastAPI · typed tool contracts", "Pydantic · agent tool schemas", "Versioned genomes · git-backed", "Golden / regression / adversarial evals", "Policy engine · immutable invariants", "Web Speech API · Arabic & English voice", "Next.js · RTL-first UI", "Synthetic UAE data · clearly labelled"];

export default function Showcase() {
  const { lang, setLang } = useI18n();
  const [screen, setScreen] = useState(SCREENS[0].path);
  const [scale, setScale] = useState(0.62);
  const [innerH, setInnerH] = useState(900);
  const frameBox = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const fit = () => { if (!frameBox.current) return; const sc = Math.min(1, frameBox.current.clientWidth / 1440); setScale(sc); setInnerH(Math.max(900, Math.round((window.innerHeight - 220) / sc))); };
    fit(); window.addEventListener("resize", fit); return () => window.removeEventListener("resize", fit);
  }, []);
  return (
    <div className="show">
      <header className="show-nav">
        <Link href="/"><Logo size={22} /></Link>
        <nav><a href="#how">How it works</a><a href="#live">Live app</a><a href="#evolve">Self-evolving</a><a href="#demo">Demo</a><a href={REPO} target="_blank" rel="noreferrer">GitHub ↗</a></nav>
        <div className="langsw"><button className={lang === "en" ? "on" : ""} onClick={() => setLang("en")}>EN</button><span>|</span><button className={lang === "ar" ? "on" : ""} onClick={() => setLang("ar")}>عربي</button></div>
      </header>

      <div className="show-body">
        {/* ---------- narrative column ---------- */}
        <main className="show-copy">
          <section className="show-hero">
            <span className="live">TDRA UAE Hackathon 2026 · CBUAE challenge</span>
            <h1>The risk platform that knows what it doesn’t know.</h1>
            <p>trace links a bank’s loans to the buildings behind them, runs a flood scenario through them, and shows where separate borrowers share one physical vulnerability — in Arabic and English, with agents that learn from every correction and refuse to invent a number.</p>
            <div className="row"><a href="#live" className="btn">Try it live →</a><a href="#how" className="btn ghost">How it works</a></div>
            <div className="note">Synthetic portfolio and an illustrative flood layer. This is a working prototype, not an operational prediction.</div>
          </section>

          <section id="how" className="show-section">
            <div className="eyebrow">How trace works</div>
            <h2>It doesn’t score risk. It investigates it.</h2>
            <p className="lead">Bring a portfolio; leave with a defensible review case. Underneath, six things happen.</p>
            <div className="fgrid">{FEATURES.map((f) => <div key={f.h} className="fcard"><span className="glyph">{f.g}</span><h3>{f.h}</h3><p>{f.p}</p></div>)}</div>
          </section>

          <section className="show-section">
            <div className="eyebrow">The discovery</div>
            <h2>Three sectors. One flood footprint.</h2>
            <p className="lead">A manufacturer, a distributor and a warehouse operator sit in different sector buckets. Their critical facilities sit in the same illustrative flood event. <b>84.8% of outstanding exposure</b> shares one physical vulnerability — and one missing fact about a switchboard moves the estimate by AED 3.4M.</p>
            <div className="quote" dir="rtl" lang="ar">ما العقارات الأكثر عرضة للفيضانات في محفظتنا، وما حجم التعرض المالي المرتبط بها؟</div>
            <p className="muted small">Ask that — or its English twin — in the ✦ assistant. It answers in your language, speaks it, and cites the tool result behind every figure.</p>
          </section>

          <section id="evolve" className="show-section">
            <div className="eyebrow">Self-evolving agents</div>
            <h2>They improve themselves. Inside a fence.</h2>
            <ol className="steps">
              <li><b>Reflector</b> clusters human corrections into hypotheses (“Arabic name variant not recognised”).</li>
              <li><b>Proposer</b> writes candidate genomes — prompts, aliases, thresholds — plus a regression eval from the correction.</li>
              <li><b>Verifier</b> runs golden, regression and adversarial suites in a sandbox. A false commit is a hard fail.</li>
              <li><b>Promoter</b> ships the best as a canary; <b>Guardian</b> watches live SLIs, graduates or rolls back, freezes after three rollbacks.</li>
            </ol>
            <div className="tiers">
              <div><span className="chip low">Tier A</span> prompts · skills · thresholds · aliases — <b>autonomous</b></div>
              <div><span className="chip medium">Tier B</span> matching rules · evals — shadow replay + signed record</div>
              <div><span className="chip high">Tier C</span> engines · hazard data · regulatory mapping — <b>proposal only</b></div>
            </div>
            <p className="muted small">Try it: in the live app answer the warehouse location question in Portfolio, then press <i>Run evolution cycle</i> in AI Agents. Watch one of three candidates get rejected and v0002 promoted.</p>
          </section>

          <section id="demo" className="show-section">
            <div className="eyebrow">Demo</div>
            <h2>Under four minutes, start to finish.</h2>
            <video className="video" controls preload="metadata" poster="/demo-poster.png"><source src="/demo.mp4" type="video/mp4" />Your browser does not support the video tag.</video>
            <p className="muted small">Upload a portfolio, answer the agents, hear the assistant in Arabic, run an evolution cycle, export the bilingual brief.</p>
          </section>

          <section className="show-section">
            <div className="eyebrow">Built with</div>
            <h2>The stack.</h2>
            <div className="stackchips">{STACK.map((s) => <span key={s} className="chip">{s}</span>)}</div>
            <p className="muted small">Agents run offline on a deterministic provider; an in-region OpenAI-compatible model is a config switch. Numbers never come from a language model.</p>
          </section>

          <footer className="show-foot"><Logo size={18} /><span className="muted small">UAE climate financial-risk intelligence · <a href={REPO} target="_blank" rel="noreferrer">GitHub ↗</a> · <Link href="/intro">Brand page</Link></span></footer>
        </main>

        {/* ---------- live app column ---------- */}
        <aside id="live" className="show-live">
          <div className="live-head">
            <span className="live">Live app running in your browser</span>
            <div className="tabs">{SCREENS.map((s) => <button key={s.path} className={screen === s.path ? "on" : ""} onClick={() => setScreen(s.path)}>{s.label}</button>)}</div>
            <a className="btn ghost sm" href={screen} target="_blank" rel="noreferrer">Open full screen ↗</a>
          </div>
          <div className="device" ref={frameBox}>
            <div className="device-bar"><span /><span /><span /><span className="url num">localhost:3000{screen}</span></div>
            <div className="device-view" style={{ height: innerH * scale }}>
              <iframe key={screen} title="trace live app" src={screen} style={{ width: 1440, height: innerH, transform: `scale(${scale})`, transformOrigin: "0 0", border: 0 }} />
            </div>
          </div>
          <p className="muted small">This is the actual build with a real (synthetic) portfolio loaded. Answer the agents’ questions, ask the assistant in Arabic, run an evolution cycle.</p>
        </aside>
      </div>
    </div>
  );
}
