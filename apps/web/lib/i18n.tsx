"use client";
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

export type Lang = "en" | "ar";

const STRINGS = {
  en: {
    app: "trace", synthetic: "Synthetic demo data — illustrative scenario, not an operational prediction",
    // landing
    hero_1: "Climate risks.", hero_2: "Financial impact.", hero_3: "A clearer picture.",
    hero_p: "See what's exposed. Know what it costs. Act first.",
    get_started: "Get started", landing_preview: "Your risk, at a glance",
    // nav
    nav_home: "Home", nav_portfolio: "Portfolio", nav_risk: "Risk Analysis", nav_agents: "AI Agents", nav_reports: "Reports", nav_settings: "Settings", bank_analyst: "Bank Analyst",
    // dashboard
    good_morning: "Good morning", good_afternoon: "Good afternoon", good_evening: "Good evening", snapshot: "Here's your portfolio's climate risk snapshot.", last_updated: "Last updated",
    kpi_portfolio: "Total loan portfolio", kpi_assets: "Assets monitored", kpi_high: "High-risk exposures", kpi_actions: "Actions recommended", across_sectors: "across {n} sectors", needs_attention: "need attention", open_questions_n: "{n} open questions", confirmed_of: "{a} of {b} locations confirmed",
    by_sector: "Portfolio by sector", outlook: "Climate risk outlook", properties: "properties", flood_risk: "Flood risk", heat_stress: "Heat stress", storm_risk: "Storm risk", not_assessed: "not assessed",
    exposure_chart: "Physical damage by asset (this scenario)", top_hazards: "Top climate hazards", hazard_flood: "Surface flooding", hazard_heat: "Extreme heat", hazard_storm: "Storms & wind", hazard_sea: "Sea level rise",
    run_agents: "Run the agents", running: "Agents working…", restart: "Re-run investigation", sketch: "Illustrative footprint sketch — not a map", scenario: "Scenario",
    // portfolio
    all: "All", search: "Search assets", loan: "Loan", overview: "Overview", climate: "Climate risk", financials: "Financials", actions: "Actions", potential_impact: "Potential impact", recommended: "Recommended actions", view_details: "View details",
    attr_switchboard: "Switchboards", attr_basement: "Basement", attr_elevation: "Floor elevation", depth: "Depth above floor", precision: "Location precision", damage: "Physical damage", bi: "Interruption cost", insured: "Insured loss", uninsured: "Uninsured share", collateral: "Collateral sensitivity", credit: "Lender loss", not_modelled: "not modelled", outstanding: "Outstanding", days: "days",
    risk_high: "High risk", risk_medium: "Medium risk", risk_low: "Low risk", risk_unknown: "Unknown", missing: "Missing information", answer: "Answer", submit: "Submit", questions: "Questions that could change the decision", no_questions: "No open questions.",
    // risk analysis
    scenarios: "Scenarios", measures: "Protective measures", comparisons: "Comparisons", baseline: "Baseline", protected: "With measure", avoided: "Avoided loss (this event)", residual: "Residual damage", capex: "Capital cost", bcr: "Event-conditional benefit / cost", npv: "NPV", top_reco: "Top recommendation", add_plan: "Add to plan", concentration: "Shared physical vulnerability", in_footprint: "assets in the same flood footprint", share: "of portfolio outstanding", changes: "Changes since previous run", no_changes: "No changes yet.",
    // agents
    agents_title: "AI Agents", agents_sub: "Autonomous agents working in the background to keep your data connected and up to date. Every number they show comes from a deterministic engine.", powered: "Human oversight · policy engine · rollback",
    ag_intake: "Document reader", ag_intake_d: "Reads Arabic & English documents; quarantines instruction-like text.", ag_extract: "Information checker", ag_extract_d: "Extracts fields, flags conflicts and low confidence.", ag_resolve: "Location & entity resolver", ag_resolve_d: "Links assets to places; asks when uncertain; never uses an HQ as a site.", ag_gap: "Evidence-gap agent", ag_gap_d: "Asks the one question that most changes the result.", ag_analyst: "Analyst", ag_analyst_d: "Answers in Arabic or English, grounded in tool results.", ag_critic: "Critic", ag_critic_d: "Second reader: parity, category separation, no regulatory claims.",
    completed: "Completed", in_progress: "In progress", active: "Active", waiting: "Waiting", evolution: "Self-evolution", genomes: "Agent genomes", run_cycle: "Run evolution cycle", rollback: "Roll back", guardian: "Guardian", proposals: "Tier C proposals awaiting model validators", last_cycle: "Last evolution cycle", nothing_promoted: "nothing promoted", promoted: "promoted", tiers: "Tier A: prompts, skills, thresholds, aliases — autonomous. Tier B: matching rules, evals — shadow + signed record. Tier C: engines, hazard data, regulatory mapping — proposal only.", frozen: "Evolution frozen by Guardian", telemetry: "Recent telemetry", audit: "Audit tail", version: "Version", state: "State", change: "Change record", score: "Eval score",
    // reports
    reports_title: "Reports & Insights", latest: "Latest", generate: "Generate bilingual brief", open_en: "Open English", open_ar: "Open Arabic", critic_blocked: "Blocked by the Critic", brief_name: "Climate risk portfolio review", brief_desc: "Bilingual review brief with separated financial columns", insight: "Better insights. Stronger decisions.", insight_p: "Climate risk shouldn't be a blind spot. Every figure in this brief is traceable to a source record, a dataset version and an engine version.", governance: "Model governance", engine: "Engine", datasets: "Datasets", dmg: "Damage functions", reg: "Regulatory mapping",
    // settings
    settings: "Settings", your_name: "Your name", language: "Interface language", voice: "Spoken replies", voice_on: "On", voice_off: "Off", api: "API endpoint", llm: "LLM provider", save: "Save",
    // chatbot
    chat_title: "trace assistant", chat_sub: "Arabic · English · voice", chat_placeholder: "Ask about exposure, concentration, unknowns…", listening: "Listening…", speak: "Speak", stop: "Stop", mic_unsupported: "Voice input needs Chrome or Edge.", chat_hello: "Hi — ask me about your portfolio in English or Arabic. I only quote numbers that come from the engines.",
    unknown: "unknown",
  },
  ar: {
    app: "trace", synthetic: "بيانات عرض اصطناعية — سيناريو توضيحي، وليس تنبؤاً تشغيلياً",
    hero_1: "مخاطر المناخ.", hero_2: "الأثر المالي.", hero_3: "صورة أوضح.",
    hero_p: "اعرف ما هو معرّض. اعرف التكلفة. تحرّك أولاً.",
    get_started: "ابدأ الآن", landing_preview: "مخاطرك في لمحة",
    nav_home: "الرئيسية", nav_portfolio: "المحفظة", nav_risk: "تحليل المخاطر", nav_agents: "وكلاء الذكاء الاصطناعي", nav_reports: "التقارير", nav_settings: "الإعدادات", bank_analyst: "محلل مصرفي",
    good_morning: "صباح الخير", good_afternoon: "مساء الخير", good_evening: "مساء الخير", snapshot: "إليك لمحة عن مخاطر المناخ في محفظتك.", last_updated: "آخر تحديث",
    kpi_portfolio: "إجمالي محفظة القروض", kpi_assets: "الأصول المراقبة", kpi_high: "التعرضات عالية المخاطر", kpi_actions: "الإجراءات الموصى بها", across_sectors: "عبر {n} قطاعات", needs_attention: "تحتاج إلى اهتمام", open_questions_n: "{n} أسئلة مفتوحة", confirmed_of: "{a} من {b} مواقع مؤكدة",
    by_sector: "المحفظة حسب القطاع", outlook: "توقعات مخاطر المناخ", properties: "عقارات", flood_risk: "خطر الفيضان", heat_stress: "الإجهاد الحراري", storm_risk: "خطر العواصف", not_assessed: "غير مقيّم",
    exposure_chart: "الأضرار المادية حسب الأصل (هذا السيناريو)", top_hazards: "أهم المخاطر المناخية", hazard_flood: "الفيضانات السطحية", hazard_heat: "الحرارة الشديدة", hazard_storm: "العواصف والرياح", hazard_sea: "ارتفاع مستوى البحر",
    run_agents: "تشغيل الوكلاء", running: "الوكلاء يعملون…", restart: "إعادة التحقيق", sketch: "رسم توضيحي للنطاق — ليس خريطة", scenario: "السيناريو",
    all: "الكل", search: "ابحث في الأصول", loan: "القرض", overview: "نظرة عامة", climate: "مخاطر المناخ", financials: "المالية", actions: "الإجراءات", potential_impact: "الأثر المحتمل", recommended: "الإجراءات الموصى بها", view_details: "عرض التفاصيل",
    attr_switchboard: "لوحات التوزيع", attr_basement: "طابق سفلي", attr_elevation: "منسوب الأرضية", depth: "العمق فوق الأرضية", precision: "دقة الموقع", damage: "الأضرار المادية", bi: "تكلفة التوقف", insured: "الخسارة المؤمنة", uninsured: "الحصة غير المؤمنة", collateral: "حساسية الضمان", credit: "خسارة المقرض", not_modelled: "غير منمذجة", outstanding: "القائم", days: "يوم",
    risk_high: "مخاطر عالية", risk_medium: "مخاطر متوسطة", risk_low: "مخاطر منخفضة", risk_unknown: "غير معروف", missing: "معلومات ناقصة", answer: "الإجابة", submit: "إرسال", questions: "أسئلة قد تغيّر القرار", no_questions: "لا توجد أسئلة مفتوحة.",
    scenarios: "السيناريوهات", measures: "الإجراءات الوقائية", comparisons: "المقارنات", baseline: "الأساس", protected: "مع الإجراء", avoided: "الخسارة المتجنبة (هذا الحدث)", residual: "الأضرار المتبقية", capex: "التكلفة الرأسمالية", bcr: "المنفعة / التكلفة المشروطة بالحدث", npv: "صافي القيمة الحالية", top_reco: "أهم توصية", add_plan: "إضافة إلى الخطة", concentration: "نقطة ضعف مادية مشتركة", in_footprint: "أصول في نطاق الفيضان نفسه", share: "من قائم المحفظة", changes: "التغييرات منذ التشغيل السابق", no_changes: "لا تغييرات بعد.",
    agents_title: "وكلاء الذكاء الاصطناعي", agents_sub: "وكلاء مستقلون يعملون في الخلفية لإبقاء بياناتك مترابطة ومحدّثة. كل رقم يعرضونه يأتي من محرك حتمي.", powered: "إشراف بشري · محرك سياسات · تراجع",
    ag_intake: "قارئ المستندات", ag_intake_d: "يقرأ المستندات العربية والإنجليزية ويعزل النصوص الشبيهة بالتعليمات.", ag_extract: "مدقق المعلومات", ag_extract_d: "يستخرج الحقول ويبلّغ عن التعارض وانخفاض الثقة.", ag_resolve: "محدد المواقع والكيانات", ag_resolve_d: "يربط الأصول بالأماكن؛ يسأل عند الشك؛ لا يستخدم المقر الرئيسي كموقع أبداً.", ag_gap: "وكيل فجوات الأدلة", ag_gap_d: "يطرح السؤال الوحيد الأكثر تأثيراً على النتيجة.", ag_analyst: "المحلل", ag_analyst_d: "يجيب بالعربية أو الإنجليزية استناداً إلى نتائج الأدوات.", ag_critic: "الناقد", ag_critic_d: "قارئ ثانٍ: التطابق، فصل الفئات، لا ادعاءات تنظيمية.",
    completed: "مكتمل", in_progress: "قيد التنفيذ", active: "نشط", waiting: "بانتظار", evolution: "التطور الذاتي", genomes: "جينومات الوكلاء", run_cycle: "تشغيل دورة التطور", rollback: "تراجع", guardian: "الحارس", proposals: "مقترحات الفئة C بانتظار مدققي النماذج", last_cycle: "آخر دورة تطور", nothing_promoted: "لم يُرقَّ شيء", promoted: "تمت الترقية", tiers: "الفئة A: التعليمات والمهارات والحدود والأسماء البديلة — مستقلة. الفئة B: قواعد المطابقة والتقييمات — ظل + سجل موقّع. الفئة C: المحركات وبيانات المخاطر والمواءمة التنظيمية — اقتراح فقط.", frozen: "التطور مجمّد من قبل الحارس", telemetry: "أحدث القياسات", audit: "سجل التدقيق", version: "الإصدار", state: "الحالة", change: "سجل التغيير", score: "درجة التقييم",
    reports_title: "التقارير والرؤى", latest: "الأحدث", generate: "إنشاء موجز ثنائي اللغة", open_en: "فتح الإنجليزية", open_ar: "فتح العربية", critic_blocked: "حجبه الناقد", brief_name: "مراجعة مخاطر المناخ للمحفظة", brief_desc: "موجز مراجعة ثنائي اللغة بأعمدة مالية منفصلة", insight: "رؤى أفضل. قرارات أقوى.", insight_p: "لا ينبغي أن تكون مخاطر المناخ نقطة عمياء. كل رقم في هذا الموجز يمكن تتبعه إلى سجل مصدر وإصدار مجموعة بيانات وإصدار محرك.", governance: "حوكمة النماذج", engine: "المحرك", datasets: "مجموعات البيانات", dmg: "دوال الضرر", reg: "المواءمة التنظيمية",
    settings: "الإعدادات", your_name: "اسمك", language: "لغة الواجهة", voice: "الردود الصوتية", voice_on: "مفعّل", voice_off: "معطّل", api: "نقطة نهاية API", llm: "مزوّد النموذج اللغوي", save: "حفظ",
    chat_title: "مساعد trace", chat_sub: "عربي · إنجليزي · صوت", chat_placeholder: "اسأل عن التعرض أو التركز أو المجهول…", listening: "أستمع…", speak: "تحدث", stop: "إيقاف", mic_unsupported: "الإدخال الصوتي يحتاج إلى Chrome أو Edge.", chat_hello: "مرحباً — اسألني عن محفظتك بالعربية أو الإنجليزية. لا أذكر إلا أرقاماً تأتي من المحركات.",
    unknown: "غير معروف",
  },
} as const;

export type Key = keyof (typeof STRINGS)["en"];
interface Prefs { name: string; voice: boolean }
const Ctx = createContext<{ lang: Lang; setLang: (l: Lang) => void; t: (k: Key, vars?: Record<string, string | number>) => string; prefs: Prefs; setPrefs: (p: Prefs) => void }>({ lang: "en", setLang: () => {}, t: (k) => k, prefs: { name: "Sarah", voice: true }, setPrefs: () => {} });

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>("en");
  const [prefs, setPrefsState] = useState<Prefs>({ name: "Sarah", voice: true });
  useEffect(() => {
    const saved = localStorage.getItem("trace.lang") as Lang | null;
    if (saved) setLangState(saved);
    const p = localStorage.getItem("trace.prefs");
    if (p) setPrefsState(JSON.parse(p));
  }, []);
  useEffect(() => { document.documentElement.lang = lang; document.documentElement.dir = lang === "ar" ? "rtl" : "ltr"; }, [lang]);
  const setLang = (l: Lang) => { localStorage.setItem("trace.lang", l); setLangState(l); };
  const setPrefs = (p: Prefs) => { localStorage.setItem("trace.prefs", JSON.stringify(p)); setPrefsState(p); };
  const t = (k: Key, vars?: Record<string, string | number>) => Object.entries(vars ?? {}).reduce((s, [a, b]) => s.replace(`{${a}}`, String(b)), STRINGS[lang][k] as string);
  return <Ctx.Provider value={{ lang, setLang, t, prefs, setPrefs }}>{children}</Ctx.Provider>;
}

export const useI18n = () => useContext(Ctx);

/** One formatter for both languages: identical digits and rounding (ar/en numeric parity). */
export function fmt(v: unknown, lang: Lang, compact = false): string {
  if (v === null || v === undefined) return STRINGS[lang].unknown;
  const n = (x: number) => compact ? compactNum(x) : Math.abs(x) >= 100 ? x.toLocaleString("en-US", { maximumFractionDigits: 0 }) : x.toLocaleString("en-US", { maximumFractionDigits: 2 });
  if (typeof v === "object") {
    const o = v as { unknown?: boolean; reason?: string; reason_ar?: string; low?: number; high?: number };
    if (o.unknown) return `${STRINGS[lang].unknown} — ${lang === "ar" && o.reason_ar ? o.reason_ar : o.reason}`;
    if (o.low !== undefined && o.high !== undefined) return `${n(o.low)} – ${n(o.high)}`;
  }
  if (typeof v === "number") return n(v);
  return String(v);
}

export function compactNum(x: number): string {
  if (Math.abs(x) >= 1e9) return `${(x / 1e9).toFixed(2)}B`;
  if (Math.abs(x) >= 1e6) return `${(x / 1e6).toFixed(x % 1e6 === 0 ? 0 : 1)}M`;
  if (Math.abs(x) >= 1e3) return `${(x / 1e3).toFixed(0)}K`;
  return x.toFixed(0);
}
