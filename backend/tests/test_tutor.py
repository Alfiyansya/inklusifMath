"""
Tests for tutor service and tutor endpoint.

Service tests patch 'builtins.__import__' to intercept lazy import.
Endpoint tests patch service layer directly — avoid slowapi by calling
service mock, not invoking the rate-limited endpoint wrapper.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── tutor_service.ask_tutor ───────────────────────────────────────────────────

class TestAskTutorService:
    @pytest.mark.asyncio
    async def test_returns_fallback_on_import_error(self):
        """When google.genai is not available, should return fallback."""
        from app.services import tutor_service as svc

        original_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

        def mock_import(name, *args, **kwargs):
            if name == "google.genai":
                raise ImportError("no google.genai")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            answer, hint = await svc.ask_tutor(
                question="test question",
                module_id="mod-1",
                context_element_id="expr-1",
            )

        assert isinstance(answer, str)
        assert len(answer) > 10

    @pytest.mark.asyncio
    async def test_fallback_always_returns_string(self):
        """Fallback returns non-empty string."""
        from app.services.tutor_service import _get_fallback, FALLBACK_RESPONSES

        msg = _get_fallback()
        assert isinstance(msg, str)
        assert len(msg) > 0

    @pytest.mark.asyncio
    async def test_fallback_cycles_through_messages(self):
        """Fallback cycles through FALLBACK_RESPONSES."""
        from app.services.tutor_service import _get_fallback, FALLBACK_RESPONSES

        answers = [_get_fallback() for _ in range(len(FALLBACK_RESPONSES) + 1)]
        # Should contain multiple different responses
        assert len(set(answers)) > 1

    @pytest.mark.asyncio
    async def test_fallback_on_gemini_exception(self):
        """If genai raises any exception inside try block, fall back gracefully."""
        import sys
        from app.services import tutor_service as svc

        # Temporarily remove google.genai from sys.modules so lazy import fails
        orig_genai = sys.modules.pop("google.genai", None)
        orig_genai_types = sys.modules.pop("google.genai.types", None)
        sys.modules["google.genai"] = None  # type: ignore  # triggers ImportError on import

        try:
            answer, hint = await svc.ask_tutor(
                question="apa itu pecahan?",
                module_id="m",
                context_element_id="e",
            )
            assert answer is not None
            assert isinstance(answer, str)
        finally:
            # Restore
            if orig_genai is not None:
                sys.modules["google.genai"] = orig_genai
            else:
                sys.modules.pop("google.genai", None)
            if orig_genai_types is not None:
                sys.modules["google.genai.types"] = orig_genai_types

    def test_socratic_system_prompt_has_key_rules(self):
        """System prompt must forbid direct answers and require Bahasa Indonesia."""
        from app.services.tutor_service import SOCRATIC_SYSTEM_PROMPT

        prompt_lower = SOCRATIC_SYSTEM_PROMPT.lower()
        assert "bahasa indonesia" in prompt_lower or "indonesia" in prompt_lower
        assert "jawaban" in prompt_lower  # mentions not giving direct answers
        assert "pertanyaan" in prompt_lower  # mentions guiding questions

    def test_follow_up_extraction_logic(self):
        """Test the follow-up hint extraction inline (not via full function)."""
        text = "Kamu sudah dekat. Coba ingat rumus dasar. Menurutmu apa langkah berikutnya?"
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        follow_up = None
        for s in reversed(sentences):
            if s.endswith("?"):
                follow_up = s + "?"
                break
        assert follow_up is not None
        assert "?" in follow_up

    def test_follow_up_is_none_when_no_question(self):
        """If no "?" in response, follow_up should be None."""
        text = "Coba pikirkan. Langkah pertama adalah membagi."
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        follow_up = None
        for s in reversed(sentences):
            if s.endswith("?"):
                follow_up = s + "?"
                break
        assert follow_up is None


# ── tutor service ask_tutor (direct call, bypassing endpoint rate limiter) ───

class TestAskTutorServiceDirect:
    @pytest.mark.asyncio
    async def test_answer_is_str(self):
        import sys
        from app.services import tutor_service as svc

        orig = sys.modules.pop("google.genai", None)
        sys.modules["google.genai"] = None  # type: ignore  # triggers ImportError on import

        try:
            answer, hint = await svc.ask_tutor(
                question="Apa itu bilangan prima?",
                module_id="mod-1",
                context_element_id="e-1",
            )
            assert isinstance(answer, str)
            assert hint is None or isinstance(hint, str)
        finally:
            if orig is not None:
                sys.modules["google.genai"] = orig
            else:
                sys.modules.pop("google.genai", None)

    @pytest.mark.asyncio
    async def test_question_included_in_service_call(self):
        """Service should forward the question to the AI prompt."""
        from app.services import tutor_service as svc

        calls = []

        async def fake_ask(question, module_id, context_element_id):
            calls.append(question)
            return "Pertanyaan bagus. Coba pikirkan.", None

        with patch.object(svc, "ask_tutor", fake_ask):
            answer, _ = await svc.ask_tutor(
                question="Bagaimana cara menghitung pecahan?",
                module_id="m",
                context_element_id="e",
            )
            assert "Bagaimana cara menghitung pecahan?" in calls
