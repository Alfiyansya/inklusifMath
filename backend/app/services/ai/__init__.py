"""
AI services package.

Exports:
    AiClarifier     — Generates verbal narrations using Gemini 2.0 Flash
    NarrationResult — Result dataclass from clarifier
"""

from app.services.ai.clarifier import AiClarifier, NarrationResult

__all__ = ["AiClarifier", "NarrationResult"]
