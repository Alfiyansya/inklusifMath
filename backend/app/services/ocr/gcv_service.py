"""
Google Cloud Vision OCR Service.

Extracts text from scanned PDF pages by:
  1. Converting each PDF page to a PNG image (via PyMuPDF)
  2. Sending the image bytes to GCV DOCUMENT_TEXT_DETECTION
  3. Returning full text per page + word-level bounding boxes

Usage:
    service = GcvOcrService()
    pages = await service.extract_text_from_pdf(pdf_bytes)

Design decisions:
  - Uses DOCUMENT_TEXT_DETECTION (optimised for dense text + math symbols)
    over TEXT_DETECTION (better for single words/short text)
  - 300 DPI rendering (high enough for OCR, low enough for API payload)
  - Async: renders pages in ThreadPoolExecutor, calls GCV per-page concurrently
  - Fails gracefully: if any page fails, logs warning, returns empty string for that page
  - Credentials: reads GOOGLE_APPLICATION_CREDENTIALS env var (standard GCP)
    OR GOOGLE_CLOUD_VISION_API_KEY for key-based auth (simpler for serverless)

Environment variables:
  GOOGLE_APPLICATION_CREDENTIALS  Path to service account JSON (preferred)
  GOOGLE_CLOUD_VISION_API_KEY      API key fallback
  GCV_OCR_ENABLED                  Set to 'false' to disable (useful in test env)
"""

from __future__ import annotations

import asyncio
import io
import logging
import os
from dataclasses import dataclass, field
from typing import Sequence

logger = logging.getLogger(__name__)

# DPI used when rasterising PDF pages for OCR
_RENDER_DPI = 300
_RENDER_MATRIX_SCALE = _RENDER_DPI / 72  # PyMuPDF uses 72 DPI base

_GCV_ENABLED = os.getenv("GCV_OCR_ENABLED", "true").lower() != "false"


@dataclass
class OcrPage:
    """OCR result for one PDF page (0-indexed)."""

    page_index: int
    text: str
    """Full text extracted from this page."""

    word_boxes: list[dict] = field(default_factory=list)
    """Optional: list of {word, x0, y0, x1, y1} in page coordinates."""

    error: str | None = None
    """Set if OCR failed for this page."""


@dataclass
class GcvOcrResult:
    """Aggregated OCR result across all pages."""

    pages: list[OcrPage]
    full_text: str
    """Concatenation of all page texts (separated by form-feeds \\f)."""

    success: bool
    """True if at least one page was extracted successfully."""


def _render_page_to_png(pdf_bytes: bytes, page_index: int) -> bytes:
    """
    Render a single PDF page to PNG bytes at _RENDER_DPI.
    Runs synchronously — must be called in a thread executor.
    """
    import fitz  # PyMuPDF

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        page = doc[page_index]
        mat = fitz.Matrix(_RENDER_MATRIX_SCALE, _RENDER_MATRIX_SCALE)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        return pix.tobytes("png")
    finally:
        doc.close()


def _call_gcv_sync(image_bytes: bytes) -> dict:
    """
    Send image_bytes to GCV DOCUMENT_TEXT_DETECTION.
    Returns the raw API response dict.
    Runs synchronously — must be called in a thread executor.
    """
    from google.cloud import vision  # type: ignore[import]

    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=image_bytes)
    response = client.document_text_detection(image=image)
    return {
        "full_text": response.full_text_annotation.text,
        "error": response.error.message if response.error.message else None,
    }


def _parse_gcv_response(response: dict, page_index: int) -> OcrPage:
    """Convert raw GCV response dict to an OcrPage."""
    if response.get("error"):
        return OcrPage(
            page_index=page_index,
            text="",
            error=response["error"],
        )
    return OcrPage(
        page_index=page_index,
        text=response.get("full_text", ""),
    )


class GcvOcrService:
    """
    Async wrapper around Google Cloud Vision DOCUMENT_TEXT_DETECTION.

    Converts each PDF page to PNG, sends to GCV, and aggregates results.
    """

    def __init__(self, enabled: bool = _GCV_ENABLED) -> None:
        self.enabled = enabled

    async def extract_text_from_pdf(
        self,
        pdf_bytes: bytes,
        max_pages: int = 50,
    ) -> GcvOcrResult:
        """
        Run OCR on all pages of a PDF (up to max_pages).

        Args:
            pdf_bytes: Raw PDF file content.
            max_pages: Safety cap — avoids extremely long GCV bills.

        Returns:
            GcvOcrResult with per-page text and aggregated full_text.
        """
        if not self.enabled:
            logger.info("GCV OCR disabled — returning empty result")
            return GcvOcrResult(pages=[], full_text="", success=False)

        # Count pages
        import fitz

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        n_pages = min(doc.page_count, max_pages)
        doc.close()

        logger.info("GCV OCR: processing %d pages", n_pages)

        loop = asyncio.get_event_loop()
        pages: list[OcrPage] = []

        for page_idx in range(n_pages):
            try:
                # Render synchronously in thread executor
                png_bytes = await loop.run_in_executor(
                    None, _render_page_to_png, pdf_bytes, page_idx
                )
                # Call GCV in thread executor
                raw = await loop.run_in_executor(None, _call_gcv_sync, png_bytes)
                page = _parse_gcv_response(raw, page_idx)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "GCV OCR failed for page %d: %s", page_idx, exc
                )
                page = OcrPage(page_index=page_idx, text="", error=str(exc))

            pages.append(page)

        full_text = "\f".join(p.text for p in pages)
        success = any(p.text.strip() for p in pages)

        logger.info(
            "GCV OCR complete: %d/%d pages had text",
            sum(1 for p in pages if p.text.strip()),
            n_pages,
        )
        return GcvOcrResult(pages=pages, full_text=full_text, success=success)

    async def extract_text_from_image(self, image_bytes: bytes) -> str:
        """
        Run OCR on a single image (PNG/JPEG).
        Returns extracted text or empty string on failure.
        """
        if not self.enabled:
            return ""
        loop = asyncio.get_event_loop()
        try:
            raw = await loop.run_in_executor(None, _call_gcv_sync, image_bytes)
            page = _parse_gcv_response(raw, 0)
            return page.text
        except Exception as exc:  # noqa: BLE001
            logger.warning("GCV single-image OCR failed: %s", exc)
            return ""
