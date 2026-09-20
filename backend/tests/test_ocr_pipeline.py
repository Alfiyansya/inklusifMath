"""
Tests for the OCR pipeline: GcvOcrService, MathpixService, and run_ocr_pipeline.

All external calls (Google Cloud Vision, Mathpix API, fitz PDF rendering) are mocked.
Tests verify:
  1. GcvOcrService — enabled/disabled, per-page text extraction, error handling
  2. MathpixService — credentials check, image_to_latex, batch processing, timeout/errors
  3. _gcv_text_to_parsed_document — heading detection, inline math, field mapping
  4. run_ocr_pipeline — integration: GCV → parse → Mathpix → OcrPipelineResult
  5. document_service.run_ocr_if_needed — hook: pending_ocr triggers OCR, others skip
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── Helpers ───────────────────────────────────────────────────────────────────

FAKE_PDF = b"%PDF-1.4 fake content"
FAKE_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100  # minimal PNG header


def _make_gcv_response(text: str = "Hello math $x^2$", error: str = "") -> dict:
    return {"full_text": text, "error": error}


# ── GcvOcrService tests ───────────────────────────────────────────────────────

class TestGcvOcrService:
    @pytest.mark.asyncio
    async def test_disabled_returns_empty_result(self):
        from app.services.ocr.gcv_service import GcvOcrService

        svc = GcvOcrService(enabled=False)
        result = await svc.extract_text_from_pdf(FAKE_PDF)

        assert result.success is False
        assert result.full_text == ""
        assert result.pages == []

    @pytest.mark.asyncio
    async def test_extracts_text_per_page(self):
        from app.services.ocr.gcv_service import GcvOcrService

        svc = GcvOcrService(enabled=True)

        with patch(
            "app.services.ocr.gcv_service._render_page_to_png",
            return_value=FAKE_PNG,
        ), patch(
            "app.services.ocr.gcv_service._call_gcv_sync",
            return_value=_make_gcv_response("Aljabar dasar $ax + b = 0$"),
        ), patch(
            "fitz.open",
        ) as mock_fitz:
            mock_doc = MagicMock()
            mock_doc.page_count = 2
            mock_doc.__getitem__ = MagicMock()
            mock_fitz.return_value.__enter__ = MagicMock(return_value=mock_doc)
            mock_fitz.return_value.__exit__ = MagicMock(return_value=False)
            mock_fitz.return_value = mock_doc

            result = await svc.extract_text_from_pdf(FAKE_PDF)

        # 2 pages processed
        assert len(result.pages) == 2
        assert result.success is True
        # full_text is joined with \f
        assert "Aljabar dasar" in result.full_text

    @pytest.mark.asyncio
    async def test_handles_page_error_gracefully(self):
        from app.services.ocr.gcv_service import GcvOcrService, OcrPage

        svc = GcvOcrService(enabled=True)

        with patch(
            "app.services.ocr.gcv_service._render_page_to_png",
            side_effect=RuntimeError("render failed"),
        ), patch("fitz.open") as mock_fitz:
            mock_doc = MagicMock()
            mock_doc.page_count = 1
            mock_fitz.return_value = mock_doc

            result = await svc.extract_text_from_pdf(FAKE_PDF)

        assert result.success is False
        assert len(result.pages) == 1
        assert result.pages[0].error is not None

    @pytest.mark.asyncio
    async def test_respects_max_pages_cap(self):
        from app.services.ocr.gcv_service import GcvOcrService

        svc = GcvOcrService(enabled=True)

        with patch(
            "app.services.ocr.gcv_service._render_page_to_png",
            return_value=FAKE_PNG,
        ), patch(
            "app.services.ocr.gcv_service._call_gcv_sync",
            return_value=_make_gcv_response("text"),
        ), patch("fitz.open") as mock_fitz:
            mock_doc = MagicMock()
            mock_doc.page_count = 100  # large PDF
            mock_fitz.return_value = mock_doc

            result = await svc.extract_text_from_pdf(FAKE_PDF, max_pages=3)

        assert len(result.pages) == 3  # capped at max_pages

    @pytest.mark.asyncio
    async def test_extract_single_image_disabled(self):
        from app.services.ocr.gcv_service import GcvOcrService

        svc = GcvOcrService(enabled=False)
        text = await svc.extract_text_from_image(FAKE_PNG)
        assert text == ""

    @pytest.mark.asyncio
    async def test_extract_single_image_success(self):
        from app.services.ocr.gcv_service import GcvOcrService

        svc = GcvOcrService(enabled=True)
        with patch(
            "app.services.ocr.gcv_service._call_gcv_sync",
            return_value=_make_gcv_response("x squared"),
        ):
            text = await svc.extract_text_from_image(FAKE_PNG)
        assert text == "x squared"

    def test_gcv_result_success_flag(self):
        from app.services.ocr.gcv_service import GcvOcrResult, OcrPage

        pages = [OcrPage(page_index=0, text="hello"), OcrPage(page_index=1, text="")]
        result = GcvOcrResult(pages=pages, full_text="hello", success=True)
        assert result.success is True

    def test_ocr_page_with_error(self):
        from app.services.ocr.gcv_service import OcrPage

        page = OcrPage(page_index=2, text="", error="GCV returned 503")
        assert page.error == "GCV returned 503"
        assert page.text == ""


# ── MathpixService tests ──────────────────────────────────────────────────────

class TestMathpixService:
    def test_disabled_returns_no_latex(self):
        from app.services.ocr.mathpix_service import MathpixService

        svc = MathpixService(enabled=False)
        result = asyncio.get_event_loop().run_until_complete(
            svc.image_to_latex(FAKE_PNG)
        )
        assert result.latex is None
        assert result.confidence == 0.0

    def test_missing_credentials_returns_error(self):
        from app.services.ocr.mathpix_service import MathpixService

        svc = MathpixService(app_id="", app_key="", enabled=True)
        assert svc.is_configured is False
        result = asyncio.get_event_loop().run_until_complete(
            svc.image_to_latex(FAKE_PNG)
        )
        assert result.latex is None
        assert result.error == "credentials_missing"

    def test_is_configured_true(self):
        from app.services.ocr.mathpix_service import MathpixService

        svc = MathpixService(app_id="id123", app_key="key456")
        assert svc.is_configured is True

    def test_mathpix_result_is_usable(self):
        from app.services.ocr.mathpix_service import MathpixResult

        good = MathpixResult(latex=r"x^2 + y^2", confidence=0.9, raw_text="x squared")
        assert good.is_usable is True

        low_conf = MathpixResult(latex=r"x^2", confidence=0.3, raw_text="x^2")
        assert low_conf.is_usable is False

        no_latex = MathpixResult(latex=None, confidence=0.8, raw_text="text")
        assert no_latex.is_usable is False

    @pytest.mark.asyncio
    async def test_image_to_latex_success(self):
        from app.services.ocr.mathpix_service import MathpixService

        svc = MathpixService(app_id="id", app_key="key", enabled=True)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "latex_simplified": r"\frac{a}{b}",
            "text": "a over b",
            "confidence": 0.95,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.post.return_value = (
                mock_response
            )
            result = await svc.image_to_latex(FAKE_PNG)

        assert result.latex == r"\frac{a}{b}"
        assert result.confidence == pytest.approx(0.95)
        assert result.is_usable is True

    @pytest.mark.asyncio
    async def test_image_to_latex_timeout(self):
        import httpx
        from app.services.ocr.mathpix_service import MathpixService

        svc = MathpixService(app_id="id", app_key="key", enabled=True)

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.post.side_effect = (
                httpx.TimeoutException("timeout")
            )
            result = await svc.image_to_latex(FAKE_PNG)

        assert result.latex is None
        assert result.error == "timeout"

    @pytest.mark.asyncio
    async def test_batch_processes_multiple_images(self):
        from app.services.ocr.mathpix_service import MathpixService, MathpixResult

        svc = MathpixService(app_id="id", app_key="key", enabled=True)

        async def fake_image_to_latex(img: bytes) -> MathpixResult:
            return MathpixResult(
                latex=r"x^2", confidence=0.9, raw_text="x squared"
            )

        with patch.object(svc, "image_to_latex", side_effect=fake_image_to_latex):
            images = [(1, FAKE_PNG), (2, FAKE_PNG), (3, FAKE_PNG)]
            results = await svc.images_to_latex_batch(images)

        assert len(results) == 3
        positions = [r[0] for r in results]
        assert positions == [1, 2, 3]
        for _pos, res in results:
            assert res.latex == r"x^2"


# ── _gcv_text_to_parsed_document tests ───────────────────────────────────────

class TestGcvTextToParsedDocument:
    def _call(self, text: str, title: str = "Test") -> "ParsedDocument":
        from app.services.ocr.ocr_pipeline import _gcv_text_to_parsed_document

        return _gcv_text_to_parsed_document(text, title)

    def test_empty_text_returns_empty_parsed_document(self):
        result = self._call("")
        assert result.title == "Test"
        assert result.file_type == "pdf"
        assert result.content_blocks == []
        assert result.math_expressions == []

    def test_single_paragraph(self):
        result = self._call("Ini adalah paragraf biasa tentang matematika.")
        assert len(result.content_blocks) == 1
        from app.services.parsing.models import BlockType
        assert result.content_blocks[0].block_type == BlockType.PARAGRAPH

    def test_detects_uppercase_heading(self):
        result = self._call("BAB I PENDAHULUAN\nIni adalah isi bab.")
        from app.services.parsing.models import BlockType
        headings = [
            b for b in result.content_blocks if b.block_type == BlockType.HEADING2
        ]
        assert len(headings) >= 1
        assert "PENDAHULUAN" in headings[0].text or "BAB" in headings[0].text

    def test_detects_numbered_section(self):
        result = self._call("1. Definisi\nIni definisi matematis.")
        from app.services.parsing.models import BlockType
        headings = [
            b for b in result.content_blocks if b.block_type == BlockType.HEADING2
        ]
        assert len(headings) >= 1

    def test_extracts_inline_latex_math(self):
        result = self._call("Persamaan linear adalah $ax + b = 0$ dengan koefisien $a$.")
        assert len(result.math_expressions) >= 1
        latexes = [e.latex_representation for e in result.math_expressions]
        assert any("ax + b" in l or "ax" in l for l in latexes)

    def test_ocr_used_set_to_gcv(self):
        result = self._call("Teks biasa")
        assert result.ocr_used == "gcv"

    def test_raw_structure_blocks_present(self):
        result = self._call("Teks dengan $x^2$")
        assert "blocks" in result.raw_structure
        assert len(result.raw_structure["blocks"]) >= 1

    def test_block_index_monotonically_increases(self):
        text = "Baris satu\nBaris dua\nBaris tiga"
        result = self._call(text)
        indices = [b.index for b in result.content_blocks]
        for i in range(len(indices) - 1):
            assert indices[i] < indices[i + 1]

    def test_skips_empty_lines(self):
        result = self._call("\n\n\nHanya satu baris\n\n\n")
        assert len(result.content_blocks) == 1


# ── run_ocr_pipeline integration tests ───────────────────────────────────────

class TestRunOcrPipeline:
    @pytest.mark.asyncio
    async def test_raises_ocr_pipeline_error_when_gcv_fails(self):
        from app.services.ocr.gcv_service import GcvOcrService, GcvOcrResult
        from app.services.ocr.mathpix_service import MathpixService
        from app.services.ocr.ocr_pipeline import OcrPipelineError, run_ocr_pipeline

        mock_gcv = MagicMock(spec=GcvOcrService)
        mock_gcv.extract_text_from_pdf = AsyncMock(
            return_value=GcvOcrResult(pages=[], full_text="", success=False)
        )
        mock_mathpix = MagicMock(spec=MathpixService)

        with pytest.raises(OcrPipelineError):
            await run_ocr_pipeline(
                FAKE_PDF, "Test", gcv_service=mock_gcv, mathpix_service=mock_mathpix
            )

    @pytest.mark.asyncio
    async def test_returns_result_with_gcv_only_when_no_math_images(self):
        from app.services.ocr.gcv_service import GcvOcrService, GcvOcrResult, OcrPage
        from app.services.ocr.mathpix_service import MathpixService
        from app.services.ocr.ocr_pipeline import run_ocr_pipeline

        page = OcrPage(page_index=0, text="Persamaan $x^2 + y^2 = r^2$")
        gcv_result = GcvOcrResult(pages=[page], full_text=page.text, success=True)

        mock_gcv = MagicMock(spec=GcvOcrService)
        mock_gcv.extract_text_from_pdf = AsyncMock(return_value=gcv_result)

        mock_mathpix = MagicMock(spec=MathpixService)
        mock_mathpix.is_configured = False
        mock_mathpix.enabled = False

        with patch(
            "app.services.ocr.ocr_pipeline._extract_math_image_regions",
            return_value=[],
        ):
            result = await run_ocr_pipeline(
                FAKE_PDF,
                "Test Doc",
                gcv_service=mock_gcv,
                mathpix_service=mock_mathpix,
            )

        assert result.pages_ocr_ok == 1
        assert result.math_images_found == 0
        assert result.ocr_method in ("gcv", "gcv_only")
        assert result.parsed_document.title == "Test Doc"
        assert result.parsed_document.ocr_used in ("gcv", "gcv_only")

    @pytest.mark.asyncio
    async def test_mathpix_enriches_math_expressions(self):
        from app.services.ocr.gcv_service import GcvOcrService, GcvOcrResult, OcrPage
        from app.services.ocr.mathpix_service import MathpixService, MathpixResult
        from app.services.ocr.ocr_pipeline import run_ocr_pipeline

        page = OcrPage(page_index=0, text="Teks biasa tanpa math")
        gcv_result = GcvOcrResult(pages=[page], full_text=page.text, success=True)

        mock_gcv = MagicMock(spec=GcvOcrService)
        mock_gcv.extract_text_from_pdf = AsyncMock(return_value=gcv_result)

        # Mathpix configured and returns good LaTeX
        mathpix_latex = MathpixResult(
            latex=r"\int_0^\infty e^{-x} dx", confidence=0.92, raw_text="integral"
        )
        mock_mathpix = MagicMock(spec=MathpixService)
        mock_mathpix.is_configured = True
        mock_mathpix.enabled = True
        mock_mathpix.images_to_latex_batch = AsyncMock(
            return_value=[(1, mathpix_latex)]
        )

        with patch(
            "app.services.ocr.ocr_pipeline._extract_math_image_regions",
            return_value=[(1, FAKE_PNG)],
        ):
            result = await run_ocr_pipeline(
                FAKE_PDF,
                "Kalkulus",
                gcv_service=mock_gcv,
                mathpix_service=mock_mathpix,
                math_engine="mathpix",
            )

        assert result.math_images_found == 1
        assert result.math_images_resolved == 1
        assert result.ocr_method == "gcv+mathpix"
        # ParsedDocument should have Mathpix expression
        latexes = [e.latex_representation for e in result.parsed_document.math_expressions]
        assert any(r"\int" in l for l in latexes)

    @pytest.mark.asyncio
    async def test_mathpix_low_confidence_not_added(self):
        from app.services.ocr.gcv_service import GcvOcrService, GcvOcrResult, OcrPage
        from app.services.ocr.mathpix_service import MathpixService, MathpixResult
        from app.services.ocr.ocr_pipeline import run_ocr_pipeline

        page = OcrPage(page_index=0, text="Teks")
        gcv_result = GcvOcrResult(pages=[page], full_text="Teks", success=True)

        mock_gcv = MagicMock(spec=GcvOcrService)
        mock_gcv.extract_text_from_pdf = AsyncMock(return_value=gcv_result)

        low_conf = MathpixResult(latex=r"x", confidence=0.3, raw_text="x")
        mock_mathpix = MagicMock(spec=MathpixService)
        mock_mathpix.is_configured = True
        mock_mathpix.enabled = True
        mock_mathpix.images_to_latex_batch = AsyncMock(
            return_value=[(1, low_conf)]
        )

        with patch(
            "app.services.ocr.ocr_pipeline._extract_math_image_regions",
            return_value=[(1, FAKE_PNG)],
        ):
            result = await run_ocr_pipeline(
                FAKE_PDF, "Doc", gcv_service=mock_gcv, mathpix_service=mock_mathpix,
                math_engine="mathpix",
            )

        assert result.math_images_resolved == 0
        assert result.ocr_method == "gcv_only"


# ── document_service.run_ocr_if_needed tests ─────────────────────────────────

class TestRunOcrIfNeeded:
    @pytest.mark.asyncio
    async def test_skips_digital_pdf(self):
        from app.services.document_service import run_ocr_if_needed
        from app.services.parsing.models import ParsedDocument

        digital = ParsedDocument(title="Digital", file_type="pdf", ocr_used="none")
        result = await run_ocr_if_needed(FAKE_PDF, digital, "Digital")

        # Should return the original document unchanged
        assert result is digital

    @pytest.mark.asyncio
    async def test_skips_docx(self):
        from app.services.document_service import run_ocr_if_needed
        from app.services.parsing.models import ParsedDocument

        docx = ParsedDocument(title="Word Doc", file_type="docx", ocr_used="none")
        result = await run_ocr_if_needed(FAKE_PDF, docx, "Word Doc")
        assert result is docx

    @pytest.mark.asyncio
    async def test_runs_ocr_for_pending_ocr(self):
        from app.services.document_service import run_ocr_if_needed
        from app.services.parsing.models import ParsedDocument
        from app.services.ocr.ocr_pipeline import OcrPipelineResult

        scanned = ParsedDocument(title="Scan", file_type="pdf", ocr_used="pending_ocr")
        enriched = ParsedDocument(title="Scan", file_type="pdf", ocr_used="gcv")

        mock_result = OcrPipelineResult(
            parsed_document=enriched,
            pages_ocr_ok=2,
            math_images_found=3,
            math_images_resolved=2,
            ocr_method="gcv+mathpix",
        )

        # Patch at the module where it is imported inside the function
        with patch(
            "app.services.ocr.ocr_pipeline.run_ocr_pipeline",
            AsyncMock(return_value=mock_result),
        ):
            # Also need to patch the import inside run_ocr_if_needed
            # Since it uses lazy import, we patch the ocr package export
            with patch(
                "app.services.ocr.run_ocr_pipeline",
                AsyncMock(return_value=mock_result),
            ):
                result = await run_ocr_if_needed(FAKE_PDF, scanned, "Scan")

        assert result is enriched
        assert result.ocr_used == "gcv"

    @pytest.mark.asyncio
    async def test_graceful_fallback_on_ocr_error(self):
        from app.services.document_service import run_ocr_if_needed
        from app.services.parsing.models import ParsedDocument

        scanned = ParsedDocument(title="Fail", file_type="pdf", ocr_used="pending_ocr")

        with patch(
            "app.services.ocr.run_ocr_pipeline",
            AsyncMock(side_effect=RuntimeError("GCV down")),
        ):
            result = await run_ocr_if_needed(FAKE_PDF, scanned, "Fail")

        # Should return original (pending_ocr) — not raise
        assert result is scanned
        assert result.ocr_used == "pending_ocr"
