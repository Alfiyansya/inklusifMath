"""
Tests for Pix2TexService (free, self-hosted math formula OCR)
and MathOcrResult shared dataclass.

All pix2tex model calls are mocked — no actual model download needed.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ── MathOcrResult tests ───────────────────────────────────────────────────────

class TestMathOcrResult:
    def test_is_usable_good_result(self):
        from app.services.ocr.math_ocr_result import MathOcrResult

        r = MathOcrResult(latex=r"x^2 + y^2", confidence=0.85, raw_text="x squared", engine="pix2tex")
        assert r.is_usable is True

    def test_is_usable_low_confidence(self):
        from app.services.ocr.math_ocr_result import MathOcrResult

        r = MathOcrResult(latex=r"x^2", confidence=0.3, raw_text="x^2", engine="pix2tex")
        assert r.is_usable is False

    def test_is_usable_no_latex(self):
        from app.services.ocr.math_ocr_result import MathOcrResult

        r = MathOcrResult(latex=None, confidence=0.8, raw_text="text", engine="pix2tex")
        assert r.is_usable is False

    def test_engine_field_default(self):
        from app.services.ocr.math_ocr_result import MathOcrResult

        r = MathOcrResult(latex="x", confidence=0.9, raw_text="x")
        assert r.engine == "unknown"

    def test_engine_field_pix2tex(self):
        from app.services.ocr.math_ocr_result import MathOcrResult

        r = MathOcrResult(latex="x", confidence=0.85, raw_text="x", engine="pix2tex")
        assert r.engine == "pix2tex"

    def test_engine_field_mathpix(self):
        from app.services.ocr.math_ocr_result import MathOcrResult

        r = MathOcrResult(latex="x", confidence=0.95, raw_text="x", engine="mathpix")
        assert r.engine == "mathpix"

    def test_backward_compat_mathpix_result_alias(self):
        """MathpixResult is now an alias for MathOcrResult."""
        from app.services.ocr.mathpix_service import MathpixResult
        from app.services.ocr.math_ocr_result import MathOcrResult

        assert MathpixResult is MathOcrResult


# ── Pix2TexService tests ─────────────────────────────────────────────────────

class TestPix2TexServiceDisabled:
    @pytest.mark.asyncio
    async def test_disabled_returns_empty(self):
        from app.services.ocr.pix2tex_service import Pix2TexService

        svc = Pix2TexService(enabled=False)
        result = await svc.image_to_latex(b"fake image bytes")

        assert result.latex is None
        assert result.confidence == 0.0
        assert result.engine == "pix2tex"

    def test_is_configured_when_enabled(self):
        from app.services.ocr.pix2tex_service import Pix2TexService

        svc = Pix2TexService(enabled=True)
        assert svc.is_configured is True

    def test_is_configured_when_disabled(self):
        from app.services.ocr.pix2tex_service import Pix2TexService

        svc = Pix2TexService(enabled=False)
        assert svc.is_configured is False


class TestPix2TexServiceModelNotAvailable:
    @pytest.mark.asyncio
    async def test_model_unavailable_returns_error(self):
        from app.services.ocr.pix2tex_service import Pix2TexService

        svc = Pix2TexService(enabled=True)

        with patch("app.services.ocr.pix2tex_service._get_model", return_value=None):
            result = await svc.image_to_latex(b"fake image bytes")

        assert result.latex is None
        assert result.error == "model_not_available"
        assert result.engine == "pix2tex"


class TestPix2TexServicePrediction:
    @pytest.mark.asyncio
    async def test_successful_prediction(self):
        from app.services.ocr.pix2tex_service import Pix2TexService

        mock_model = MagicMock()
        mock_model.return_value = r"x^{2}+y^{2}=r^{2}"

        mock_image = MagicMock()

        svc = Pix2TexService(enabled=True)

        with patch("app.services.ocr.pix2tex_service._get_model", return_value=mock_model):
            with patch("PIL.Image.open") as mock_open:
                mock_open.return_value.convert.return_value = mock_image
                result = await svc.image_to_latex(b"fake PNG bytes")

        assert result.latex == r"x^{2}+y^{2}=r^{2}"
        assert result.confidence == 0.85
        assert result.engine == "pix2tex"
        assert result.is_usable is True

    @pytest.mark.asyncio
    async def test_strips_dollar_signs(self):
        from app.services.ocr.pix2tex_service import Pix2TexService

        mock_model = MagicMock()
        mock_model.return_value = "$x^2 + 1$"

        svc = Pix2TexService(enabled=True)

        with patch("app.services.ocr.pix2tex_service._get_model", return_value=mock_model):
            with patch("PIL.Image.open") as mock_open:
                mock_open.return_value.convert.return_value = MagicMock()
                result = await svc.image_to_latex(b"image bytes")

        assert result.latex == "x^2 + 1"

    @pytest.mark.asyncio
    async def test_strips_double_dollar_signs(self):
        from app.services.ocr.pix2tex_service import Pix2TexService

        mock_model = MagicMock()
        mock_model.return_value = "$$\\frac{1}{2}$$"

        svc = Pix2TexService(enabled=True)

        with patch("app.services.ocr.pix2tex_service._get_model", return_value=mock_model):
            with patch("PIL.Image.open") as mock_open:
                mock_open.return_value.convert.return_value = MagicMock()
                result = await svc.image_to_latex(b"image bytes")

        assert result.latex == "\\frac{1}{2}"

    @pytest.mark.asyncio
    async def test_empty_output_returns_error(self):
        from app.services.ocr.pix2tex_service import Pix2TexService

        mock_model = MagicMock()
        mock_model.return_value = ""

        svc = Pix2TexService(enabled=True)

        with patch("app.services.ocr.pix2tex_service._get_model", return_value=mock_model):
            with patch("PIL.Image.open") as mock_open:
                mock_open.return_value.convert.return_value = MagicMock()
                result = await svc.image_to_latex(b"image bytes")

        assert result.latex is None
        assert result.error == "empty_output"
        assert result.is_usable is False

    @pytest.mark.asyncio
    async def test_exception_returns_error(self):
        from app.services.ocr.pix2tex_service import Pix2TexService

        mock_model = MagicMock()
        mock_model.side_effect = RuntimeError("GPU out of memory")

        svc = Pix2TexService(enabled=True)

        with patch("app.services.ocr.pix2tex_service._get_model", return_value=mock_model):
            with patch("PIL.Image.open") as mock_open:
                mock_open.return_value.convert.return_value = MagicMock()
                result = await svc.image_to_latex(b"image bytes")

        assert result.latex is None
        assert "GPU out of memory" in result.error
        assert result.engine == "pix2tex"


class TestPix2TexServiceBatch:
    @pytest.mark.asyncio
    async def test_batch_processes_all_images(self):
        from app.services.ocr.pix2tex_service import Pix2TexService

        mock_model = MagicMock()
        mock_model.side_effect = [r"x^2", r"\frac{a}{b}", r"\sqrt{n}"]

        svc = Pix2TexService(enabled=True)

        images = [(1, b"img1"), (2, b"img2"), (3, b"img3")]

        with patch("app.services.ocr.pix2tex_service._get_model", return_value=mock_model):
            with patch("PIL.Image.open") as mock_open:
                mock_open.return_value.convert.return_value = MagicMock()
                results = await svc.images_to_latex_batch(images)

        assert len(results) == 3
        assert results[0][0] == 1
        assert results[0][1].latex == r"x^2"
        assert results[1][1].latex == r"\frac{a}{b}"
        assert results[2][1].latex == r"\sqrt{n}"

    @pytest.mark.asyncio
    async def test_batch_empty_list(self):
        from app.services.ocr.pix2tex_service import Pix2TexService

        svc = Pix2TexService(enabled=True)
        results = await svc.images_to_latex_batch([])
        assert results == []


# ── Pipeline engine selection tests ──────────────────────────────────────────

class TestPipelineEngineSelection:
    def test_config_default_is_pix2tex(self):
        from app.core.config import settings

        assert settings.MATH_OCR_ENGINE == "pix2tex"
