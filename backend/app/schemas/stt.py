"""
Pydantic schemas for STT (Speech-to-Text) endpoint.
"""

from pydantic import BaseModel, Field


class SttTranscribeResponse(BaseModel):
    """Response from the STT transcription endpoint."""
    transcript: str
    language: str
    duration_seconds: float | None = None
    model_used: str = "faster-whisper-tiny"
