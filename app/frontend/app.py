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
from app.backend.advanced import compute_advanced
from app.backend.reports import export_csv, export_excel, export_pdf

# --- Page Config ---
st.set_page_config(
    page_title="وكيل التحليلات — ذكاء التجارة الإلكترونية",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
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

    /* Hide sidebar completely (upload moved to page body) */
    [data-testid="stSidebar"] { display: none !important; }

    /* === NUCLEAR ICON FIX ===
       Material Symbols font fails on Render. The browser renders the icon
       name as raw text (e.g. "upload", "keyboard_ar"). We hide ALL of them
       using every possible selector variant. */
    [data-testid="stSidebar"] button[kind="headerNoPadding"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }

    /* Attribute wildcard — catches .material-symbols-rounded, .material-symbols-outlined, etc. */
    [class*="material-symbol"] {
        font-size: 0 !important;
        line-height: 0 !important;
        width: 0 !important;
        height: 0 !important;
        max-width: 0 !important;
        max-height: 0 !important;
        overflow: hidden !important;
        visibility: hidden !important;
        display: inline-block !important;
        padding: 0 !important;
        margin: 0 !important;
        border: none !important;
        opacity: 0 !important;
    }

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
    .soft-card {
        background: #ffffff;
        border-radius: 18px;
        border: 1px solid rgba(0,0,0,0.06);
        box-shadow: 0 6px 20px rgba(0,0,0,0.04);
        padding: 14px;
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

    /* Upload panel */
    .upload-panel {
        background: #ffffff;
        border-radius: 20px;
        padding: 22px;
        border: 1px solid rgba(108,92,231,0.12);
        box-shadow: 0 4px 24px rgba(108,92,231,0.06);
        margin-bottom: 16px;
    }

    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .block-container {
            padding-top: 0.5rem;
            padding-left: 0.6rem;
            padding-right: 0.6rem;
        }
        .hero {
            padding: 22px 16px !important;
            border-radius: 16px;
        }
        .hero h1 {
            font-size: 28px !important;
        }
        .hero p {
            font-size: 15px !important;
            line-height: 1.7 !important;
        }
        .section-title {
            font-size: 19px;
            margin: 24px 0 12px 0;
        }
        .kpi-card {
            border-radius: 16px;
            padding: 18px 14px;
        }
        .kpi-value {
            font-size: 24px;
        }
        .feature-card,
        .tips-box,
        .upload-panel,
        .ai-panel {
            border-radius: 16px;
            padding: 16px !important;
        }
        .stButton > button {
            min-height: 44px;
            font-size: 15px;
            border-radius: 12px;
        }

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
# --- Inject JS to remove broken Material Icon text nodes ---
st.markdown("""
<script>
(function() {
    function purgeIcons() {
        // Remove any element whose class includes 'material-symbol'
        document.querySelectorAll('[class*="material-symbol"]').forEach(function(el) {
            el.style.cssText = 'font-size:0!important;width:0!important;height:0!important;overflow:hidden!important;visibility:hidden!important;display:inline-block!important;';
        });
    }
    purgeIcons();
    // Re-run every time Streamlit re-renders the DOM
    var observer = new MutationObserver(function() { purgeIcons(); });
    observer.observe(document.documentElement, { childList: true, subtree: true });
})();
</script>
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


# --- Top Upload Area ---
st.markdown("""
<div class="hero" style="padding: 28px 32px; margin-bottom: 18px;">
    <h1 style="font-size:32px;">وكيل تحليلات التجارة الإلكترونية</h1>
    <p>ارفع ملف بيانات المبيعات (CSV أو Excel) واحصل على تحليلات شاملة وتوصيات ذكية بنفس الهوية البصرية الحالية.</p>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="upload-panel">', unsafe_allow_html=True)
uploaded_file = st.file_uploader(
    "📁 اسحب ملفك هنا أو اختر ملف",
    type=["csv", "xlsx", "xls"],
    help="يدعم ملفات CSV و Excel بأي تنسيق أعمدة",
)
use_sample = st.button("تحميل بيانات تجريبية", use_container_width=True, type="primary")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
<div class="tips-box">
    <h3>نصائح للحصول على أفضل نتائج</h3>
    <ul>
        <li>أضف عمود <b>التاريخ</b> لعرض الاتجاهات الشهرية</li>
        <li>أضف عمود <b>المنتج</b> لمعرفة الأ��ثر مبيعاً</li>
        <li>أضف عمود <b>السعر/المبلغ</b> لحساب الإيرادات</li>
        <li>أضف عمود <b>العميل</b> لتحليل الولاء</li>
        <li>أضف عمود <b>التصنيف</b> لتحليل الفئات</li>
        <li>أضف عمود <b>المنطقة</b> لتحليل المناطق</li>
    </ul>
</div>
""", unsafe_allow_html=True)
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
    st.info("ارفع ملف بيانات أو اضغط **تحميل بيانات تجريبية** للبدء")
    st.stop()


# --- Compute Analytics ---
analytics = compute_analytics(df)
kpis = analytics["kpis"]
col_map = analytics.get("column_mapping", {})

# --- Compute Advanced Analytics (forecast, recommendations, anomalies, churn, inventory) ---
@st.cache_data(show_spinner=False)
def _cached_advanced(_df, churn_rate):
    return compute_advanced(_df, churn_rate=churn_rate)

advanced = _cached_advanced(df, kpis.get("churn_rate", 0))

# Show detected columns
filename = st.session_state.get("filename", "ملف")
st.markdown(f"""
<div class="hero" style="padding: 24px 40px;">
    <h1>لوحة تحلي��ات المبيعات</h1>
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

show_raw = st.checkbox("عرض البيانات الخام", value=False)
if show_raw:
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
# ADVANCED INSIGHTS (NEW)
# ============================
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">تحليلات متقدمة</div>', unsafe_allow_html=True)

a1, a2 = st.columns(2)
with a1:
    src_df = pd.DataFrame(analytics.get("traffic_source_performance", []))
    if not src_df.empty:
        fig = go.Figure(data=[go.Bar(
            x=src_df["source"], y=src_df["revenue"],
            marker=dict(color="#6c5ce7", cornerradius=8),
            hovertemplate="<b>%{x}</b><br>الإيراد: $%{y:,.2f}<extra></extra>",
        )])
        fig.update_layout(title="الأداء حسب مصدر الزيارات", height=360, **theme)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown('<div class="soft-card">أضف عمود مصدر الزيارات (source/channel) لعرض أداء القنوات.</div>', unsafe_allow_html=True)

with a2:
    seg_df = pd.DataFrame(analytics.get("customer_segments", []))
    if not seg_df.empty:
        fig = go.Figure(data=[go.Pie(
            labels=seg_df["segment"], values=seg_df["customers"], hole=0.5,
            marker=dict(colors=["#00b894", "#0984e3", "#e17055"]),
            textinfo="label+percent",
        )])
        fig.update_layout(title="توزيع شرائح العملاء (RFM-lite)", height=360, showlegend=False, **theme)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown('<div class="soft-card">أضف بيانات العميل + التاريخ لعرض شرائح العملاء.</div>', unsafe_allow_html=True)

b1, b2, b3 = st.columns(3)
with b1:
    status_df = pd.DataFrame(analytics.get("order_status_breakdown", []))
    st.markdown("#### حالات الطلب")
    if not status_df.empty:
        st.dataframe(status_df, use_container_width=True, hide_index=True, height=220)
    else:
        st.markdown('<div class="soft-card">لا يوجد عمود حالة طلب.</div>', unsafe_allow_html=True)
with b2:
    pay_df = pd.DataFrame(analytics.get("payment_method_breakdown", []))
    st.markdown("#### طرق الدفع")
    if not pay_df.empty:
        st.dataframe(pay_df, use_container_width=True, hide_index=True, height=220)
    else:
        st.markdown('<div class="soft-card">لا يوجد عمود طريقة الدفع.</div>', unsafe_allow_html=True)
with b3:
    refund_df = pd.DataFrame(analytics.get("refund_reason_breakdown", []))
    st.markdown("#### أسباب الاسترجاع")
    if not refund_df.empty:
        st.dataframe(refund_df, use_container_width=True, hide_index=True, height=220)
    else:
        st.markdown('<div class="soft-card">لا يوجد عمود سبب الاسترجاع.</div>', unsafe_allow_html=True)

camp_df = pd.DataFrame(analytics.get("campaign_performance", []))
if not camp_df.empty:
    st.markdown("#### أداء الحملات التسويقية")
    st.dataframe(camp_df, use_container_width=True, hide_index=True)


# ============================
# SMART ALERTS
# ============================
anomalies = advanced.get("anomalies", {})
alerts = anomalies.get("alerts", [])
if alerts:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">التنبيهات الذكية</div>', unsafe_allow_html=True)
    alert_styles = {
        "critical": ("#e17055", "rgba(225,112,85,0.08)", "خطر"),
        "warning": ("#f39c12", "rgba(243,156,18,0.08)", "تحذير"),
        "ok": ("#00b894", "rgba(0,184,148,0.08)", "سليم"),
    }
    for al in alerts:
        color, bg, tag = alert_styles.get(al["level"], alert_styles["ok"])
        st.markdown(f"""
        <div style="background:{bg}; border-right:4px solid {color}; border-radius:12px;
                    padding:14px 18px; margin:8px 0;">
            <span style="background:{color}; color:#fff; font-size:11px; font-weight:700;
                         padding:2px 10px; border-radius:12px;">{tag}</span>
            <span style="font-weight:700; color:#2d3436; margin-right:8px;">{al['title']}</span>
            <div style="color:#636e72; font-size:14px; margin-top:6px;">{al['message']}</div>
        </div>
        """, unsafe_allow_html=True)


# ============================
# REVENUE FORECAST & SEASONALITY
# ============================
forecast = advanced.get("forecast", {})
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">توقع الإيرادات والموسمية</div>', unsafe_allow_html=True)

if forecast.get("available"):
    horizons = forecast.get("horizons", {})
    if forecast.get("granularity") == "daily":
        h1c, h2c, h3c = st.columns(3)
        with h1c:
            render_kpi("7", f"${horizons.get('7_day', 0):,.0f}", "توقع 7 أيام", "purple")
        with h2c:
            render_kpi("30", f"${horizons.get('30_day', 0):,.0f}", "توقع 30 يوماً", "blue")
        with h3c:
            render_kpi("90", f"${horizons.get('90_day', 0):,.0f}", "توقع 90 يوماً", "green")
    else:
        h1c, h2c = st.columns(2)
        with h1c:
            render_kpi("M", f"${horizons.get('next_month', 0):,.0f}", "توقع الشهر القادم", "purple")
        with h2c:
            render_kpi("Q", f"${horizons.get('next_3_months', 0):,.0f}", "توقع 3 أشهر", "blue")

    st.markdown("<br>", unsafe_allow_html=True)
    hist_df = pd.DataFrame(forecast.get("history", []))
    fc_df = pd.DataFrame(forecast.get("forecast", []))
    if not hist_df.empty and not fc_df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hist_df["date"], y=hist_df["revenue"], mode="lines",
            name="الإيراد الفعلي", line=dict(color="#0984e3", width=2.5),
            hovertemplate="<b>%{x}</b><br>فعلي: $%{y:,.2f}<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=fc_df["date"], y=fc_df["upper"], mode="lines",
            line=dict(width=0), showlegend=False, hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=fc_df["date"], y=fc_df["lower"], mode="lines", fill="tonexty",
            fillcolor="rgba(108,92,231,0.12)", line=dict(width=0),
            name="نطاق الثقة", hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=fc_df["date"], y=fc_df["predicted"], mode="lines",
            name="التوقع", line=dict(color="#6c5ce7", width=2.5, dash="dash"),
            hovertemplate="<b>%{x}</b><br>متوقع: $%{y:,.2f}<extra></extra>",
        ))
        fig.update_layout(title="الإيراد الفعلي مقابل المتوقع", height=420,
                          legend=dict(orientation="h", y=-0.18), **theme)
        fig.update_yaxes(gridcolor="rgba(0,0,0,0.04)")
        fig.update_xaxes(gridcolor="rgba(0,0,0,0.04)")
        st.plotly_chart(fig, use_container_width=True)

    season = forecast.get("seasonality", [])
    if season:
        col_s1, col_s2 = st.columns([2, 1])
        with col_s1:
            sdf = pd.DataFrame(season)
            fig = go.Figure(data=[go.Bar(
                x=sdf["weekday"], y=sdf["factor"],
                marker=dict(color="#00b894", cornerradius=8),
                hovertemplate="<b>%{x}</b><br>معامل: %{y:.2f}<extra></extra>",
            )])
            fig.add_hline(y=1.0, line_dash="dot", line_color="#636e72")
            fig.update_layout(title="الموسمية حسب يوم الأسبوع (1.0 = المتوسط)", height=320, **theme)
            st.plotly_chart(fig, use_container_width=True)
        with col_s2:
            st.markdown(f"""
            <div class="soft-card" style="margin-top:48px;">
                <div style="font-weight:700; color:#2d3436; margin-bottom:10px;">ملخص الاتجاه</div>
                <div style="color:#636e72; line-height:2;">
                    الاتجاه العام: <b style="color:#6c5ce7;">{forecast.get('trend_direction','')}</b><br>
                    أفضل يوم: <b>{forecast.get('best_day','')}</b><br>
                    أضعف يوم: <b>{forecast.get('worst_day','')}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.markdown(f'<div class="soft-card">{forecast.get("note", "التوقعات غير متاحة.")}</div>', unsafe_allow_html=True)


# ============================
# RECOMMENDATION ENGINE
# ============================
recommendations = advanced.get("recommendations", {})
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">محرك التوصيات — المنتجات المشتراة معاً</div>', unsafe_allow_html=True)

if recommendations.get("available"):
    st.caption(
        f"تم تحليل {recommendations.get('orders_analyzed', 0)} طلب — "
        f"{recommendations.get('multi_item_orders', 0)} طلب يحتوي أكثر من منتج."
    )
    pairs_df = pd.DataFrame(recommendations.get("pairs", []))
    if not pairs_df.empty:
        rename = {
            "product_a": "المنتج (أ)", "product_b": "المنتج (ب)", "count": "مرات التكرار",
            "support": "الدعم", "confidence": "الثقة", "lift": "معامل الرفع",
        }
        st.markdown("#### أقوى ارتباطات المنتجات")
        st.dataframe(pairs_df.rename(columns=rename), use_container_width=True, hide_index=True)

    by_prod = recommendations.get("by_product", [])
    if by_prod:
        st.markdown("#### توصيات البيع المتقاطع لكل منتج")
        cols = st.columns(2)
        for i, item in enumerate(by_prod[:6]):
            with cols[i % 2]:
                recs = " ".join(
                    f'<span class="col-map-item">{r["product"]} ({r["count"]})</span>'
                    for r in item["recommendations"]
                )
                st.markdown(f"""
                <div class="soft-card" style="margin-bottom:10px;">
                    <div style="font-weight:700; color:#2d3436;">عند شراء: {item['product']}</div>
                    <div style="color:#636e72; font-size:13px; margin:6px 0;">اقترح أيضاً:</div>
                    {recs}
                </div>
                """, unsafe_allow_html=True)
else:
    st.markdown(f'<div class="soft-card">{recommendations.get("note", "التوصيات غير متاحة.")}</div>', unsafe_allow_html=True)


# ============================
# CHURN PREDICTION & RETENTION
# ============================
churn = advanced.get("churn_prediction", {})
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">التنبؤ بفقدان العملاء والاحتفاظ بهم</div>', unsafe_allow_html=True)

if churn.get("available"):
    summary = churn.get("summary", {})
    k1, k2, k3 = st.columns(3)
    with k1:
        render_kpi("!", f"{summary.get('high_risk', 0)}", "عملاء بخطورة مرتفعة", "pink",
                   f"{summary.get('high_risk_pct', 0)}%", "warn")
    with k2:
        render_kpi("$", f"${summary.get('revenue_at_risk', 0):,.0f}", "إيرادات معرضة للخطر", "orange")
    with k3:
        render_kpi("U", f"{summary.get('total_customers', 0)}", "إجمالي العملاء المحللين", "blue")

    st.markdown("<br>", unsafe_allow_html=True)
    col_c1, col_c2 = st.columns([1, 2])
    with col_c1:
        dist_df = pd.DataFrame(churn.get("distribution", []))
        if not dist_df.empty:
            fig = go.Figure(data=[go.Pie(
                labels=dist_df["tier"], values=dist_df["customers"], hole=0.55,
                marker=dict(colors=["#e17055", "#f39c12", "#00b894"]),
                textinfo="label+percent",
            )])
            fig.update_layout(title="توزيع مستوى الخطورة", height=320, showlegend=False, **theme)
            st.plotly_chart(fig, use_container_width=True)
    with col_c2:
        at_risk_df = pd.DataFrame(churn.get("at_risk_customers", []))
        if not at_risk_df.empty:
            rename = {
                "customer": "العميل", "recency_days": "أيام منذ آخر طلب",
                "avg_gap_days": "متوسط الفجوة", "orders": "الطلبات",
                "total_spent": "إجمالي الإنفاق", "risk_score": "درجة الخطورة",
                "risk_tier": "المستوى",
            }
            st.markdown("#### العملاء الأكثر عرضة للفقدان")
            st.dataframe(at_risk_df.rename(columns=rename), use_container_width=True,
                         hide_index=True, height=320)

    tips = churn.get("retention_tips", [])
    if tips:
        tips_html = "".join(f"<li>{t}</li>" for t in tips)
        st.markdown(f"""
        <div class="tips-box">
            <h3>توصيات الاحتفاظ بالعملاء</h3>
            <ul>{tips_html}</ul>
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown(f'<div class="soft-card">{churn.get("note", "غير متاح.")}</div>', unsafe_allow_html=True)


# ============================
# INVENTORY & DEMAND SIGNALS
# ============================
inventory = advanced.get("inventory", {})
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">المخزون وإشارات الطلب</div>', unsafe_allow_html=True)

if inventory.get("available"):
    if inventory.get("note"):
        st.caption(inventory["note"])
    col_i1, col_i2 = st.columns(2)
    with col_i1:
        vel_df = pd.DataFrame(inventory.get("velocity", []))
        if not vel_df.empty:
            vdf = vel_df.sort_values("velocity", ascending=True)
            fig = go.Figure(data=[go.Bar(
                x=vdf["velocity"], y=vdf["product"], orientation="h",
                marker=dict(color="#0984e3", cornerradius=6),
                hovertemplate="<b>%{y}</b><br>سرعة البيع: %{x} وحدة/يوم<extra></extra>",
            )])
            fig.update_layout(title="أسرع المنتجات مبيعاً (وحدة/يوم)", height=420, **theme)
            st.plotly_chart(fig, use_container_width=True)
    with col_i2:
        slow_df = pd.DataFrame(inventory.get("slow_movers", []))
        if not slow_df.empty:
            st.markdown("#### المنتجات بطيئة الحركة")
            keep = [c for c in ["product", "units", "velocity", "momentum_pct"] if c in slow_df.columns]
            rename = {"product": "المنتج", "units": "الوحدات", "velocity": "السرعة", "momentum_pct": "الزخم %"}
            st.dataframe(slow_df[keep].rename(columns=rename), use_container_width=True,
                         hide_index=True, height=380)

    risk_df = pd.DataFrame(inventory.get("stock_risk", []))
    if not risk_df.empty:
        title = "مخاطر نفاد المخزون" if inventory.get("has_stock_data") else "أولويات إعادة التخزين (تقديرية)"
        st.markdown(f"#### {title}")
        st.dataframe(risk_df, use_container_width=True, hide_index=True)
else:
    st.markdown(f'<div class="soft-card">{inventory.get("note", "غير متاح.")}</div>', unsafe_allow_html=True)


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
    st.markdown(
        f'<div style="direction: rtl; text-align: right; line-height: 2.2; font-size: 16px;">'
        f'{result["insights_text"]}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ============================
# REPORTS & EXPORT
# ============================
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">التقارير والتصدير</div>', unsafe_allow_html=True)

st.markdown("""
<div class="soft-card" style="margin-bottom:14px;">
    حمّل تقريراً شاملاً يتضمن مؤشرات الأداء، التوقعات، التوصيات، تحليل الفقدان والمخزون
    بثلاث صيغ: CSV للملخص، Excel متعدد الأوراق، وPDF منسّق بالعربية.
</div>
""", unsafe_allow_html=True)

ai_text_for_pdf = st.session_state.get("ai_insights", {}).get("insights_text")
base_name = os.path.splitext(st.session_state.get("filename", "report"))[0]

e1, e2, e3 = st.columns(3)
with e1:
    st.download_button(
        "تحميل CSV (ملخص المؤشرات)",
        data=export_csv(analytics),
        file_name=f"{base_name}_kpis.csv",
        mime="text/csv",
        use_container_width=True,
    )
with e2:
    st.download_button(
        "تحميل Excel (تقرير كامل)",
        data=export_excel(analytics, advanced),
        file_name=f"{base_name}_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
with e3:
    @st.cache_data(show_spinner=False)
    def _build_pdf(_analytics, _advanced, _ai):
        return export_pdf(_analytics, _advanced, _ai)

    st.download_button(
        "تحميل PDF (تقرير عربي)",
        data=_build_pdf(analytics, advanced, ai_text_for_pdf),
        file_name=f"{base_name}_report.pdf",
        mime="application/pdf",
        use_container_width=True,
        type="primary",
    )
st.caption("PDF يتضمن توصيات الذكاء الاصطناعي إذا تم توليدها أعلاه.")
