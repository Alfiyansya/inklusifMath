"""
Pydantic schemas for document and narration endpoints.
"""

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    document_id: str
    title: str
    status: str
    message: str


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
