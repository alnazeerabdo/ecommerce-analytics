"""
Reports & Export Module
=======================
Builds downloadable reports from the analytics + advanced analytics payloads.

- export_csv(analytics)              -> bytes  (KPI summary, single CSV table)
- export_excel(analytics, advanced)  -> bytes  (multi-sheet .xlsx workbook)
- export_pdf(analytics, advanced, ai_text) -> bytes (formatted Arabic PDF)

Arabic text in the PDF is shaped with `arabic_reshaper` + `python-bidi` and
rendered with a bundled Tajawal TTF so it matches the dashboard identity.
"""

from __future__ import annotations

import io
import os
from datetime import datetime

import pandas as pd

FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "fonts")
FONT_REGULAR = os.path.join(FONT_DIR, "Tajawal-Regular.ttf")
FONT_BOLD = os.path.join(FONT_DIR, "Tajawal-Bold.ttf")


# --------------------------------------------------------------------------- #
# CSV
# --------------------------------------------------------------------------- #
def export_csv(analytics: dict) -> bytes:
    """Flat CSV of the headline KPIs and date range."""
    kpis = analytics.get("kpis", {})
    dr = analytics.get("date_range", {})
    labels = {
        "total_revenue": "إجمالي الإيرادات",
        "total_orders": "إجمالي الطلبات",
        "total_customers": "عدد العملاء",
        "total_products": "عدد المنتجات",
        "avg_order_value": "متوسط قيمة الطلب",
        "avg_items_per_order": "منتجات لكل طلب",
        "repeat_customer_rate": "معدل تكرار الشراء %",
        "churn_rate": "معدل فقدان العملاء %",
        "active_customers": "عملاء نشطون",
        "inactive_customers": "عملاء غير نشطين",
    }
    rows = [{"المؤشر": "الفترة", "القيمة": f"{dr.get('start','N/A')} → {dr.get('end','N/A')}"}]
    rows += [{"المؤشر": labels.get(k, k), "القيمة": v} for k, v in kpis.items()]
    df = pd.DataFrame(rows)
    return df.to_csv(index=False).encode("utf-8-sig")


# --------------------------------------------------------------------------- #
# Excel (multi-sheet)
# --------------------------------------------------------------------------- #
def export_excel(analytics: dict, advanced: dict | None = None) -> bytes:
    """Multi-sheet workbook covering core + advanced analytics."""
    advanced = advanced or {}
    buf = io.BytesIO()

    def _df(data):
        return pd.DataFrame(data) if data else pd.DataFrame()

    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        # KPIs
        kpis = analytics.get("kpis", {})
        pd.DataFrame([kpis]).T.rename(columns={0: "value"}).to_excel(
            writer, sheet_name="KPIs"
        )

        sheets = {
            "Monthly Revenue": analytics.get("monthly_revenue"),
            "Top Products": analytics.get("top_products"),
            "Categories": analytics.get("category_breakdown"),
            "Regions": analytics.get("regional_performance"),
            "Top Customers": analytics.get("top_customers"),
            "Campaigns": analytics.get("campaign_performance"),
        }
        for name, data in sheets.items():
            d = _df(data)
            if not d.empty:
                d.to_excel(writer, sheet_name=name[:31], index=False)

        # Advanced sheets
        fc = advanced.get("forecast", {})
        if fc.get("available"):
            _df(fc.get("forecast")).to_excel(writer, sheet_name="Forecast", index=False)
        rec = advanced.get("recommendations", {})
        if rec.get("available"):
            _df(rec.get("pairs")).to_excel(writer, sheet_name="Recommendations", index=False)
        ch = advanced.get("churn_prediction", {})
        if ch.get("available"):
            _df(ch.get("at_risk_customers")).to_excel(writer, sheet_name="Churn Risk", index=False)
        inv = advanced.get("inventory", {})
        if inv.get("available"):
            _df(inv.get("velocity")).to_excel(writer, sheet_name="Inventory Velocity", index=False)
        an = advanced.get("anomalies", {})
        if an.get("available"):
            _df(an.get("revenue_anomalies")).to_excel(writer, sheet_name="Anomalies", index=False)

    buf.seek(0)
    return buf.getvalue()


# --------------------------------------------------------------------------- #
# PDF (Arabic, RTL)
# --------------------------------------------------------------------------- #
def _ar(text: str) -> str:
    """Reshape + bidi an Arabic string for correct RTL rendering in reportlab."""
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display

        return get_display(arabic_reshaper.reshape(str(text)))
    except Exception:
        return str(text)


def _register_fonts():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    registered = pdfmetrics.getRegisteredFontNames()
    if "Tajawal" not in registered and os.path.exists(FONT_REGULAR):
        pdfmetrics.registerFont(TTFont("Tajawal", FONT_REGULAR))
    if "Tajawal-Bold" not in registered and os.path.exists(FONT_BOLD):
        pdfmetrics.registerFont(TTFont("Tajawal-Bold", FONT_BOLD))


def export_pdf(analytics: dict, advanced: dict | None = None, ai_text: str | None = None) -> bytes:
    """Generate a polished Arabic PDF business report."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_RIGHT, TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
    )

    advanced = advanced or {}
    _register_fonts()
    base_font = "Tajawal" if os.path.exists(FONT_REGULAR) else "Helvetica"
    bold_font = "Tajawal-Bold" if os.path.exists(FONT_BOLD) else "Helvetica-Bold"

    PURPLE = colors.HexColor("#6c5ce7")
    DARK = colors.HexColor("#2d3436")
    GREY = colors.HexColor("#636e72")
    LIGHT = colors.HexColor("#f8f9fe")

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontName=bold_font,
                        fontSize=20, alignment=TA_CENTER, textColor=DARK, spaceAfter=4)
    sub = ParagraphStyle("sub", parent=styles["Normal"], fontName=base_font,
                         fontSize=10, alignment=TA_CENTER, textColor=GREY, spaceAfter=12)
    sec = ParagraphStyle("sec", parent=styles["Heading2"], fontName=bold_font,
                         fontSize=14, alignment=TA_RIGHT, textColor=PURPLE, spaceBefore=14, spaceAfter=6)
    body = ParagraphStyle("body", parent=styles["Normal"], fontName=base_font,
                          fontSize=10.5, alignment=TA_RIGHT, textColor=DARK, leading=18)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm,
        leftMargin=15 * mm, rightMargin=15 * mm,
        title="E-commerce Analytics Report",
    )
    story = []

    dr = analytics.get("date_range", {})
    story.append(Paragraph(_ar("تقرير تحليلات التجارة الإلكترونية"), h1))
    story.append(Paragraph(
        _ar(f"الفترة: {dr.get('start','N/A')} إلى {dr.get('end','N/A')}  •  "
            f"تم الإنشاء: {datetime.now().strftime('%Y-%m-%d %H:%M')}"), sub))
    story.append(HRFlowable(width="100%", color=PURPLE, thickness=1.2, spaceAfter=10))

    # ---- KPI table ----
    kpis = analytics.get("kpis", {})
    story.append(Paragraph(_ar("مؤشرات الأداء الرئيسية"), sec))
    kpi_rows = [
        [_ar("إجمالي الإيرادات"), f"${kpis.get('total_revenue', 0):,.2f}"],
        [_ar("إجمالي الطلبات"), f"{kpis.get('total_orders', 0):,}"],
        [_ar("عدد العملاء"), f"{kpis.get('total_customers', 0):,}"],
        [_ar("متوسط قيمة الطلب"), f"${kpis.get('avg_order_value', 0):,.2f}"],
        [_ar("معدل تكرار الشراء"), f"{kpis.get('repeat_customer_rate', 0)}%"],
        [_ar("معدل فقدان العملاء"), f"{kpis.get('churn_rate', 0)}%"],
    ]
    story.append(_kpi_table(kpi_rows, base_font, bold_font, PURPLE, LIGHT, DARK))

    # ---- Forecast ----
    fc = advanced.get("forecast", {})
    if fc.get("available"):
        story.append(Paragraph(_ar("توقعات الإيرادات والموسمية"), sec))
        h = fc.get("horizons", {})
        if fc.get("granularity") == "daily":
            txt = (f"الاتجاه العام: {fc.get('trend_direction','')} ({fc.get('trend_pct',0)}% يومياً). "
                   f"التوقع: 7 أيام ≈ ${h.get('7_day',0):,.0f}، "
                   f"30 يوماً ≈ ${h.get('30_day',0):,.0f}، "
                   f"90 يوماً ≈ ${h.get('90_day',0):,.0f}. "
                   f"أفضل يوم: {fc.get('best_day','')}، أضعف يوم: {fc.get('worst_day','')}.")
        else:
            txt = (f"الاتجاه العام: {fc.get('trend_direction','')} ({fc.get('trend_pct',0)}% شهرياً). "
                   f"توقع الشهر القادم ≈ ${h.get('next_month',0):,.0f}، "
                   f"الأشهر الثلاثة القادمة ≈ ${h.get('next_3_months',0):,.0f}.")
        story.append(Paragraph(_ar(txt), body))

    # ---- Alerts ----
    an = advanced.get("anomalies", {})
    alerts = an.get("alerts", [])
    if alerts:
        story.append(Paragraph(_ar("التنبيهات"), sec))
        for a in alerts:
            story.append(Paragraph(_ar(f"• {a['title']}: {a['message']}"), body))

    # ---- Churn ----
    ch = advanced.get("churn_prediction", {})
    if ch.get("available") and ch.get("summary"):
        s = ch["summary"]
        story.append(Paragraph(_ar("التنبؤ بفقدان العملاء"), sec))
        story.append(Paragraph(_ar(
            f"عدد العملاء المعرضين لخطر مرتفع: {s.get('high_risk',0)} "
            f"({s.get('high_risk_pct',0)}%) — الإيرادات المعرضة للخطر ≈ "
            f"${s.get('revenue_at_risk',0):,.0f}."), body))

    # ---- Top products ----
    tp = analytics.get("top_products", [])
    if tp:
        story.append(Paragraph(_ar("أفضل المنتجات"), sec))
        rows = [[_ar("المنتج"), _ar("الإيراد")]]
        for p in tp[:8]:
            rows.append([_ar(str(p.get("product_name", ""))), f"${p.get('revenue', 0):,.2f}"])
        story.append(_data_table(rows, base_font, bold_font, PURPLE, LIGHT, DARK))

    # ---- AI insights ----
    if ai_text:
        story.append(Paragraph(_ar("توصيات الذكاء الاصطناعي"), sec))
        for line in _clean_markdown(ai_text):
            story.append(Paragraph(_ar(line), body))
            story.append(Spacer(1, 2))

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()


def _kpi_table(rows, base_font, bold_font, accent, light, dark):
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle

    t = Table(rows, colWidths=[110 * 1, 380])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), base_font),
        ("FONTNAME", (0, 0), (0, -1), bold_font),
        ("FONTSIZE", (0, 0), (-1, -1), 10.5),
        ("ALIGN", (0, 0), (0, -1), "RIGHT"),
        ("ALIGN", (1, 0), (1, -1), "LEFT"),
        ("TEXTCOLOR", (0, 0), (-1, -1), dark),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [light, colors.white]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#e0e0e0")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    return t


def _data_table(rows, base_font, bold_font, accent, light, dark):
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle

    t = Table(rows, colWidths=[360, 130])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), base_font),
        ("FONTNAME", (0, 0), (-1, 0), bold_font),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (0, 0), (-1, 0), accent),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("TEXTCOLOR", (0, 1), (-1, -1), dark),
        ("ALIGN", (0, 0), (0, -1), "RIGHT"),
        ("ALIGN", (1, 0), (1, -1), "LEFT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [light, colors.white]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def _clean_markdown(text: str) -> list[str]:
    """Strip markdown syntax to plain lines suitable for PDF paragraphs."""
    import re

    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)   # bold
        line = re.sub(r"`(.*?)`", r"\1", line)          # code
        line = re.sub(r"^#+\s*", "", line)               # headings
        line = re.sub(r"^\s*[-*]\s*", "• ", line)        # bullets
        out.append(line)
    return out
