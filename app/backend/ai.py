"""
AI Insights Module — Google Gemini API + smart rule-based fallback.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """أنت محلل أعمال خبير في التجارة الإلكترونية بخبرة 15 سنة.
بناءً على ملخص التحليلات المقدم، قدم تحليلاً شاملاً ومفصلاً باللغة العربية.

اكتب تقريراً مطولاً يتضمن:

## الرؤى الرئيسية
- 5-8 نقاط مفصلة عن ما يعمل بشكل جيد
- اشرح لماذا هذه النقاط مهمة وما دلالتها
- استخدم الأرقام الفعلية من البيانات
- قارن بمعايير الصناعة إن أمكن

## المشاكل المكتشفة
- 5-8 نقاط عن المخاطر والمشاكل
- اشرح تأثير كل مشكلة على الأعمال
- قدّر الخسائر المحتملة بالأرقام

## خطة عمل لزيادة الإيرادات
- 7-10 خطوات مفصلة وعملية
- لكل خطوة: الهدف، التنفيذ، النتيجة المتوقعة، والأولوية (عالية/متوسطة/منخفضة)
- أعطِ تقديرات للعائد المتوقع من كل خطوة

## ملخص تنفيذي
- فقرة ختامية تلخص أهم 3 إجراءات يجب اتخاذها فوراً

كن دقيقاً بالأرقام. اشر إلى البيانات الفعلية. اكتب بأسلوب مهني ومفصل.
استخدم تنسيق Markdown. اكتب تقريراً لا يقل عن 800 كلمة."""


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
            model_name="gemini-3.1-flash-lite-preview",
            system_instruction=SYSTEM_PROMPT,
        )

        response = model.generate_content(
            f"حلل بيانات التجارة الإلكترونية التالية وقدم تقريراً شاملاً ومفصلاً باللغة العربية:\n\n{summary_text}",
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=4000,
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

    # --- Detailed Insights ---
    rev_per_customer = round(kpis['total_revenue'] / kpis['total_customers'], 2) if kpis['total_customers'] > 0 else 0

    insights.append(
        f"حقق متجرك إيرادات إجمالية **${kpis['total_revenue']:,.2f}** "
        f"من **{kpis['total_orders']}** طلب و **{kpis['total_customers']}** عميل. "
        f"هذا يعني أن كل عميل ساهم بمعدل **${rev_per_customer:,.2f}** في الإيرادات الإجمالية."
    )

    if kpis["repeat_customer_rate"] > 30:
        insights.append(
            f"نسبة تكرار الشراء ممتازة عند **{kpis['repeat_customer_rate']}%** — "
            f"هذا يدل على رضا العملاء عن المنتجات والخدمة. المعدل العالمي للتجارة الإلكترونية يتراوح بين 20-30%، "
            f"مما يضع متجرك في مركز متقدم."
        )
    else:
        insights.append(
            f"معدل التكرار عند **{kpis['repeat_customer_rate']}%** وهو أقل من المعدل المثالي (30%+). "
            f"هذا يعني أن معظم العملاء يشترون مرة واحدة ولا يعودون، "
            f"مما يشير إلى فرصة كبيرة لتحسين تجربة ما بعد البيع وبرامج الولاء."
        )

    insights.append(
        f"متوسط قيمة الطلب: **${kpis['avg_order_value']:,.2f}**. "
        f"لرفع هذا المعدل، يمكن تقديم عروض 'اشترِ أكثر ووفّر أكثر' أو إضافة منتجات تكميلية عند السلة."
    )

    if top_products:
        insights.append(
            f"المنتج الأكثر مبيعاً هو **{top_products[0]['product_name']}** بإيرادات **${top_products[0]['revenue']:,.2f}**. "
            f"هذا المنتج يمثل محرك نمو أساسي ويجب حمايته من نفاد المخزون وتعزيز ظهوره."
        )
        if len(top_products) >= 3:
            top3_rev = sum(p['revenue'] for p in top_products[:3])
            top3_pct = round((top3_rev / kpis['total_revenue']) * 100, 1) if kpis['total_revenue'] > 0 else 0
            insights.append(
                f"أفضل 3 منتجات تمثل **{top3_pct}%** من الإيرادات الإجمالية "
                f"(${top3_rev:,.2f} من ${kpis['total_revenue']:,.2f}). "
                f"يُنصح بتنويع مصادر الإيراد لتقليل المخاطر."
            )

    if len(monthly) >= 3:
        recent = monthly[-1]["revenue"]
        previous = monthly[-2]["revenue"]
        if recent > previous:
            pct = round(((recent - previous) / previous) * 100, 1) if previous > 0 else 0
            insights.append(
                f"الإيرادات في اتجاه صعودي: شهر {monthly[-1]['month']} حقق **${recent:,.2f}** "
                f"بنمو **{pct}%** مقارنة بالشهر السابق ({monthly[-2]['month']}: ${previous:,.2f}). "
                f"هذا مؤشر إيجابي يدل على فعالية الاستراتيجيات الحالية."
            )
        elif recent < previous:
            pct = round(((previous - recent) / previous) * 100, 1) if previous > 0 else 0
            insights.append(
                f"تراجع الإيرادات: شهر {monthly[-1]['month']} حقق **${recent:,.2f}** "
                f"بانخفاض **{pct}%** مقارنة بالشهر السابق. يجب تحليل الأسباب واتخاذ إجراءات تصحيحية."
            )

    if categories and len(categories) >= 2:
        insights.append(
            f"التصنيف الأقوى هو **'{categories[0]['category']}'** بإيرادات **${categories[0]['revenue']:,.2f}**، "
            f"بينما الأضعف هو **'{categories[-1]['category']}'** بإيرادات **${categories[-1]['revenue']:,.2f}**. "
            f"التنويع في التصنيفات يحمي من تقلبات السوق."
        )

    # --- Detailed Problems ---
    if kpis["churn_rate"] > 50:
        lost_revenue = round(rev_per_customer * kpis['inactive_customers'], 2)
        problems.append(
            f"معدل فقدان عملاء مرتفع جداً عند **{kpis['churn_rate']}%** — "
            f"هناك **{kpis['inactive_customers']}** عميل غير نشط من أصل {kpis['total_customers']}. "
            f"الخسارة المحتملة تقدر بـ **${lost_revenue:,.2f}** إذا لم يتم إعادة تنشيطهم."
        )
    elif kpis["churn_rate"] > 30:
        problems.append(
            f"معدل فقدان متوسط عند **{kpis['churn_rate']}%**: "
            f"**{kpis['inactive_customers']}** عميل لم يشترِ خلال 30 يوماً. "
            f"يُنصح بإرسال عروض حصرية وحوافز للعودة."
        )

    if kpis["repeat_customer_rate"] < 25:
        problems.append(
            f"معدل تكرار منخفض جداً عند **{kpis['repeat_customer_rate']}%** — "
            f"هذا يعني أن **{100 - kpis['repeat_customer_rate']}%** من العملاء يشترون مرة واحدة فقط. "
            f"تكلفة اكتساب عميل جديد أعلى 5-7 مرات من الاحتفاظ بعميل حالي."
        )

    if kpis["avg_items_per_order"] < 1.5:
        problems.append(
            f"حجم سلة التسوق منخفض عند **{kpis['avg_items_per_order']} منتج/طلب** — "
            f"رفع هذا المعدل إلى 2.0+ يمكن أن يزيد الإيرادات بنسبة 30-50% بدون تكلفة اكتساب إضافية."
        )

    if categories and len(categories) > 1:
        if categories[0]["revenue"] > categories[-1]["revenue"] * 3:
            problems.append(
                f"تركز خطير في الإيرادات: تصنيف **'{categories[0]['category']}'** يحقق "
                f"**${categories[0]['revenue']:,.2f}** مقابل **${categories[-1]['revenue']:,.2f}** "
                f"لتصنيف **'{categories[-1]['category']}'**."
            )

    if regions and len(regions) > 1:
        problems.append(
            f"تفاوت جغرافي: **'{regions[0]['region']}'** تحقق "
            f"**${regions[0]['revenue']:,.2f}** بينما **'{regions[-1]['region']}'** تحقق "
            f"**${regions[-1]['revenue']:,.2f}** فقط."
        )

    if not problems:
        problems.append("لا توجد مشاكل حرجة حالياً. ركز على توسيع ما ينجح وتحسين الأداء التشغيلي.")

    # --- Detailed Actions ---
    actions.append(
        f"**برنامج ولاء واسترداد العملاء**: أطلق حملة لاستهداف **{kpis['inactive_customers']}** عميل غير نشط "
        f"عبر بريد إلكتروني مخصص مع خصم 15-20%. النتيجة المتوقعة: استرداد 10-15% من العملاء "
        f"وإيرادات إضافية تقدر بـ **${round(rev_per_customer * kpis['inactive_customers'] * 0.1, 2):,.2f}**. *أولوية عالية*"
    )
    actions.append(
        f"**تحسين البيع المتقاطع**: رفع متوسط المنتجات/طلب من **{kpis['avg_items_per_order']}** "
        f"إلى 2.0+ عبر اقتراحات 'منتجات مكملة'. "
        f"النتيجة المتوقعة: زيادة متوسط قيمة الطلب بنسبة 20-35%. *أولوية عالية*"
    )

    if top_products and len(top_products) >= 2:
        actions.append(
            f"**تعزيز المنتجات الرائدة**: ضاعف الجهود التسويقية على "
            f"**'{top_products[0]['product_name']}'** و**'{top_products[1]['product_name']}'** "
            f"عبر إعلانات مدفوعة ومحتوى تسويقي. *أولوية متوسطة*"
        )
    if categories and len(categories) >= 2:
        actions.append(
            f"**تطوير التصنيفات الضعيفة**: تصنيف **'{categories[-1]['category']}'** يحقق فقط "
            f"**${categories[-1]['revenue']:,.2f}**. راجع التسعير والعرض وأطلق عروض ترويجية مخصصة. *أولوية متوسطة*"
        )
    if regions and len(regions) >= 2:
        actions.append(
            f"**التوسع الجغرافي**: المنطقة **'{regions[-1]['region']}'** تحقق فقط "
            f"**${regions[-1]['revenue']:,.2f}**. قدم عروض شحن مجاني أو خصومات إقليمية. *أولوية متوسطة*"
        )

    actions.append(
        "**أتمتة التسويق بالبريد الإلكتروني**: أنشئ 4 حملات: "
        "ترحيب، استرداد السلة المهجورة، متابعة ما بعد الشراء، ونشرة أسبوعية. "
        "النتيجة المتوقعة: زيادة الإيرادات 15-25%. *أولوية عالية*"
    )
    actions.append(
        "**تحسين تجربة المستخدم**: راجع سرعة التحميل وعملية الدفع. "
        "كل ثانية تأخير تقلل التحويلات بنسبة 7%. أضف مراجعات العملاء وصور عالية الجودة. *أولوية متوسطة*"
    )
    actions.append(
        "**التخطيط الموسمي**: حلل أنماط الشراء الشهرية واستعد للذروة بمخزون كافٍ. "
        "خطط لعروض المناسبات (رمضان، الجمعة البيضاء، نهاية السنة). *أولوية منخفضة*"
    )

    # --- Build Report ---
    parts = ["## الرؤى الرئيسية\n"]
    parts.extend(f"- {i}\n\n" for i in insights)
    parts.append("\n## المشاكل المكتشفة\n")
    parts.extend(f"- {p}\n\n" for p in problems)
    parts.append("\n## خطة عمل لزيادة الإيرادات\n")
    for idx, a in enumerate(actions, 1):
        parts.append(f"{idx}. {a}\n\n")

    parts.append("\n## ملخص تنفيذي\n")
    parts.append(
        f"بناءً على تحليل بياناتك، أهم 3 إجراءات يجب اتخاذها فوراً: "
        f"**(1)** إطلاق برنامج استرداد العملاء غير النشطين ({kpis['inactive_customers']} عميل)، "
        f"**(2)** تحسين البيع المتقاطع لرفع متوسط قيمة الطلب، "
        f"**(3)** أتمتة التسويق بالبريد الإلكتروني. "
        f"تنفيذ هذه الخطوات يمكن أن يزيد الإيرادات بنسبة **25-40%** خلال الربع القادم.\n"
    )

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
