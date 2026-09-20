"""
Tests for Error Handling Taxonomy (TDD Section 10).

Tests cover:
  - ErrorCode enum completeness (all 14 codes)
  - AppError construction and properties
  - Default messages in Bahasa Indonesia
  - Default HTTP status codes
  - AppError.to_http_exception() conversion
  - app_error_handler response format
  - GeminiTimeoutError / GeminiUnavailableError classes
  - AI_003 timeout in tutor_service
  - AI_001/AI_002 in clarifier retry logic
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient


# ── ErrorCode enum ────────────────────────────────────────────────────────────

class TestErrorCodeEnum:
    def test_all_14_codes_present(self):
        from app.core.errors import ErrorCode
        codes = {e.value for e in ErrorCode}
        expected = {
            "DOC_001", "DOC_002", "DOC_003",
            "PARSE_001", "PARSE_002", "PARSE_003",
            "AI_001", "AI_002", "AI_003",
            "STT_001", "STT_002", "STT_003", "STT_004", "STT_005",
            "AUTH_001", "AUTH_002",
        }
        assert expected.issubset(codes), f"Missing codes: {expected - codes}"

    def test_doc_codes(self):
        from app.core.errors import ErrorCode
        assert ErrorCode.DOC_001 == "DOC_001"
        assert ErrorCode.DOC_002 == "DOC_002"
        assert ErrorCode.DOC_003 == "DOC_003"

    def test_parse_codes(self):
        from app.core.errors import ErrorCode
        assert ErrorCode.PARSE_001 == "PARSE_001"
        assert ErrorCode.PARSE_002 == "PARSE_002"
        assert ErrorCode.PARSE_003 == "PARSE_003"

    def test_ai_codes(self):
        from app.core.errors import ErrorCode
        assert ErrorCode.AI_001 == "AI_001"
        assert ErrorCode.AI_002 == "AI_002"
        assert ErrorCode.AI_003 == "AI_003"

    def test_stt_codes(self):
        from app.core.errors import ErrorCode
        assert ErrorCode.STT_001 == "STT_001"
        assert ErrorCode.STT_002 == "STT_002"
        assert ErrorCode.STT_003 == "STT_003"
        assert ErrorCode.STT_004 == "STT_004"
        assert ErrorCode.STT_005 == "STT_005"


# ── AppError construction ─────────────────────────────────────────────────────

class TestAppError:
    def test_default_message_and_status(self):
        from app.core.errors import AppError, ErrorCode
        err = AppError(ErrorCode.DOC_001)
        assert err.code == ErrorCode.DOC_001
        assert err.status_code == 413
        assert "20 MB" in err.message or "batas" in err.message.lower()
        assert err.detail is None
        assert err.extra == {}

    def test_custom_message_overrides_default(self):
        from app.core.errors import AppError, ErrorCode
        err = AppError(ErrorCode.PARSE_001, message="Custom parse error msg")
        assert err.message == "Custom parse error msg"

    def test_custom_status_overrides_default(self):
        from app.core.errors import AppError, ErrorCode
        err = AppError(ErrorCode.AI_001, status_code=500)
        assert err.status_code == 500

    def test_detail_stored(self):
        from app.core.errors import AppError, ErrorCode
        err = AppError(ErrorCode.AI_001, detail="timeout after 2 retries")
        assert err.detail == "timeout after 2 retries"

    def test_extra_stored(self):
        from app.core.errors import AppError, ErrorCode
        err = AppError(ErrorCode.DOC_001, extra={"document_id": "abc"})
        assert err.extra == {"document_id": "abc"}

    def test_is_exception(self):
        from app.core.errors import AppError, ErrorCode
        err = AppError(ErrorCode.STT_001)
        assert isinstance(err, Exception)
        assert str(err) == err.message

    def test_to_http_exception(self):
        from app.core.errors import AppError, ErrorCode
        err = AppError(ErrorCode.DOC_002)
        http_exc = err.to_http_exception()
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 415
        assert http_exc.detail["error_code"] == "DOC_002"
        assert "message" in http_exc.detail

    def test_to_http_exception_includes_detail(self):
        from app.core.errors import AppError, ErrorCode
        err = AppError(ErrorCode.AI_001, detail="timed out")
        http_exc = err.to_http_exception()
        assert http_exc.detail["detail"] == "timed out"

    def test_to_http_exception_includes_extra(self):
        from app.core.errors import AppError, ErrorCode
        err = AppError(ErrorCode.PARSE_001, extra={"document_id": "xyz"})
        http_exc = err.to_http_exception()
        assert http_exc.detail["document_id"] == "xyz"


# ── Status codes ──────────────────────────────────────────────────────────────

class TestDefaultStatusCodes:
    def test_doc_001_is_413(self):
        from app.core.errors import AppError, ErrorCode
        assert AppError(ErrorCode.DOC_001).status_code == 413

    def test_doc_002_is_415(self):
        from app.core.errors import AppError, ErrorCode
        assert AppError(ErrorCode.DOC_002).status_code == 415

    def test_doc_003_is_422(self):
        from app.core.errors import AppError, ErrorCode
        assert AppError(ErrorCode.DOC_003).status_code == 422

    def test_parse_001_is_422(self):
        from app.core.errors import AppError, ErrorCode
        assert AppError(ErrorCode.PARSE_001).status_code == 422

    def test_ai_001_is_503(self):
        from app.core.errors import AppError, ErrorCode
        assert AppError(ErrorCode.AI_001).status_code == 503

    def test_ai_002_is_503(self):
        from app.core.errors import AppError, ErrorCode
        assert AppError(ErrorCode.AI_002).status_code == 503

    def test_ai_003_is_503(self):
        from app.core.errors import AppError, ErrorCode
        assert AppError(ErrorCode.AI_003).status_code == 503

    def test_stt_001_is_503(self):
        from app.core.errors import AppError, ErrorCode
        assert AppError(ErrorCode.STT_001).status_code == 503

    def test_stt_003_is_413(self):
        from app.core.errors import AppError, ErrorCode
        assert AppError(ErrorCode.STT_003).status_code == 413

    def test_auth_001_is_401(self):
        from app.core.errors import AppError, ErrorCode
        assert AppError(ErrorCode.AUTH_001).status_code == 401


# ── Helper functions ──────────────────────────────────────────────────────────

class TestHelpers:
    def test_get_error_message(self):
        from app.core.errors import ErrorCode, get_error_message
        msg = get_error_message(ErrorCode.DOC_001)
        assert isinstance(msg, str)
        assert len(msg) > 5

    def test_get_error_status(self):
        from app.core.errors import ErrorCode, get_error_status
        assert get_error_status(ErrorCode.DOC_001) == 413
        assert get_error_status(ErrorCode.AI_001) == 503

    def test_all_codes_have_messages(self):
        from app.core.errors import ErrorCode, get_error_message
        for code in ErrorCode:
            msg = get_error_message(code)
            assert msg, f"Missing message for {code.value}"
            assert len(msg) > 10, f"Message too short for {code.value}"

    def test_all_codes_have_status_codes(self):
        from app.core.errors import ErrorCode, get_error_status
        for code in ErrorCode:
            status = get_error_status(code)
            assert status in {200, 400, 401, 403, 413, 415, 422, 503}, \
                f"Unexpected status {status} for {code.value}"


# ── GeminiTimeoutError / GeminiUnavailableError ───────────────────────────────

class TestGeminiErrorClasses:
    def test_timeout_error_is_exception(self):
        from app.services.ai.clarifier import GeminiTimeoutError
        err = GeminiTimeoutError("timed out")
        assert isinstance(err, Exception)
        assert str(err) == "timed out"

    def test_unavailable_error_is_exception(self):
        from app.services.ai.clarifier import GeminiUnavailableError
        err = GeminiUnavailableError("503 Service Unavailable")
        assert isinstance(err, Exception)

    def test_timeout_and_unavailable_are_distinct(self):
        from app.services.ai.clarifier import GeminiTimeoutError, GeminiUnavailableError
        assert GeminiTimeoutError is not GeminiUnavailableError
        assert not issubclass(GeminiTimeoutError, GeminiUnavailableError)


# ── AI_003: Tutor timeout test ────────────────────────────────────────────────

class TestTutorAI003:
    @pytest.mark.asyncio
    async def test_tutor_returns_fallback_on_timeout(self):
        """AI_003: TimeoutError in Gemini call → fallback response returned."""
        import sys
        from app.services import tutor_service as svc

        svc._fallback_idx = 0  # reset cycling

        # Simulate TimeoutError by patching asyncio.timeout to raise immediately
        orig_timeout = asyncio.timeout

        class _AlwaysTimeout:
            async def __aenter__(self):
                raise TimeoutError("mock timeout")
            async def __aexit__(self, *args):
                pass

        with patch("asyncio.timeout", return_value=_AlwaysTimeout()):
            # Inject mock genai module to get past lazy import
            mock_genai = MagicMock()
            mock_genai.Client.return_value = MagicMock()
            sys.modules["google.genai"] = mock_genai
            sys.modules["google.genai.types"] = MagicMock()

            try:
                answer, hint = await svc.ask_tutor(
                    question="apa itu pecahan?",
                    module_id="test-mod",
                    context_element_id="formula-1",
                )
                # Should return fallback, not raise
                assert isinstance(answer, str)
                assert len(answer) > 10
                assert hint is None
            finally:
                sys.modules.pop("google.genai", None)
                sys.modules.pop("google.genai.types", None)

    @pytest.mark.asyncio
    async def test_tutor_timeout_constant_is_reasonable(self):
        """AI_003 timeout constant should be between 10 and 60 seconds."""
        from app.services.tutor_service import _TUTOR_TIMEOUT_SECONDS
        assert 10 <= _TUTOR_TIMEOUT_SECONDS <= 60


# ── AI_001/AI_002: Clarifier retry constants ──────────────────────────────────

class TestClarifierRetryConfig:
    def test_timeout_constant(self):
        from app.services.ai.clarifier import _GEMINI_TIMEOUT_SECONDS
        assert 10 <= _GEMINI_TIMEOUT_SECONDS <= 60

    def test_retry_constant(self):
        from app.services.ai.clarifier import _GEMINI_MAX_RETRIES
        assert _GEMINI_MAX_RETRIES >= 1

    @pytest.mark.asyncio
    async def test_call_gemini_raises_unavailable_on_non_timeout_error(self):
        """AI_002: non-timeout exception → GeminiUnavailableError immediately."""
        from app.services.ai.clarifier import AiClarifier, GeminiUnavailableError
        import sys

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("503 quota exceeded")

        clarifier = AiClarifier()
        clarifier._client = mock_client
        clarifier._api_key = "test-key"

        with pytest.raises(GeminiUnavailableError):
            await clarifier._call_gemini_with_retry(
                prompt="test", max_output_tokens=100, context="test"
            )

    @pytest.mark.asyncio
    async def test_call_gemini_raises_timeout_after_retries_exhausted(self):
        """AI_001: TimeoutError repeated → GeminiTimeoutError after max retries."""
        from app.services.ai.clarifier import (
            AiClarifier,
            GeminiTimeoutError,
            _GEMINI_MAX_RETRIES,
        )

        clarifier = AiClarifier()
        clarifier._api_key = "test-key"

        call_count = 0

        async def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise TimeoutError("mock timeout")

        # Patch run_in_executor and asyncio.sleep
        with patch.object(asyncio, "sleep", new_callable=AsyncMock) as mock_sleep:
            loop = asyncio.get_event_loop()
            with patch.object(loop, "run_in_executor", side_effect=mock_execute):
                with pytest.raises(GeminiTimeoutError):
                    await clarifier._call_gemini_with_retry(
                        prompt="test", max_output_tokens=100, context="test"
                    )

        # Should have retried exactly _GEMINI_MAX_RETRIES times
        assert call_count == _GEMINI_MAX_RETRIES
