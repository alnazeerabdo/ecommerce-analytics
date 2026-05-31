"""
FastAPI Backend — E-commerce Analytics Agent API Server.
"""

import os
import io
import json
import logging
from typing import Optional

import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from dotenv import load_dotenv

from app.backend.analytics import (
    validate_csv, compute_analytics, generate_summary_text, read_file,
)
from app.backend.advanced import compute_advanced
from app.backend.reports import export_csv, export_excel, export_pdf
from app.backend.ai import generate_insights

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Supabase client ---
supabase_client = None
try:
    from supabase import create_client
    sb_url = os.getenv("SUPABASE_URL", "")
    sb_key = os.getenv("SUPABASE_KEY", "")
    if sb_url and sb_key:
        supabase_client = create_client(sb_url, sb_key)
        logger.info("Supabase client initialized.")
    else:
        logger.warning("Supabase credentials not set. Running without database caching.")
except Exception as e:
    logger.warning(f"Supabase init failed: {e}. Running without database.")

# --- FastAPI app ---
app = FastAPI(
    title="E-commerce Analytics Agent",
    description="Upload CSV data, get analytics and AI-powered business insights.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "supabase_connected": supabase_client is not None,
        "version": "1.0.0",
    }


@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload a CSV file. Validates structure and stores metadata.
    Returns upload_id and validation results.
    """
    # Check file type
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    # Read file content
    content = await file.read()

    # Check file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Max size is {MAX_FILE_SIZE // (1024*1024)}MB.")

    # Parse CSV
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")

    # Validate columns
    validation = validate_csv(df)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["message"])

    # Store in Supabase
    upload_id = None
    if supabase_client:
        try:
            result = supabase_client.table("uploads").insert({
                "filename": file.filename,
                "file_size_bytes": len(content),
                "row_count": len(df),
                "column_names": list(df.columns),
            }).execute()
            upload_id = result.data[0]["id"]
        except Exception as e:
            logger.error(f"Supabase insert error: {e}")

    return {
        "upload_id": upload_id,
        "filename": file.filename,
        "row_count": len(df),
        "columns": list(df.columns),
        "validation": validation,
    }


@app.post("/analyze")
async def analyze_data(file: UploadFile = File(...), upload_id: Optional[str] = None):
    """
    Analyze uploaded CSV data. Returns comprehensive KPIs and breakdowns.
    """
    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large.")

    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")

    validation = validate_csv(df)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["message"])

    # Compute analytics
    analytics = compute_analytics(df)

    # Cache in Supabase
    if supabase_client and upload_id:
        try:
            supabase_client.table("analytics_cache").insert({
                "upload_id": upload_id,
                "kpi_data": analytics["kpis"],
                "monthly_revenue": analytics["monthly_revenue"],
                "top_products": analytics["top_products"],
                "category_breakdown": analytics["category_breakdown"],
                "regional_performance": analytics["regional_performance"],
                "customer_insights": analytics.get("top_customers"),
                "full_analytics": analytics,
            }).execute()
        except Exception as e:
            logger.error(f"Failed to cache analytics: {e}")

    return analytics


@app.post("/insights")
async def get_insights(file: UploadFile = File(...), upload_id: Optional[str] = None):
    """
    Generate AI-powered business insights from CSV data.
    """
    content = await file.read()

    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")

    validation = validate_csv(df)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["message"])

    # Compute analytics first
    analytics = compute_analytics(df)
    summary_text = generate_summary_text(analytics)

    # Generate AI insights
    result = generate_insights(analytics, summary_text)

    # Cache in Supabase
    if supabase_client and upload_id:
        try:
            supabase_client.table("ai_insights_cache").insert({
                "upload_id": upload_id,
                "insights_text": result["insights_text"],
                "model_used": result["model_used"],
                "source": result["source"],
            }).execute()
        except Exception as e:
            logger.error(f"Failed to cache insights: {e}")

    return result


def _read_upload(content: bytes, filename: str) -> pd.DataFrame:
    """Parse an uploaded CSV/Excel file, raising HTTP 400 on failure."""
    try:
        return read_file(content, filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")


@app.post("/advanced")
async def advanced_analysis(file: UploadFile = File(...)):
    """
    Predictive / prescriptive analytics: forecasting, recommendations,
    anomaly detection, churn prediction and inventory signals.
    """
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large.")

    df = _read_upload(content, file.filename)
    validation = validate_csv(df)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["message"])

    analytics = compute_analytics(df)
    advanced = compute_advanced(df, churn_rate=analytics["kpis"].get("churn_rate", 0))
    return {"analytics": analytics, "advanced": advanced}


@app.post("/report")
async def build_report(file: UploadFile = File(...), format: str = "pdf", include_ai: bool = True):
    """
    Generate a downloadable report. `format` is one of: csv | excel | pdf.
    """
    fmt = format.lower()
    if fmt not in {"csv", "excel", "xlsx", "pdf"}:
        raise HTTPException(status_code=400, detail="format must be csv, excel or pdf.")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large.")

    df = _read_upload(content, file.filename)
    validation = validate_csv(df)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["message"])

    analytics = compute_analytics(df)
    advanced = compute_advanced(df, churn_rate=analytics["kpis"].get("churn_rate", 0))

    if fmt == "csv":
        data = export_csv(analytics)
        return Response(
            content=data, media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=report.csv"},
        )
    if fmt in {"excel", "xlsx"}:
        data = export_excel(analytics, advanced)
        return Response(
            content=data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=report.xlsx"},
        )

    ai_text = None
    if include_ai:
        try:
            ai_text = generate_insights(analytics, generate_summary_text(analytics))["insights_text"]
        except Exception as e:
            logger.error(f"AI insights for report failed: {e}")
    data = export_pdf(analytics, advanced, ai_text)
    return Response(
        content=data, media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=report.pdf"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.backend.main:app", host="0.0.0.0", port=8000, reload=True)
