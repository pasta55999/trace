"use client";
import { useEffect, useRef, useState } from "react";
import { api, type Answer } from "@/lib/api";
import { useI18n, type Lang } from "@/lib/i18n";

/* Minimal typings for the Web Speech API (Chrome / Edge). */
interface SRResultEvent { results: ArrayLike<ArrayLike<{ transcript: string }>> }
interface SR { lang: string; interimResults: boolean; continuous: boolean; onresult: ((e: SRResultEvent) => void) | null; onend: (() => void) | null; onerror: (() => void) | null; start: () => void; stop: () => void }
type SRCtor = new () => SR;
const getSR = (): SRCtor | null => (typeof window === "undefined" ? null : ((window as unknown as { SpeechRecognition?: SRCtor; webkitSpeechRecognition?: SRCtor }).SpeechRecognition ?? (window as unknown as { webkitSpeechRecognition?: SRCtor }).webkitSpeechRecognition ?? null));

const SUGGEST: Record<Lang, string[]> = {
  en: ["Which properties are most exposed to flooding?", "Is there concentration across sectors?", "What is unknown and why?", "How much is insured?"],
  ar: ["ما العقارات الأكثر عرضة للفيضانات؟", "هل هناك تركز عبر القطاعات؟", "ما هي العناصر غير المعروفة ولماذا؟", "كم هو المؤمن؟"],
};

interface Msg { role: "user" | "bot"; text: string; lang: Lang; a?: Answer }

function pickVoice(lang: Lang): SpeechSynthesisVoice | undefined {
  const voices = window.speechSynthesis?.getVoices() ?? [];
  const pref = lang === "ar" ? ["ar-AE", "ar-SA", "ar"] : ["en-GB", "en-US", "en"];
  for (const p of pref) { const v = voices.find((x) => x.lang.toLowerCase().startsWith(p.toLowerCase())); if (v) return v; }
  return undefined;
}

export default function Chatbot() {
  const { lang, t, prefs } = useI18n();
  const [open, setOpen] = useState(false);
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [micLang, setMicLang] = useState<Lang>(lang);
  const recRef = useRef<SR | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const supported = !!getSR();

  useEffect(() => { setMicLang(lang); }, [lang]);
  useEffect(() => { if (open && msgs.length === 0) setMsgs([{ role: "bot", text: t("chat_hello"), lang }]); }, [open, msgs.length, t, lang]);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs, busy]);
  useEffect(() => { window.speechSynthesis?.getVoices(); }, []);

  const speak = (text: string, l: Lang) => {
    if (!prefs.voice || typeof window === "undefined" || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text.replace(/^- /gm, "").replace(/[–—]/g, l === "ar" ? " إلى " : " to ").replace(/\n+/g, ". "));
    u.lang = l === "ar" ? "ar-AE" : "en-GB";
    const v = pickVoice(l);
    if (v) u.voice = v;
    u.rate = 1;
    u.onstart = () => setSpeaking(true);
    u.onend = () => setSpeaking(false);
    u.onerror = () => setSpeaking(false);
    window.speechSynthesis.speak(u);
  };
  const stopSpeaking = () => { window.speechSynthesis?.cancel(); setSpeaking(false); };

  const ask = async (text: string) => {
    const question = text.trim();
    if (!question || busy) return;
    const qLang: Lang = /[\u0600-\u06FF]/.test(question) ? "ar" : "en";
    setMsgs((m) => [...m, { role: "user", text: question, lang: qLang }]);
    setQ(""); setBusy(true);
    try {
      const a = await api.ask(question);
      const al = (a.lang as Lang) ?? qLang;
      setMsgs((m) => [...m, { role: "bot", text: a.text, lang: al, a }]);
      speak(a.text, al);
    } catch (e) {
      setMsgs((m) => [...m, { role: "bot", text: String(e), lang: qLang }]);
    } finally { setBusy(false); }
  };

  const toggleMic = () => {
    const Ctor = getSR();
    if (!Ctor) return;
    if (listening) { recRef.current?.stop(); return; }
    stopSpeaking();
    const rec = new Ctor();
    rec.lang = micLang === "ar" ? "ar-AE" : "en-US";
    rec.interimResults = false; rec.continuous = false;
    rec.onresult = (e) => { const text = Array.from({ length: e.results.length }, (_, i) => e.results[i][0].transcript).join(" "); setQ(text); void ask(text); };
    rec.onend = () => setListening(false);
    rec.onerror = () => setListening(false);
    recRef.current = rec;
    setListening(true);
    rec.start();
  };

  if (!open) return <button className="chat-fab" onClick={() => setOpen(true)} aria-label="open assistant">✦</button>;
  return (
    <div className="chat" role="dialog" aria-label={t("chat_title")}>
      <div className="head">
        <span className="avatar">✦</span>
        <div><div>{t("chat_title")}</div><div className="status">{listening ? t("listening") : t("chat_sub")}</div></div>
        <div className="row" style={{ marginInlineStart: "auto" }}>
          <div className="tabs" title="microphone language">
            <button className={micLang === "en" ? "on" : ""} onClick={() => setMicLang("en")}>EN</button>
            <button className={micLang === "ar" ? "on" : ""} onClick={() => setMicLang("ar")}>ع</button>
          </div>
          <button className="iconbtn" onClick={() => { stopSpeaking(); setOpen(false); }} aria-label="close">×</button>
        </div>
      </div>
      <div className="msgs">
        {msgs.map((m, i) => (
          <div key={i} className={`msg ${m.role}`} dir={m.lang === "ar" ? "rtl" : "ltr"} lang={m.lang}>
            {m.text}
            {m.a && (
              <div className="meta">
                <span className="chip accent">{m.a.intent}</span>
                <span className="chip">{m.a.agent} · {m.a.genome}</span>
                <button className="chip" onClick={() => speak(m.text, m.lang)} title={t("speak")}>🔊</button>
                {m.a.refs.slice(0, 3).map((r) => <span key={r} className="chip">{r}</span>)}
              </div>
            )}
          </div>
        ))}
        {busy && <div className="msg bot muted">…</div>}
        <div ref={endRef} />
      </div>
      <div className="suggest">{SUGGEST[lang].map((s) => <button key={s} onClick={() => ask(s)} disabled={busy}>{s}</button>)}</div>
      <div className="compose">
        <button className={`iconbtn ${listening ? "on" : ""}`} onClick={toggleMic} disabled={!supported} title={supported ? t("speak") : t("mic_unsupported")} aria-label="microphone">🎤</button>
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t("chat_placeholder")} onKeyDown={(e) => e.key === "Enter" && ask(q)} dir="auto" />
        {speaking ? <button className="iconbtn speaking" onClick={stopSpeaking} title={t("stop")}>■</button> : <button className="iconbtn" onClick={() => ask(q)} disabled={busy} aria-label="send">➤</button>}
      </div>
    </div>
  );
}
