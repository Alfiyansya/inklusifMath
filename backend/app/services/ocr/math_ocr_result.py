"""
Shared result dataclass for math formula OCR engines.

Used by both Pix2TexService (free, self-hosted) and MathpixService (paid API).
Provides a unified interface so the OCR pipeline can swap engines transparently.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MathOcrResult:
    """Result from a math OCR engine for a single formula image."""

    latex: str | None
    """LaTeX string extracted, or None if failed/low confidence."""

    confidence: float
    """0–1 confidence score. pix2tex: fixed 0.85 on success. Mathpix: from API."""

    raw_text: str | None
    """Human-readable text (alternative to LaTeX). May be None."""

    error: str | None = None
    """Error message if the recognition failed."""

    engine: str = field(default="unknown")
    """Which engine produced this result: 'pix2tex' | 'mathpix' | 'unknown'."""

    @property
    def is_usable(self) -> bool:
        """True if we have a LaTeX string that passes minimum confidence."""
        return self.latex is not None and self.confidence >= 0.5
