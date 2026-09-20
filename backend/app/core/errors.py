"""
Error taxonomy for InklusifMath backend.

Centralized error codes matching TDD Section 10 (Error Handling).
All structured errors use this taxonomy so frontend can display
accessible, user-friendly messages.

Format: {domain}_{number} — e.g., DOC_001, AI_001, STT_001

Usage in endpoints:
    from app.core.errors import AppError, ErrorCode
    raise AppError(ErrorCode.PARSE_001)

    # Or with custom message:
    raise AppError(ErrorCode.AI_001, detail="Gemini timed out after 2 retries")

Usage in FastAPI exception handler:
    from app.core.errors import app_error_handler
    app.add_exception_handler(AppError, app_error_handler)
"""

from __future__ import annotations

from enum import Enum
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


# ── Error code registry ───────────────────────────────────────────────────────

class ErrorCode(str, Enum):
    """All structured error codes used by the InklusifMath backend."""

    # Document upload errors (DOC)
    DOC_001 = "DOC_001"   # File > 20MB (413)
    DOC_002 = "DOC_002"   # Format tidak didukung (415)
    DOC_003 = "DOC_003"   # File corrupt / terlalu kecil (422)

    # Parsing errors (PARSE)
    PARSE_001 = "PARSE_001"  # Gagal ekstraksi teks (422)
    PARSE_002 = "PARSE_002"  # OCR fallback gagal (422)
    PARSE_003 = "PARSE_003"  # Dokumen tanpa rumus — informational only

    # AI Clarifier errors (AI)
    AI_001 = "AI_001"    # Gemini timeout > 30s → retry 2x (503)
    AI_002 = "AI_002"    # Gemini down → graceful degradation (503)
    AI_003 = "AI_003"    # Tutor Gemini timeout → fallback response (503)

    # STT errors (STT)
    STT_001 = "STT_001"  # Model tidak tersedia (503)
    STT_002 = "STT_002"  # File audio kosong (422)
    STT_003 = "STT_003"  # File terlalu besar (413)
    STT_004 = "STT_004"  # Format tidak didukung (415)
    STT_005 = "STT_005"  # Audio tidak dapat diproses (422)

    # Auth errors (AUTH)
    AUTH_001 = "AUTH_001"  # Token expired → Firebase auto-refresh
    AUTH_002 = "AUTH_002"  # Refresh token expired → redirect login


# ── Default messages ──────────────────────────────────────────────────────────

_DEFAULT_MESSAGES: dict[ErrorCode, str] = {
    # DOC
    ErrorCode.DOC_001: "Ukuran file melebihi batas maksimum. Gunakan file di bawah 20 MB.",
    ErrorCode.DOC_002: "Format file tidak didukung. Gunakan DOCX atau PDF.",
    ErrorCode.DOC_003: "File tampaknya kosong atau rusak. Coba unggah file lain.",

    # PARSE
    ErrorCode.PARSE_001: "Gagal memproses dokumen. Pastikan file tidak rusak dan dapat dibuka.",
    ErrorCode.PARSE_002: "OCR gagal mengenali teks dari dokumen scan. Coba dokumen digital (bukan scan).",
    ErrorCode.PARSE_003: "Dokumen berhasil diproses. Tidak ada ekspresi matematika yang ditemukan.",

    # AI
    ErrorCode.AI_001: "Layanan AI tidak merespons setelah beberapa percobaan. Coba lagi dalam beberapa menit.",
    ErrorCode.AI_002: "Layanan AI sedang tidak tersedia. Narasi akan diisi manual oleh guru.",
    ErrorCode.AI_003: "Tutor tidak dapat merespons saat ini. Coba lagi atau ketik pertanyaan.",

    # STT
    ErrorCode.STT_001: "Layanan transkripsi tidak tersedia. Gunakan input teks.",
    ErrorCode.STT_002: "File audio kosong. Silakan rekam ulang.",
    ErrorCode.STT_003: "File audio terlalu besar. Maksimum 5 MB.",
    ErrorCode.STT_004: "Format audio tidak didukung. Gunakan WAV, WebM, OGG, atau MP3.",
    ErrorCode.STT_005: "Gagal memproses audio. Pastikan rekaman berisi suara yang jelas.",

    # AUTH
    ErrorCode.AUTH_001: "Sesi login telah berakhir. Memperbarui sesi secara otomatis.",
    ErrorCode.AUTH_002: "Sesi login telah kedaluwarsa. Silakan masuk kembali.",
}

# ── Default HTTP status codes ─────────────────────────────────────────────────

_DEFAULT_STATUS_CODES: dict[ErrorCode, int] = {
    ErrorCode.DOC_001: 413,
    ErrorCode.DOC_002: 415,
    ErrorCode.DOC_003: 422,
    ErrorCode.PARSE_001: 422,
    ErrorCode.PARSE_002: 422,
    ErrorCode.PARSE_003: 200,   # Informational — not an error HTTP status
    ErrorCode.AI_001: 503,
    ErrorCode.AI_002: 503,
    ErrorCode.AI_003: 503,
    ErrorCode.STT_001: 503,
    ErrorCode.STT_002: 422,
    ErrorCode.STT_003: 413,
    ErrorCode.STT_004: 415,
    ErrorCode.STT_005: 422,
    ErrorCode.AUTH_001: 401,
    ErrorCode.AUTH_002: 401,
}


# ── Custom exception ──────────────────────────────────────────────────────────

class AppError(Exception):
    """
    Structured application error with an error code.

    Raise this in service/endpoint code instead of bare HTTPException
    to ensure consistent error format and accessibility message quality.

    Example:
        raise AppError(ErrorCode.PARSE_001)
        raise AppError(ErrorCode.AI_001, detail="timeout after 2 retries")
        raise AppError(ErrorCode.DOC_001, status_code=413, message="Terlalu besar")
    """

    def __init__(
        self,
        code: ErrorCode,
        *,
        message: str | None = None,
        detail: str | None = None,
        status_code: int | None = None,
        extra: dict | None = None,
    ) -> None:
        self.code = code
        self.message = message or _DEFAULT_MESSAGES.get(code, str(code))
        self.detail = detail
        self.status_code = status_code or _DEFAULT_STATUS_CODES.get(code, 500)
        self.extra = extra or {}
        super().__init__(self.message)

    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException for use in endpoint handlers."""
        body: dict = {
            "error_code": self.code.value,
            "message": self.message,
        }
        if self.detail:
            body["detail"] = self.detail
        body.update(self.extra)
        return HTTPException(status_code=self.status_code, detail=body)


# ── FastAPI exception handler ─────────────────────────────────────────────────

async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """
    Global exception handler for AppError.

    Register with:
        app.add_exception_handler(AppError, app_error_handler)
    """
    body: dict = {
        "error_code": exc.code.value,
        "message": exc.message,
    }
    if exc.detail:
        body["detail"] = exc.detail
    body.update(exc.extra)
    return JSONResponse(status_code=exc.status_code, content=body)


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_error_message(code: ErrorCode) -> str:
    """Get the default user-facing message for an error code."""
    return _DEFAULT_MESSAGES.get(code, str(code))


def get_error_status(code: ErrorCode) -> int:
    """Get the default HTTP status code for an error code."""
    return _DEFAULT_STATUS_CODES.get(code, 500)
