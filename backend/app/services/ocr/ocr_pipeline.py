"""
OCR Pipeline Orchestrator.

Ties together GcvOcrService + MathpixService + PdfParser to process
scanned PDFs that arrive with ocr_used='pending_ocr'.

Pipeline:
  Scanned PDF bytes
      │
      ├─ GCV DOCUMENT_TEXT_DETECTION → full text per page
      │
      ├─ Run PdfParser on OCR'd text (as if it were a digital PDF)
      │      ↳ heading/paragraph detection + inline math regex
      │
      ├─ Detect math image regions (PyMuPDF image list per page)
      │      ↳ For each image region → Mathpix API → LaTeX
      │
      └─ Merge: text blocks from GCV + math expressions from Mathpix
             → ParsedDocument (identical shape to digital PDF result)

Integration with document_service:
  After parse_document() returns a ParsedDocument with ocr_used='pending_ocr',
  call run_ocr_pipeline() which returns a new/enriched ParsedDocument.
  The document_service then persists this enriched result.

Error strategy:
  - GCV failure → raise OcrPipelineError (document stays pending_ocr)
  - Mathpix failure per-image → log warning, use GCV text as fallback
  - Partial results are valid (some expressions may have no LaTeX)
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from app.services.ocr.gcv_service import GcvOcrService
from app.services.ocr.mathpix_service import MathpixService
from app.services.ocr.pix2tex_service import Pix2TexService
from app.core.config import settings
from app.services.parsing.models import (
    BlockType,
    ContentBlock,
    MathExpressionResult,
    ParsedDocument,
)

logger = logging.getLogger(__name__)


class OcrPipelineError(Exception):
    """Raised when the OCR pipeline cannot produce any usable output."""
    pass


@dataclass
class OcrPipelineResult:
    """Output of run_ocr_pipeline()."""

    parsed_document: ParsedDocument
    """Enriched ParsedDocument with OCR text + Mathpix LaTeX."""

    pages_ocr_ok: int
    """Number of pages where GCV extracted text successfully."""

    math_images_found: int
    """Total math image regions detected across all pages."""

    math_images_resolved: int
    """Number of images where Mathpix returned usable LaTeX."""

    ocr_method: str
    """'gcv', 'gcv+mathpix', or 'gcv_only'"""


def _extract_math_image_regions(pdf_bytes: bytes) -> list[tuple[int, bytes]]:
    """
    Extract embedded image regions from a PDF.
    Returns list of (position_order, png_bytes) for images that look like math.

    Heuristic: images with aspect ratio < 0.5 height/width or very small
    are likely inline formulas. Large images are page scans (skip).

    Position order starts at 1 and is relative to document-wide order.
    """
    import fitz  # PyMuPDF

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    regions: list[tuple[int, bytes]] = []
    position = 1

    try:
        for page_num in range(doc.page_count):
            page = doc[page_num]
            image_list = page.get_images(full=True)

            for img_info in image_list:
                xref = img_info[0]
                try:
                    base_image = doc.extract_image(xref)
                    w = base_image.get("width", 0)
                    h = base_image.get("height", 0)

                    # Skip full-page scans (>1500px either dim)
                    # Skip tiny thumbnails (<30px)
                    if w > 1500 or h > 1500 or w < 30 or h < 30:
                        continue

                    # Only keep images that look like inline formulas:
                    # narrow tall strip or wide short strip — math-like aspect ratio
                    aspect = h / max(w, 1)
                    if 0.1 <= aspect <= 3.0:  # reasonable formula proportions
                        image_bytes = base_image["image"]
                        regions.append((position, image_bytes))
                        position += 1
                except Exception as exc:  # noqa: BLE001
                    logger.debug("Could not extract image xref=%d: %s", xref, exc)
    finally:
        doc.close()

    return regions


def _gcv_text_to_parsed_document(
    full_text: str,
    title: str,
) -> ParsedDocument:
    """
    Convert raw OCR text (from GCV) into a ParsedDocument.

    Applies simple heading heuristics and inline math detection
    on the OCR'd text, producing a ParsedDocument identical in
    shape to what PdfParser produces for digital PDFs.
    """
    # Import math extraction helpers from pdf_parser
    from app.services.parsing.pdf_parser import (
        _extract_math_spans,  # type: ignore[attr-defined]
        _clean_latex,          # type: ignore[attr-defined]
    )

    lines = full_text.split("\n")
    content_blocks: list[ContentBlock] = []
    math_expressions: list[MathExpressionResult] = []
    block_idx = 0
    math_pos = 1

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Heading heuristic for OCR text
        import re as _re
        _numbered = _re.match(r"^\d+[.)]\s+\S", stripped)
        is_heading = (
            len(stripped) < 80 and (
                stripped.isupper()
                or _numbered is not None
                or stripped.startswith(("BAB ", "Bab ", "BAGAN ", "TABEL "))
            )
        )

        block_type = BlockType.HEADING2 if is_heading else BlockType.PARAGRAPH

        content_blocks.append(
            ContentBlock(
                block_type=block_type,
                text=stripped,
                level=2 if is_heading else 0,
                index=block_idx,
            )
        )

        # Detect inline math expressions using pdf_parser patterns
        math_spans = _extract_math_spans(stripped)
        for raw_expr in math_spans:
            latex = _clean_latex(raw_expr)
            if latex:
                math_expressions.append(
                    MathExpressionResult(
                        original_notation=raw_expr,
                        latex_representation=latex,
                        position_order=math_pos,
                        block_index=block_idx,
                        conversion_confidence=0.85,  # OCR-sourced, moderate confidence
                    )
                )
                math_pos += 1

        block_idx += 1

    return ParsedDocument(
        title=title,
        file_type="pdf",
        content_blocks=content_blocks,
        math_expressions=math_expressions,
        ocr_used="gcv",
        raw_structure={"blocks": [
            {"type": cb.block_type.value, "text": cb.text, "level": cb.level, "index": cb.index}
            for cb in content_blocks
        ]},
    )


async def run_ocr_pipeline(
    pdf_bytes: bytes,
    title: str,
    gcv_service: GcvOcrService | None = None,
    mathpix_service: MathpixService | None = None,
    pix2tex_service: Pix2TexService | None = None,
    include_mathpix: bool = True,
    math_engine: str | None = None,
) -> OcrPipelineResult:
    """
    Run the full OCR pipeline on a scanned PDF.

    Args:
        pdf_bytes:         Raw PDF content (must be a scanned/image PDF).
        title:             Document title (used for ParsedDocument).
        gcv_service:       Injectable GCV service (creates default if None).
        mathpix_service:   Injectable Mathpix service (creates default if None).
        pix2tex_service:   Injectable Pix2Tex service (creates default if None).
        include_mathpix:   Whether to run math OCR on detected math images.
        math_engine:       Engine for math formula recognition:
                           "pix2tex" (free, default), "mathpix" (paid), "auto".
                           None → use MATH_OCR_ENGINE from config.

    Returns:
        OcrPipelineResult with enriched ParsedDocument.

    Raises:
        OcrPipelineError: If GCV returns no text for any page (total failure).
    """
    gcv = gcv_service or GcvOcrService()

    # Resolve math engine
    engine = math_engine or settings.MATH_OCR_ENGINE
    if engine not in ("pix2tex", "mathpix", "auto"):
        logger.warning("Unknown MATH_OCR_ENGINE '%s', defaulting to 'pix2tex'", engine)
        engine = "pix2tex"

    # Create math OCR service based on engine choice
    if engine == "mathpix":
        math_svc = mathpix_service or MathpixService()
    elif engine == "pix2tex":
        math_svc = pix2tex_service or Pix2TexService()
    else:  # "auto" — try pix2tex first, fallback to mathpix
        math_svc = pix2tex_service or Pix2TexService()

    logger.info("OCR pipeline: math_engine=%s", engine)

    # ── Step 1: GCV text extraction ───────────────────────────────────────────
    logger.info("OCR pipeline: starting GCV extraction for '%s'", title)
    gcv_result = await gcv.extract_text_from_pdf(pdf_bytes)

    if not gcv_result.success:
        raise OcrPipelineError(
            f"GCV OCR returned no text for document '{title}'. "
            "PDF may be corrupt or pages are blank."
        )

    pages_ok = sum(1 for p in gcv_result.pages if p.text.strip())
    logger.info("GCV: %d pages with text", pages_ok)

    # ── Step 2: Parse OCR'd text into ParsedDocument ──────────────────────────
    parsed = _gcv_text_to_parsed_document(gcv_result.full_text, title)

    # ── Step 3: Math formula OCR on image regions (pix2tex or Mathpix) ────────
    math_images_found = 0
    math_images_resolved = 0
    ocr_method = "gcv"

    if include_mathpix and math_svc.is_configured and math_svc.enabled:
        logger.info("OCR pipeline: extracting math image regions")
        image_regions = await asyncio.get_event_loop().run_in_executor(
            None, _extract_math_image_regions, pdf_bytes
        )
        math_images_found = len(image_regions)

        if image_regions:
            logger.info(
                "OCR pipeline: sending %d math images to %s", len(image_regions), engine
            )
            math_results = await math_svc.images_to_latex_batch(image_regions)

            # "auto" mode: if pix2tex returned nothing usable, try Mathpix fallback
            if engine == "auto":
                usable_count = sum(1 for _, r in math_results if r.is_usable)
                if usable_count == 0 and math_images_found > 0:
                    mathpix_fallback = mathpix_service or MathpixService()
                    if mathpix_fallback.is_configured and mathpix_fallback.enabled:
                        logger.info("OCR pipeline: pix2tex returned 0 usable, trying Mathpix fallback")
                        math_results = await mathpix_fallback.images_to_latex_batch(image_regions)

            # Merge results: add new MathExpressionResult for each usable LaTeX
            existing_positions = {e.position_order for e in parsed.math_expressions}
            base_pos = max(existing_positions, default=0)

            for _pos, mx_result in math_results:
                if mx_result.is_usable:
                    new_pos = base_pos + 1
                    base_pos = new_pos
                    parsed.math_expressions.append(
                        MathExpressionResult(
                            original_notation=mx_result.raw_text or mx_result.latex or "",
                            latex_representation=mx_result.latex or "",
                            position_order=new_pos,
                            block_index=0,  # image region, not tied to a text block
                            conversion_confidence=mx_result.confidence,
                        )
                    )
                    math_images_resolved += 1

            engine_label = engine if engine != "auto" else (
                math_results[0][1].engine if math_results else "pix2tex"
            )
            ocr_method = f"gcv+{engine_label}" if math_images_resolved > 0 else "gcv_only"
            parsed.ocr_used = ocr_method
        else:
            ocr_method = "gcv_only"
            parsed.ocr_used = "gcv"
    else:
        parsed.ocr_used = "gcv"

    logger.info(
        "OCR pipeline complete: method=%s math_images=%d/%d",
        ocr_method,
        math_images_resolved,
        math_images_found,
    )

    return OcrPipelineResult(
        parsed_document=parsed,
        pages_ocr_ok=pages_ok,
        math_images_found=math_images_found,
        math_images_resolved=math_images_resolved,
        ocr_method=ocr_method,
    )
