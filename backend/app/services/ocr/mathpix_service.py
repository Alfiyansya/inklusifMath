"""
Mathpix API Service — Convert math formula images to LaTeX.

Mathpix is specialised for math recognition (far better than GCV for formulas).
API: https://docs.mathpix.com/

Workflow:
  1. Receive an image (PNG bytes) containing a math formula
  2. POST to https://api.mathpix.com/v3/text or /v3/latex
  3. Return the LaTeX string

Environment variables:
  MATHPIX_APP_ID      Mathpix application ID (required)
  MATHPIX_APP_KEY     Mathpix application key (required)
  MATHPIX_ENABLED     Set to 'false' to disable (default: true)

Cost management:
  - We only call Mathpix for images where GCV text is empty or mostly non-ASCII
  - Max 1 image per math expression (cropped region)
  - Response includes confidence — below 0.5 we fall back to GCV text
"""

from __future__ import annotations

import asyncio
import logging
import os

import httpx

from app.services.ocr.math_ocr_result import MathOcrResult

logger = logging.getLogger(__name__)

# Backward-compat alias — callers can still use MathpixResult
MathpixResult = MathOcrResult

_MATHPIX_ENDPOINT = "https://api.mathpix.com/v3/text"
_MATHPIX_ENABLED = os.getenv("MATHPIX_ENABLED", "true").lower() != "false"
_MATHPIX_TIMEOUT = 15.0  # seconds


class MathpixService:
    """
    Async client for the Mathpix text/latex API.

    Converts images of math formulas to LaTeX strings.
    Returns None on failure — callers must handle missing LaTeX gracefully.
    """

    def __init__(
        self,
        app_id: str | None = None,
        app_key: str | None = None,
        enabled: bool = _MATHPIX_ENABLED,
    ) -> None:
        self.app_id = app_id or os.getenv("MATHPIX_APP_ID", "")
        self.app_key = app_key or os.getenv("MATHPIX_APP_KEY", "")
        self.enabled = enabled

    @property
    def is_configured(self) -> bool:
        """True if both credentials are set."""
        return bool(self.app_id and self.app_key)

    async def image_to_latex(self, image_bytes: bytes) -> MathpixResult:
        """
        Send a PNG image to Mathpix and return the extracted LaTeX.

        Args:
            image_bytes: PNG or JPEG image bytes containing a math formula.

        Returns:
            MathpixResult with latex and confidence.
        """
        if not self.enabled:
            logger.debug("Mathpix disabled — skipping")
            return MathpixResult(latex=None, confidence=0.0, raw_text=None, engine="mathpix")

        if not self.is_configured:
            logger.warning(
                "Mathpix credentials not set (MATHPIX_APP_ID / MATHPIX_APP_KEY)"
            )
            return MathpixResult(
                latex=None,
                confidence=0.0,
                raw_text=None,
                error="credentials_missing",
                engine="mathpix",
            )

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._call_mathpix_sync, image_bytes
        )

    def _call_mathpix_sync(self, image_bytes: bytes) -> MathpixResult:
        """Synchronous HTTP call — runs in thread executor."""
        import base64

        b64 = base64.b64encode(image_bytes).decode("ascii")
        payload = {
            "src": f"data:image/png;base64,{b64}",
            "formats": ["latex_simplified", "text"],
            "math_inline_delimiters": ["$", "$"],
            "math_display_delimiters": ["$$", "$$"],
        }
        headers = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=_MATHPIX_TIMEOUT) as client:
                resp = client.post(
                    _MATHPIX_ENDPOINT, json=payload, headers=headers
                )
            resp.raise_for_status()
            data = resp.json()
        except httpx.TimeoutException:
            logger.warning("Mathpix API timeout after %.1fs", _MATHPIX_TIMEOUT)
            return MathpixResult(
                latex=None, confidence=0.0, raw_text=None, error="timeout", engine="mathpix"
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Mathpix API error: %s", exc)
            return MathpixResult(
                latex=None, confidence=0.0, raw_text=None, error=str(exc), engine="mathpix"
            )

        # Parse response
        latex = data.get("latex_simplified") or data.get("latex_styled")
        text = data.get("text")
        confidence = float(data.get("confidence", 0.0))

        if not latex and text:
            # Mathpix returns text when it can't produce clean LaTeX
            latex = None  # mark as not usable as math

        logger.debug(
            "Mathpix result: confidence=%.2f latex_len=%d",
            confidence,
            len(latex) if latex else 0,
        )
        return MathpixResult(latex=latex, confidence=confidence, raw_text=text, engine="mathpix")

    async def images_to_latex_batch(
        self,
        images: list[tuple[int, bytes]],
    ) -> list[tuple[int, MathpixResult]]:
        """
        Process a batch of (position_order, image_bytes) pairs concurrently.

        Returns list of (position_order, MathpixResult) in input order.
        Concurrency: max 3 parallel requests (Mathpix rate limit for free tier).
        """
        semaphore = asyncio.Semaphore(3)

        async def _process_one(pos: int, img: bytes) -> tuple[int, MathpixResult]:
            async with semaphore:
                result = await self.image_to_latex(img)
                return pos, result

        tasks = [_process_one(pos, img) for pos, img in images]
        return await asyncio.gather(*tasks)
