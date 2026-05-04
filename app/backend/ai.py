"""
AI Insights Module — Google Gemini API + smart rule-based fallback.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert e-commerce business analyst with 15 years of experience.
Given an analytics summary, provide a structured analysis:

1. **💡 KEY INSIGHTS** (3-5 bullet points) — What's working well, patterns, standout metrics
2. **⚠️ PROBLEMS DETECTED** (3-5 bullet points) — Revenue risks, retention issues, underperformance
3. **🚀 ACTION PLAN TO INCREASE REVENUE** (5-7 steps) — Specific, measurable, prioritized with HIGH/MEDIUM/LOW

Be specific with numbers. Reference the actual data. Professional but accessible tone.
Use markdown formatting with bold text and bullet points."""


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
        f"Your store generated **${kpis['total_revenue']:,.2f}** in total revenue "
        f"across **{kpis['total_orders']}** orders from **{kpis['total_customers']}** customers."
    )
    if kpis["repeat_customer_rate"] > 30:
        insights.append(f"Strong loyalty: **{kpis['repeat_customer_rate']}%** repeat buyers.")
    else:
        insights.append(f"Repeat rate at **{kpis['repeat_customer_rate']}%** — room to improve retention.")

    insights.append(f"Average order value: **${kpis['avg_order_value']:,.2f}**.")

    if top_products:
        insights.append(f"Top seller: **{top_products[0]['product_name']}** (${top_products[0]['revenue']:,.2f}).")

    if len(monthly) >= 3:
        recent = monthly[-1]["revenue"]
        previous = monthly[-2]["revenue"]
        if recent > previous:
            pct = round(((recent - previous) / previous) * 100, 1) if previous > 0 else 0
            insights.append(f"Revenue trending up: {monthly[-1]['month']} grew **{pct}%** vs prior month.")

    # --- Problems ---
    if kpis["churn_rate"] > 50:
        problems.append(f"⚠️ High churn ({kpis['churn_rate']}%): {kpis['inactive_customers']} inactive customers.")
    elif kpis["churn_rate"] > 30:
        problems.append(f"Moderate churn ({kpis['churn_rate']}%): re-engage {kpis['inactive_customers']} customers.")

    if kpis["repeat_customer_rate"] < 25:
        problems.append(f"Low repeat rate ({kpis['repeat_customer_rate']}%): most buy only once.")

    if kpis["avg_items_per_order"] < 1.5:
        problems.append(f"Low basket size ({kpis['avg_items_per_order']} items/order).")

    if categories and len(categories) > 1:
        if categories[0]["revenue"] > categories[-1]["revenue"] * 3:
            problems.append(
                f"Revenue concentration: '{categories[0]['category']}' at ${categories[0]['revenue']:,.2f} "
                f"vs '{categories[-1]['category']}' at ${categories[-1]['revenue']:,.2f}."
            )

    if not problems:
        problems.append("No critical issues. Focus on scaling what works.")

    # --- Actions ---
    actions.append(f"🎯 **Loyalty program**: Target {kpis['inactive_customers']} inactive customers. *HIGH*")
    actions.append(f"📦 **Cross-selling**: Boost items/order from {kpis['avg_items_per_order']} to 2.0+. *HIGH*")

    if top_products and len(top_products) >= 2:
        actions.append(
            f"📢 **Promote winners**: Push '{top_products[0]['product_name']}' & "
            f"'{top_products[1]['product_name']}'. *MEDIUM*"
        )
    if categories and len(categories) >= 2:
        actions.append(f"📊 **Boost '{categories[-1]['category']}'**: Only ${categories[-1]['revenue']:,.2f}. *MEDIUM*")
    if regions and len(regions) >= 2:
        actions.append(f"🌍 **Expand '{regions[-1]['region']}'**: ${regions[-1]['revenue']:,.2f}. *MEDIUM*")

    actions.append("📧 **Email automation**: Cart recovery, post-purchase, newsletters. *HIGH*")
    actions.append("📈 **Seasonal planning**: Prep for peaks, promote in slow months. *LOW*")

    parts = ["## 💡 Key Insights\n"]
    parts.extend(f"- {i}\n" for i in insights)
    parts.append("\n## ⚠️ Problems Detected\n")
    parts.extend(f"- {p}\n" for p in problems)
    parts.append("\n## 🚀 Action Plan to Increase Revenue\n")
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
