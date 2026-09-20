"""
Document service layer.

Handles business logic for:
  - Saving uploaded files to disk
  - Creating Document records in PostgreSQL
  - Running DOCX/PDF parsers
  - Persisting MathExpression records from parsed output
  - Generating AI narrations via AiClarifier (Gemini 2.0 Flash + Leksikon Baku)
  - Querying document status and narrations
  - Updating teacher narrations
  - Approving documents → creating LearningModule

This module is intentionally synchronous-safe for CPU-bound parsing calls
(run_in_executor is used in the endpoint layer if needed).
AI narration uses async (awaited in the endpoint layer).
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

import aiofiles
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.document import Document, LearningModule, MathExpression
from app.models.user import User
from app.services.parsing import DocxParser, PdfParser
from app.services.parsing.models import ParsedDocument

logger = logging.getLogger(__name__)

_UPLOAD_DIR = Path(settings.UPLOAD_DIR)
_MAX_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

_ALLOWED_MIME = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/pdf": "pdf",
}


# ── File helpers ──────────────────────────────────────────────────────────────

async def save_upload_file(file_bytes: bytes, filename: str) -> Path:
    """
    Persist uploaded bytes to UPLOAD_DIR/<uuid>_<filename>.
    Returns the absolute path.
    """
    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}_{Path(filename).name}"
    dest = _UPLOAD_DIR / safe_name
    async with aiofiles.open(dest, "wb") as f:
        await f.write(file_bytes)
    logger.info("Saved upload: %s (%d bytes)", dest, len(file_bytes))
    return dest


def get_file_type(content_type: str) -> str | None:
    """Return 'docx' | 'pdf' | None from MIME type."""
    return _ALLOWED_MIME.get(content_type)


# ── Parsing ───────────────────────────────────────────────────────────────────

def parse_document(file_bytes: bytes, file_type: str, title: str) -> ParsedDocument:
    """
    Run the appropriate parser for file_type.
    Called synchronously — wrap with run_in_executor for async contexts.
    """
    if file_type == "docx":
        return DocxParser().parse(file_bytes, title=title)
    if file_type == "pdf":
        return PdfParser().parse(file_bytes, title=title)
    raise ValueError(f"Unsupported file type: {file_type}")


async def run_ocr_if_needed(
    file_bytes: bytes,
    parsed: ParsedDocument,
    title: str,
) -> ParsedDocument:
    """
    If parse_document returned a scanned PDF (ocr_used='pending_ocr'),
    run the full OCR pipeline (GCV + optional Mathpix) and return an
    enriched ParsedDocument.

    If OCR is not needed or fails gracefully, returns the original `parsed`.

    This is called in the upload endpoint AFTER parse_document() and BEFORE
    persisting MathExpression records.
    """
    if parsed.ocr_used != "pending_ocr":
        return parsed  # digital PDF or DOCX — no OCR needed

    logger.info(
        "Document '%s' is a scanned PDF — starting OCR pipeline", title
    )

    try:
        from app.services.ocr import OcrPipelineError, run_ocr_pipeline

        ocr_result = await run_ocr_pipeline(pdf_bytes=file_bytes, title=title)
        logger.info(
            "OCR pipeline succeeded: method=%s pages_ok=%d math_images=%d/%d",
            ocr_result.ocr_method,
            ocr_result.pages_ocr_ok,
            ocr_result.math_images_resolved,
            ocr_result.math_images_found,
        )
        return ocr_result.parsed_document

    except Exception as exc:  # noqa: BLE001
        # OCR failure is non-fatal — keep the 'pending_ocr' status and log
        logger.error(
            "OCR pipeline failed for '%s': %s. Document stays as pending_ocr.",
            title,
            exc,
        )
        return parsed


# ── AI Narration ──────────────────────────────────────────────────────────────

async def generate_ai_narrations(
    db: AsyncSession,
    document_id: "uuid.UUID",
    expressions: list["MathExpression"],
) -> int:
    """
    Generate AI narrations for all MathExpression records of a document.

    Calls AiClarifier.clarify_batch() then persists:
      - MathExpression.ai_narration = narration text
      - MathExpression.status = 'ai_generated' (if successful)

    Returns:
        Number of expressions successfully narrated.

    Raises:
        Does NOT raise — logs errors and returns partial count.
        Expressions that fail get ai_narration=None and status stays 'pending'.
    """
    if not expressions:
        return 0

    # Lazy import to avoid circular import and allow mocking in tests
    from app.services.ai.clarifier import (
        AiClarifier,
        GeminiTimeoutError,
        GeminiUnavailableError,
    )

    clarifier = AiClarifier()

    # Build input list for clarifier
    expr_inputs = [
        {
            "position_order": e.position_order,
            "original_notation": e.original_notation,
            "latex": e.latex_representation or e.original_notation,
        }
        for e in expressions
    ]

    try:
        results = await clarifier.clarify_batch(expr_inputs)
    except GeminiTimeoutError as exc:
        # AI_001: exhausted retries — log with code, return 0 (non-fatal)
        logger.error(
            "[AI_001] Gemini timeout for document %s after %d retries: %s",
            document_id, 2, exc,
        )
        return 0
    except GeminiUnavailableError as exc:
        # AI_002: Gemini down — log with code, return 0 (non-fatal)
        logger.error(
            "[AI_002] Gemini unavailable for document %s: %s",
            document_id, exc,
        )
        return 0
    except Exception as exc:
        logger.error(
            "AI clarifier batch failed for document %s: %s", document_id, exc
        )
        return 0

    # Map results by position_order for fast lookup
    result_map = {r.position_order: r for r in results}

    success_count = 0
    for expr in expressions:
        result = result_map.get(expr.position_order)
        if result and result.narration:
            expr.ai_narration = result.narration
            expr.status = "ai_generated"
            success_count += 1
        else:
            logger.warning(
                "No narration for expression position=%d (doc=%s)",
                expr.position_order,
                document_id,
            )

    await db.flush()
    logger.info(
        "AI narration complete: %d/%d succeeded for document %s",
        success_count,
        len(expressions),
        document_id,
    )
    return success_count


# ── Database operations ───────────────────────────────────────────────────────


async def get_user_by_firebase_uid(
    db: AsyncSession, firebase_uid: str
) -> User | None:
    """Look up a User record by firebase_uid."""
    result = await db.execute(
        select(User).where(User.firebase_uid == firebase_uid)
    )
    return result.scalar_one_or_none()


async def create_document_record(
    db: AsyncSession,
    teacher_id: uuid.UUID,
    title: str,
    file_type: str,
    file_path: str,
    parsing_status: str = "processing",
) -> Document:
    """Insert a new Document row and return it (flushed, not committed)."""
    doc = Document(
        teacher_id=teacher_id,
        title=title,
        file_type=file_type,
        original_file_path=file_path,
        parsing_status=parsing_status,
    )
    db.add(doc)
    await db.flush()  # populate doc.id without committing
    return doc


async def save_math_expressions(
    db: AsyncSession,
    document_id: uuid.UUID,
    parsed: ParsedDocument,
) -> list[MathExpression]:
    """
    Persist all MathExpressionResult objects from a ParsedDocument.
    Returns the list of created ORM objects.
    """
    expressions: list[MathExpression] = []
    for expr in parsed.math_expressions:
        me = MathExpression(
            document_id=document_id,
            original_notation=expr.original_notation,
            latex_representation=expr.latex_representation or None,
            status="pending",
            position_order=expr.position_order,
        )
        db.add(me)
        expressions.append(me)
    if expressions:
        await db.flush()
    return expressions


async def update_document_after_parse(
    db: AsyncSession,
    doc: Document,
    parsed: ParsedDocument,
) -> Document:
    """
    Update a Document record with parsing results:
    - Set parsing_status to 'parsed' (or 'failed' on error)
    - Store raw_structure JSONB
    - Store ocr_used flag
    """
    if parsed.parse_error:
        doc.parsing_status = "failed"
        doc.error_code = "PARSE_001"
    else:
        doc.parsing_status = "parsed"
        doc.ocr_used = parsed.ocr_used
        doc.raw_structure = parsed.raw_structure

    doc.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return doc



async def list_documents_for_teacher(
    db: AsyncSession,
    teacher_firebase_uid: str,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Document], int]:
    """
    List all documents owned by a teacher, newest first.

    Returns (documents, total_count) for pagination.
    Uses composite index ix_documents_teacher_created (teacher_id, created_at).
    Does NOT load math_expressions (heavy) — use get_document_detail for that.
    """
    teacher = await get_user_by_firebase_uid(db, teacher_firebase_uid)
    if teacher is None:
        return [], 0

    # Count query
    count_stmt = (
        select(func.count(Document.id))
        .where(Document.teacher_id == teacher.id)
    )
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    # Listing query — load learning_module to know publish status
    stmt = (
        select(Document)
        .options(selectinload(Document.learning_module))
        .where(Document.teacher_id == teacher.id)
        .order_by(Document.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    docs = list(result.scalars().all())

    return docs, total


async def get_document_detail(
    db: AsyncSession,
    document_id: uuid.UUID,
    teacher_firebase_uid: str,
) -> Document | None:
    """
    Get full document detail with math_expressions + learning_module.
    Verifies ownership — returns None if not found or not owned by teacher.
    """
    teacher = await get_user_by_firebase_uid(db, teacher_firebase_uid)
    if teacher is None:
        return None

    stmt = (
        select(Document)
        .options(
            selectinload(Document.math_expressions),
            selectinload(Document.learning_module),
        )
        .where(
            Document.id == document_id,
            Document.teacher_id == teacher.id,
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_document_by_id(
    db: AsyncSession,
    document_id: uuid.UUID,
    teacher_firebase_uid: str | None = None,
) -> Document | None:
    """
    Fetch a Document by ID.
    If teacher_firebase_uid is given, also verify ownership.
    Loads related math_expressions eagerly.
    """
    stmt = (
        select(Document)
        .options(selectinload(Document.math_expressions))
        .where(Document.id == document_id)
    )
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()

    if doc is None:
        return None

    if teacher_firebase_uid is not None:
        teacher = await get_user_by_firebase_uid(db, teacher_firebase_uid)
        if teacher is None or doc.teacher_id != teacher.id:
            return None  # not authorized

    return doc


async def get_narrations_for_document(
    db: AsyncSession,
    document_id: uuid.UUID,
    teacher_firebase_uid: str,
) -> tuple[Document | None, list[MathExpression]]:
    """
    Get all math expressions for a document.
    Returns (document, expressions) or (None, []) if not found/authorized.
    """
    doc = await get_document_by_id(db, document_id, teacher_firebase_uid)
    if doc is None:
        return None, []
    return doc, doc.math_expressions


async def update_narration(
    db: AsyncSession,
    narration_id: uuid.UUID,
    teacher_narration: str,
    teacher_firebase_uid: str,
) -> MathExpression | None:
    """
    Update teacher_narration on a MathExpression.
    Verifies ownership via document.teacher_id.
    Returns updated expression, or None if not found/unauthorized.
    """
    stmt = (
        select(MathExpression)
        .options(selectinload(MathExpression.document))
        .where(MathExpression.id == narration_id)
    )
    result = await db.execute(stmt)
    expr = result.scalar_one_or_none()

    if expr is None:
        return None

    # Check ownership
    teacher = await get_user_by_firebase_uid(db, teacher_firebase_uid)
    if teacher is None or expr.document.teacher_id != teacher.id:
        return None

    expr.teacher_narration = teacher_narration
    expr.status = "reviewed"
    await db.flush()
    return expr


async def approve_and_publish(
    db: AsyncSession,
    document_id: uuid.UUID,
    teacher_firebase_uid: str,
) -> LearningModule | None:
    """
    Mark all expressions as approved and create/update the LearningModule.
    Returns the LearningModule or None if not authorized.
    """
    doc = await get_document_by_id(db, document_id, teacher_firebase_uid)
    if doc is None:
        return None

    # Approve all expressions
    for expr in doc.math_expressions:
        if expr.status in ("pending", "ai_generated", "reviewed"):
            expr.status = "approved"

    # Build simple HTML content from raw_structure blocks
    html_content = _build_html_from_structure(doc)

    # Get teacher user record for approved_by
    teacher = await get_user_by_firebase_uid(db, teacher_firebase_uid)

    # Create or update LearningModule
    if doc.learning_module:
        module = doc.learning_module
        module.html_content = html_content
        module.is_published = True
        module.published_at = datetime.now(timezone.utc)
        module.approved_by = teacher.id if teacher else None
    else:
        module = LearningModule(
            document_id=doc.id,
            html_content=html_content,
            is_published=True,
            published_at=datetime.now(timezone.utc),
            approved_by=teacher.id if teacher else None,
        )
        db.add(module)

    doc.parsing_status = "parsed"
    await db.flush()
    return module


async def toggle_module_publish(
    db: AsyncSession,
    module_id: uuid.UUID,
    teacher_firebase_uid: str,
    publish: bool,
) -> "LearningModule | None":
    """
    Toggle the is_published flag on a LearningModule.

    Verifies that the requesting teacher owns the linked Document.
    - If publish=True: sets is_published=True and published_at=now()
    - If publish=False: sets is_published=False and published_at=None

    Returns the updated LearningModule, or None if not found / not authorized.
    """
    teacher = await get_user_by_firebase_uid(db, teacher_firebase_uid)
    if teacher is None:
        return None

    stmt = (
        select(LearningModule)
        .options(selectinload(LearningModule.document))
        .where(LearningModule.id == module_id)
    )
    result = await db.execute(stmt)
    module = result.scalar_one_or_none()

    if module is None:
        return None

    # Verify ownership via the linked document
    if module.document is None or module.document.teacher_id != teacher.id:
        return None

    module.is_published = publish
    module.published_at = datetime.now(timezone.utc) if publish else None
    await db.flush()
    return module


def _build_html_from_structure(doc: Document) -> str:
    """
    Build a minimal semantic HTML string from raw_structure blocks.
    Used as placeholder until the AI clarifier generates rich HTML.
    """
    if not doc.raw_structure or "blocks" not in doc.raw_structure:
        return f"<article><h1>{doc.title}</h1></article>"

    lines = [f"<article aria-label=\"{doc.title}\">"]

    for block in doc.raw_structure.get("blocks", []):
        btype = block.get("type", "paragraph")
        text = block.get("text", "").replace("<", "&lt;").replace(">", "&gt;")

        if btype == "heading1":
            lines.append(f"  <h1>{text}</h1>")
        elif btype == "heading2":
            lines.append(f"  <h2>{text}</h2>")
        elif btype == "heading3":
            lines.append(f"  <h3>{text}</h3>")
        elif btype == "table":
            lines.append(f"  <pre>{text}</pre>")
        else:
            lines.append(f"  <p>{text}</p>")

    lines.append("</article>")
    return "\n".join(lines)
