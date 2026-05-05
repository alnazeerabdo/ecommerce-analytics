"""
AI Insights Module — Google Gemini API + smart rule-based fallback.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """أنت محلل أعمال خبير في التجارة الإلكترونية بخبرة 15 سنة.
بناءً على ملخص التحليلات المقدم، قدم تحليلاً منظماً باللغة العربية:

1. **الرؤى الرئيسية** (3-5 نقاط) — ما الذي يعمل بشكل جيد، الأنماط، المقاييس البارزة
2. **المشاكل المكتشفة** (3-5 نقاط) — مخاطر الإيرادات، مشاكل الاحتفاظ، ضعف الأداء
3. **خطة عمل لزيادة الإيرادات** (5-7 خطوات) — خطوات محددة وقابلة للقياس ومرتبة حسب الأولوية (عالي/متوسط/منخفض)

كن دقيقاً بالأرقام. اشر إلى البيانات الفعلية. اكتب بأسلوب مهني وسهل الفهم.
استخدم تنسيق Markdown مع النص العريض والنقاط."""


def _get_google_api_key() -> str:
    """Get Google API key from Streamlit secrets or environment."""
    # Try Streamlit secrets first (for cloud deployment)
    try:
        import streamlit as st
        key = st.secrets.get("google", {}).get("api_key", "")
        if key:
            return key
    except Exception:
        pass
    # Fall back to env var
    return os.getenv("GOOGLE_API_KEY", "")


def _generate_with_gemini(summary_text: str, api_key: str) -> Optional[str]:
    """Call Google Gemini API for AI insights."""
    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)

        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=SYSTEM_PROMPT,
        )

        response = model.generate_content(
            f"Analyze this e-commerce data and provide actionable insights:\n\n{summary_text}",
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=1500,
                temperature=0.7,
            ),
        )

        return response.text

    except ImportError:
        logger.warning("google-generativeai not installed. Falling back to built-in analysis.")
        return None
    except Exception as e:
        logger.error(f"Google Gemini API error: {e}")
        return None


def _generate_fallback_insights(analytics: dict) -> str:
    """Rule-based insights when AI API is unavailable."""
    kpis = analytics["kpis"]
    monthly = analytics.get("monthly_revenue", [])
    top_products = analytics.get("top_products", [])
    categories = analytics.get("category_breakdown", [])
    regions = analytics.get("regional_performance", [])

    insights = []
    problems = []
    actions = []

    # --- Insights ---
    insights.append(
        f"حقق متجرك إيرادات إجمالية **${kpis['total_revenue']:,.2f}** "
        f"من **{kpis['total_orders']}** طلب و **{kpis['total_customers']}** عميل."
    )
    if kpis["repeat_customer_rate"] > 30:
        insights.append(f"ولاء قوي: **{kpis['repeat_customer_rate']}%** من العملاء يشترون أكثر من مرة.")
    else:
        insights.append(f"معدل التكرار **{kpis['repeat_customer_rate']}%** — هناك فرصة لتحسين الاحتفاظ بالعملاء.")

    insights.append(f"متوسط قيمة الطلب: **${kpis['avg_order_value']:,.2f}**.")

    if top_products:
        insights.append(f"المنتج الأكثر مبيعاً: **{top_products[0]['product_name']}** (${top_products[0]['revenue']:,.2f}).")

    if len(monthly) >= 3:
        recent = monthly[-1]["revenue"]
        previous = monthly[-2]["revenue"]
        if recent > previous:
            pct = round(((recent - previous) / previous) * 100, 1) if previous > 0 else 0
            insights.append(f"الإيرادات في ارتفاع: {monthly[-1]['month']} نمت **{pct}%** مقارنة بالشهر السابق.")

    # --- Problems ---
    if kpis["churn_rate"] > 50:
        problems.append(f"معدل فقدان عملاء مرتفع ({kpis['churn_rate']}%): {kpis['inactive_customers']} عميل غير نشط.")
    elif kpis["churn_rate"] > 30:
        problems.append(f"معدل فقدان متوسط ({kpis['churn_rate']}%): أعد استهداف {kpis['inactive_customers']} عميل.")

    if kpis["repeat_customer_rate"] < 25:
        problems.append(f"معدل تكرار منخفض ({kpis['repeat_customer_rate']}%): معظم العملاء يشترون مرة واحدة فقط.")

    if kpis["avg_items_per_order"] < 1.5:
        problems.append(f"حجم سلة منخفض ({kpis['avg_items_per_order']} منتج/طلب).")

    if categories and len(categories) > 1:
        if categories[0]["revenue"] > categories[-1]["revenue"] * 3:
            problems.append(
                f"تركز الإيرادات: '{categories[0]['category']}' بقيمة ${categories[0]['revenue']:,.2f} "
                f"مقابل '{categories[-1]['category']}' بقيمة ${categories[-1]['revenue']:,.2f}."
            )

    if not problems:
        problems.append("لا توجد مشاكل حرجة. ركز على توسيع ما ينجح.")

    # --- Actions ---
    actions.append(f"**برنامج ولاء**: استهدف {kpis['inactive_customers']} عميل غير نشط. *أولوية عالية*")
    actions.append(f"**البيع المتقاطع**: رفع المنتجات/طلب من {kpis['avg_items_per_order']} إلى 2.0+. *أولوية عالية*")

    if top_products and len(top_products) >= 2:
        actions.append(
            f"**ترويج الأفضل**: ادفع '{top_products[0]['product_name']}' و "
            f"'{top_products[1]['product_name']}'. *أولوية متوسطة*"
        )
    if categories and len(categories) >= 2:
        actions.append(f"**تعزيز '{categories[-1]['category']}'**: فقط ${categories[-1]['revenue']:,.2f}. *أولوية متوسطة*")
    if regions and len(regions) >= 2:
        actions.append(f"**التوسع في '{regions[-1]['region']}'**: ${regions[-1]['revenue']:,.2f}. *أولوية متوسطة*")

    actions.append("**أتمتة البريد الإلكتروني**: استرداد السلة، ما بعد الشراء، النشرات الإخبارية. *أولوية عالية*")
    actions.append("**التخطيط الموسمي**: استعد للذروة، روّج في الأشهر البطيئة. *أولوية منخفضة*")

    parts = ["## الرؤى الرئيسية\n"]
    parts.extend(f"- {i}\n" for i in insights)
    parts.append("\n## المشاكل المكتشفة\n")
    parts.extend(f"- {p}\n" for p in problems)
    parts.append("\n## خطة عمل لزيادة الإيرادات\n")
    for idx, a in enumerate(actions, 1):
        parts.append(f"{idx}. {a}\n\n")

    return "".join(parts)


def generate_insights(analytics: dict, summary_text: str) -> dict:
    """Generate insights — Google Gemini first, fallback to rule-based."""
    api_key = _get_google_api_key()

    insights_text = None
    model_used = None
    source = "fallback"

    if api_key and api_key != "your_google_api_key_here":
        logger.info("Calling Google Gemini API...")
        insights_text = _generate_with_gemini(summary_text, api_key)
        if insights_text:
            model_used = "Google Gemini 2.0 Flash"
            source = "gemini"
            logger.info("Successfully generated AI insights via Gemini.")

    if not insights_text:
        logger.info("Using built-in rule-based analysis engine.")
        insights_text = _generate_fallback_insights(analytics)
        model_used = "Built-in Analytics Engine"
        source = "builtin"

    return {"insights_text": insights_text, "model_used": model_used, "source": source}
