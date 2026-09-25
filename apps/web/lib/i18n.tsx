"use client";
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

export type Lang = "en" | "ar";

const STRINGS = {
  en: {
    app: "TRACE", tagline: "UAE climate financial-risk intelligence - prototype", synthetic: "SYNTHETIC DATA - illustrative scenario, not an operational prediction",
    nav_review: "Review", nav_assistant: "Assistant", nav_brief: "Brief", nav_governance: "Governance",
    start: "Upload portfolio (synthetic demo)", restart: "Restart investigation", starting: "Running agents...",
    coverage: "Coverage", confirmed: "asset locations confirmed", district_only: "district-level only", unresolved: "unresolved", firewall: "documents with quarantined instruction text", open_q: "open questions", cases: "open cases",
    concentration: "Shared physical vulnerability", in_footprint: "assets in the same flood footprint", outstanding: "outstanding exposure in footprint", share: "of portfolio", damage: "single-event physical damage", sectors: "sectors",
    assets: "Assets", asset: "Asset", borrower: "Borrower", sector: "Sector", precision: "Precision", depth: "Depth above floor (m)", exposure: "Outstanding (AED)", phys: "Physical damage (AED)", bi: "Interruption cost (AED)", insured: "Insured loss (AED)", collateral: "Collateral sensitivity (AED)", credit: "Lender loss", not_modelled: "not modelled", status: "Status",
    questions: "Questions that could change the decision", answer: "Answer", send: "Submit", changes: "Changes since previous run", no_changes: "No changes yet.", kind: "kind",
    ask_placeholder: "Ask in English or Arabic, e.g. Which properties are most exposed to flooding?", ask: "Ask", grounded: "Every number comes from a referenced tool result; the policy engine blocks anything else.", refs: "references", intent: "intent",
    brief_title: "Bilingual review brief", measure: "Protective measure for A-001", generate: "Generate brief", open_ar: "Open Arabic PDF-ready view", open_en: "Open English PDF-ready view", critic_blocked: "Blocked by the Critic:", avoided: "Avoided loss (this event)", residual: "Residual damage", capex: "Capital cost", bcr: "Event-conditional benefit/cost", npv: "NPV",
    gov_title: "Model governance & evolution", engine: "Engine", datasets: "Datasets", dmg: "Damage functions", reg: "Regulatory mapping", genomes: "Agent genomes", version: "version", active: "active", state: "state", change: "change record", score: "eval score", run_cycle: "Run evolution cycle now", rollback: "Roll back", guardian: "Guardian", proposals: "Tier C proposals awaiting model validators", telemetry: "Recent telemetry", audit: "Audit tail", frozen: "EVOLUTION FROZEN by Guardian", tiers: "Tier A: prompts, skills, thresholds, aliases (autonomous). Tier B: matching rules, evals (shadow + signed record). Tier C: engines, hazard data, regulatory mapping, policy (proposal only).",
    unknown: "unknown", decide: "Record decision (human)", decided: "decided",
  },
  ar: {
    app: "TRACE", tagline: "ذكاء المخاطر المالية المناخية في الإمارات - نموذج أولي", synthetic: "بيانات اصطناعية - سيناريو توضيحي، وليس تنبؤاً تشغيلياً",
    nav_review: "المراجعة", nav_assistant: "المساعد", nav_brief: "الموجز", nav_governance: "الحوكمة",
    start: "رفع المحفظة (عرض توضيحي اصطناعي)", restart: "إعادة بدء التحقيق", starting: "الوكلاء يعملون...",
    coverage: "التغطية", confirmed: "مواقع أصول مؤكدة", district_only: "على مستوى المنطقة فقط", unresolved: "غير محددة", firewall: "مستندات تحتوي نص تعليمات معزول", open_q: "أسئلة مفتوحة", cases: "حالات مفتوحة",
    concentration: "نقطة ضعف مادية مشتركة", in_footprint: "أصول داخل نطاق الفيضان نفسه", outstanding: "التعرض القائم داخل النطاق", share: "من المحفظة", damage: "أضرار مادية لحدث واحد", sectors: "قطاعات",
    assets: "الأصول", asset: "الأصل", borrower: "المقترض", sector: "القطاع", precision: "الدقة", depth: "العمق فوق الأرضية (م)", exposure: "القائم (درهم)", phys: "الأضرار المادية (درهم)", bi: "تكلفة التوقف (درهم)", insured: "الخسارة المؤمنة (درهم)", collateral: "حساسية الضمان (درهم)", credit: "خسارة المقرض", not_modelled: "غير منمذجة", status: "الحالة",
    questions: "أسئلة قد تغيّر القرار", answer: "الإجابة", send: "إرسال", changes: "التغييرات منذ التشغيل السابق", no_changes: "لا تغييرات بعد.", kind: "النوع",
    ask_placeholder: "اسأل بالعربية أو الإنجليزية، مثال: ما العقارات الأكثر عرضة للفيضانات؟", ask: "اسأل", grounded: "كل رقم يأتي من نتيجة أداة مرجعية؛ محرك السياسات يحجب ما عدا ذلك.", refs: "المراجع", intent: "القصد",
    brief_title: "موجز المراجعة ثنائي اللغة", measure: "إجراء وقائي للأصل A-001", generate: "إنشاء الموجز", open_ar: "فتح النسخة العربية الجاهزة للطباعة", open_en: "فتح النسخة الإنجليزية الجاهزة للطباعة", critic_blocked: "حجبه الناقد:", avoided: "الخسارة المتجنبة (هذا الحدث)", residual: "الأضرار المتبقية", capex: "التكلفة الرأسمالية", bcr: "المنفعة/التكلفة المشروطة بالحدث", npv: "صافي القيمة الحالية",
    gov_title: "حوكمة النماذج والتطور", engine: "المحرك", datasets: "مجموعات البيانات", dmg: "دوال الضرر", reg: "المواءمة التنظيمية", genomes: "جينومات الوكلاء", version: "الإصدار", active: "نشط", state: "الحالة", change: "سجل التغيير", score: "درجة التقييم", run_cycle: "تشغيل دورة التطور الآن", rollback: "تراجع", guardian: "الحارس", proposals: "مقترحات الفئة C بانتظار مدققي النماذج", telemetry: "أحدث القياسات", audit: "سجل التدقيق", frozen: "التطور مجمّد من قبل الحارس", tiers: "الفئة A: التعليمات والمهارات والحدود والأسماء البديلة (مستقلة). الفئة B: قواعد المطابقة والتقييمات (ظل + سجل موقّع). الفئة C: المحركات وبيانات المخاطر والمواءمة التنظيمية والسياسات (اقتراح فقط).",
    unknown: "غير معروف", decide: "تسجيل القرار (بشري)", decided: "تم البت",
  },
} as const;

type Key = keyof (typeof STRINGS)["en"];
const Ctx = createContext<{ lang: Lang; setLang: (l: Lang) => void; t: (k: Key) => string }>({ lang: "en", setLang: () => {}, t: (k) => k });

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>("en");
  useEffect(() => {
    const saved = typeof window !== "undefined" ? (localStorage.getItem("trace.lang") as Lang | null) : null;
    if (saved) setLangState(saved);
  }, []);
  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
  }, [lang]);
  const setLang = (l: Lang) => { localStorage.setItem("trace.lang", l); setLangState(l); };
  return <Ctx.Provider value={{ lang, setLang, t: (k) => STRINGS[lang][k] }}>{children}</Ctx.Provider>;
}

export const useI18n = () => useContext(Ctx);

/** One formatter for both languages: identical digits and rounding (ar/en numeric parity). */
export function fmt(v: unknown, lang: Lang): string {
  if (v === null || v === undefined) return STRINGS[lang].unknown;
  if (typeof v === "object") {
    const o = v as { unknown?: boolean; reason?: string; reason_ar?: string; low?: number; high?: number; driver?: string };
    if (o.unknown) return `${STRINGS[lang].unknown} - ${lang === "ar" && o.reason_ar ? o.reason_ar : o.reason}`;
    if (o.low !== undefined && o.high !== undefined) return `${o.low.toLocaleString("en-US", { maximumFractionDigits: 0 })} – ${o.high.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
  }
  if (typeof v === "number") return Math.abs(v) >= 100 ? v.toLocaleString("en-US", { maximumFractionDigits: 0 }) : v.toLocaleString("en-US", { maximumFractionDigits: 2 });
  return String(v);
}
