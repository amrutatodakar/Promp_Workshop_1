from datetime import datetime, timezone
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.schemas.report import ExtractionResponse, ReportAnalysisResponse
from app.services.extractor import process_report_file
from app.services.ocr import is_ocr_available
from app.services.gemini import explain_report_with_gemini
from app.services.supabase import is_supabase_enabled

logger = logging.getLogger("reportsaathi.api")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for ReportSaathi - Educational Medical Lab Report Explainer"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "documentation": "/docs"
    }

@app.get("/api/health")
def health_check():
    ocr_ok = is_ocr_available()
    gemini_ready = bool(settings.GEMINI_API_KEY.strip())
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "services": {
            "api": "up",
            "tesseract_ocr": "available" if ocr_ok else "not_configured",
            "gemini_ai": "ready" if gemini_ready else "pending_key_or_demo_mode",
            "gemini_model": settings.GEMINI_MODEL,
            "supabase": "connected" if is_supabase_enabled() else "guest_mode"
        }
    }

@app.post(
    "/api/reports/extract",
    response_model=ExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract text, tables, and parameters from a medical lab report",
    description="Accepts PDF, JPG, JPEG, and PNG files. Redacts patient PII and returns structured lab parameters."
)
async def extract_report(
    file: UploadFile = File(..., description="Medical report file (PDF, JPG, JPEG, PNG)")
):
    filename = file.filename or "unknown_file"
    content_type = file.content_type or ""

    try:
        file_bytes = await file.read()
        result = process_report_file(
            file_bytes=file_bytes,
            filename=filename,
            content_type=content_type
        )
        return result
    except ValueError as ve:
        logger.warning(f"Validation/Extraction error for '{filename}': {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as exc:
        logger.error(f"Unexpected extraction failure for '{filename}': {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the document: {str(exc)}"
        )
    finally:
        await file.close()

@app.post(
    "/api/reports/analyze",
    response_model=ReportAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Full pipeline: Extract, Redact PII, and Explain with Gemini AI",
    description="Accepts medical lab report (PDF/Images), extracts data, masks PII, and returns clear educational explanations."
)
async def analyze_report(
    file: UploadFile = File(..., description="Medical report file (PDF, JPG, JPEG, PNG)")
):
    filename = file.filename or "unknown_file"
    content_type = file.content_type or ""

    try:
        file_bytes = await file.read()
        extraction = process_report_file(
            file_bytes=file_bytes,
            filename=filename,
            content_type=content_type
        )
        
        # Generate educational explanation with Gemini (or fallback demo mode)
        analysis = explain_report_with_gemini(extraction)
        return analysis

    except ValueError as ve:
        logger.warning(f"Validation error for '{filename}': {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as exc:
        logger.error(f"Unexpected analysis failure for '{filename}': {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while analyzing the report: {str(exc)}"
        )
    finally:
        await file.close()
