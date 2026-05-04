"""
Streamlit Dashboard — E-commerce Analytics Agent.
Premium UI with KPI cards, interactive charts, and AI insights panel.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import io
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.backend.analytics import validate_csv, compute_analytics, generate_summary_text
from app.backend.ai import generate_insights

# --- Page Config ---
st.set_page_config(
    page_title="Analytics Agent — E-commerce Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Premium Custom CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* Global Styles */
    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Main container */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 1400px;
    }

    /* KPI Card Styles */
    .kpi-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #6c5ce7, #a29bfe, #fd79a8);
    }
    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(108, 92, 231, 0.2);
    }
    .kpi-icon {
        font-size: 28px;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 32px;
        font-weight: 800;
        color: #ffffff;
        margin: 4px 0;
        letter-spacing: -0.5px;
    }
    .kpi-label {
        font-size: 13px;
        color: #a0aec0;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        font-weight: 500;
    }
    .kpi-delta {
        font-size: 13px;
        font-weight: 600;
        margin-top: 6px;
        padding: 3px 10px;
        border-radius: 20px;
        display: inline-block;
    }
    .kpi-delta-positive {
        color: #00e676;
        background: rgba(0, 230, 118, 0.1);
    }
    .kpi-delta-negative {
        color: #ff5252;
        background: rgba(255, 82, 82, 0.1);
    }

    /* Section Headers */
    .section-header {
        font-size: 22px;
        font-weight: 700;
        color: #e2e8f0;
        margin: 32px 0 16px 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .section-header::after {
        content: '';
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, rgba(108, 92, 231, 0.5), transparent);
    }

    /* AI Insights Panel */
    .ai-panel {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #1a1a2e 100%);
        border-radius: 16px;
        padding: 28px;
        border: 1px solid rgba(108, 92, 231, 0.3);
        box-shadow: 0 8px 32px rgba(108, 92, 231, 0.1);
        position: relative;
        overflow: hidden;
    }
    .ai-panel::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #6c5ce7, #00b894, #fd79a8);
    }
    .ai-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: linear-gradient(135deg, #6c5ce7, #a29bfe);
        color: white;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 16px;
    }

    /* Hero Header */
    .hero {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #1a1a2e 100%);
        border-radius: 20px;
        padding: 40px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.06);
        margin-bottom: 32px;
        position: relative;
        overflow: hidden;
    }
    .hero::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(108, 92, 231, 0.08) 0%, transparent 50%);
        animation: pulse 4s ease-in-out infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 0.5; }
        50% { opacity: 1; }
    }
    .hero h1 {
        font-size: 36px;
        font-weight: 800;
        background: linear-gradient(135deg, #a29bfe, #6c5ce7, #fd79a8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
        position: relative;
    }
    .hero p {
        color: #a0aec0;
        font-size: 16px;
        position: relative;
    }

    /* Chart containers */
    .chart-container {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 16px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.06);
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #e2e8f0;
    }

    /* Divider */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(108, 92, 231, 0.3), transparent);
        margin: 24px 0;
    }

    /* Data table */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)


# --- Helper Functions ---
def render_kpi_card(icon: str, value: str, label: str, delta: str = None, delta_type: str = "positive"):
    """Render a premium KPI card."""
    delta_html = ""
    if delta:
        delta_class = f"kpi-delta-{delta_type}"
        delta_html = f'<div class="kpi-delta {delta_class}">{delta}</div>'

    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def create_chart_theme():
    """Common Plotly chart theme for consistent premium look."""
    return dict(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#a0aec0"),
        margin=dict(l=20, r=20, t=40, b=20),
    )


# --- Sidebar ---
with st.sidebar:
    st.markdown("## 📊 Analytics Agent")
    st.markdown("---")
    st.markdown("### Upload Your Data")

    uploaded_file = st.file_uploader(
        "Drop your CSV file here",
        type=["csv"],
        help="Upload an e-commerce CSV with columns: order_id, order_date, customer_id, product_name, category, quantity, unit_price, total_price",
    )

    st.markdown("---")

    # Sample data button
    use_sample = st.button("📁 Load Sample Data", use_container_width=True, type="primary")

    st.markdown("---")
    st.markdown("### About")
    st.markdown(
        "AI-powered e-commerce analytics platform. "
        "Upload your sales data and get instant insights, "
        "trend analysis, and growth recommendations."
    )
    st.markdown("---")
    st.markdown(
        "<div style='text-align:center; color:#4a5568; font-size:12px;'>"
        "Built with ❤️ using Streamlit + FastAPI + Supabase"
        "</div>",
        unsafe_allow_html=True,
    )


# --- Load Data ---
df = None

if use_sample:
    sample_path = Path(__file__).resolve().parent.parent.parent / "data_sample.csv"
    if sample_path.exists():
        df = pd.read_csv(sample_path)
        st.session_state["data"] = df
        st.session_state["filename"] = "data_sample.csv"
    else:
        st.error("Sample file not found.")

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.session_state["data"] = df
        st.session_state["filename"] = uploaded_file.name
    except Exception as e:
        st.error(f"Error reading file: {e}")

if df is None and "data" in st.session_state:
    df = st.session_state["data"]


# --- Main Content ---
if df is None:
    # Landing / Hero
    st.markdown("""
    <div class="hero">
        <h1>📊 E-commerce Analytics Agent</h1>
        <p>Upload your sales CSV data to unlock powerful analytics and AI-driven business insights</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="kpi-card" style="text-align:left; padding:28px;">
            <div style="font-size:32px; margin-bottom:12px;">📤</div>
            <div style="font-size:18px; font-weight:700; color:#fff; margin-bottom:8px;">1. Upload Data</div>
            <div style="color:#a0aec0; font-size:14px;">Upload your e-commerce CSV file with order, product, and customer data.</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="kpi-card" style="text-align:left; padding:28px;">
            <div style="font-size:32px; margin-bottom:12px;">📈</div>
            <div style="font-size:18px; font-weight:700; color:#fff; margin-bottom:8px;">2. View Analytics</div>
            <div style="color:#a0aec0; font-size:14px;">Get instant KPIs, revenue trends, product performance, and customer insights.</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="kpi-card" style="text-align:left; padding:28px;">
            <div style="font-size:32px; margin-bottom:12px;">🤖</div>
            <div style="font-size:18px; font-weight:700; color:#fff; margin-bottom:8px;">3. AI Insights</div>
            <div style="color:#a0aec0; font-size:14px;">Receive AI-powered recommendations to grow revenue and fix problems.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.info("👈 Upload a CSV file or click **Load Sample Data** in the sidebar to get started.")
    st.stop()


# --- Validate & Compute ---
validation = validate_csv(df)
if not validation["valid"]:
    st.error(f"❌ {validation['message']}")
    st.write("Available columns:", validation.get("available_columns", []))
    st.stop()

# Cache analytics computation
@st.cache_data
def get_analytics(data_hash):
    return compute_analytics(df)

data_hash = pd.util.hash_pandas_object(df).sum()
analytics = get_analytics(data_hash)
kpis = analytics["kpis"]

# --- Header ---
filename = st.session_state.get("filename", "data")
st.markdown(f"""
<div class="hero" style="padding: 24px 40px;">
    <h1>📊 E-commerce Analytics Agent</h1>
    <p>Analyzing <strong>{filename}</strong> — {kpis['total_orders']} orders • {analytics['date_range']['start']} to {analytics['date_range']['end']}</p>
</div>
""", unsafe_allow_html=True)


# ============================
# KPI CARDS
# ============================
st.markdown('<div class="section-header">📋 Key Performance Indicators</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1:
    render_kpi_card("💰", f"${kpis['total_revenue']:,.2f}", "Total Revenue")
with c2:
    render_kpi_card("📦", f"{kpis['total_orders']:,}", "Total Orders")
with c3:
    render_kpi_card("👥", f"{kpis['total_customers']:,}", "Total Customers")
with c4:
    render_kpi_card("🛒", f"${kpis['avg_order_value']:,.2f}", "Avg Order Value")

st.markdown("<br>", unsafe_allow_html=True)

c5, c6, c7, c8 = st.columns(4)
with c5:
    render_kpi_card("🏷️", f"{kpis['total_products']}", "Unique Products")
with c6:
    render_kpi_card("📊", f"{kpis['avg_items_per_order']}", "Items / Order")
with c7:
    delta_type = "positive" if kpis['repeat_customer_rate'] > 30 else "negative"
    render_kpi_card("🔄", f"{kpis['repeat_customer_rate']}%", "Repeat Rate",
                    "Healthy" if delta_type == "positive" else "Needs Work", delta_type)
with c8:
    delta_type = "negative" if kpis['churn_rate'] > 40 else "positive"
    render_kpi_card("📉", f"{kpis['churn_rate']}%", "Churn Rate (30d)",
                    "High Risk" if delta_type == "negative" else "Stable", delta_type)


# ============================
# CHARTS
# ============================
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-header">📈 Revenue Analytics</div>', unsafe_allow_html=True)

chart_theme = create_chart_theme()

# Row 1: Revenue Trend + Category Breakdown
col_left, col_right = st.columns([2, 1])

with col_left:
    # Monthly Revenue Area Chart
    monthly_df = pd.DataFrame(analytics["monthly_revenue"])
    if not monthly_df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=monthly_df["month"],
            y=monthly_df["revenue"],
            mode="lines+markers",
            fill="tozeroy",
            line=dict(color="#6c5ce7", width=3),
            fillcolor="rgba(108, 92, 231, 0.15)",
            marker=dict(size=8, color="#a29bfe", line=dict(width=2, color="#6c5ce7")),
            hovertemplate="<b>%{x}</b><br>Revenue: $%{y:,.2f}<extra></extra>",
        ))
        fig.update_layout(
            title="Monthly Revenue Trend",
            xaxis_title="Month",
            yaxis_title="Revenue ($)",
            height=400,
            **chart_theme,
        )
        fig.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
        fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
        st.plotly_chart(fig, use_container_width=True)

with col_right:
    # Category Donut Chart
    cat_df = pd.DataFrame(analytics["category_breakdown"])
    if not cat_df.empty:
        colors = ["#6c5ce7", "#a29bfe", "#fd79a8", "#00b894", "#fdcb6e", "#e17055"]
        fig = go.Figure(data=[go.Pie(
            labels=cat_df["category"],
            values=cat_df["revenue"],
            hole=0.55,
            marker=dict(colors=colors[:len(cat_df)]),
            textinfo="label+percent",
            textfont=dict(size=12, color="#e2e8f0"),
            hovertemplate="<b>%{label}</b><br>Revenue: $%{value:,.2f}<br>Share: %{percent}<extra></extra>",
        )])
        fig.update_layout(
            title="Revenue by Category",
            height=400,
            showlegend=False,
            **chart_theme,
        )
        st.plotly_chart(fig, use_container_width=True)


# Row 2: Top Products + Regional Performance
st.markdown('<div class="section-header">🏆 Product & Regional Performance</div>', unsafe_allow_html=True)

col_left2, col_right2 = st.columns(2)

with col_left2:
    # Top Products Horizontal Bar
    prod_df = pd.DataFrame(analytics["top_products"])
    if not prod_df.empty:
        prod_df = prod_df.sort_values("revenue", ascending=True)
        fig = go.Figure(data=[go.Bar(
            x=prod_df["revenue"],
            y=prod_df["product_name"],
            orientation="h",
            marker=dict(
                color=prod_df["revenue"],
                colorscale=[[0, "#a29bfe"], [0.5, "#6c5ce7"], [1, "#fd79a8"]],
                cornerradius=6,
            ),
            hovertemplate="<b>%{y}</b><br>Revenue: $%{x:,.2f}<extra></extra>",
        )])
        fig.update_layout(
            title="Top 10 Products by Revenue",
            xaxis_title="Revenue ($)",
            height=450,
            **chart_theme,
        )
        fig.update_yaxes(gridcolor="rgba(255,255,255,0.03)")
        fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
        st.plotly_chart(fig, use_container_width=True)

with col_right2:
    # Regional Performance
    region_df = pd.DataFrame(analytics["regional_performance"])
    if not region_df.empty:
        fig = go.Figure(data=[go.Bar(
            x=region_df["region"],
            y=region_df["revenue"],
            marker=dict(
                color=["#6c5ce7", "#a29bfe", "#00b894", "#fd79a8", "#fdcb6e"][:len(region_df)],
                cornerradius=8,
            ),
            hovertemplate="<b>%{x}</b><br>Revenue: $%{y:,.2f}<extra></extra>",
        )])
        fig.update_layout(
            title="Revenue by Region",
            yaxis_title="Revenue ($)",
            height=450,
            **chart_theme,
        )
        fig.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No regional data available in the CSV.")


# ============================
# DATA EXPLORER
# ============================
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-header">🔍 Data Explorer</div>', unsafe_allow_html=True)

with st.expander("View Raw Data", expanded=False):
    # Filters
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        if "category" in df.columns:
            categories = ["All"] + sorted(df["category"].unique().tolist())
            selected_cat = st.selectbox("Filter by Category", categories)
    with filter_col2:
        if "region" in df.columns:
            regions = ["All"] + sorted(df["region"].unique().tolist())
            selected_region = st.selectbox("Filter by Region", regions)

    display_df = df.copy()
    if "category" in df.columns and selected_cat != "All":
        display_df = display_df[display_df["category"] == selected_cat]
    if "region" in df.columns and selected_region != "All":
        display_df = display_df[display_df["region"] == selected_region]

    st.dataframe(display_df, use_container_width=True, height=400)
    st.caption(f"Showing {len(display_df)} of {len(df)} rows")


# ============================
# TOP CUSTOMERS
# ============================
st.markdown('<div class="section-header">👑 Top Customers</div>', unsafe_allow_html=True)

cust_df = pd.DataFrame(analytics["top_customers"])
if not cust_df.empty:
    display_cols = [c for c in ["customer_name", "customer_id", "total_spent", "order_count", "first_order", "last_order"] if c in cust_df.columns]
    st.dataframe(
        cust_df[display_cols].style.format({"total_spent": "${:,.2f}"}) if "total_spent" in display_cols else cust_df,
        use_container_width=True,
        hide_index=True,
    )


# ============================
# AI INSIGHTS
# ============================
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-header">🤖 AI Business Insights</div>', unsafe_allow_html=True)

st.markdown("""
<div class="ai-panel">
    <div class="ai-badge">🤖 AI-Powered Analysis</div>
    <p style="color: #a0aec0; margin: 0;">
        Click the button below to generate AI-powered insights, problem detection, and growth recommendations for your business.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

if st.button("🚀 Generate AI Insights", use_container_width=True, type="primary"):
    with st.spinner("🤖 Analyzing your data and generating insights..."):
        summary_text = generate_summary_text(analytics)
        result = generate_insights(analytics, summary_text)

        st.session_state["ai_insights"] = result

if "ai_insights" in st.session_state:
    result = st.session_state["ai_insights"]

    # Show source badge
    source_label = "🤖 Google Gemini AI" if result["source"] == "gemini" else "📊 Built-in Engine"
    st.caption(f"Powered by: **{result['model_used']}** ({source_label})")

    st.markdown(f"""
    <div class="ai-panel">
        {result['insights_text']}
    </div>
    """, unsafe_allow_html=True)

    # Also render with proper markdown
    st.markdown("---")
    st.markdown(result["insights_text"])
