"""
Pydantic schemas for document and narration endpoints.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    document_id: str
    title: str
    status: str
    message: str
    math_expressions_count: int = 0
    ocr_used: str = "none"


class DocumentStatusResponse(BaseModel):
    document_id: str
    status: str
    ocr_used: str
    math_expressions_count: int
    created_at: str


class MathExpressionResponse(BaseModel):
    id: str
    original_notation: str
    latex: str | None
    ai_narration: str | None
    teacher_narration: str | None
    status: str
    position_order: int

    model_config = {"from_attributes": True}


class NarrationListResponse(BaseModel):
    document_id: str
    title: str
    expressions: list[MathExpressionResponse]


class NarrationUpdateRequest(BaseModel):
    teacher_narration: str = Field(min_length=1)


class NarrationUpdateResponse(BaseModel):
    id: str
    status: str
    teacher_narration: str


class ApproveResponse(BaseModel):
    module_id: str
    document_id: str
    is_published: bool
    published_at: str


# ── GET /documents (listing) ──────────────────────────────────────────────────

class DocumentListItem(BaseModel):
    """Summary row for the teacher's document listing page."""
    document_id: str
    title: str
    file_type: str
    parsing_status: str
    ocr_used: str
    math_expressions_count: int
    is_published: bool
    module_id: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    documents: list[DocumentListItem]
    total: int
    limit: int
    offset: int


# ── GET /documents/{id} (detail) ─────────────────────────────────────────────

class DocumentDetailResponse(BaseModel):
    """Full document detail with narration progress summary."""
    document_id: str
    title: str
    file_type: str
    parsing_status: str
    ocr_used: str
    error_code: str | None
    # Narration progress
    math_expressions_count: int
    narrations_pending: int
    narrations_ai_generated: int
    narrations_reviewed: int
    narrations_approved: int
    # Publication
    is_published: bool
    module_id: str | None
    published_at: str | None
    # Timestamps
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


# ── SSE progress event ────────────────────────────────────────────────────────

class DocumentProgressEvent(BaseModel):
    """Payload emitted as a Server-Sent Event during document parsing."""

    status: str       # queued | processing | done | error
    progress: int     # 0-100
    message: str      # human-readable status in Bahasa Indonesia
    document_id: str
