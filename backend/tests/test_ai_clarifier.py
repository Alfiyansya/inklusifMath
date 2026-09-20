"""
Tests for AI Semantic Clarifier and Leksikon module.

Strategy:
  - AiClarifier tested with fully mocked Gemini client (no real API calls)
  - Confidence scoring tested with various narration strings
  - Batch response parsing tested with real/malformed JSON
  - generate_ai_narrations (document_service) tested with mocked clarifier
  - Leksikon constants verified for required content
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ai.clarifier import AiClarifier, NarrationResult
from app.services.ai.leksikon import (
    BATCH_PROMPT_TEMPLATE,
    SINGLE_PROMPT_TEMPLATE,
    SYSTEM_PROMPT,
)


# ── Leksikon module tests ─────────────────────────────────────────────────────

class TestLeksikon:
    """Verify that the leksikon constants contain required content."""

    def test_system_prompt_not_empty(self):
        assert len(SYSTEM_PROMPT) > 100

    def test_system_prompt_contains_key_rules(self):
        assert "pecahan" in SYSTEM_PROMPT.lower()
        assert "pangkat" in SYSTEM_PROMPT.lower()
        assert "akar kuadrat" in SYSTEM_PROMPT.lower()
        assert "bahasa indonesia" in SYSTEM_PROMPT.lower()

    def test_system_prompt_forbids_english(self):
        assert "JANGAN gunakan istilah Inggris" in SYSTEM_PROMPT

    def test_batch_prompt_template_has_placeholders(self):
        assert "{count}" in BATCH_PROMPT_TEMPLATE
        assert "{expressions_json}" in BATCH_PROMPT_TEMPLATE

    def test_single_prompt_template_has_placeholders(self):
        assert "{latex}" in SINGLE_PROMPT_TEMPLATE
        assert "{original}" in SINGLE_PROMPT_TEMPLATE

    def test_batch_prompt_renders(self):
        rendered = BATCH_PROMPT_TEMPLATE.format(
            count=2,
            expressions_json='[{"index":0,"latex":"x^2"}]',
        )
        assert "2" in rendered
        assert "x^2" in rendered

    def test_single_prompt_renders(self):
        rendered = SINGLE_PROMPT_TEMPLATE.format(
            latex=r"\frac{1}{2}",
            original="1/2",
        )
        assert r"\frac{1}{2}" in rendered
        assert "1/2" in rendered


# ── NarrationResult dataclass ─────────────────────────────────────────────────

class TestNarrationResult:
    def test_default_confidence(self):
        r = NarrationResult(
            position_order=1,
            original_notation="x^2",
            latex="x^{2}",
            narration="x kuadrat",
        )
        assert r.confidence == 1.0

    def test_none_narration(self):
        r = NarrationResult(
            position_order=1,
            original_notation="x^2",
            latex="x^{2}",
            narration=None,
            confidence=0.0,
        )
        assert r.narration is None
        assert r.confidence == 0.0


# ── AiClarifier._score_narration ──────────────────────────────────────────────

class TestScoreNarration:
    def setup_method(self):
        self.clarifier = AiClarifier()

    def test_none_returns_zero(self):
        assert self.clarifier._score_narration(None, "x^2") == 0.0

    def test_too_short_returns_low(self):
        assert self.clarifier._score_narration("x", "x") == 0.3

    def test_english_terms_penalized(self):
        score = self.clarifier._score_narration("x squared plus one", "x^2+1")
        assert score == 0.5

    def test_leksikon_terms_rewarded(self):
        score = self.clarifier._score_narration("x pangkat dua ditambah satu", "x^2+1")
        assert score == 0.95

    def test_medium_quality_returns_medium(self):
        # No English, no leksikon key terms, but enough length
        score = self.clarifier._score_narration("sebuah ekspresi matematika", "x")
        assert score == 0.8

    def test_pecahan_term_rewarded(self):
        score = self.clarifier._score_narration(
            "pecahan dengan pembilang satu dan penyebut dua", "1/2"
        )
        assert score == 0.95

    def test_akar_kuadrat_rewarded(self):
        score = self.clarifier._score_narration(
            "akar kuadrat dari x ditambah satu", r"\sqrt{x+1}"
        )
        assert score == 0.95


# ── AiClarifier._parse_batch_response ────────────────────────────────────────

class TestParseBatchResponse:
    def setup_method(self):
        self.clarifier = AiClarifier()

    def test_valid_json_array(self):
        raw = json.dumps([
            {"index": 0, "narasi": "x kuadrat"},
            {"index": 1, "narasi": "satu per dua"},
        ])
        result = self.clarifier._parse_batch_response(raw, 2)
        assert result[0] == "x kuadrat"
        assert result[1] == "satu per dua"

    def test_strips_markdown_fence(self):
        raw = "```json\n[{\"index\": 0, \"narasi\": \"x kuadrat\"}]\n```"
        result = self.clarifier._parse_batch_response(raw, 1)
        assert result[0] == "x kuadrat"

    def test_strips_plain_fence(self):
        raw = "```\n[{\"index\": 0, \"narasi\": \"a pangkat dua\"}]\n```"
        result = self.clarifier._parse_batch_response(raw, 1)
        assert result[0] == "a pangkat dua"

    def test_empty_narasi_excluded(self):
        raw = json.dumps([
            {"index": 0, "narasi": ""},
            {"index": 1, "narasi": "x ditambah y"},
        ])
        result = self.clarifier._parse_batch_response(raw, 2)
        assert 0 not in result
        assert result[1] == "x ditambah y"

    def test_invalid_json_returns_empty(self):
        result = self.clarifier._parse_batch_response("not json", 3)
        assert result == {}

    def test_out_of_range_index_excluded(self):
        raw = json.dumps([{"index": 99, "narasi": "x"}])
        result = self.clarifier._parse_batch_response(raw, 2)
        assert result == {}

    def test_supports_narration_key_alias(self):
        raw = json.dumps([{"index": 0, "narration": "x kuadrat"}])
        result = self.clarifier._parse_batch_response(raw, 1)
        assert result[0] == "x kuadrat"


# ── AiClarifier._build_results ───────────────────────────────────────────────

class TestBuildResults:
    def setup_method(self):
        self.clarifier = AiClarifier()

    def test_maps_narrations_to_results(self):
        chunk = [
            {"position_order": 1, "original_notation": "x^2", "latex": "x^{2}"},
            {"position_order": 2, "original_notation": "1/2", "latex": r"\frac{1}{2}"},
        ]
        parsed = {0: "x kuadrat", 1: "satu per dua"}
        results = self.clarifier._build_results(chunk, parsed)
        assert len(results) == 2
        assert results[0].narration == "x kuadrat"
        assert results[0].position_order == 1
        assert results[1].narration == "satu per dua"
        assert results[1].position_order == 2

    def test_missing_narration_gives_none(self):
        chunk = [{"position_order": 1, "original_notation": "x", "latex": "x"}]
        results = self.clarifier._build_results(chunk, {})
        assert results[0].narration is None
        assert results[0].confidence == 0.0

    def test_confidence_set_for_good_narration(self):
        chunk = [{"position_order": 1, "original_notation": "x^2", "latex": "x^{2}"}]
        parsed = {0: "x pangkat dua"}
        results = self.clarifier._build_results(chunk, parsed)
        assert results[0].confidence == 0.95


# ── AiClarifier.clarify_single (mocked Gemini) ───────────────────────────────

class TestClarifySingle:
    def setup_method(self):
        self.clarifier = AiClarifier()

    @pytest.mark.asyncio
    async def test_success_path(self):
        mock_response = MagicMock()
        mock_response.text = "x pangkat dua"

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        self.clarifier._client = mock_client
        self.clarifier._api_key = "fake-key"

        result = await self.clarifier.clarify_single({
            "position_order": 1,
            "original_notation": "x^2",
            "latex": "x^{2}",
        })

        assert result.narration == "x pangkat dua"
        assert result.position_order == 1
        assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_api_error_raises_gemini_unavailable(self):
        """AI_002: Non-timeout Gemini errors now raise GeminiUnavailableError (not return None)."""
        from app.services.ai.clarifier import GeminiUnavailableError

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API error")

        self.clarifier._client = mock_client
        self.clarifier._api_key = "fake-key"

        with pytest.raises(GeminiUnavailableError):
            await self.clarifier.clarify_single({
                "position_order": 3,
                "original_notation": "1/2",
                "latex": r"\frac{1}{2}",
            })

    @pytest.mark.asyncio
    async def test_no_api_key_raises_on_client_init(self):
        self.clarifier._api_key = ""
        self.clarifier._client = None

        result = await self.clarifier.clarify_single({
            "position_order": 1,
            "original_notation": "x",
            "latex": "x",
        })
        # Should fail gracefully, not raise
        assert result.narration is None


# ── AiClarifier.clarify_batch (mocked Gemini) ────────────────────────────────

class TestClarifyBatch:
    def setup_method(self):
        self.clarifier = AiClarifier()

    @pytest.mark.asyncio
    async def test_empty_input_returns_empty(self):
        result = await self.clarifier.clarify_batch([])
        assert result == []

    @pytest.mark.asyncio
    async def test_batch_success_path(self):
        good_response = json.dumps([
            {"index": 0, "narasi": "x pangkat dua"},
            {"index": 1, "narasi": "satu per dua"},
        ])
        mock_response = MagicMock()
        mock_response.text = good_response

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        self.clarifier._client = mock_client
        self.clarifier._api_key = "fake-key"

        expressions = [
            {"position_order": 1, "original_notation": "x^2", "latex": "x^{2}"},
            {"position_order": 2, "original_notation": "1/2", "latex": r"\frac{1}{2}"},
        ]
        results = await self.clarifier.clarify_batch(expressions)

        assert len(results) == 2
        assert results[0].narration == "x pangkat dua"
        assert results[1].narration == "satu per dua"

    @pytest.mark.asyncio
    async def test_batch_json_parse_fail_falls_back_to_single(self):
        """If batch JSON parsing fails, should fall back to single-call for each."""
        batch_response = MagicMock()
        batch_response.text = "INVALID JSON"

        single_response = MagicMock()
        single_response.text = "x pangkat dua"

        mock_client = MagicMock()
        # First call returns bad JSON, subsequent single calls return good text
        mock_client.models.generate_content.side_effect = [
            batch_response,
            single_response,
        ]

        self.clarifier._client = mock_client
        self.clarifier._api_key = "fake-key"

        expressions = [
            {"position_order": 1, "original_notation": "x^2", "latex": "x^{2}"},
        ]
        results = await self.clarifier.clarify_batch(expressions)
        # Falls back to single — should still return a result
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_batch_splits_into_chunks(self):
        """clarify_batch should chunk large lists into _BATCH_SIZE groups."""
        from app.services.ai import clarifier as clarifier_module

        call_count = 0
        original_chunk = self.clarifier._clarify_chunk

        async def counting_chunk(chunk):
            nonlocal call_count
            call_count += 1
            return [
                NarrationResult(
                    position_order=e.get("position_order", i),
                    original_notation=e.get("original_notation", ""),
                    latex=e.get("latex", ""),
                    narration="narasi",
                    confidence=0.9,
                )
                for i, e in enumerate(chunk)
            ]

        self.clarifier._clarify_chunk = counting_chunk

        # 25 expressions → should trigger 2 chunks (20 + 5)
        expressions = [
            {"position_order": i, "original_notation": f"x^{i}", "latex": f"x^{{{i}}}"}
            for i in range(1, 26)
        ]
        results = await self.clarifier.clarify_batch(expressions)
        assert len(results) == 25
        assert call_count == 2  # ceil(25/20) = 2 chunks


# ── generate_ai_narrations (document_service) ─────────────────────────────────

class TestGenerateAiNarrations:
    @pytest.mark.asyncio
    async def test_empty_expressions_returns_zero(self):
        from app.services import document_service as svc
        import uuid
        from unittest.mock import AsyncMock
        db = AsyncMock()
        result = await svc.generate_ai_narrations(db, uuid.uuid4(), [])
        assert result == 0

    @pytest.mark.asyncio
    async def test_successful_narration_updates_expressions(self):
        from app.services import document_service as svc
        import uuid
        from unittest.mock import AsyncMock, patch

        db = AsyncMock()
        db.flush = AsyncMock()

        expr1 = MagicMock()
        expr1.position_order = 1
        expr1.original_notation = "x^2"
        expr1.latex_representation = "x^{2}"

        expr2 = MagicMock()
        expr2.position_order = 2
        expr2.original_notation = "1/2"
        expr2.latex_representation = r"\frac{1}{2}"

        mock_results = [
            NarrationResult(1, "x^2", "x^{2}", "x pangkat dua", 0.95),
            NarrationResult(2, "1/2", r"\frac{1}{2}", "satu per dua", 0.95),
        ]

        # Patch at the module where AiClarifier is *imported inside* the function
        with patch("app.services.ai.clarifier.AiClarifier") as MockClarifier:
            instance = AsyncMock()
            instance.clarify_batch = AsyncMock(return_value=mock_results)
            MockClarifier.return_value = instance

            count = await svc.generate_ai_narrations(
                db, uuid.uuid4(), [expr1, expr2]
            )

        assert count == 2
        assert expr1.ai_narration == "x pangkat dua"
        assert expr1.status == "ai_generated"
        assert expr2.ai_narration == "satu per dua"
        assert expr2.status == "ai_generated"

    @pytest.mark.asyncio
    async def test_partial_failure_returns_partial_count(self):
        from app.services import document_service as svc
        import uuid

        db = AsyncMock()
        db.flush = AsyncMock()

        expr1 = MagicMock()
        expr1.position_order = 1
        expr1.original_notation = "x^2"
        expr1.latex_representation = "x^{2}"

        expr2 = MagicMock()
        expr2.position_order = 2
        expr2.original_notation = "bad"
        expr2.latex_representation = None

        mock_results = [
            NarrationResult(1, "x^2", "x^{2}", "x pangkat dua", 0.95),
            NarrationResult(2, "bad", "bad", None, 0.0),  # failed
        ]

        with patch("app.services.ai.clarifier.AiClarifier") as MockClarifier:
            instance = AsyncMock()
            instance.clarify_batch = AsyncMock(return_value=mock_results)
            MockClarifier.return_value = instance

            count = await svc.generate_ai_narrations(
                db, uuid.uuid4(), [expr1, expr2]
            )

        assert count == 1
        assert expr1.status == "ai_generated"
        # expr2 status unchanged (MagicMock default)
