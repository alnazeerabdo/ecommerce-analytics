"""
Advanced Analytics Engine
==========================
Adds six predictive / prescriptive capabilities on top of the core analytics:

1. Revenue forecasting & seasonality  -> forecast_revenue()
2. Recommendation engine (FBT)         -> recommend_products()
3. Anomaly detection & alerts          -> detect_anomalies()
4. Churn prediction & retention        -> predict_churn()
5. Inventory & demand signals          -> inventory_signals()

A single entry point `compute_advanced(df)` runs everything it can given the
columns present in the uploaded file, degrading gracefully when data is missing.

All functions are defensive: they never raise on malformed/sparse data, they
return plain JSON-serialisable dicts/lists, and they include an Arabic `note`
field explaining what is missing when a capability can't run.
"""

from __future__ import annotations

from datetime import timedelta
from itertools import combinations
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

from app.backend.analytics import detect_columns, detect_optional_columns


# --------------------------------------------------------------------------- #
# Shared preparation
# --------------------------------------------------------------------------- #
def _prepare(df: pd.DataFrame) -> dict:
    """Detect columns and coerce types once, return a context dict."""
    df = df.copy()
    col_map = detect_columns(df)

    date_col = col_map.get("date")
    order_col = col_map.get("order_id")
    customer_col = col_map.get("customer_id") or col_map.get("customer_name")
    product_col = col_map.get("product")
    category_col = col_map.get("category")
    quantity_col = col_map.get("quantity")
    total_col = col_map.get("total_price")
    unit_price_col = col_map.get("unit_price")

    used = set(v for v in col_map.values() if v)
    optional_map = detect_optional_columns(df, used)
    stock_col = _detect_stock_column(df, used)

    # Compute total if missing but derivable
    if total_col is None and col_map.get("_compute_total"):
        df["_total"] = (
            pd.to_numeric(df[unit_price_col], errors="coerce")
            * pd.to_numeric(df[quantity_col], errors="coerce")
        )
        total_col = "_total"

    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col])
    if total_col:
        df[total_col] = pd.to_numeric(df[total_col], errors="coerce").fillna(0)
    if quantity_col:
        df[quantity_col] = pd.to_numeric(df[quantity_col], errors="coerce").fillna(0)

    return {
        "df": df,
        "date_col": date_col,
        "order_col": order_col,
        "customer_col": customer_col,
        "product_col": product_col,
        "category_col": category_col,
        "quantity_col": quantity_col,
        "total_col": total_col,
        "stock_col": stock_col,
        "status_col": optional_map.get("order_status"),
        "refund_reason_col": optional_map.get("refund_reason"),
    }


def _detect_stock_column(df: pd.DataFrame, used: set) -> str | None:
    """Detect an inventory / stock-on-hand column if one exists."""
    import re

    patterns = [r"stock", r"inventory", r"on.?hand", r"المخزون", r"الكمية.?المتوفرة", r"available.?qty"]
    for col in df.columns:
        if col in used:
            continue
        low = col.lower().strip()
        if any(re.search(p, low, re.IGNORECASE) for p in patterns):
            return col
    return None


# --------------------------------------------------------------------------- #
# 1) Revenue forecasting & seasonality
# --------------------------------------------------------------------------- #
def forecast_revenue(ctx: dict) -> dict:
    """
    Forecast future revenue using a linear trend plus seasonality multipliers.
    - If >= 21 distinct days are available -> daily model with weekly seasonality,
      projecting 7 / 30 / 90 day horizons.
    - Else if >= 4 months -> monthly model projecting the next 3 months.
    Returns history, forecast points, confidence band and a trend summary.
    """
    df, date_col, total_col = ctx["df"], ctx["date_col"], ctx["total_col"]
    empty = {
        "available": False,
        "note": "أضف عمود التاريخ وعمود المبلغ للحصول على توقعات الإيرادات.",
        "history": [], "forecast": [], "granularity": None,
        "horizons": {}, "trend_pct": 0, "seasonality": [],
    }
    if not date_col or not total_col or df.empty:
        return empty

    daily = df.groupby(df[date_col].dt.normalize())[total_col].sum()
    if daily.empty:
        return empty

    full_idx = pd.date_range(daily.index.min(), daily.index.max(), freq="D")
    daily = daily.reindex(full_idx, fill_value=0.0)
    n_days = len(daily)

    # Decide granularity
    if n_days >= 21:
        return _forecast_daily(daily)
    monthly = df.groupby(df[date_col].dt.to_period("M"))[total_col].sum()
    if len(monthly) >= 4:
        return _forecast_monthly(monthly)
    return {**empty, "note": "البيانات قليلة جداً للتنبؤ (يلزم 21 يوماً أو 4 أشهر على الأقل)."}


def _linfit(y: np.ndarray):
    x = np.arange(len(y), dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    return slope, intercept


def _forecast_daily(daily: pd.Series) -> dict:
    y = daily.values.astype(float)
    slope, intercept = _linfit(y)
    x = np.arange(len(y), dtype=float)
    fitted = slope * x + intercept
    fitted_safe = np.where(fitted > 0, fitted, np.nan)

    # Weekly seasonality factors (day-of-week multiplier, normalised to mean 1)
    ratio = np.where(np.isfinite(fitted_safe), y / fitted_safe, np.nan)
    wk = pd.Series(ratio, index=daily.index).groupby(daily.index.dayofweek).mean()
    wk = wk.reindex(range(7)).fillna(1.0)
    if wk.mean() > 0:
        wk = wk / wk.mean()
    season_factors = {int(k): round(float(v), 3) for k, v in wk.items()}

    resid_std = float(np.nanstd(y - fitted))

    horizon = 90
    fut_x = np.arange(len(y), len(y) + horizon, dtype=float)
    fut_dates = pd.date_range(daily.index.max() + timedelta(days=1), periods=horizon, freq="D")
    fut_trend = slope * fut_x + intercept
    fut_season = np.array([wk.get(d, 1.0) for d in fut_dates.dayofweek])
    fut_pred = np.clip(fut_trend * fut_season, 0, None)

    forecast = [
        {
            "date": d.strftime("%Y-%m-%d"),
            "predicted": round(float(p), 2),
            "lower": round(float(max(p - 1.96 * resid_std, 0)), 2),
            "upper": round(float(p + 1.96 * resid_std), 2),
        }
        for d, p in zip(fut_dates, fut_pred)
    ]

    # last ~60 days of history for charting
    hist_tail = daily.tail(60)
    history = [
        {"date": d.strftime("%Y-%m-%d"), "revenue": round(float(v), 2)}
        for d, v in hist_tail.items()
    ]

    horizons = {
        "7_day": round(float(fut_pred[:7].sum()), 2),
        "30_day": round(float(fut_pred[:30].sum()), 2),
        "90_day": round(float(fut_pred[:90].sum()), 2),
    }
    daily_avg = float(y.mean()) if len(y) else 0
    trend_pct = round((slope / daily_avg) * 100, 2) if daily_avg > 0 else 0

    weekdays_ar = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
    seasonality = [
        {"weekday": weekdays_ar[k], "factor": v} for k, v in season_factors.items()
    ]
    best_day = weekdays_ar[int(max(season_factors, key=season_factors.get))]
    worst_day = weekdays_ar[int(min(season_factors, key=season_factors.get))]

    return {
        "available": True,
        "granularity": "daily",
        "note": "",
        "history": history,
        "forecast": forecast,
        "horizons": horizons,
        "trend_pct": trend_pct,
        "trend_direction": "صاعد" if slope > 0 else ("هابط" if slope < 0 else "مستقر"),
        "seasonality": seasonality,
        "best_day": best_day,
        "worst_day": worst_day,
    }


def _forecast_monthly(monthly: pd.Series) -> dict:
    y = monthly.values.astype(float)
    slope, intercept = _linfit(y)
    resid_std = float(np.std(y - (slope * np.arange(len(y)) + intercept)))

    horizon = 3
    fut_x = np.arange(len(y), len(y) + horizon, dtype=float)
    fut_pred = np.clip(slope * fut_x + intercept, 0, None)
    last_period = monthly.index.max()
    fut_periods = [(last_period + i + 1).strftime("%Y-%m") for i in range(horizon)]

    forecast = [
        {
            "date": p,
            "predicted": round(float(v), 2),
            "lower": round(float(max(v - 1.96 * resid_std, 0)), 2),
            "upper": round(float(v + 1.96 * resid_std), 2),
        }
        for p, v in zip(fut_periods, fut_pred)
    ]
    history = [
        {"date": p.strftime("%Y-%m"), "revenue": round(float(v), 2)}
        for p, v in monthly.items()
    ]
    monthly_avg = float(y.mean()) if len(y) else 0
    trend_pct = round((slope / monthly_avg) * 100, 2) if monthly_avg > 0 else 0

    return {
        "available": True,
        "granularity": "monthly",
        "note": "تنبؤ شهري (البيانات اليومية غير كافية).",
        "history": history,
        "forecast": forecast,
        "horizons": {
            "next_month": round(float(fut_pred[0]), 2) if len(fut_pred) else 0,
            "next_3_months": round(float(fut_pred.sum()), 2),
        },
        "trend_pct": trend_pct,
        "trend_direction": "صاعد" if slope > 0 else ("هابط" if slope < 0 else "مستقر"),
        "seasonality": [],
        "best_day": None,
        "worst_day": None,
    }


# --------------------------------------------------------------------------- #
# 2) Recommendation engine — frequently bought together (market basket)
# --------------------------------------------------------------------------- #
def recommend_products(ctx: dict, max_per_product: int = 4, top_products: int = 12) -> dict:
    """Compute co-occurrence based 'frequently bought together' associations."""
    df = ctx["df"]
    order_col, product_col = ctx["order_col"], ctx["product_col"]
    empty = {
        "available": False,
        "note": "يلزم عمود رقم الطلب وعمود المنتج لبناء محرك التوصيات.",
        "pairs": [], "by_product": [],
    }
    if not order_col or not product_col or df.empty:
        return empty

    baskets = (
        df.groupby(order_col)[product_col]
        .apply(lambda s: sorted(set(str(x) for x in s.dropna())))
    )
    baskets = [b for b in baskets if len(b) >= 1]
    n_orders = len(baskets)
    if n_orders == 0:
        return empty

    item_counts = Counter()
    pair_counts = Counter()
    for items in baskets:
        for it in items:
            item_counts[it] += 1
        for a, b in combinations(items, 2):
            pair_counts[(a, b)] += 1

    multi_item_baskets = sum(1 for b in baskets if len(b) >= 2)
    if not pair_counts:
        return {
            **empty,
            "available": False,
            "note": "لا توجد طلبات تحتوي على أكثر من منتج واحد لاكتشاف الارتباطات.",
        }

    # Global top pairs by lift (with a minimum support of 2 co-occurrences)
    pairs = []
    for (a, b), c in pair_counts.items():
        if c < 2:
            continue
        support = c / n_orders
        lift = support / ((item_counts[a] / n_orders) * (item_counts[b] / n_orders))
        confidence_ab = c / item_counts[a]
        pairs.append(
            {
                "product_a": a,
                "product_b": b,
                "count": int(c),
                "support": round(support, 4),
                "confidence": round(confidence_ab, 3),
                "lift": round(lift, 2),
            }
        )
    pairs.sort(key=lambda p: (p["lift"], p["count"]), reverse=True)

    # Per-product recommendations
    assoc = defaultdict(list)
    for (a, b), c in pair_counts.items():
        if c < 2:
            continue
        assoc[a].append((b, c))
        assoc[b].append((a, c))

    ranked_products = [p for p, _ in item_counts.most_common(top_products)]
    by_product = []
    for prod in ranked_products:
        recs = sorted(assoc.get(prod, []), key=lambda x: x[1], reverse=True)[:max_per_product]
        if not recs:
            continue
        by_product.append(
            {
                "product": prod,
                "bought_count": int(item_counts[prod]),
                "recommendations": [
                    {
                        "product": r,
                        "count": int(c),
                        "confidence": round(c / item_counts[prod], 3),
                    }
                    for r, c in recs
                ],
            }
        )

    return {
        "available": True,
        "note": "",
        "orders_analyzed": n_orders,
        "multi_item_orders": multi_item_baskets,
        "pairs": pairs[:25],
        "by_product": by_product,
    }


# --------------------------------------------------------------------------- #
# 3) Anomaly detection & alerts
# --------------------------------------------------------------------------- #
def detect_anomalies(ctx: dict, churn_rate: float = 0.0) -> dict:
    """Detect revenue anomalies (z-score) and build an actionable alert feed."""
    df, date_col, total_col = ctx["df"], ctx["date_col"], ctx["total_col"]
    result = {
        "available": False,
        "note": "",
        "revenue_anomalies": [],
        "alerts": [],
    }

    anomalies = []
    if date_col and total_col and not df.empty:
        daily = df.groupby(df[date_col].dt.normalize())[total_col].sum()
        if len(daily) >= 14:
            full_idx = pd.date_range(daily.index.min(), daily.index.max(), freq="D")
            daily = daily.reindex(full_idx, fill_value=0.0)
            roll_mean = daily.rolling(7, min_periods=3).mean()
            roll_std = daily.rolling(7, min_periods=3).std().replace(0, np.nan)
            z = (daily - roll_mean) / roll_std
            for d, score in z.items():
                if pd.notna(score) and abs(score) >= 2.5:
                    val = float(daily[d])
                    exp = float(roll_mean[d])
                    anomalies.append(
                        {
                            "date": d.strftime("%Y-%m-%d"),
                            "value": round(val, 2),
                            "expected": round(exp, 2),
                            "z_score": round(float(score), 2),
                            "direction": "ارتفاع" if score > 0 else "انخفاض",
                            "severity": "عالية" if abs(score) >= 3.5 else "متوسطة",
                        }
                    )
            result["available"] = True
            # keep the most extreme 15
            anomalies.sort(key=lambda a: abs(a["z_score"]), reverse=True)
            result["revenue_anomalies"] = anomalies[:15]
        else:
            result["note"] = "يلزم 14 يوماً على الأقل لاكتشاف الشذوذ في الإيرادات."
    else:
        result["note"] = "أضف عمود التاريخ والمبلغ لاكتشاف الشذوذ."

    # ---- Build alert feed ----
    alerts = []
    if churn_rate >= 50:
        alerts.append(
            {
                "level": "critical",
                "title": "معدل فقدان العملاء مرتفع جداً",
                "message": f"معدل الفقدان الحالي {churn_rate}% — يتطلب حملة استرداد فورية.",
            }
        )
    elif churn_rate >= 35:
        alerts.append(
            {
                "level": "warning",
                "title": "ارتفاع معدل فقدان العملاء",
                "message": f"معدل الفقدان {churn_rate}% أعلى من المعدل الصحي (أقل من 30%).",
            }
        )

    # Recent negative revenue anomalies -> alert
    recent_drops = [a for a in result["revenue_anomalies"] if a["direction"] == "انخفاض"]
    if recent_drops:
        worst = recent_drops[0]
        alerts.append(
            {
                "level": "warning" if worst["severity"] == "متوسطة" else "critical",
                "title": "انخفاض غير اعتيادي في الإيرادات",
                "message": f"بتاريخ {worst['date']} بلغت الإيرادات ${worst['value']:,.0f} مقابل متوقع ${worst['expected']:,.0f}.",
            }
        )

    # Return-rate signal
    status_col, refund_col = ctx["status_col"], ctx["refund_reason_col"]
    if status_col and not df.empty:
        statuses = df[status_col].fillna("").astype(str).str.lower()
        returned = statuses.str.contains("return|refund|cancel|مرتجع|إلغاء|استرجاع", regex=True)
        rate = round(float(returned.mean()) * 100, 1)
        if rate >= 10:
            alerts.append(
                {
                    "level": "warning",
                    "title": "ارتفاع نسبة المرتجعات / الإلغاءات",
                    "message": f"نسبة المرتجعات أو الإلغاءات {rate}% من الطلبات — راجع جودة المنتجات والوصف.",
                }
            )
    elif refund_col and not df.empty:
        rate = round(float(df[refund_col].notna().mean()) * 100, 1)
        if rate >= 10:
            alerts.append(
                {
                    "level": "warning",
                    "title": "ارتفاع نسبة الاسترجاع",
                    "message": f"تم تسجيل سبب استرجاع في {rate}% من السجلات.",
                }
            )

    if not alerts:
        alerts.append(
            {
                "level": "ok",
                "title": "لا توجد تنبيهات حرجة",
                "message": "المؤشرات ضمن النطاق الطبيعي. واصل مراقبة الأداء.",
            }
        )

    result["alerts"] = alerts
    return result


# --------------------------------------------------------------------------- #
# 4) Churn prediction & retention
# --------------------------------------------------------------------------- #
def predict_churn(ctx: dict, top_n: int = 15) -> dict:
    """
    Per-customer churn risk based on recency vs. each customer's typical
    inter-purchase gap. Produces risk tiers, an at-risk list and retention tips.
    """
    df = ctx["df"]
    date_col, customer_col, total_col, order_col = (
        ctx["date_col"], ctx["customer_col"], ctx["total_col"], ctx["order_col"],
    )
    empty = {
        "available": False,
        "note": "يلزم عمود العميل وعمود التاريخ للتنبؤ بفقدان العملاء.",
        "distribution": [], "at_risk_customers": [], "retention_tips": [],
    }
    if not date_col or not customer_col or df.empty:
        return empty

    snapshot = df[date_col].max()
    rows = []
    # Median global gap for single-purchase customers
    all_gaps = []
    grouped = df.sort_values(date_col).groupby(customer_col)
    cust_dates = {}
    for cust, g in grouped:
        dates = g[date_col].dt.normalize().drop_duplicates().sort_values()
        cust_dates[cust] = dates
        if len(dates) >= 2:
            all_gaps.extend(np.diff(dates.values).astype("timedelta64[D]").astype(int).tolist())
    global_gap = float(np.median(all_gaps)) if all_gaps else 30.0

    for cust, dates in cust_dates.items():
        recency = int((snapshot - dates.max()).days)
        if len(dates) >= 2:
            gaps = np.diff(dates.values).astype("timedelta64[D]").astype(int)
            avg_gap = float(np.mean(gaps)) if len(gaps) else global_gap
        else:
            avg_gap = global_gap
        avg_gap = max(avg_gap, 1.0)
        ratio = recency / avg_gap
        risk_score = round(min(ratio / 3.0, 1.0) * 100, 1)  # 0..100
        if ratio >= 2:
            tier = "مرتفع"
        elif ratio >= 1:
            tier = "متوسط"
        else:
            tier = "منخفض"
        cust_df = df[df[customer_col] == cust]
        spent = round(float(cust_df[total_col].sum()), 2) if total_col else 0
        orders = int(cust_df[order_col].nunique()) if order_col else len(cust_df)
        rows.append(
            {
                "customer": str(cust),
                "recency_days": recency,
                "avg_gap_days": round(avg_gap, 1),
                "orders": orders,
                "total_spent": spent,
                "risk_score": risk_score,
                "risk_tier": tier,
            }
        )

    if not rows:
        return empty

    rdf = pd.DataFrame(rows)
    dist = (
        rdf["risk_tier"].value_counts()
        .reindex(["مرتفع", "متوسط", "منخفض"]).fillna(0).astype(int)
    )
    distribution = [{"tier": k, "customers": int(v)} for k, v in dist.items()]

    # At-risk = high tier, prioritised by money at stake
    at_risk = (
        rdf[rdf["risk_tier"] == "مرتفع"]
        .sort_values("total_spent", ascending=False)
        .head(top_n)
        .to_dict(orient="records")
    )

    total = len(rdf)
    high = int(dist.get("مرتفع", 0))
    revenue_at_risk = round(
        float(rdf[rdf["risk_tier"] == "مرتفع"]["total_spent"].sum()), 2
    )

    tips = [
        "أرسل عرضاً حصرياً (خصم 15-20%) للعملاء ذوي الخطورة المرتفعة خلال 48 ساعة.",
        "فعّل تسلسل بريد إلكتروني آلي لاسترداد العملاء بعد تجاوز ضعف متوسط فترة الشراء.",
        "قدّم برنامج ولاء بنقاط لتحفيز الشراء المتكرر وتقليل الفجوة بين الطلبات.",
        "اطلب ملاحظات العملاء غير النشطين لفهم أسباب التوقف ومعالجتها.",
    ]

    return {
        "available": True,
        "note": "",
        "distribution": distribution,
        "at_risk_customers": at_risk,
        "summary": {
            "total_customers": total,
            "high_risk": high,
            "high_risk_pct": round((high / total) * 100, 1) if total else 0,
            "revenue_at_risk": revenue_at_risk,
        },
        "retention_tips": tips,
    }


# --------------------------------------------------------------------------- #
# 5) Inventory & demand signals
# --------------------------------------------------------------------------- #
def inventory_signals(ctx: dict, top_n: int = 10) -> dict:
    """
    Sell-through velocity, demand momentum, slow movers and stock-out risk.
    Uses an explicit stock column when present, otherwise flags restock
    priorities from velocity + recent momentum.
    """
    df = ctx["df"]
    date_col, product_col, quantity_col, total_col, stock_col = (
        ctx["date_col"], ctx["product_col"], ctx["quantity_col"],
        ctx["total_col"], ctx["stock_col"],
    )
    empty = {
        "available": False,
        "note": "يلزم عمود المنتج وعمود الكمية لتحليل المخزون والطلب.",
        "velocity": [], "slow_movers": [], "fast_movers": [], "stock_risk": [],
        "has_stock_data": False,
    }
    if not product_col or df.empty:
        return empty

    qcol = quantity_col
    if qcol is None:
        # fall back to counting rows as 1 unit each
        df = df.copy()
        df["_qty"] = 1
        qcol = "_qty"

    # Time span for velocity (days)
    if date_col:
        span_days = max((df[date_col].max() - df[date_col].min()).days, 1)
    else:
        span_days = None

    agg = {"units": (qcol, "sum")}
    if total_col:
        agg["revenue"] = (total_col, "sum")
    grp = df.groupby(product_col).agg(**agg)

    # Velocity = units per day
    if span_days:
        grp["velocity"] = (grp["units"] / span_days).round(3)
    else:
        grp["velocity"] = grp["units"].round(3)

    # Recent momentum: last 1/3 of timeline vs first 1/3
    momentum = {}
    if date_col:
        tmin, tmax = df[date_col].min(), df[date_col].max()
        third = (tmax - tmin) / 3
        if third.total_seconds() > 0:
            early = df[df[date_col] <= tmin + third]
            late = df[df[date_col] >= tmax - third]
            early_u = early.groupby(product_col)[qcol].sum()
            late_u = late.groupby(product_col)[qcol].sum()
            for p in grp.index:
                e = float(early_u.get(p, 0))
                l = float(late_u.get(p, 0))
                if e > 0:
                    momentum[p] = round(((l - e) / e) * 100, 1)
                elif l > 0:
                    momentum[p] = 100.0
                else:
                    momentum[p] = 0.0
    grp["momentum_pct"] = grp.index.map(lambda p: momentum.get(p, 0.0))

    has_stock = stock_col is not None
    if has_stock:
        stock_by_prod = (
            pd.to_numeric(df[stock_col], errors="coerce")
            .groupby(df[product_col]).last()
        )
        grp["stock_on_hand"] = grp.index.map(lambda p: float(stock_by_prod.get(p, 0)))
        grp["days_of_cover"] = grp.apply(
            lambda r: round(r["stock_on_hand"] / r["velocity"], 1)
            if r["velocity"] > 0 else None,
            axis=1,
        )

    grp = grp.reset_index().rename(columns={product_col: "product"})
    grp["product"] = grp["product"].astype(str)

    def _round(records):
        for r in records:
            for k, v in list(r.items()):
                if isinstance(v, float):
                    r[k] = round(v, 2)
        return records

    velocity = _round(
        grp.sort_values("velocity", ascending=False).head(top_n).to_dict(orient="records")
    )
    fast_movers = velocity[:5]
    slow_movers = _round(
        grp[grp["units"] > 0].sort_values("velocity", ascending=True).head(top_n).to_dict(orient="records")
    )

    # Stock-out risk
    stock_risk = []
    if has_stock:
        risk_df = grp[grp["days_of_cover"].notna()].sort_values("days_of_cover")
        for r in risk_df.head(top_n).to_dict(orient="records"):
            doc = r["days_of_cover"]
            if doc is None:
                continue
            level = "حرجة" if doc <= 7 else ("متوسطة" if doc <= 21 else "منخفضة")
            if level == "منخفضة":
                continue
            stock_risk.append(
                {
                    "product": r["product"],
                    "stock_on_hand": r.get("stock_on_hand"),
                    "velocity": r["velocity"],
                    "days_of_cover": doc,
                    "risk": level,
                }
            )
    else:
        # Heuristic: high velocity + positive momentum => restock priority
        heur = grp[(grp["velocity"] > 0) & (grp["momentum_pct"] >= 10)]
        heur = heur.sort_values(["velocity", "momentum_pct"], ascending=False)
        for r in heur.head(top_n).to_dict(orient="records"):
            stock_risk.append(
                {
                    "product": r["product"],
                    "velocity": round(float(r["velocity"]), 2),
                    "momentum_pct": round(float(r["momentum_pct"]), 1),
                    "risk": "أولوية إعادة تخزين (طلب مرتفع ومتزايد)",
                }
            )

    note = "" if has_stock else "لا يوجد عمود مخزون — يتم تقدير أولوية إعادة التخزين من سرعة البيع والزخم."
    return {
        "available": True,
        "note": note,
        "has_stock_data": has_stock,
        "span_days": span_days,
        "velocity": velocity,
        "fast_movers": fast_movers,
        "slow_movers": slow_movers,
        "stock_risk": stock_risk,
    }


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def compute_advanced(df: pd.DataFrame, churn_rate: float = 0.0) -> dict:
    """Run every advanced capability available for the given DataFrame."""
    ctx = _prepare(df)
    forecast = forecast_revenue(ctx)
    recommendations = recommend_products(ctx)
    churn = predict_churn(ctx)
    # Prefer the per-customer churn rate if core didn't supply one
    eff_churn = churn_rate
    if (not eff_churn) and churn.get("available") and churn.get("summary"):
        eff_churn = churn["summary"].get("high_risk_pct", 0)
    anomalies = detect_anomalies(ctx, churn_rate=eff_churn)
    inventory = inventory_signals(ctx)

    return {
        "forecast": forecast,
        "recommendations": recommendations,
        "anomalies": anomalies,
        "churn_prediction": churn,
        "inventory": inventory,
    }
