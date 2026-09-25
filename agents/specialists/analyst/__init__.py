from __future__ import annotations

from typing import Any

from agents.runtime import Agent
from services.common import has_arabic


def _num(v: Any) -> float | None:
    if isinstance(v, dict):
        return None if v.get("unknown") else (v["low"] + v["high"]) / 2
    return float(v) if v is not None else None


def _fmt(v: Any, lang: str) -> str:
    if isinstance(v, dict):
        if v.get("unknown"):
            return ("غير معروف - " + (v.get("reason_ar") or v["reason"])) if lang == "ar" else f"unknown - {v['reason']}"
        return f"{v['low']:,.0f}–{v['high']:,.0f}"
    return f"{v:,.0f}"


class AnalystAgent(Agent):
    """Bilingual grounded assistant. Composes answers only from run data; every number is referenced."""

    name = "analyst"

    GREETINGS = ("hello", "hi ", "hi!", "hey", "مرحبا", "مرحباً", "السلام", "أهلا", "أهلاً", "صباح", "مساء", "help", "مساعدة", "what can you")

    def intent(self, q: str) -> str:
        low = q.lower().strip()
        for name, words in self.genome.param("intents", {}).items():
            if any(w in low for w in words):
                return name
        if any(low.startswith(g) or g in low for g in self.GREETINGS) or len(low.split()) <= 2:
            return "help"
        return "flood_ranking"

    def ask(self, question: str, run: dict[str, Any], diff: dict[str, Any] | None = None) -> dict[str, Any]:
        lang = "ar" if has_arabic(question) else "en"
        intent = self.intent(question)
        self.decide("question", intent, lang=lang)
        refs: dict[str, Any] = {}
        if intent == "help":
            cov = {"assets": len(run["assets"]), "in_footprint": len(run["aggregation"]["concentration"]["assets_in_footprint"])}
            refs["result://coverage"] = cov
            text = (f"مرحباً. أتابع {cov['assets']} أصول في هذا السيناريو التوضيحي، منها {cov['in_footprint']} داخل نطاق الفيضان نفسه. يمكنك أن تسألني: ما العقارات الأكثر عرضة للفيضانات؟ هل هناك تركز؟ ما هي العناصر غير المعروفة؟ ما الذي تغير؟ كم هو المؤمن؟ لا أذكر إلا أرقاماً تأتي من محركات الحساب."
                    if lang == "ar" else
                    f"Hello. I am tracking {cov['assets']} assets in this illustrative scenario, {cov['in_footprint']} of them inside the same flood footprint. You can ask me: which properties are most exposed to flooding? Is there concentration? What is unknown? What changed? How much is insured? I only quote numbers that come from the calculation engines.")
        elif intent == "flood_ranking":
            rows = sorted([a for a in run["assets"] if _num(a["flood_depth_m"]) is not None], key=lambda a: _num(a["physical_damage_total_aed"]) or 0, reverse=True)
            unknown = [a for a in run["assets"] if _num(a["flood_depth_m"]) is None]
            lines = []
            for a in rows:
                refs[a["ref"]] = {k: a[k] for k in ("flood_depth_m", "depth_above_floor_m", "physical_damage_total_aed", "outstanding_allocated_aed", "insured_loss_aed")}
                name = a["borrower_ar"] if lang == "ar" else a["borrower"]
                lines.append((f"- {a['asset_id']} ({name}): عمق {_fmt(a['depth_above_floor_m'], lang)} م فوق الأرضية، أضرار مادية {_fmt(a['physical_damage_total_aed'], lang)} درهم، تعرض قائم {_fmt(a['outstanding_allocated_aed'], lang)} درهم، خسارة مؤمنة {_fmt(a['insured_loss_aed'], lang)}") if lang == "ar" else
                             (f"- {a['asset_id']} ({name}): {_fmt(a['depth_above_floor_m'], lang)} m above floor, physical damage {_fmt(a['physical_damage_total_aed'], lang)} AED, outstanding exposure {_fmt(a['outstanding_allocated_aed'], lang)} AED, insured loss {_fmt(a['insured_loss_aed'], lang)}"))
            for a in unknown:
                refs[a["ref"]] = {"flood_depth_m": a["flood_depth_m"]}
                lines.append(f"- {a['asset_id']}: {_fmt(a['flood_depth_m'], lang)}")
            head = "الأصول مرتبة حسب الأضرار المادية المقدرة في السيناريو التوضيحي (المدى يعني أن سمة ما مجهولة):" if lang == "ar" else "Assets ranked by estimated physical damage in the illustrative scenario (a range means an attribute is unknown):"
            tail = "الفئات المالية منفصلة: الأضرار المادية ليست خسارة ائتمانية. لم تُحتسب خسائر المقرض." if lang == "ar" else "Financial categories are separate: physical damage is not a credit loss. Lender loss is not modelled."
            text = "\n".join([head, *lines, tail])
        elif intent == "concentration":
            c = run["aggregation"]["concentration"]
            pct = round(c["share_of_portfolio_outstanding"] * 100, 1)
            refs["result://aggregation/concentration"] = {**c, "share_pct": pct}
            text = (f"{len(c['assets_in_footprint'])} أصول لـ {len(c['borrowers'])} مقترضين في {len(c['sectors'])} قطاعات ({'، '.join(c['sectors'])}) تقع داخل نطاق الفيضان نفسه. التعرض القائم داخل النطاق {c['outstanding_in_footprint_aed']:,.0f} درهم ({pct}% من المحفظة). الأضرار المادية للحدث الواحد: {_fmt(c['physical_damage_total_aed'], lang)} درهم. {run['aggregation']['diversification_warning_ar']}"
                    if lang == "ar" else
                    f"{len(c['assets_in_footprint'])} assets of {len(c['borrowers'])} borrowers across {len(c['sectors'])} sectors ({', '.join(c['sectors'])}) sit inside the same flood footprint. Outstanding exposure in the footprint: {c['outstanding_in_footprint_aed']:,.0f} AED ({pct}% of the portfolio). Single-event physical damage: {_fmt(c['physical_damage_total_aed'], lang)} AED. {run['aggregation']['diversification_warning_en']}")
        elif intent == "unknowns":
            items = []
            for a in run["assets"]:
                if a["status"] != "computed":
                    refs[a["ref"]] = {"status": a["status"], "flood_depth_m": a["flood_depth_m"], "damage": a["physical_damage_total_aed"], "insured": a["insured_loss_aed"]}
                    why = a["flood_depth_m"] if isinstance(a["flood_depth_m"], dict) else a["physical_damage_total_aed"] if isinstance(a["physical_damage_total_aed"], dict) else a["insured_loss_aed"]
                    items.append(f"- {a['asset_id']} ({a['precision']}): {_fmt(why, lang)}")
            text = ("العناصر غير المحسومة وأسبابها:\n" if lang == "ar" else "Unresolved items and why:\n") + ("\n".join(items) or ("لا شيء" if lang == "ar" else "none"))
        elif intent == "changes":
            d = diff or {"changes": [], "summary_en": "No previous run.", "summary_ar": "لا يوجد تشغيل سابق."}
            refs["result://diff"] = d
            text = (d["summary_ar"] if lang == "ar" else d["summary_en"]) + "\n" + "\n".join(f"- {c['asset_id']} {c['field']}: {c['from']} → {c['to']} ({c['kind']})" for c in d["changes"][:8])
        else:  # insurance
            lines = []
            for a in run["assets"]:
                refs[a["ref"]] = {"insured": a["insured_loss_aed"], "gap": a["uninsured_physical_damage_aed"]}
                lines.append(f"- {a['asset_id']}: " + ("خسارة مؤمنة " if lang == "ar" else "insured loss ") + _fmt(a["insured_loss_aed"], lang) + (" ، الفجوة غير المؤمنة " if lang == "ar" else ", uninsured share ") + _fmt(a["uninsured_physical_damage_aed"], lang))
            text = "\n".join(lines)
        refs["scenario"] = run["scenario"]
        return {**self.say(text, refs, lang, user=question), "intent": intent}
