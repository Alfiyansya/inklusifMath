"""
Tests for STT service and endpoint.

STT service tests use mocked faster-whisper to avoid downloading the model.
Endpoint tests call the service layer directly to avoid slowapi/starlette issues.
"""

from __future__ import annotations

import io
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest


# ── stt_service helpers ───────────────────────────────────────────────────────

class TestSttServiceHelpers:
    def test_reset_model_for_testing(self):
        """reset_model_for_testing() clears both singleton and attempted flag."""
        from app.services import stt_service as svc

        # Simulate a loaded model
        svc._model = MagicMock()
        svc._model_load_attempted = True

        svc.reset_model_for_testing()

        assert svc._model is None
        assert svc._model_load_attempted is False

    def test_get_model_raises_runtime_error_if_package_missing(self):
        """If faster_whisper is not importable, _get_model raises RuntimeError."""
        import sys
        from app.services import stt_service as svc

        svc.reset_model_for_testing()
        orig = sys.modules.pop("faster_whisper", None)
        sys.modules["faster_whisper"] = None  # type: ignore

        try:
            with pytest.raises(RuntimeError, match="faster-whisper"):
                svc._get_model()
        finally:
            svc.reset_model_for_testing()
            if orig is not None:
                sys.modules["faster_whisper"] = orig
            else:
                sys.modules.pop("faster_whisper", None)

    def test_get_model_raises_on_failed_load(self):
        """If WhisperModel() raises, _get_model raises RuntimeError."""
        import sys
        from app.services import stt_service as svc

        svc.reset_model_for_testing()

        mock_fw = MagicMock()
        mock_fw.WhisperModel.side_effect = Exception("CUDA not found")
        sys.modules["faster_whisper"] = mock_fw

        try:
            with pytest.raises(RuntimeError, match="Gagal memuat"):
                svc._get_model()
        finally:
            svc.reset_model_for_testing()
            sys.modules.pop("faster_whisper", None)

    def test_get_model_caches_after_first_load(self):
        """Second call to _get_model returns the cached model."""
        import sys
        from app.services import stt_service as svc

        svc.reset_model_for_testing()
        mock_model_instance = MagicMock()
        mock_fw = MagicMock()
        mock_fw.WhisperModel.return_value = mock_model_instance
        sys.modules["faster_whisper"] = mock_fw

        try:
            m1 = svc._get_model()
            m2 = svc._get_model()
            assert m1 is m2
            # WhisperModel() called only once
            assert mock_fw.WhisperModel.call_count == 1
        finally:
            svc.reset_model_for_testing()
            sys.modules.pop("faster_whisper", None)

    def test_get_model_does_not_retry_after_failure(self):
        """After failed load, _get_model_load_attempted is True → next call skips."""
        import sys
        from app.services import stt_service as svc

        svc.reset_model_for_testing()
        mock_fw = MagicMock()
        mock_fw.WhisperModel.side_effect = Exception("fail once")
        sys.modules["faster_whisper"] = mock_fw

        try:
            with pytest.raises(RuntimeError):
                svc._get_model()

            # Second call should raise immediately (no retry) with different message
            with pytest.raises(RuntimeError, match="startup"):
                svc._get_model()

            # WhisperModel called only once (not retried)
            assert mock_fw.WhisperModel.call_count == 1
        finally:
            svc.reset_model_for_testing()
            sys.modules.pop("faster_whisper", None)


# ── stt_service.transcribe_audio ──────────────────────────────────────────────

class TestTranscribeAudio:
    @pytest.mark.asyncio
    async def test_raises_value_error_for_empty_bytes(self):
        from app.services import stt_service as svc
        svc.reset_model_for_testing()

        with pytest.raises(ValueError, match="kosong"):
            await svc.transcribe_audio(b"")

    @pytest.mark.asyncio
    async def test_returns_transcript_on_success(self):
        """With mocked model, returns expected transcript dict."""
        import sys
        from app.services import stt_service as svc

        svc.reset_model_for_testing()

        # Mock the segment
        mock_segment = MagicMock()
        mock_segment.text = "apa itu bilangan prima"

        # Mock transcription info
        mock_info = MagicMock()
        mock_info.language = "id"
        mock_info.duration = 3.5

        # Mock model
        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([mock_segment], mock_info)

        mock_fw = MagicMock()
        mock_fw.WhisperModel.return_value = mock_model
        sys.modules["faster_whisper"] = mock_fw

        try:
            result = await svc.transcribe_audio(
                audio_bytes=b"fake wav data" * 100,
                audio_filename="test.wav",
            )
            assert result["transcript"] == "apa itu bilangan prima"
            assert result["language"] == "id"
            assert result["duration_seconds"] == 3.5
        finally:
            svc.reset_model_for_testing()
            sys.modules.pop("faster_whisper", None)

    @pytest.mark.asyncio
    async def test_handles_multiple_segments(self):
        """Multiple segments get joined with spaces."""
        import sys
        from app.services import stt_service as svc

        svc.reset_model_for_testing()

        seg1, seg2, seg3 = MagicMock(), MagicMock(), MagicMock()
        seg1.text = "apa"
        seg2.text = "itu"
        seg3.text = "pecahan?"

        mock_info = MagicMock()
        mock_info.language = "id"
        mock_info.duration = 2.0

        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([seg1, seg2, seg3], mock_info)

        mock_fw = MagicMock()
        mock_fw.WhisperModel.return_value = mock_model
        sys.modules["faster_whisper"] = mock_fw

        try:
            result = await svc.transcribe_audio(b"fake" * 100, "x.wav")
            assert result["transcript"] == "apa itu pecahan?"
        finally:
            svc.reset_model_for_testing()
            sys.modules.pop("faster_whisper", None)

    @pytest.mark.asyncio
    async def test_raises_value_error_on_transcribe_exception(self):
        """When model.transcribe() raises, service raises ValueError."""
        import sys
        from app.services import stt_service as svc

        svc.reset_model_for_testing()

        mock_model = MagicMock()
        mock_model.transcribe.side_effect = Exception("decode error")

        mock_fw = MagicMock()
        mock_fw.WhisperModel.return_value = mock_model
        sys.modules["faster_whisper"] = mock_fw

        try:
            with pytest.raises(ValueError, match="Gagal memproses"):
                await svc.transcribe_audio(b"bad audio" * 100, "bad.wav")
        finally:
            svc.reset_model_for_testing()
            sys.modules.pop("faster_whisper", None)

    @pytest.mark.asyncio
    async def test_uses_id_language_always(self):
        """Language is always 'id' in transcribe call."""
        import sys
        from app.services import stt_service as svc

        svc.reset_model_for_testing()

        mock_model = MagicMock()
        mock_info = MagicMock()
        mock_info.language = "id"
        mock_info.duration = 1.0
        mock_model.transcribe.return_value = ([], mock_info)

        mock_fw = MagicMock()
        mock_fw.WhisperModel.return_value = mock_model
        sys.modules["faster_whisper"] = mock_fw

        try:
            await svc.transcribe_audio(b"x" * 100, "test.webm")
            # Check language=id was passed
            call_kwargs = mock_model.transcribe.call_args
            assert call_kwargs.kwargs.get("language") == "id"
        finally:
            svc.reset_model_for_testing()
            sys.modules.pop("faster_whisper", None)


# ── STT endpoint validation ───────────────────────────────────────────────────

class TestSttEndpointValidation:
    """Test endpoint-level validation (size, MIME) without slowapi issues."""

    def test_max_audio_size_constant(self):
        from app.api.v1.endpoints.stt import MAX_AUDIO_SIZE_BYTES
        assert MAX_AUDIO_SIZE_BYTES == 5 * 1024 * 1024

    def test_allowed_content_types_includes_common_formats(self):
        from app.api.v1.endpoints.stt import ALLOWED_CONTENT_TYPES
        assert "audio/wav" in ALLOWED_CONTENT_TYPES
        assert "audio/webm" in ALLOWED_CONTENT_TYPES
        assert "audio/ogg" in ALLOWED_CONTENT_TYPES
        assert "audio/mpeg" in ALLOWED_CONTENT_TYPES

    def test_stt_response_schema(self):
        from app.schemas.stt import SttTranscribeResponse

        r = SttTranscribeResponse(
            transcript="halo dunia",
            language="id",
            duration_seconds=2.5,
        )
        assert r.transcript == "halo dunia"
        assert r.language == "id"
        assert r.duration_seconds == 2.5
        assert r.model_used == "faster-whisper-tiny"

    def test_stt_response_duration_optional(self):
        from app.schemas.stt import SttTranscribeResponse

        r = SttTranscribeResponse(transcript="test", language="id")
        assert r.duration_seconds is None
