"""Bilingual reporting from one structured result tree.

The same `brief_tree` feeds both languages, so numbers are identical in ar and en by
construction. Financial categories are rendered in separate columns and never totalled across.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from services.register import Store

TEMPLATES = Path(__file__).parent / "templates"

STRINGS = {
    "en": {
        "title": "Portfolio physical-risk review brief", "illustrative": "ILLUSTRATIVE SCENARIO - synthetic data, not an operational prediction",
        "scenario": "Scenario", "coverage": "Coverage", "assets_confirmed": "asset locations confirmed", "open_questions": "open questions",
        "asset": "Asset", "borrower": "Borrower", "sector": "Sector", "precision": "Location precision", "depth": "Depth above floor (m)",
        "outstanding": "Outstanding exposure (AED)", "damage": "Physical damage estimate (AED)", "bi": "Interruption cost (AED)", "insured": "Insured loss after terms (AED)",
        "collateral": "Collateral value sensitivity (AED)", "credit_loss": "Modelled lender loss", "not_modelled": "not modelled (requires institution credit model)",
        "concentration": "Shared physical vulnerability", "changes": "Changes since previous run", "adaptation": "Protective measure comparison",
        "assumptions": "Assumptions and provenance", "glossary": "Glossary", "unknown": "unknown", "no_changes": "No changes recorded.",
        "avoided": "Avoided loss (this event)", "residual": "Residual damage (this event)", "capex": "Capital cost", "bcr": "Event-conditional benefit / cost",
        "columns_note": "Columns are separate financial categories and must not be summed across.",
    },
    "ar": {
        "title": "موجز مراجعة المخاطر المادية للمحفظة", "illustrative": "سيناريو توضيحي - بيانات اصطناعية، وليس تنبؤاً تشغيلياً",
        "scenario": "السيناريو", "coverage": "التغطية", "assets_confirmed": "مواقع أصول مؤكدة", "open_questions": "أسئلة مفتوحة",
        "asset": "الأصل", "borrower": "المقترض", "sector": "القطاع", "precision": "دقة الموقع", "depth": "العمق فوق الأرضية (م)",
        "outstanding": "التعرض القائم (درهم)", "damage": "تقدير الأضرار المادية (درهم)", "bi": "تكلفة التوقف (درهم)", "insured": "الخسارة المؤمنة بعد الشروط (درهم)",
        "collateral": "حساسية قيمة الضمان (درهم)", "credit_loss": "خسارة المقرض المنمذجة", "not_modelled": "غير منمذجة (تتطلب نموذج ائتمان المؤسسة)",
        "concentration": "نقطة ضعف مادية مشتركة", "changes": "التغييرات منذ التشغيل السابق", "adaptation": "مقارنة الإجراء الوقائي",
        "assumptions": "الافتراضات والمصدر", "glossary": "المصطلحات", "unknown": "غير معروف", "no_changes": "لم تُسجل تغييرات.",
        "avoided": "الخسارة المتجنبة (هذا الحدث)", "residual": "الأضرار المتبقية (هذا الحدث)", "capex": "التكلفة الرأسمالية", "bcr": "المنفعة / التكلفة المشروطة بالحدث",
        "columns_note": "الأعمدة فئات مالية منفصلة ولا يجوز جمعها معاً.",
    },
}

GLOSSARY = [
    {"term_en": "Physical risk", "term_ar": "المخاطر المادية", "def_en": "Potential loss from physical climate hazards affecting assets or operations.", "def_ar": "الخسارة المحتملة من المخاطر المناخية المادية التي تؤثر على الأصول أو العمليات."},
    {"term_en": "Replacement value", "term_ar": "قيمة الاستبدال", "def_en": "Cost to rebuild or replace; distinct from market value.", "def_ar": "تكلفة إعادة البناء أو الاستبدال؛ تختلف عن القيمة السوقية."},
    {"term_en": "Expected annual loss", "term_ar": "الخسارة السنوية المتوقعة", "def_en": "Loss integrated over annual event probabilities; requires a probabilistic model.", "def_ar": "الخسارة المتكاملة عبر احتمالات الأحداث السنوية؛ تتطلب نموذجاً احتمالياً."},
    {"term_en": "Scenario analysis", "term_ar": "تحليل السيناريو", "def_en": "Outcome conditional on one specified event and pathway.", "def_ar": "النتيجة المشروطة بحدث ومسار محددين."},
]


def fmt(v: Any, lang: str) -> str:
    """One formatter for both languages: identical digits, identical rounding."""
    u = STRINGS[lang]["unknown"]
    if v is None:
        return u
    if isinstance(v, dict):
        if v.get("unknown"):
            return f"{u} - {v.get('reason_ar') or v.get('reason') if lang == 'ar' else v.get('reason')}"
        return f"{v['low']:,.0f} – {v['high']:,.0f}"
    if isinstance(v, float):
        return f"{v:,.0f}" if abs(v) >= 100 else f"{v:,.2f}"
    return str(v)


@lru_cache(maxsize=1)
def _env() -> Environment:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES)), autoescape=select_autoescape(["html"]))
    return env


def brief_tree(store: Store, run: dict[str, Any], diff: dict[str, Any] | None = None, adaptation: dict[str, Any] | None = None) -> dict[str, Any]:
    cov = store.coverage()
    return {"run": run, "coverage": cov, "diff": diff, "adaptation": adaptation, "questions": [q.model_dump() for q in store.open_questions()], "glossary": GLOSSARY, "cases": [c.model_dump() for c in store.s.cases.values()]}


def render_brief(tree: dict[str, Any], lang: str) -> str:
    t = _env().get_template("brief.html.j2")
    return t.render(t=STRINGS[lang], lang=lang, dir="rtl" if lang == "ar" else "ltr", tree=tree, fmt=lambda v: fmt(v, lang))


def numeric_parity(tree: dict[str, Any]) -> bool:
    """Invariant 7: the results tables must contain identical numeric tokens in both languages."""
    import re

    def table_numbers(html: str) -> list[str]:
        body = "".join(re.findall(r"<!--RESULTS-->(.*?)<!--/RESULTS-->", html, re.S))
        return re.findall(r"\d[\d,]*(?:\.\d+)?", body)

    return table_numbers(render_brief(tree, "en")) == table_numbers(render_brief(tree, "ar"))
