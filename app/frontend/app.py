"""
لوحة التحليلات — وكيل تحليلات التجارة الإلكترونية
تصميم عصري فاتح باللغة العربية
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.backend.analytics import compute_analytics, generate_summary_text, read_file, detect_columns
from app.backend.ai import generate_insights

# --- Page Config ---
st.set_page_config(
    page_title="وكيل التحليلات — ذكاء التجارة الإلكترونية",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Modern Light Arabic CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;800&display=swap');

    * { font-family: 'Tajawal', sans-serif !important; }

    .stApp {
        background: linear-gradient(135deg, #f8f9fe 0%, #eef1f8 50%, #f0f4ff 100%);
        direction: rtl;
    }

    #MainMenu, footer, header { visibility: hidden; }

    /* Wider sidebar */
    [data-testid="stSidebar"] { min-width: 320px !important; max-width: 320px !important; }
    [data-testid="stSidebar"] > div:first-child { width: 320px !important; }

    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 1400px;
    }

    /* Flat icon circles */
    .flat-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 48px;
        height: 48px;
        border-radius: 14px;
        font-size: 20px;
        margin-bottom: 10px;
        font-weight: 700;
        color: #fff;
    }
    .fi-purple { background: #6c5ce7; }
    .fi-blue { background: #0984e3; }
    .fi-green { background: #00b894; }
    .fi-pink { background: #e17055; }
    .fi-teal { background: #00cec9; }
    .fi-orange { background: #f39c12; }

    /* KPI Cards */
    .kpi-card {
        background: #ffffff;
        border-radius: 20px;
        padding: 24px 20px;
        text-align: center;
        border: 1px solid rgba(0,0,0,0.05);
        box-shadow: 0 4px 20px rgba(0,0,0,0.04);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 4px;
        border-radius: 20px 20px 0 0;
    }
    .kpi-card.purple::before { background: linear-gradient(90deg, #6c5ce7, #a29bfe); }
    .kpi-card.blue::before { background: linear-gradient(90deg, #0984e3, #74b9ff); }
    .kpi-card.green::before { background: linear-gradient(90deg, #00b894, #55efc4); }
    .kpi-card.pink::before { background: linear-gradient(90deg, #e17055, #fab1a0); }
    .kpi-card.teal::before { background: linear-gradient(90deg, #00cec9, #81ecec); }
    .kpi-card.orange::before { background: linear-gradient(90deg, #f39c12, #ffeaa7); }
    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.08);
    }
    .kpi-icon { margin-bottom: 8px; }
    .kpi-value {
        font-size: 28px;
        font-weight: 800;
        color: #2d3436;
        margin: 4px 0;
    }
    .kpi-label {
        font-size: 14px;
        color: #636e72;
        font-weight: 500;
    }
    .kpi-badge {
        font-size: 12px;
        font-weight: 700;
        margin-top: 8px;
        padding: 4px 12px;
        border-radius: 20px;
        display: inline-block;
    }
    .badge-good { color: #00b894; background: rgba(0,184,148,0.1); }
    .badge-warn { color: #e17055; background: rgba(225,112,85,0.1); }

    /* Section Headers */
    .section-title {
        font-size: 22px;
        font-weight: 800;
        color: #2d3436;
        margin: 36px 0 16px 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .section-title::after {
        content: '';
        flex: 1;
        height: 2px;
        background: linear-gradient(90deg, rgba(108,92,231,0.3), transparent);
        border-radius: 2px;
    }

    /* Hero */
    .hero {
        background: #ffffff;
        border-radius: 24px;
        padding: 48px 40px;
        text-align: center;
        border: 1px solid rgba(0,0,0,0.05);
        box-shadow: 0 4px 24px rgba(0,0,0,0.04);
        margin-bottom: 32px;
        position: relative;
        overflow: hidden;
    }
    .hero::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 5px;
        background: linear-gradient(90deg, #6c5ce7, #0984e3, #00b894, #f39c12);
    }
    .hero h1 {
        font-size: 38px;
        font-weight: 800;
        color: #2d3436;
        margin-bottom: 12px;
    }
    .hero p { color: #636e72; font-size: 17px; line-height: 1.8; }

    /* Tips Box */
    .tips-box {
        background: linear-gradient(135deg, #dfe6e9, #f0f4ff);
        border-radius: 16px;
        padding: 24px;
        border-right: 4px solid #6c5ce7;
        margin: 16px 0;
    }
    .tips-box h3 { color: #6c5ce7; margin-bottom: 12px; font-size: 18px; }
    .tips-box ul { color: #2d3436; line-height: 2; padding-right: 20px; }

    /* AI Panel */
    .ai-panel {
        background: #ffffff;
        border-radius: 20px;
        padding: 28px;
        border: 1px solid rgba(108,92,231,0.15);
        box-shadow: 0 4px 24px rgba(108,92,231,0.06);
        position: relative;
        overflow: hidden;
    }
    .ai-panel::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 4px;
        background: linear-gradient(90deg, #6c5ce7, #0984e3, #00b894);
    }
    .ai-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: linear-gradient(135deg, #6c5ce7, #a29bfe);
        color: white;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 700;
        margin-bottom: 16px;
    }

    /* Feature Cards */
    .feature-card {
        background: #ffffff;
        border-radius: 20px;
        padding: 32px 24px;
        text-align: center;
        border: 1px solid rgba(0,0,0,0.05);
        box-shadow: 0 4px 20px rgba(0,0,0,0.04);
        transition: all 0.3s ease;
    }
    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.08);
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #ffffff;
        border-left: 1px solid rgba(0,0,0,0.06);
        padding-top: 1rem;
    }

    /* Divider */
    .divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(108,92,231,0.15), transparent);
        margin: 28px 0;
        border-radius: 2px;
    }

    /* Columns mapping */
    .col-map {
        background: #f8f9fe;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid rgba(0,0,0,0.05);
        margin: 8px 0;
    }
    .col-map-item {
        display: inline-block;
        background: #ffffff;
        padding: 4px 14px;
        border-radius: 20px;
        margin: 4px;
        font-size: 13px;
        border: 1px solid rgba(108,92,231,0.2);
        color: #6c5ce7;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# --- Helper Functions ---
def render_kpi(icon_letter, value, label, color="purple", badge=None, badge_type="good"):
    badge_html = ""
    if badge:
        badge_html = f'<div class="kpi-badge badge-{badge_type}">{badge}</div>'
    st.markdown(f"""
    <div class="kpi-card {color}">
        <div class="kpi-icon"><span class="flat-icon fi-{color}" style="width:40px;height:40px;border-radius:12px;font-size:16px;">{icon_letter}</span></div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
        {badge_html}
    </div>
    """, unsafe_allow_html=True)


def chart_layout():
    return dict(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Tajawal, sans-serif", color="#2d3436", size=13),
        margin=dict(l=20, r=20, t=44, b=20),
    )


# --- Sidebar ---
with st.sidebar:
    st.markdown("## وكيل التحليلات")
    st.markdown("---")
    st.markdown("### رفع ملف البيانات")

    uploaded_file = st.file_uploader(
        "اسحب ملفك هنا أو اختر ملف",
        type=["csv", "xlsx", "xls"],
        help="يدعم ملفات CSV و Excel بأي تنسيق أعمدة",
    )

    st.markdown("---")
    use_sample = st.button("تحميل بيانات تجريبية", use_container_width=True, type="primary")
    st.markdown("---")

    # Tips section
    st.markdown("""
    <div class="tips-box">
        <h3>نصائح للحصول على أفضل نتائج</h3>
        <ul>
            <li>أضف عمود <b>التاريخ</b> لعرض الاتجاهات الشهرية</li>
            <li>أضف عمود <b>المنتج</b> لمعرفة الأكثر مبيعاً</li>
            <li>أضف عمود <b>السعر/المبلغ</b> لحساب الإيرادات</li>
            <li>أضف عمود <b>العميل</b> لتحليل الولاء</li>
            <li>أضف عمود <b>التصنيف</b> لتحليل الفئات</li>
            <li>أضف عمود <b>المنطقة</b> لتحليل المناطق</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.caption("يدعم أسماء الأعمدة بالعربية والإنجليزية")
    st.caption("مبني باستخدام Streamlit + Supabase + Gemini")


# --- Load Data ---
df = None

if use_sample:
    sample_path = Path(__file__).resolve().parent.parent.parent / "data_sample.csv"
    if sample_path.exists():
        df = pd.read_csv(sample_path)
        st.session_state["data"] = df
        st.session_state["filename"] = "data_sample.csv"

if uploaded_file is not None:
    try:
        content = uploaded_file.read()
        df = read_file(content, uploaded_file.name)
        st.session_state["data"] = df
        st.session_state["filename"] = uploaded_file.name
    except Exception as e:
        st.error(f"❌ خطأ في قراءة الملف: {e}")

if df is None and "data" in st.session_state:
    df = st.session_state["data"]


# --- Landing Page ---
if df is None:
    st.markdown("""
    <div class="hero">
        <h1>وكيل تحليلات التجارة الإلكترونية</h1>
        <p>ارفع ملف بيانات المبيعات (CSV أو Excel) واحصل على تحليلات شاملة<br>وتوصيات ذكية مدعومة بالذكاء الاصطناعي لتنمية أعمالك</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="feature-card">
            <div class="flat-icon fi-purple">&#8593;</div>
            <div style="font-size:20px; font-weight:700; color:#2d3436; margin-bottom:8px;">١. ارفع بياناتك</div>
            <div style="color:#636e72; font-size:15px; line-height:1.8;">ارفع ملف CSV أو Excel بأي تنسيق — النظام يكتشف الأعمدة تلقائياً</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="feature-card">
            <div class="flat-icon fi-blue">&#9650;</div>
            <div style="font-size:20px; font-weight:700; color:#2d3436; margin-bottom:8px;">٢. شاهد التحليلات</div>
            <div style="color:#636e72; font-size:15px; line-height:1.8;">مؤشرات الأداء، اتجاهات الإيرادات، أفضل المنتجات، وتحليل العملاء</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="feature-card">
            <div class="flat-icon fi-green">AI</div>
            <div style="font-size:20px; font-weight:700; color:#2d3436; margin-bottom:8px;">٣. توصيات الذكاء الاصطناعي</div>
            <div style="color:#636e72; font-size:15px; line-height:1.8;">احصل على توصيات عملية مدعومة بـ Google Gemini لزيادة الأرباح</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.info("ارفع ملف بيانات أو اضغط **تحميل بيانات تجريبية** من الشريط الجانبي للبدء")
    st.stop()


# --- Compute Analytics ---
analytics = compute_analytics(df)
kpis = analytics["kpis"]
col_map = analytics.get("column_mapping", {})

# Show detected columns
filename = st.session_state.get("filename", "ملف")
st.markdown(f"""
<div class="hero" style="padding: 24px 40px;">
    <h1>لوحة تحليلات المبيعات</h1>
    <p>تحليل <strong>{filename}</strong> — {kpis['total_orders']} طلب • {analytics['date_range']['start']} إلى {analytics['date_range']['end']}</p>
</div>
""", unsafe_allow_html=True)

# Show column mapping
if col_map:
    role_labels = {
        "date": "التاريخ", "order_id": "رقم الطلب", "customer_id": "رقم العميل",
        "customer_name": "اسم العميل", "product": "المنتج", "category": "التصنيف",
        "quantity": "الكمية", "total_price": "المبلغ", "unit_price": "سعر الوحدة",
        "region": "المنطقة",
    }
    chips = " ".join(
        f'<span class="col-map-item">{role_labels.get(role, role)}: {col}</span>'
        for role, col in col_map.items()
    )
    st.markdown(f"""
    <div class="col-map">
        <span style="font-weight:700; color:#2d3436; font-size:14px;">الأعمدة المكتشفة تلقائياً:</span><br>
        {chips}
    </div>
    """, unsafe_allow_html=True)


# ============================
# KPI CARDS
# ============================
st.markdown('<div class="section-title">مؤشرات الأداء الرئيسية</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1:
    render_kpi("$", f"${kpis['total_revenue']:,.2f}", "إجمالي الإيرادات", "purple")
with c2:
    render_kpi("#", f"{kpis['total_orders']:,}", "إجمالي الطلبات", "blue")
with c3:
    render_kpi("U", f"{kpis['total_customers']:,}", "عدد العملاء", "green")
with c4:
    render_kpi("~", f"${kpis['avg_order_value']:,.2f}", "متوسط قيمة الطلب", "pink")

st.markdown("<br>", unsafe_allow_html=True)

c5, c6, c7, c8 = st.columns(4)
with c5:
    render_kpi("P", f"{kpis['total_products']}", "عدد المنتجات", "teal")
with c6:
    render_kpi("x", f"{kpis['avg_items_per_order']}", "منتجات لكل طلب", "orange")
with c7:
    bt = "good" if kpis['repeat_customer_rate'] > 30 else "warn"
    bl = "جيد" if bt == "good" else "يحتاج تحسين"
    render_kpi("%", f"{kpis['repeat_customer_rate']}%", "معدل تكرار الشراء", "green", bl, bt)
with c8:
    bt = "warn" if kpis['churn_rate'] > 40 else "good"
    bl = "مرتفع" if bt == "warn" else "مستقر"
    render_kpi("!", f"{kpis['churn_rate']}%", "معدل فقدان العملاء", "pink", bl, bt)


# ============================
# CHARTS
# ============================
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">تحليل الإيرادات</div>', unsafe_allow_html=True)

theme = chart_layout()

col_l, col_r = st.columns([2, 1])

with col_l:
    monthly_df = pd.DataFrame(analytics["monthly_revenue"])
    if not monthly_df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=monthly_df["month"], y=monthly_df["revenue"],
            mode="lines+markers", fill="tozeroy",
            line=dict(color="#6c5ce7", width=3),
            fillcolor="rgba(108,92,231,0.08)",
            marker=dict(size=8, color="#6c5ce7"),
            hovertemplate="<b>%{x}</b><br>الإيراد: $%{y:,.2f}<extra></extra>",
        ))
        fig.update_layout(title="اتجاه الإيرادات الشهرية", height=400, **theme)
        fig.update_yaxes(gridcolor="rgba(0,0,0,0.04)")
        fig.update_xaxes(gridcolor="rgba(0,0,0,0.04)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("أضف عمود تاريخ في بياناتك لعرض الاتجاهات الشهرية")

with col_r:
    cat_df = pd.DataFrame(analytics["category_breakdown"])
    if not cat_df.empty:
        colors = ["#6c5ce7", "#0984e3", "#00b894", "#e17055", "#f39c12", "#fd79a8"]
        fig = go.Figure(data=[go.Pie(
            labels=cat_df["category"], values=cat_df["revenue"],
            hole=0.55, marker=dict(colors=colors[:len(cat_df)]),
            textinfo="label+percent",
            textfont=dict(size=12, color="#2d3436"),
            hovertemplate="<b>%{label}</b><br>الإيراد: $%{value:,.2f}<br>النسبة: %{percent}<extra></extra>",
        )])
        fig.update_layout(title="الإيرادات حسب التصنيف", height=400, showlegend=False, **theme)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("أضف عمود تصنيف في بياناتك لعرض هذا الرسم")


# Row 2
st.markdown('<div class="section-title">أداء المنتجات والمناطق</div>', unsafe_allow_html=True)

col_l2, col_r2 = st.columns(2)

with col_l2:
    prod_df = pd.DataFrame(analytics["top_products"])
    if not prod_df.empty:
        prod_df = prod_df.sort_values("revenue", ascending=True)
        fig = go.Figure(data=[go.Bar(
            x=prod_df["revenue"], y=prod_df["product_name"],
            orientation="h",
            marker=dict(
                color=prod_df["revenue"],
                colorscale=[[0, "#a29bfe"], [0.5, "#6c5ce7"], [1, "#0984e3"]],
                cornerradius=6,
            ),
            hovertemplate="<b>%{y}</b><br>الإيراد: $%{x:,.2f}<extra></extra>",
        )])
        fig.update_layout(title="أفضل ١٠ منتجات", height=450, **theme)
        fig.update_yaxes(gridcolor="rgba(0,0,0,0.02)")
        fig.update_xaxes(gridcolor="rgba(0,0,0,0.04)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("أضف عمود اسم المنتج لعرض أفضل المنتجات")

with col_r2:
    region_df = pd.DataFrame(analytics["regional_performance"])
    if not region_df.empty:
        fig = go.Figure(data=[go.Bar(
            x=region_df["region"], y=region_df["revenue"],
            marker=dict(
                color=["#6c5ce7", "#0984e3", "#00b894", "#e17055", "#f39c12"][:len(region_df)],
                cornerradius=8,
            ),
            hovertemplate="<b>%{x}</b><br>الإيراد: $%{y:,.2f}<extra></extra>",
        )])
        fig.update_layout(title="الإيرادات حسب المنطقة", height=450, **theme)
        fig.update_yaxes(gridcolor="rgba(0,0,0,0.04)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("أضف عمود المنطقة/المدينة لعرض الأداء الجغرافي")


# ============================
# DATA EXPLORER
# ============================
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">مستكشف البيانات</div>', unsafe_allow_html=True)

with st.expander("عرض البيانات الخام", expanded=False):
    st.dataframe(df, use_container_width=True, height=400)
    st.caption(f"إجمالي الصفوف: {len(df)}")


# ============================
# TOP CUSTOMERS
# ============================
if analytics["top_customers"]:
    st.markdown('<div class="section-title">أفضل العملاء</div>', unsafe_allow_html=True)
    cust_df = pd.DataFrame(analytics["top_customers"])
    st.dataframe(cust_df, use_container_width=True, hide_index=True)


# ============================
# AI INSIGHTS
# ============================
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">توصيات الذكاء الاصطناعي</div>', unsafe_allow_html=True)

st.markdown("""
<div class="ai-panel">
    <div class="ai-badge">AI — تحليل مدعوم بالذكاء الاصطناعي</div>
    <p style="color: #636e72; margin: 0; font-size: 15px; line-height: 1.8;">
        اضغط الزر أدناه للحصول على تحليل ذكي لبياناتك يتضمن رؤى رئيسية، مشاكل مكتشفة، وخطة عمل لزيادة الإيرادات.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

if st.button("توليد تحليل الذكاء الاصطناعي", use_container_width=True, type="primary"):
    with st.spinner("جاري تحليل بياناتك وتوليد التوصيات..."):
        summary_text = generate_summary_text(analytics)
        result = generate_insights(analytics, summary_text)
        st.session_state["ai_insights"] = result

if "ai_insights" in st.session_state:
    result = st.session_state["ai_insights"]
    source_label = "Google Gemini AI" if result["source"] == "gemini" else "محرك التحليل المدمج"
    st.caption(f"مدعوم بـ: **{result['model_used']}** ({source_label})")
    st.markdown("---")
    st.markdown(result["insights_text"])
