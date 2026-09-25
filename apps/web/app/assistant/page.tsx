"use client";
import { useState } from "react";
import { api, type Answer } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

const SUGGESTIONS = [
  "Which properties in our portfolio are most exposed to flooding, and what financial exposure is associated with them?",
  "ما العقارات الأكثر عرضة للفيضانات في محفظتنا، وما حجم التعرض المالي المرتبط بها؟",
  "Is there concentration across sectors?",
  "ما هي العناصر غير المعروفة ولماذا؟",
  "What changed since the last run?",
  "How much is insured?",
];

export default function AssistantPage() {
  const { t } = useI18n();
  const [q, setQ] = useState("");
  const [log, setLog] = useState<{ q: string; a?: Answer; err?: string }[]>([]);
  const [busy, setBusy] = useState(false);

  const ask = async (question: string) => {
    if (!question.trim()) return;
    setBusy(true);
    setLog((l) => [...l, { q: question }]);
    try {
      const a = await api.ask(question);
      setLog((l) => l.map((x, i) => (i === l.length - 1 ? { ...x, a } : x)));
    } catch (e) {
      setLog((l) => l.map((x, i) => (i === l.length - 1 ? { ...x, err: String(e) } : x)));
    } finally { setBusy(false); setQ(""); }
  };

  return (
    <div className="stack">
      <div className="panel">
        <p className="muted">{t("grounded")}</p>
        <div className="row">
          <input style={{ flex: 1 }} value={q} onChange={(e) => setQ(e.target.value)} placeholder={t("ask_placeholder")} onKeyDown={(e) => e.key === "Enter" && ask(q)} />
          <button className="primary" disabled={busy} onClick={() => ask(q)}>{t("ask")}</button>
        </div>
        <div className="row" style={{ marginTop: 8 }}>
          {SUGGESTIONS.map((s) => <button key={s} className="ghost" disabled={busy} onClick={() => ask(s)} dir="auto">{s}</button>)}
        </div>
      </div>
      {log.slice().reverse().map((e, i) => (
        <div className="panel" key={i}>
          <div dir="auto"><b>{e.q}</b></div>
          {e.err && <p className="bad">{e.err}</p>}
          {e.a && (
            <>
              <div className="answer" dir={e.a.lang === "ar" ? "rtl" : "ltr"} style={{ marginTop: 8 }}>{e.a.text}</div>
              <div className="row" style={{ marginTop: 8 }}>
                <span className="chip">{t("intent")}: {e.a.intent}</span>
                <span className="chip">{e.a.agent} · {e.a.genome}</span>
                {e.a.refs.map((r) => <span className="chip" key={r}>{r}</span>)}
              </div>
            </>
          )}
        </div>
      ))}
    </div>
  );
}
