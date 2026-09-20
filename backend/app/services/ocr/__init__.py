"""
OCR services package.

Exports:
  GcvOcrService      — Google Cloud Vision OCR for scanned PDFs
  MathpixService     — Mathpix API for formula image → LaTeX
  run_ocr_pipeline   — Orchestrate full OCR pipeline
  OcrPipelineError   — Raised when OCR fails completely
  OcrPipelineResult  — Return type from run_ocr_pipeline
"""

from app.services.ocr.gcv_service import GcvOcrService, GcvOcrResult, OcrPage
from app.services.ocr.mathpix_service import MathpixService, MathpixResult
from app.services.ocr.ocr_pipeline import (
    OcrPipelineError,
    OcrPipelineResult,
    run_ocr_pipeline,
)

__all__ = [
    "GcvOcrService",
    "GcvOcrResult",
    "OcrPage",
    "MathpixService",
    "MathpixResult",
    "OcrPipelineError",
    "OcrPipelineResult",
    "run_ocr_pipeline",
]
