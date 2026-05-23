"""
Analytics Engine — Smart column detection + Pandas-based analysis.
Accepts any CSV/Excel format and auto-detects relevant columns.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re


# --- Smart Column Detection ---
COLUMN_PATTERNS = {
    "date": [
        r"date", r"تاريخ", r"order.?date", r"purchase.?date", r"created",
        r"timestamp", r"time", r"day", r"يوم",
    ],
    "order_id": [
        r"order.?id", r"order.?no", r"order.?num", r"invoice", r"رقم.?الطلب",
        r"transaction.?id", r"receipt", r"فاتورة",
    ],
    "customer_id": [
        r"customer.?id", r"client.?id", r"buyer.?id", r"user.?id",
        r"رقم.?العميل", r"رقم.?الزبون", r"معرف.?العميل",
    ],
    "customer_name": [
        r"customer.?name", r"client.?name", r"buyer.?name", r"اسم.?العميل",
        r"اسم.?الزبون", r"full.?name", r"الاسم", r"العميل", r"العملاء",
        r"customer", r"client", r"buyer",
    ],
    "product": [
        r"product", r"item", r"المنتج", r"اسم.?المنتج", r"السلعة",
        r"goods", r"sku.?name", r"description", r"الوصف",
    ],
    "category": [
        r"category", r"cat", r"التصنيف", r"الفئة", r"النوع", r"type",
        r"group", r"المجموعة", r"department", r"القسم",
    ],
    "quantity": [
        r"qty", r"quantity", r"الكمية", r"عدد", r"count", r"units",
        r"الوحدات", r"amount",
    ],
    "unit_price": [
        r"unit.?price", r"price", r"سعر.?الوحدة", r"السعر", r"cost",
        r"rate", r"سعر",
    ],
    "total_price": [
        r"total", r"الإجمالي", r"المبلغ", r"revenue", r"الإيراد",
        r"subtotal", r"sum", r"المجموع", r"net", r"صافي", r"value",
        r"القيمة", r"amount",
    ],
    "region": [
        r"region", r"المنطقة", r"city", r"المدينة", r"country", r"الدولة",
        r"state", r"الولاية", r"location", r"الموقع", r"area", r"zone",
    ],
}


def _match_column(col_name: str, patterns: list) -> bool:
    """Check if a column name matches any pattern."""
    col_lower = col_name.lower().strip()
    for pattern in patterns:
        if re.search(pattern, col_lower, re.IGNORECASE):
            return True
    return False


def detect_columns(df: pd.DataFrame) -> dict:
    """
    Auto-detect column roles from any DataFrame.
    Returns a mapping: role -> column_name (or None if not found).
    """
    mapping = {}
    used_cols = set()

    # Priority order matters — total_price before unit_price, etc.
    detection_order = [
        "date", "order_id", "customer_id", "customer_name",
        "product", "category", "quantity", "total_price",
        "unit_price", "region",
    ]

    for role in detection_order:
        patterns = COLUMN_PATTERNS[role]
        best_match = None

        for col in df.columns:
            if col in used_cols:
                continue
            if _match_column(col, patterns):
                best_match = col
                break

        if best_match:
            mapping[role] = best_match
            used_cols.add(best_match)
        else:
            mapping[role] = None

    # Fallback: if no total_price but we have unit_price + quantity, we can compute it
    if mapping["total_price"] is None and mapping["unit_price"] and mapping["quantity"]:
        mapping["_compute_total"] = True

    # Fallback: try to detect date column by parsing
    if mapping["date"] is None:
        for col in df.columns:
            if col in used_cols:
                continue
            try:
                parsed = pd.to_datetime(df[col], errors="coerce")
                if parsed.notna().sum() > len(df) * 0.5:
                    mapping["date"] = col
                    used_cols.add(col)
                    break
            except Exception:
                continue

    # Fallback: detect numeric columns for price if still missing
    if mapping["total_price"] is None and mapping["unit_price"] is None:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col in used_cols:
                continue
            # Pick the first numeric column with reasonable values as total_price
            if df[col].mean() > 0:
                mapping["total_price"] = col
                used_cols.add(col)
                break

    return mapping


def read_file(file_content: bytes, filename: str) -> pd.DataFrame:
    """Read CSV or Excel file into a DataFrame."""
    import io

    fname_lower = filename.lower()

    if fname_lower.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(file_content), engine="openpyxl")
    elif fname_lower.endswith(".csv"):
        # Try different encodings
        for encoding in ["utf-8", "utf-8-sig", "cp1256", "latin-1"]:
            try:
                return pd.read_csv(io.BytesIO(file_content), encoding=encoding)
            except (UnicodeDecodeError, Exception):
                continue
        return pd.read_csv(io.BytesIO(file_content), encoding="utf-8", errors="replace")
    else:
        # Try CSV first, then Excel
        try:
            return pd.read_csv(io.BytesIO(file_content))
        except Exception:
            return pd.read_excel(io.BytesIO(file_content), engine="openpyxl")


def compute_analytics(df: pd.DataFrame) -> dict:
    """
    Run analytics on any e-commerce DataFrame.
    Auto-detects columns and computes everything possible.
    """
    df = df.copy()
    col_map = detect_columns(df)

    # --- Prepare columns ---
    date_col = col_map.get("date")
    order_col = col_map.get("order_id")
    customer_col = col_map.get("customer_id") or col_map.get("customer_name")
    customer_name_col = col_map.get("customer_name")
    product_col = col_map.get("product")
    category_col = col_map.get("category")
    quantity_col = col_map.get("quantity")
    total_col = col_map.get("total_price")
    unit_price_col = col_map.get("unit_price")
    region_col = col_map.get("region")

    # Compute total if needed
    if total_col is None and col_map.get("_compute_total"):
        df["_total"] = pd.to_numeric(df[unit_price_col], errors="coerce") * pd.to_numeric(df[quantity_col], errors="coerce")
        total_col = "_total"

    # Parse date
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col])

    # Parse numeric columns
    if total_col:
        df[total_col] = pd.to_numeric(df[total_col], errors="coerce").fillna(0)
    if quantity_col:
        df[quantity_col] = pd.to_numeric(df[quantity_col], errors="coerce").fillna(0)

    # --- Core KPIs ---
    total_revenue = round(float(df[total_col].sum()), 2) if total_col else 0

    if order_col:
        total_orders = int(df[order_col].nunique())
    else:
        total_orders = len(df)

    total_customers = int(df[customer_col].nunique()) if customer_col else 0
    total_products = int(df[product_col].nunique()) if product_col else 0
    avg_order_value = round(total_revenue / total_orders, 2) if total_orders > 0 else 0

    avg_items_per_order = 0
    if quantity_col and order_col:
        avg_items_per_order = round(float(df.groupby(order_col)[quantity_col].sum().mean()), 2)

    # Date range
    date_range = {"start": "N/A", "end": "N/A"}
    if date_col:
        date_range["start"] = df[date_col].min().strftime("%Y-%m-%d")
        date_range["end"] = df[date_col].max().strftime("%Y-%m-%d")

    # --- Monthly Revenue ---
    monthly_revenue = []
    monthly_orders = []
    if date_col and total_col:
        df["_ym"] = df[date_col].dt.to_period("M").astype(str)
        monthly_revenue = (
            df.groupby("_ym")[total_col].sum().round(2)
            .reset_index().rename(columns={"_ym": "month", total_col: "revenue"})
            .to_dict(orient="records")
        )
        if order_col:
            monthly_orders = (
                df.groupby("_ym")[order_col].nunique()
                .reset_index().rename(columns={"_ym": "month", order_col: "orders"})
                .to_dict(orient="records")
            )

    # --- Top Products ---
    top_products = []
    if product_col and total_col:
        agg = {"revenue": (total_col, "sum")}
        if quantity_col:
            agg["units_sold"] = (quantity_col, "sum")
        top_products = (
            df.groupby(product_col).agg(**agg).round(2)
            .sort_values("revenue", ascending=False).head(10)
            .reset_index().rename(columns={product_col: "product_name"})
            .to_dict(orient="records")
        )

    # --- Category Breakdown ---
    category_breakdown = []
    if category_col and total_col:
        agg = {"revenue": (total_col, "sum")}
        if order_col:
            agg["orders"] = (order_col, "nunique")
        category_breakdown = (
            df.groupby(category_col).agg(**agg).round(2)
            .sort_values("revenue", ascending=False)
            .reset_index().rename(columns={category_col: "category"})
            .to_dict(orient="records")
        )

    # --- Regional Performance ---
    regional_data = []
    if region_col and total_col:
        agg = {"revenue": (total_col, "sum")}
        if order_col:
            agg["orders"] = (order_col, "nunique")
        if customer_col:
            agg["customers"] = (customer_col, "nunique")
        regional_data = (
            df.groupby(region_col).agg(**agg).round(2)
            .sort_values("revenue", ascending=False)
            .reset_index().rename(columns={region_col: "region"})
            .to_dict(orient="records")
        )

    # --- Customer Insights ---
    top_customers = []
    churn_rate = 0
    repeat_rate = 0
    active_customers = 0
    inactive_customers = 0

    if customer_col and total_col:
        cust_agg = {
            "total_spent": (total_col, "sum"),
        }
        if order_col:
            cust_agg["order_count"] = (order_col, "nunique")
        if date_col:
            cust_agg["last_order"] = (date_col, "max")
            cust_agg["first_order"] = (date_col, "min")

        customer_stats = df.groupby(customer_col).agg(**cust_agg).round(2)

        top_cust = customer_stats.sort_values("total_spent", ascending=False).head(10).reset_index()

        if date_col and "last_order" in top_cust.columns:
            top_cust["last_order"] = top_cust["last_order"].dt.strftime("%Y-%m-%d")
            top_cust["first_order"] = top_cust["first_order"].dt.strftime("%Y-%m-%d")

        if customer_name_col and customer_name_col != customer_col:
            name_map = df.drop_duplicates(customer_col).set_index(customer_col)[customer_name_col]
            top_cust["customer_name"] = top_cust[customer_col].map(name_map)

        top_cust = top_cust.rename(columns={customer_col: "customer_id"})
        top_customers = top_cust.to_dict(orient="records")

        # Churn
        if date_col and "last_order" in customer_stats.columns:
            date_max = df[date_col].max()
            cutoff = date_max - timedelta(days=30)
            active_customers = int((customer_stats["last_order"] >= cutoff).sum())
            inactive_customers = total_customers - active_customers
            churn_rate = round((inactive_customers / total_customers) * 100, 1) if total_customers > 0 else 0

        # Repeat rate
        if "order_count" in customer_stats.columns:
            repeat_customers = int((customer_stats["order_count"] > 1).sum())
            repeat_rate = round((repeat_customers / total_customers) * 100, 1) if total_customers > 0 else 0

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
        "date_range": date_range,
        "monthly_revenue": monthly_revenue,
        "monthly_orders": monthly_orders,
        "top_products": top_products,
        "category_breakdown": category_breakdown,
        "regional_performance": regional_data,
        "top_customers": top_customers,
        "column_mapping": {k: v for k, v in col_map.items() if v is not None and k != "_compute_total"},
    }


def generate_summary_text(analytics: dict) -> str:
    """Generate a plain-text summary for AI consumption."""
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
    ]

    if analytics["monthly_revenue"]:
        lines.append("\nMONTHLY REVENUE:")
        for m in analytics["monthly_revenue"]:
            lines.append(f"  {m['month']}: ${m['revenue']:,.2f}")

    if analytics["top_products"]:
        lines.append("\nTOP PRODUCTS:")
        for i, p in enumerate(analytics["top_products"], 1):
            lines.append(f"  {i}. {p['product_name']}: ${p['revenue']:,.2f}")

    if analytics["category_breakdown"]:
        lines.append("\nCATEGORIES:")
        for c in analytics["category_breakdown"]:
            lines.append(f"  {c['category']}: ${c['revenue']:,.2f}")

    if analytics["regional_performance"]:
        lines.append("\nREGIONS:")
        for r in analytics["regional_performance"]:
            lines.append(f"  {r['region']}: ${r['revenue']:,.2f}")

    return "\n".join(lines)
