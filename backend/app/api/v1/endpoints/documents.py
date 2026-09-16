"""
Document management endpoints: upload, status, progress, narrations, approve.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.core.dependencies import get_current_user, require_role
from app.schemas.document import (
    ApproveResponse,
    DocumentStatusResponse,
    DocumentUploadResponse,
    NarrationListResponse,
    NarrationUpdateRequest,
    NarrationUpdateResponse,
)

router = APIRouter()


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_document(
    file: UploadFile,
    title: str,
    current_user: Annotated[dict, Depends(require_role("teacher", "admin"))],
):
    """Upload a DOCX or PDF document for processing."""
    # Validate file type
    allowed_types = {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/pdf",
    }
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Format file tidak didukung. Gunakan DOCX atau PDF.",
        )

    # TODO: Save file, trigger parsing pipeline
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Document upload not yet implemented",
    )


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: str,
    current_user: Annotated[dict, Depends(require_role("teacher", "admin"))],
):
    """Check the processing status of a document."""
    # TODO: Implement
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not yet implemented",
    )


@router.get("/{document_id}/narrations", response_model=NarrationListResponse)
async def get_narrations(
    document_id: str,
    current_user: Annotated[dict, Depends(require_role("teacher", "admin"))],
):
    """Get all AI-generated narrations for teacher review."""
    # TODO: Implement
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not yet implemented",
    )


@router.patch("/narrations/{narration_id}", response_model=NarrationUpdateResponse)
async def update_narration(
    narration_id: str,
    body: NarrationUpdateRequest,
    current_user: Annotated[dict, Depends(require_role("teacher", "admin"))],
):
    """Teacher edits an AI-generated narration."""
    # TODO: Implement
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not yet implemented",
    )


@router.post("/{document_id}/approve", response_model=ApproveResponse)
async def approve_document(
    document_id: str,
    current_user: Annotated[dict, Depends(require_role("teacher", "admin"))],
):
    """Approve all narrations and publish the learning module."""
    # TODO: Implement
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not yet implemented",
    )
