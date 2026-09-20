"""
STT Service — faster-whisper backend transcription.

Used as a fallback when the browser's Web Speech API is unavailable
(e.g., Firefox desktop, some mobile browsers, offline scenarios).

Design decisions:
  - Model: "tiny" (39 MB, ~10x realtime on CPU, good enough for spoken questions)
  - Language: "id" (Bahasa Indonesia) — fixed, no auto-detection overhead
  - Compute type: "int8" for minimal CPU memory footprint
  - Device: "cpu" — no GPU assumption, runs anywhere
  - Lazy loading: model loaded on first request, cached as module-level singleton
  - Max audio size: 5 MB (enforced in endpoint layer)
  - Max duration: 60 seconds (enforced in endpoint layer via file size proxy)
  - Audio format: WAV preferred; WebM/OGG/MP3 supported via ffmpeg (if available)

Model download behaviour:
  - faster-whisper auto-downloads to ~/.cache/huggingface/hub on first run
  - If download fails (no internet), raises RuntimeError → endpoint returns 503
  - Subsequent calls use cached model (no re-download)

Error handling:
  - No faster-whisper package → ImportError → 503 with clear message
  - Audio decode failure → ValueError → 422
  - Empty transcript → returns empty string (caller decides)
  - Model not yet cached (first boot) → may take 30–60s, logged as warning
"""

from __future__ import annotations

import io
import logging
import tempfile
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# ── Model singleton ───────────────────────────────────────────────────────────

_model = None
_model_load_attempted = False


def _get_model():
    """Lazy-load and cache the faster-whisper model."""
    global _model, _model_load_attempted

    if _model is not None:
        return _model

    if _model_load_attempted:
        # Previous attempt failed — don't retry on every request
        raise RuntimeError("faster-whisper model failed to load on startup.")

    _model_load_attempted = True

    try:
        from faster_whisper import WhisperModel

        logger.info("[stt_service] Loading faster-whisper 'tiny' model…")
        _model = WhisperModel(
            "tiny",
            device="cpu",
            compute_type="int8",
        )
        logger.info("[stt_service] Model loaded successfully.")
        return _model

    except ImportError:
        raise RuntimeError(
            "Package 'faster-whisper' tidak terpasang. "
            "Jalankan: pip install faster-whisper"
        )
    except Exception as exc:
        logger.error("[stt_service] Gagal memuat model: %s", exc)
        raise RuntimeError(f"Gagal memuat STT model: {exc}") from exc


# ── Main transcription function ───────────────────────────────────────────────

async def transcribe_audio(
    audio_bytes: bytes,
    audio_filename: str = "audio.wav",
) -> dict:
    """
    Transcribe audio bytes to text using faster-whisper.

    Args:
        audio_bytes: Raw audio data (WAV, WebM, OGG, MP3).
        audio_filename: Original filename — used to infer format for temp file extension.

    Returns:
        dict with keys: transcript (str), language (str), duration_seconds (float | None)

    Raises:
        RuntimeError: If model cannot be loaded.
        ValueError: If audio cannot be decoded.
    """
    if not audio_bytes:
        raise ValueError("Audio data kosong.")

    model = _get_model()

    # Determine file extension for temp file
    ext = os.path.splitext(audio_filename)[-1].lower() or ".wav"
    if ext not in (".wav", ".webm", ".ogg", ".mp3", ".m4a", ".flac"):
        ext = ".wav"  # default safe

    # Write to temp file — faster-whisper needs a file path
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        segments, info = model.transcribe(
            tmp_path,
            language="id",           # Bahasa Indonesia
            beam_size=1,             # Fast mode (beam_size=1 = greedy)
            vad_filter=True,         # Skip silence
            vad_parameters=dict(
                min_silence_duration_ms=300,
            ),
            word_timestamps=False,   # Not needed, saves compute
        )

        # Collect all segment texts and apply math normalization
        from app.services.math_normalizer import normalize_math_terms

        raw_text = " ".join(seg.text.strip() for seg in segments).strip()
        full_text = normalize_math_terms(raw_text)

        return {
            "transcript": full_text,
            "raw_transcript": raw_text,
            "language": info.language if hasattr(info, "language") else "id",
            "duration_seconds": getattr(info, "duration", None),
        }

    except Exception as exc:
        logger.warning("[stt_service] Transkrip gagal: %s", exc)
        raise ValueError(f"Gagal memproses audio: {exc}") from exc

    finally:
        # Always clean up temp file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def reset_model_for_testing() -> None:
    """Reset model singleton — only for test isolation."""
    global _model, _model_load_attempted
    _model = None
    _model_load_attempted = False
