"""
Document management endpoints: upload, status, narrations, update, approve.

All endpoints require Firebase authentication.
POST /upload and approve require 'teacher' or 'admin' role.

Pipeline for POST /upload:
  1. Validate MIME type + file size (≤ MAX_UPLOAD_SIZE_MB)
  2. Read file bytes into memory
  3. Save to UPLOAD_DIR (async, via aiofiles)
  4. Create Document row in DB (status='processing')
  5. Run parser synchronously in thread pool (parse_document)
  6. Run OCR pipeline if scanned PDF (run_ocr_if_needed)
  7. Persist MathExpression rows
  8. Update Document.parsing_status + raw_structure
  9. Return 202 with document_id + math count

Rate limits (TDD Section 1.11):
  POST /upload              — 10/hour  (CPU-heavy: parse + AI)
  GET  /{id}/status         — 120/minute (polling-friendly)
  GET  /{id}/narrations     — 60/minute (review page loads)
  PATCH /narrations/{id}    — 120/hour (teacher editing)
  POST /{id}/approve        — 20/hour  (publish action)
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Annotated, AsyncGenerator

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from sse_starlette.sse import EventSourceResponse
except ImportError:  # pragma: no cover — sse-starlette not yet installed
    # Thin compatibility shim so the endpoint can be imported before the library
    # is installed (e.g. during unit tests that never trigger the streaming loop).
    class EventSourceResponse(StreamingResponse):  # type: ignore[no-redef]
        """Fallback SSE response using StreamingResponse with text/event-stream."""

        def __init__(self, content: AsyncGenerator, **kwargs):  # type: ignore[override]
            async def _wrap():
                async for chunk in content:
                    if isinstance(chunk, dict):
                        data = chunk.get("data", "")
                        event = chunk.get("event", "")
                        prefix = f"event: {event}\n" if event else ""
                        yield f"{prefix}data: {data}\n\n".encode()
                    else:
                        yield f"data: {chunk}\n\n".encode()

            super().__init__(
                content=_wrap(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                },
            )

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.core.rate_limiter import limiter
from app.schemas.document import (
    ApproveResponse,
    DocumentDetailResponse,
    DocumentListItem,
    DocumentListResponse,
    DocumentProgressEvent,
    DocumentStatusResponse,
    DocumentUploadResponse,
    MathExpressionResponse,
    NarrationListResponse,
    NarrationUpdateRequest,
    NarrationUpdateResponse,
)
from app.services import document_service as svc
from app.services.storage import storage
from app.worker.tasks import process_document

logger = logging.getLogger(__name__)

router = APIRouter()

_ALLOWED_MIME = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/pdf",
}


# ── GET /documents ────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List teacher's documents",
)
@limiter.limit("60/minute")
async def list_documents(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    current_user: Annotated[dict, Depends(require_role("teacher", "admin"))] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    List all documents uploaded by the authenticated teacher.

    - Results are sorted newest-first.
    - Includes publication status (is_published) from linked LearningModule.
    - Does NOT include full narration list (use GET /{id} for that).

    Query params:
      limit:  max 50 (default 50)
      offset: pagination offset (default 0)
    """
    limit = min(max(1, limit), 50)   # clamp 1–50
    offset = max(0, offset)

    docs, total = await svc.list_documents_for_teacher(
        db=db,
        teacher_firebase_uid=current_user["firebase_uid"],
        limit=limit,
        offset=offset,
    )

    items = []
    for doc in docs:
        is_published = bool(doc.learning_module and doc.learning_module.is_published)
        module_id = str(doc.learning_module.id) if doc.learning_module else None
        # math_expressions not loaded — use raw_structure count if available
        math_count = (
            doc.raw_structure.get("math_count", 0)
            if doc.raw_structure
            else 0
        )
        items.append(
            DocumentListItem(
                document_id=str(doc.id),
                title=doc.title,
                file_type=doc.file_type,
                parsing_status=doc.parsing_status,
                ocr_used=doc.ocr_used,
                math_expressions_count=math_count,
                is_published=is_published,
                module_id=module_id,
                created_at=doc.created_at.isoformat(),
                updated_at=doc.updated_at.isoformat(),
            )
        )

    return DocumentListResponse(
        documents=items,
        total=total,
        limit=limit,
        offset=offset,
    )


# ── Progress helpers ──────────────────────────────────────────────────────────

#: Human-readable status messages in Bahasa Indonesia
_PROGRESS_MESSAGES: dict[str, str] = {
    "queued": "Dokumen dalam antrian pemrosesan…",
    "processing": "Dokumen sedang diproses…",
    "done": "Dokumen berhasil diproses.",
    "error": "Terjadi kesalahan saat memproses dokumen.",
}

#: Progress percentage for each status (0-100)
_PROGRESS_MAP: dict[str, int] = {
    "queued": 10,
    "processing": 50,
    "done": 100,
    "error": 0,
}

_TERMINAL_STATUSES = {"done", "error"}


def _make_progress_event(doc_id: str, parsing_status: str) -> str:
    """Serialise a DocumentProgressEvent to a JSON string for the SSE data field."""
    progress = _PROGRESS_MAP.get(parsing_status, 0)
    message = _PROGRESS_MESSAGES.get(parsing_status, "Status tidak diketahui.")
    event = DocumentProgressEvent(
        status=parsing_status,
        progress=progress,
        message=message,
        document_id=doc_id,
    )
    return event.model_dump_json()


# ── GET /documents/{document_id}/progress (SSE) ───────────────────────────────

@router.get(
    "/{document_id}/progress",
    summary="SSE stream for document parsing progress",
    response_class=EventSourceResponse,
)
@limiter.limit("60/minute")
async def stream_document_progress(
    request: Request,
    document_id: uuid.UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    Open a Server-Sent Events stream that polls document parsing status every 2 s.

    - Emits `{"status": …, "progress": 0-100, "message": …, "document_id": …}` events.
    - Stops automatically when status reaches 'done' or 'error'.
    - Stops after 60 iterations (~2 minutes) as a safety timeout.
    - Returns 403 if the authenticated user is not the document owner.
    - Returns 404 if the document does not exist.

    Progress mapping:
      queued=10, processing=50, done=100, error=0
    """
    firebase_uid = current_user["firebase_uid"]

    # ── Initial ownership check (404 / 403 before opening the stream) ──
    # First check existence without uid filter, then verify ownership.
    doc_exists = await svc.get_document_by_id(db, document_id)
    if doc_exists is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dokumen tidak ditemukan.",
        )

    doc_owned = await svc.get_document_by_id(db, document_id, firebase_uid)
    if doc_owned is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anda tidak memiliki izin untuk dokumen ini.",
        )

    async def _event_generator() -> AsyncGenerator[dict, None]:
        _MAX_ITERATIONS = 60
        _POLL_INTERVAL = 2  # seconds

        for _ in range(_MAX_ITERATIONS):
            if await request.is_disconnected():
                logger.info("SSE client disconnected for doc %s", document_id)
                return

            # Re-fetch from DB each iteration (avoid stale session cache)
            current_doc = await svc.get_document_by_id(db, document_id, firebase_uid)
            if current_doc is None:
                return

            parsing_status = current_doc.parsing_status
            yield {
                "data": _make_progress_event(str(document_id), parsing_status),
            }

            if parsing_status in _TERMINAL_STATUSES:
                return

            await asyncio.sleep(_POLL_INTERVAL)

        # Timeout — emit final event with last known status
        final_doc = await svc.get_document_by_id(db, document_id, firebase_uid)
        if final_doc:
            yield {
                "data": _make_progress_event(str(document_id), final_doc.parsing_status),
            }

    return EventSourceResponse(_event_generator())


# ── GET /documents/{document_id} ──────────────────────────────────────────────

@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Get document detail with narration progress",
)
@limiter.limit("60/minute")
async def get_document(
    request: Request,
    document_id: str,
    current_user: Annotated[dict, Depends(require_role("teacher", "admin"))] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get full detail for a single document owned by the authenticated teacher.

    Includes:
    - Parsing status and OCR info
    - Narration progress breakdown (pending/ai_generated/reviewed/approved)
    - Publication status and module_id

    Does NOT include the narration text list — use GET /{id}/narrations for that.
    """
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dokumen tidak ditemukan.",
        )

    doc = await svc.get_document_detail(
        db=db,
        document_id=doc_uuid,
        teacher_firebase_uid=current_user["firebase_uid"],
    )
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dokumen tidak ditemukan.",
        )

    # Narration progress by status
    exprs = doc.math_expressions or []
    status_counts = {"pending": 0, "ai_generated": 0, "reviewed": 0, "approved": 0}
    for e in exprs:
        status_counts[e.status] = status_counts.get(e.status, 0) + 1

    is_published = bool(doc.learning_module and doc.learning_module.is_published)
    module_id = str(doc.learning_module.id) if doc.learning_module else None
    published_at = (
        doc.learning_module.published_at.isoformat()
        if doc.learning_module and doc.learning_module.published_at
        else None
    )

    return DocumentDetailResponse(
        document_id=str(doc.id),
        title=doc.title,
        file_type=doc.file_type,
        parsing_status=doc.parsing_status,
        ocr_used=doc.ocr_used,
        error_code=doc.error_code,
        math_expressions_count=len(exprs),
        narrations_pending=status_counts["pending"],
        narrations_ai_generated=status_counts["ai_generated"],
        narrations_reviewed=status_counts["reviewed"],
        narrations_approved=status_counts["approved"],
        is_published=is_published,
        module_id=module_id,
        published_at=published_at,
        created_at=doc.created_at.isoformat(),
        updated_at=doc.updated_at.isoformat(),
    )


# ── POST /documents/upload ────────────────────────────────────────────────────

@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload DOCX/PDF document for parsing",
)
@limiter.limit("10/hour")
async def upload_document(
    request: Request,
    file: Annotated[UploadFile, File(description="DOCX or PDF file, max 20 MB")],
    title: Annotated[str, Form(min_length=1, max_length=500)],
    current_user: Annotated[dict, Depends(require_role("teacher", "admin"))],
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a DOCX or PDF document.

    Steps:
    1. Validate MIME + file size
    2. Read file bytes
    3. Look up teacher
    4. Save file to storage (local disk or GCS)
    5. Create Document record (status=queued)
    6. Flush to DB so worker can read the record
    7. Enqueue Celery task (non-blocking) → return 202 immediately
    """
    from app.core.config import settings

    # ── 1. Validate MIME type ──
    if file.content_type not in _ALLOWED_MIME:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "error_code": "DOC_002",
                "message": "Format file tidak didukung. Gunakan DOCX atau PDF.",
            },
        )

    file_type = svc.get_file_type(file.content_type)  # 'docx' | 'pdf'

    # ── 2. Read bytes + validate size ──
    file_bytes = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error_code": "DOC_001",
                "message": f"Ukuran file melebihi {settings.MAX_UPLOAD_SIZE_MB} MB.",
            },
        )

    if len(file_bytes) < 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "DOC_003",
                "message": "File tampaknya kosong atau rusak.",
            },
        )

    # ── 3. Look up teacher in DB ──
    firebase_uid = current_user["firebase_uid"]
    teacher = await svc.get_user_by_firebase_uid(db, firebase_uid)
    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Profil guru tidak ditemukan. Daftarkan profil terlebih dahulu.",
        )

    # ── 4. Save file to storage (local disk or GCS) ──
    filename = file.filename or f"upload.{file_type}"
    file_path = await storage.save(file_bytes, filename)

    # ── 5. Create Document record (status=queued) ──
    doc = await svc.create_document_record(
        db=db,
        teacher_id=teacher.id,
        title=title,
        file_type=file_type,
        file_path=file_path,
        parsing_status="queued",
    )

    # ── 6. Flush to DB so worker can read the document ──
    await db.flush()

    # ── 7. Enqueue Celery task (async, non-blocking) ──
    process_document.delay(str(doc.id))
    logger.info("Queued process_document task for doc %s", doc.id)

    # Session commit happens in get_db() on exit
    logger.info("Upload queued: doc %s → Celery worker", doc.id)

    return DocumentUploadResponse(
        document_id=str(doc.id),
        title=doc.title,
        status="queued",
        message="Dokumen berhasil diunggah dan sedang diproses. Periksa status di halaman review.",
        math_expressions_count=0,
        ocr_used="none",
    )


# ── GET /documents/{document_id}/status ──────────────────────────────────────

@router.get(
    "/{document_id}/status",
    response_model=DocumentStatusResponse,
    summary="Get document parsing status",
)
@limiter.limit("120/minute")
async def get_document_status(
    request: Request,
    document_id: str,
    current_user: Annotated[dict, Depends(require_role("teacher", "admin"))],
    db: AsyncSession = Depends(get_db),
):
    """Check the processing status of a document. Rate limited: 120/minute."""
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dokumen tidak ditemukan.")

    doc = await svc.get_document_by_id(db, doc_uuid, current_user["firebase_uid"])
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dokumen tidak ditemukan.")

    return DocumentStatusResponse(
        document_id=str(doc.id),
        status=doc.parsing_status,
        ocr_used=doc.ocr_used,
        math_expressions_count=len(doc.math_expressions),
        created_at=doc.created_at.isoformat(),
    )


# ── GET /documents/{document_id}/narrations ───────────────────────────────────

@router.get(
    "/{document_id}/narrations",
    response_model=NarrationListResponse,
    summary="Get math expressions for teacher review",
)
@limiter.limit("60/minute")
async def get_narrations(
    request: Request,
    document_id: str,
    current_user: Annotated[dict, Depends(require_role("teacher", "admin"))],
    db: AsyncSession = Depends(get_db),
):
    """Get all math expressions (with AI/teacher narrations) for a document. Rate limited: 60/minute."""
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dokumen tidak ditemukan.")

    doc, expressions = await svc.get_narrations_for_document(
        db, doc_uuid, current_user["firebase_uid"]
    )
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dokumen tidak ditemukan.")

    return NarrationListResponse(
        document_id=str(doc.id),
        title=doc.title,
        expressions=[
            MathExpressionResponse(
                id=str(e.id),
                original_notation=e.original_notation,
                latex=e.latex_representation,
                ai_narration=e.ai_narration,
                teacher_narration=e.teacher_narration,
                status=e.status,
                position_order=e.position_order,
            )
            for e in sorted(expressions, key=lambda x: x.position_order)
        ],
    )


# ── PATCH /documents/narrations/{narration_id} ────────────────────────────────

@router.patch(
    "/narrations/{narration_id}",
    response_model=NarrationUpdateResponse,
    summary="Teacher edits a narration",
)
@limiter.limit("120/hour")
async def update_narration(
    request: Request,
    narration_id: str,
    body: NarrationUpdateRequest,
    current_user: Annotated[dict, Depends(require_role("teacher", "admin"))],
    db: AsyncSession = Depends(get_db),
):
    """Teacher manually edits an AI-generated narration. Rate limited: 120/hour."""
    try:
        narration_uuid = uuid.UUID(narration_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Narasi tidak ditemukan.")

    expr = await svc.update_narration(
        db=db,
        narration_id=narration_uuid,
        teacher_narration=body.teacher_narration,
        teacher_firebase_uid=current_user["firebase_uid"],
    )
    if expr is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Narasi tidak ditemukan.")

    return NarrationUpdateResponse(
        id=str(expr.id),
        status=expr.status,
        teacher_narration=expr.teacher_narration,
    )


# ── POST /documents/{document_id}/approve ─────────────────────────────────────

@router.post(
    "/{document_id}/approve",
    response_model=ApproveResponse,
    summary="Approve narrations and publish module",
)
@limiter.limit("20/hour")
async def approve_document(
    request: Request,
    document_id: str,
    current_user: Annotated[dict, Depends(require_role("teacher", "admin"))],
    db: AsyncSession = Depends(get_db),
):
    """
    Approve all narrations and publish as an accessible learning module.
    Creates or updates the LearningModule with semantic HTML content.
    Rate limited: 20/hour.
    """
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dokumen tidak ditemukan.")

    module = await svc.approve_and_publish(
        db=db,
        document_id=doc_uuid,
        teacher_firebase_uid=current_user["firebase_uid"],
    )
    if module is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dokumen tidak ditemukan.")

    return ApproveResponse(
        module_id=str(module.id),
        document_id=document_id,
        is_published=module.is_published,
        published_at=module.published_at.isoformat(),
    )
