"""
pix2tex (LaTeX-OCR) Service — Free, self-hosted math formula → LaTeX.

Uses the pix2tex library (MIT license, ~170MB model) to recognise
mathematical formulas from cropped images and return LaTeX strings.

Model is downloaded automatically on first use (one-time, cached).
All inference runs locally — no data leaves the machine.

Installation:
  pip install pix2tex

Environment variables:
  PIX2TEX_ENABLED     Set to 'false' to disable (default: true)
"""

from __future__ import annotations

import asyncio
import logging
import os
from functools import lru_cache
from typing import TYPE_CHECKING

from app.services.ocr.math_ocr_result import MathOcrResult

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

_PIX2TEX_ENABLED = os.getenv("PIX2TEX_ENABLED", "true").lower() != "false"


@lru_cache(maxsize=1)
def _get_model():
    """
    Lazy-load the LatexOCR model (singleton).

    First call downloads weights (~170MB) if not cached.
    Subsequent calls return the cached model instantly.
    """
    try:
        from pix2tex.cli import LatexOCR

        logger.info("Loading pix2tex (LaTeX-OCR) model...")
        model = LatexOCR()
        logger.info("pix2tex model loaded successfully")
        return model
    except ImportError:
        logger.error(
            "pix2tex not installed. Run: pip install pix2tex"
        )
        return None
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to load pix2tex model: %s", exc)
        return None


class Pix2TexService:
    """
    Self-hosted math formula OCR using pix2tex (LaTeX-OCR).

    Free, MIT-licensed, no API key needed.
    Returns MathOcrResult with engine='pix2tex'.
    """

    def __init__(self, enabled: bool = _PIX2TEX_ENABLED) -> None:
        self.enabled = enabled

    @property
    def is_configured(self) -> bool:
        """True if pix2tex is enabled (no credentials needed)."""
        return self.enabled

    async def image_to_latex(self, image_bytes: bytes) -> MathOcrResult:
        """
        Convert an image of a math formula to LaTeX.

        Args:
            image_bytes: PNG or JPEG image bytes containing a math formula.

        Returns:
            MathOcrResult with engine='pix2tex'.
        """
        if not self.enabled:
            logger.debug("pix2tex disabled — skipping")
            return MathOcrResult(
                latex=None, confidence=0.0, raw_text=None, engine="pix2tex"
            )

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._predict_sync, image_bytes
        )

    def _predict_sync(self, image_bytes: bytes) -> MathOcrResult:
        """Synchronous prediction — runs in thread executor."""
        import io

        from PIL import Image

        model = _get_model()
        if model is None:
            return MathOcrResult(
                latex=None,
                confidence=0.0,
                raw_text=None,
                error="model_not_available",
                engine="pix2tex",
            )

        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            latex = model(img)

            # pix2tex returns raw LaTeX string (no confidence score natively)
            # We assign 0.85 fixed confidence when successful
            if latex and latex.strip():
                # Clean up: remove wrapping $ or $$ if present
                cleaned = latex.strip()
                if cleaned.startswith("$$") and cleaned.endswith("$$"):
                    cleaned = cleaned[2:-2].strip()
                elif cleaned.startswith("$") and cleaned.endswith("$"):
                    cleaned = cleaned[1:-1].strip()

                logger.debug(
                    "pix2tex result: latex_len=%d", len(cleaned)
                )
                return MathOcrResult(
                    latex=cleaned,
                    confidence=0.85,
                    raw_text=cleaned,
                    engine="pix2tex",
                )
            else:
                return MathOcrResult(
                    latex=None,
                    confidence=0.0,
                    raw_text=None,
                    error="empty_output",
                    engine="pix2tex",
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("pix2tex prediction failed: %s", exc)
            return MathOcrResult(
                latex=None,
                confidence=0.0,
                raw_text=None,
                error=str(exc),
                engine="pix2tex",
            )

    async def images_to_latex_batch(
        self,
        images: list[tuple[int, bytes]],
    ) -> list[tuple[int, MathOcrResult]]:
        """
        Process a batch of (position_order, image_bytes) pairs.

        Unlike Mathpix (which needs semaphore for rate limits),
        pix2tex runs locally so we process sequentially (model is not thread-safe).

        Returns list of (position_order, MathOcrResult) in input order.
        """
        results: list[tuple[int, MathOcrResult]] = []
        for pos, img in images:
            result = await self.image_to_latex(img)
            results.append((pos, result))
        return results
