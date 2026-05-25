# AI-Powered E-Commerce Analytics System

This project is an Arabic-first analytics app (Streamlit + FastAPI + Pandas) for e-commerce teams.
It now aligns with a broader AI analytics blueprint: richer inputs, deeper analysis, and clearer outputs.

## 1) Data Inputs Supported

### Core (already supported)
- Orders/transactions: order id, date/time, quantity, prices, totals.
- Customers: customer id/name.
- Products: product and category.
- Region/location: city/region/country style columns.

### Optional advanced inputs (newly auto-detected)
- `order_status`
- `payment_method`
- `discount_amount`
- `refund_reason`
- `traffic_source`
- `campaign`
- `ad_spend`

> The engine auto-detects Arabic and English naming variants where possible.

## 2) Analysis Types Implemented

### Existing analyses
- KPI summary: revenue, orders, customers, products, AOV, churn, repeat rate.
- Monthly revenue and order trends.
- Top products, category breakdown, regional performance.
- Top customers + customer activity/churn indicators.

### New analyses added in this update
- Order status breakdown.
- Payment method breakdown.
- Refund reason breakdown.
- Traffic source performance (revenue by source).
- Campaign performance with ROAS when ad spend exists.
- RFM-lite customer segmentation (`loyal_high_value`, `regular`, `at_risk`).

## 3) Outputs

- Interactive dashboard (Arabic UI, responsive/mobile-friendly).
- AI-generated insight text from computed analytics.
- Structured JSON outputs from backend `/analyze` endpoint for downstream reports/alerts.

## 4) Run Locally

```bash
pip install -r requirements.txt
python -m uvicorn app.backend.main:app --reload --port 8000
streamlit run app/frontend/app.py
```

Open: `http://localhost:8501`

## 5) API Endpoints

- `GET /health`
- `POST /upload`
- `POST /analyze`
- `POST /insights`

## 6) Notes

- If a dataset does not contain an optional column, related advanced sections are returned as empty lists.
- Column detection is heuristic; for best results use clear field names matching business semantics.
