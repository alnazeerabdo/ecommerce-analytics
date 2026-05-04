# 📊 E-commerce Analytics Agent

AI-powered SaaS dashboard that analyzes e-commerce CSV data and provides actionable business insights.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

Required:
- `SUPABASE_URL` — Your Supabase project URL
- `SUPABASE_KEY` — Your Supabase anon key

Optional:
- `HF_API_TOKEN` — HuggingFace API token for AI insights (app works without it)

### 3. Run the Backend (FastAPI)
```bash
python -m uvicorn app.backend.main:app --reload --port 8000
```

### 4. Run the Frontend (Streamlit)
```bash
streamlit run app/frontend/app.py
```

### 5. Open the Dashboard
Visit `http://localhost:8501` in your browser.

## 📁 Project Structure
```
analyist/
├── app/
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI server
│   │   ├── analytics.py     # Pandas analytics engine
│   │   └── ai.py            # AI insights (HuggingFace + fallback)
│   └── frontend/
│       └── app.py            # Streamlit dashboard
├── data_sample.csv            # 150-row demo dataset
├── requirements.txt
├── .env                       # Your credentials (not committed)
├── .env.example               # Template
└── README.md
```

## 📊 Features
- **CSV Upload** — Drag & drop e-commerce data
- **KPI Dashboard** — Revenue, orders, customers, AOV, churn
- **Interactive Charts** — Monthly trends, product performance, categories, regions
- **Data Explorer** — Filter and browse raw data
- **AI Insights** — Business recommendations powered by HuggingFace or built-in engine

## 🧰 Tech Stack
| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Pandas |
| Frontend | Streamlit + Plotly |
| Database | Supabase (PostgreSQL) |
| AI | HuggingFace Inference API |
