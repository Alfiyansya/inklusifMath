"""
STT endpoint — POST /stt/transcribe

Fallback speech-to-text menggunakan faster-whisper (self-hosted, gratis).
Digunakan ketika Web Speech API browser tidak tersedia (Firefox, offline, dll).

Request: multipart/form-data
  - audio_file: UploadFile (WAV/WebM/OGG/MP3, max 5 MB)

Response: SttTranscribeResponse
  - transcript: str
  - language: str ("id")
  - duration_seconds: float | None
  - model_used: str

Rate limit: 20/jam per user (voice requests biasanya pendek)
Max file: 5 MB (~60 detik WAV 16kHz mono)
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, status

from app.core.dependencies import get_current_user
from app.core.rate_limiter import limiter
from app.schemas.stt import SttTranscribeResponse
from app.services import stt_service as svc

logger = logging.getLogger(__name__)

router = APIRouter()

# 5 MB max audio file size
MAX_AUDIO_SIZE_BYTES = 5 * 1024 * 1024

ALLOWED_CONTENT_TYPES = {
    "audio/wav",
    "audio/wave",
    "audio/x-wav",
    "audio/webm",
    "audio/ogg",
    "audio/mpeg",
    "audio/mp4",
    "audio/flac",
    "audio/x-flac",
}


@router.post(
    "/transcribe",
    response_model=SttTranscribeResponse,
    summary="Transcribe audio to text (faster-whisper fallback)",
)
@limiter.limit("20/hour")
async def transcribe_audio(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    audio_file: UploadFile = File(
        ...,
        description="Audio file (WAV/WebM/OGG/MP3, max 5 MB)",
    ),
):
    """
    Transcribe speech to text using self-hosted faster-whisper.

    This endpoint is the fallback for browsers that don't support the
    Web Speech API (Firefox, some mobile browsers). The frontend useTutor
    hook calls this when `isSpeechSupported` is false.

    - Model: Whisper tiny (Bahasa Indonesia, CPU int8)
    - Rate limited: 20/hour per user
    - Max file: 5 MB
    - Returns transcript in Bahasa Indonesia
    """
    # ── Validate content type ──
    content_type = (audio_file.content_type or "").split(";")[0].strip().lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "error_code": "STT_004",
                "message": f"Format audio tidak didukung: {content_type}. Gunakan WAV, WebM, OGG, atau MP3.",
            },
        )

    # ── Read and validate size ──
    audio_bytes = await audio_file.read()
    if len(audio_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "STT_002",
                "message": "File audio kosong.",
            },
        )
    if len(audio_bytes) > MAX_AUDIO_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error_code": "STT_003",
                "message": f"File audio terlalu besar (max {MAX_AUDIO_SIZE_BYTES // 1024 // 1024} MB).",
            },
        )

    # ── Transcribe ──
    try:
        result = await svc.transcribe_audio(
            audio_bytes=audio_bytes,
            audio_filename=audio_file.filename or "audio.wav",
        )

        logger.info(
            "[stt] user=%s lang=%s duration=%.1fs transcript_len=%d",
            current_user.get("user_id", "?"),
            result["language"],
            result["duration_seconds"] or 0,
            len(result["transcript"]),
        )

        return SttTranscribeResponse(
            transcript=result["transcript"],
            language=result["language"],
            duration_seconds=result["duration_seconds"],
        )

    except RuntimeError as exc:
        # Model not available (not installed / download failed)
        logger.error("[stt] Model tidak tersedia: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_code": "STT_001",
                "message": "Layanan transkripsi tidak tersedia. Gunakan input teks.",
                "detail": str(exc),
            },
        )
    except ValueError as exc:
        # Audio decode failure
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "STT_005",
                "message": f"Gagal memproses audio: {exc}",
            },
        )
