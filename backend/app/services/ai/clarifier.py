"""
AI Semantic Clarifier — generates verbal narrations for math expressions.

Uses Gemini 2.0 Flash via google-genai SDK with:
  - System prompt from Leksikon Matematika Baku (docs/leksikon_matematika_baku.md)
  - Batch processing (up to 20 expressions per API call) to reduce latency/cost
  - Single-expression fallback for retry logic
  - Confidence scoring based on narration quality heuristics
  - Graceful degradation: returns None on API error (teacher reviews manually)

Architecture:
  clarifier = AiClarifier()           # reads settings at construction
  results = await clarifier.clarify_batch(expressions)   # main entry point
  result  = await clarifier.clarify_single(expr)         # single fallback

Integration:
  - Called by document_service.generate_ai_narrations() after parsing
  - Results stored in MathExpression.ai_narration + status='ai_generated'
  - Teacher reviews via /documents/{id}/narrations endpoint
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass

from google import genai
from google.genai import types as genai_types

from app.core.config import settings
from app.services.ai.leksikon import (
    BATCH_PROMPT_TEMPLATE,
    SINGLE_PROMPT_TEMPLATE,
    SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)

# Max expressions per Gemini call (stays well within token budget)
_BATCH_SIZE = 20

# AI_001: Gemini timeout + retry config (TDD 10.7)
_GEMINI_TIMEOUT_SECONDS = 30    # per call timeout
_GEMINI_MAX_RETRIES = 2         # retry twice on timeout, then raise AI_001

# Gemini safety settings — math content, no harmful content expected
_SAFETY_SETTINGS = [
    genai_types.SafetySetting(
        category=genai_types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=genai_types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    ),
    genai_types.SafetySetting(
        category=genai_types.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=genai_types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    ),
]


@dataclass
class NarrationResult:
    """Result of narrating a single math expression."""
    position_order: int          # matches MathExpressionResult.position_order
    original_notation: str
    latex: str
    narration: str | None        # None = failed / API error
    confidence: float = 1.0      # 0.0–1.0 based on output heuristics


# ── Custom AI error exceptions ────────────────────────────────────────────────

class GeminiTimeoutError(Exception):
    """AI_001: Gemini did not respond within timeout after all retries."""


class GeminiUnavailableError(Exception):
    """AI_002: Gemini is down or returned a non-recoverable error."""


class AiClarifier:
    """
    Generates verbal narrations for math expressions using Gemini 2.0 Flash.

    Usage:
        clarifier = AiClarifier()
        results = await clarifier.clarify_batch(expressions)

    Where `expressions` is a list of dicts with keys:
        - position_order: int
        - original_notation: str
        - latex: str  (may be empty if conversion failed)
    """

    def __init__(self) -> None:
        self._api_key = settings.GEMINI_API_KEY
        self._model = settings.GEMINI_MODEL
        self._client: genai.Client | None = None

    def _get_client(self) -> genai.Client:
        """Lazy-initialize the Gemini client (avoids issues at import time)."""
        if self._client is None:
            if not self._api_key:
                raise ValueError(
                    "GEMINI_API_KEY not set. Add it to backend/.env"
                )
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    async def _call_gemini_with_retry(
        self,
        prompt: str,
        max_output_tokens: int,
        context: str = "",
    ) -> str:
        """
        Call Gemini with timeout + retry logic.

        Implements:
          - AI_001: timeout > 30s → retry up to 2 times, then raise GeminiTimeoutError
          - AI_002: Gemini down (non-timeout errors) → raises GeminiUnavailableError

        Args:
            prompt: The user prompt to send.
            max_output_tokens: Token budget for response.
            context: Human-readable label for logging (e.g., "batch(5 items)").

        Returns:
            Raw text response from Gemini.

        Raises:
            GeminiTimeoutError: All retries exhausted due to timeouts.
            GeminiUnavailableError: Non-timeout API error (e.g., 503, network down).
        """
        client = self._get_client()
        config = genai_types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.1,
            max_output_tokens=max_output_tokens,
            safety_settings=_SAFETY_SETTINGS,
        )

        last_exc: Exception | None = None
        for attempt in range(1, _GEMINI_MAX_RETRIES + 1):
            try:
                # Run synchronous Gemini SDK call in executor to support asyncio.timeout
                loop = asyncio.get_running_loop()
                async with asyncio.timeout(_GEMINI_TIMEOUT_SECONDS):
                    response = await loop.run_in_executor(
                        None,
                        lambda: client.models.generate_content(
                            model=self._model,
                            contents=prompt,
                            config=config,
                        ),
                    )
                return self._extract_text(response)

            except TimeoutError:
                logger.warning(
                    "[AI_001] Gemini timeout (attempt %d/%d) for %s",
                    attempt, _GEMINI_MAX_RETRIES, context,
                )
                last_exc = TimeoutError(
                    f"Gemini timed out after {_GEMINI_TIMEOUT_SECONDS}s (attempt {attempt})"
                )
                # Brief pause before retry
                await asyncio.sleep(1.0 * attempt)

            except Exception as exc:
                # Non-timeout error (network down, 503, quota, etc.) — don't retry
                logger.error("[AI_002] Gemini unavailable for %s: %s", context, exc)
                raise GeminiUnavailableError(str(exc)) from exc

        # All retries exhausted
        raise GeminiTimeoutError(
            f"Gemini timeout after {_GEMINI_MAX_RETRIES} retries for {context}"
        ) from last_exc

    # ── Public API ────────────────────────────────────────────────────────────

    async def clarify_batch(
        self,
        expressions: list[dict],
    ) -> list[NarrationResult]:
        """
        Generate narrations for a list of math expressions.

        Processes in chunks of _BATCH_SIZE to stay within Gemini token limits.
        Falls back to single-expression calls if batch parsing fails.

        Args:
            expressions: list of {"position_order", "original_notation", "latex"}

        Returns:
            list[NarrationResult] in same order as input
        """
        if not expressions:
            return []

        results: list[NarrationResult] = []

        # Process in batches
        for chunk_start in range(0, len(expressions), _BATCH_SIZE):
            chunk = expressions[chunk_start : chunk_start + _BATCH_SIZE]
            chunk_results = await self._clarify_chunk(chunk)
            results.extend(chunk_results)

        return results

    async def clarify_single(self, expression: dict) -> NarrationResult:
        """
        Generate narration for a single expression.
        Used as fallback when batch fails for a specific item.

        Args:
            expression: {"position_order", "original_notation", "latex"}
        """
        position = expression.get("position_order", 0)
        original = expression.get("original_notation", "")
        latex = expression.get("latex", "") or original

        try:
            prompt = SINGLE_PROMPT_TEMPLATE.format(
                latex=latex,
                original=original,
            )
            narration = await self._call_gemini_with_retry(
                prompt=prompt,
                max_output_tokens=200,
                context=f"single(position={position})",
            )
            confidence = self._score_narration(narration, latex)

            return NarrationResult(
                position_order=position,
                original_notation=original,
                latex=latex,
                narration=narration,
                confidence=confidence,
            )

        except (GeminiTimeoutError, GeminiUnavailableError):
            # Re-raise — let caller decide whether to degrade gracefully
            raise

        except Exception as exc:
            logger.warning(
                "Single clarify failed for position %d: %s", position, exc
            )
            return NarrationResult(
                position_order=position,
                original_notation=original,
                latex=latex,
                narration=None,
                confidence=0.0,
            )

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _clarify_chunk(self, chunk: list[dict]) -> list[NarrationResult]:
        """Process one chunk via a single Gemini batch call."""
        # Build JSON input for Gemini
        expressions_json = json.dumps(
            [
                {
                    "index": i,
                    "latex": expr.get("latex", "") or expr.get("original_notation", ""),
                    "original": expr.get("original_notation", ""),
                }
                for i, expr in enumerate(chunk)
            ],
            ensure_ascii=False,
            indent=2,
        )

        prompt = BATCH_PROMPT_TEMPLATE.format(
            count=len(chunk),
            expressions_json=expressions_json,
        )

        try:
            raw_text = await self._call_gemini_with_retry(
                prompt=prompt,
                max_output_tokens=100 * len(chunk),
                context=f"batch({len(chunk)} items)",
            )
            parsed = self._parse_batch_response(raw_text, len(chunk))
            return self._build_results(chunk, parsed)

        except (GeminiTimeoutError, GeminiUnavailableError) as exc:
            # Propagate AI errors — caller (clarify_batch) may log and degrade
            raise

        except Exception as exc:
            logger.error("Batch clarify failed (%d items): %s", len(chunk), exc)
            # Fallback: try each individually
            results = []
            for expr in chunk:
                result = await self.clarify_single(expr)
                results.append(result)
            return results

    def _parse_batch_response(
        self, raw_text: str, expected_count: int
    ) -> dict[int, str]:
        """
        Parse Gemini batch response (JSON array) into {index: narration} dict.
        Handles markdown fences and minor JSON formatting issues.
        """
        # Strip markdown code fences if present
        cleaned = re.sub(r"```(?:json)?\s*", "", raw_text).strip()
        cleaned = re.sub(r"```\s*$", "", cleaned).strip()

        try:
            data = json.loads(cleaned)
            result: dict[int, str] = {}
            for item in data:
                idx = item.get("index", -1)
                narasi = item.get("narasi", "") or item.get("narration", "")
                if isinstance(idx, int) and 0 <= idx < expected_count and narasi:
                    result[idx] = narasi.strip()
            return result
        except json.JSONDecodeError as exc:
            logger.warning("Batch response JSON parse failed: %s | raw: %s", exc, raw_text[:200])
            return {}

    def _build_results(
        self, chunk: list[dict], parsed: dict[int, str]
    ) -> list[NarrationResult]:
        """Map parsed narrations back to NarrationResult objects."""
        results = []
        for i, expr in enumerate(chunk):
            narration = parsed.get(i)
            latex = expr.get("latex", "") or expr.get("original_notation", "")
            confidence = self._score_narration(narration, latex) if narration else 0.0
            results.append(NarrationResult(
                position_order=expr.get("position_order", i + 1),
                original_notation=expr.get("original_notation", ""),
                latex=latex,
                narration=narration,
                confidence=confidence,
            ))
        return results

    def _extract_text(self, response) -> str:
        """Extract text from Gemini response, handling blocked/empty cases."""
        try:
            return response.text or ""
        except Exception:
            return ""

    def _score_narration(self, narration: str | None, latex: str) -> float:
        """
        Score a narration on 0.0–1.0 based on quality heuristics.

        Rules:
        - None → 0.0
        - Too short (< 5 chars) → 0.3
        - Contains forbidden English words → 0.5
        - Contains leksikon key terms → 0.95
        - Otherwise → 0.8
        """
        if not narration:
            return 0.0
        text = narration.strip().lower()
        if len(text) < 5:
            return 0.3

        # Penalize English math terms
        english_terms = {"squared", "cubed", "root", "times", "divided", "equals", "plus", "minus"}
        if any(term in text for term in english_terms):
            return 0.5

        # Reward leksikon key terms
        good_terms = {
            "pangkat", "ditambah", "dikurangi", "dikali", "dibagi",
            "sama dengan", "akar kuadrat", "pecahan", "pembilang",
            "penyebut", "nilai mutlak", "negatif", "positif",
        }
        if any(term in text for term in good_terms):
            return 0.95

        return 0.8
