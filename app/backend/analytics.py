"""
Analytics Engine — Pandas-based e-commerce data analysis.
Computes KPIs, trends, product performance, and customer insights.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def validate_csv(df: pd.DataFrame) -> dict:
    """Validate that the uploaded CSV has the required columns."""
    required_columns = [
        "order_id", "order_date", "customer_id", "product_name",
        "category", "quantity", "unit_price", "total_price"
    ]
    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        return {
            "valid": False,
            "message": f"Missing required columns: {', '.join(missing)}",
            "available_columns": list(df.columns)
        }

    return {"valid": True, "message": "CSV is valid", "row_count": len(df)}


def compute_analytics(df: pd.DataFrame) -> dict:
    """
    Run the full analytics pipeline on an e-commerce DataFrame.
    Returns a comprehensive dictionary of KPIs, trends, and breakdowns.
    """
    # --- Clean & prepare data ---
    df = df.copy()
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["total_price"] = pd.to_numeric(df["total_price"], errors="coerce").fillna(0)
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce").fillna(0)

    # Drop rows with invalid dates
    df = df.dropna(subset=["order_date"])

    # --- Core KPIs ---
    total_revenue = round(float(df["total_price"].sum()), 2)
    total_orders = int(df["order_id"].nunique())
    total_customers = int(df["customer_id"].nunique())
    total_products = int(df["product_name"].nunique())
    avg_order_value = round(total_revenue / total_orders, 2) if total_orders > 0 else 0
    avg_items_per_order = round(float(df.groupby("order_id")["quantity"].sum().mean()), 2)

    # Date range
    date_min = df["order_date"].min()
    date_max = df["order_date"].max()

    # --- Monthly Revenue Trend ---
    df["year_month"] = df["order_date"].dt.to_period("M").astype(str)
    monthly_revenue = (
        df.groupby("year_month")["total_price"]
        .sum()
        .round(2)
        .reset_index()
        .rename(columns={"year_month": "month", "total_price": "revenue"})
        .to_dict(orient="records")
    )

    # Monthly order count
    monthly_orders = (
        df.groupby("year_month")["order_id"]
        .nunique()
        .reset_index()
        .rename(columns={"year_month": "month", "order_id": "orders"})
        .to_dict(orient="records")
    )

    # --- Top Products by Revenue ---
    top_products = (
        df.groupby("product_name")
        .agg(revenue=("total_price", "sum"), units_sold=("quantity", "sum"))
        .round(2)
        .sort_values("revenue", ascending=False)
        .head(10)
        .reset_index()
        .to_dict(orient="records")
    )

    # --- Category Breakdown ---
    category_breakdown = (
        df.groupby("category")
        .agg(
            revenue=("total_price", "sum"),
            orders=("order_id", "nunique"),
            units_sold=("quantity", "sum")
        )
        .round(2)
        .sort_values("revenue", ascending=False)
        .reset_index()
        .to_dict(orient="records")
    )

    # --- Regional Performance ---
    regional_data = []
    if "region" in df.columns:
        regional_data = (
            df.groupby("region")
            .agg(
                revenue=("total_price", "sum"),
                orders=("order_id", "nunique"),
                customers=("customer_id", "nunique")
            )
            .round(2)
            .sort_values("revenue", ascending=False)
            .reset_index()
            .to_dict(orient="records")
        )

    # --- Customer Insights ---
    customer_stats = df.groupby("customer_id").agg(
        total_spent=("total_price", "sum"),
        order_count=("order_id", "nunique"),
        last_order=("order_date", "max"),
        first_order=("order_date", "min")
    )

    # Top customers
    top_customers = (
        customer_stats
        .sort_values("total_spent", ascending=False)
        .head(10)
        .round(2)
        .reset_index()
    )
    top_customers["last_order"] = top_customers["last_order"].dt.strftime("%Y-%m-%d")
    top_customers["first_order"] = top_customers["first_order"].dt.strftime("%Y-%m-%d")

    # Add customer names if available
    if "customer_name" in df.columns:
        name_map = df.drop_duplicates("customer_id").set_index("customer_id")["customer_name"]
        top_customers["customer_name"] = top_customers["customer_id"].map(name_map)

    top_customers = top_customers.to_dict(orient="records")

    # Churn approximation: customers inactive for >30 days from last date in dataset
    cutoff_date = date_max - timedelta(days=30)
    active_customers = int((customer_stats["last_order"] >= cutoff_date).sum())
    inactive_customers = total_customers - active_customers
    churn_rate = round((inactive_customers / total_customers) * 100, 1) if total_customers > 0 else 0

    # Repeat customer rate
    repeat_customers = int((customer_stats["order_count"] > 1).sum())
    repeat_rate = round((repeat_customers / total_customers) * 100, 1) if total_customers > 0 else 0

    # --- Revenue distribution ---
    revenue_per_order = df.groupby("order_id")["total_price"].sum()
    revenue_stats = {
        "min": round(float(revenue_per_order.min()), 2),
        "max": round(float(revenue_per_order.max()), 2),
        "median": round(float(revenue_per_order.median()), 2),
        "std": round(float(revenue_per_order.std()), 2),
    }

    # --- Build result ---
    return {
        "kpis": {
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "total_customers": total_customers,
            "total_products": total_products,
            "avg_order_value": avg_order_value,
            "avg_items_per_order": avg_items_per_order,
            "repeat_customer_rate": repeat_rate,
            "churn_rate": churn_rate,
            "active_customers": active_customers,
            "inactive_customers": inactive_customers,
        },
        "date_range": {
            "start": date_min.strftime("%Y-%m-%d"),
            "end": date_max.strftime("%Y-%m-%d"),
        },
        "monthly_revenue": monthly_revenue,
        "monthly_orders": monthly_orders,
        "top_products": top_products,
        "category_breakdown": category_breakdown,
        "regional_performance": regional_data,
        "top_customers": top_customers,
        "revenue_stats": revenue_stats,
    }


def generate_summary_text(analytics: dict) -> str:
    """
    Generate a plain-text summary of the analytics for AI consumption.
    """
    kpis = analytics["kpis"]
    dr = analytics["date_range"]

    lines = [
        f"E-Commerce Analytics Summary ({dr['start']} to {dr['end']})",
        f"",
        f"KEY METRICS:",
        f"- Total Revenue: ${kpis['total_revenue']:,.2f}",
        f"- Total Orders: {kpis['total_orders']}",
        f"- Total Customers: {kpis['total_customers']}",
        f"- Total Products: {kpis['total_products']}",
        f"- Average Order Value: ${kpis['avg_order_value']:,.2f}",
        f"- Avg Items Per Order: {kpis['avg_items_per_order']}",
        f"- Repeat Customer Rate: {kpis['repeat_customer_rate']}%",
        f"- Churn Rate (30-day): {kpis['churn_rate']}%",
        f"- Active Customers: {kpis['active_customers']}",
        f"- Inactive Customers: {kpis['inactive_customers']}",
        f"",
        f"MONTHLY REVENUE TREND:",
    ]

    for m in analytics["monthly_revenue"]:
        lines.append(f"  {m['month']}: ${m['revenue']:,.2f}")

    lines.append("")
    lines.append("TOP 10 PRODUCTS (by revenue):")
    for i, p in enumerate(analytics["top_products"], 1):
        lines.append(f"  {i}. {p['product_name']}: ${p['revenue']:,.2f} ({p['units_sold']} units)")

    lines.append("")
    lines.append("CATEGORY BREAKDOWN:")
    for c in analytics["category_breakdown"]:
        lines.append(f"  {c['category']}: ${c['revenue']:,.2f} ({c['orders']} orders)")

    if analytics["regional_performance"]:
        lines.append("")
        lines.append("REGIONAL PERFORMANCE:")
        for r in analytics["regional_performance"]:
            lines.append(f"  {r['region']}: ${r['revenue']:,.2f} ({r['orders']} orders, {r['customers']} customers)")

    return "\n".join(lines)
