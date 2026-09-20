"""
Celery tasks for InklusifMath.

Main task:
  process_document(document_id)  — parse, OCR, AI narration, update status
"""
from __future__ import annotations

import asyncio
import logging
import uuid

from celery import shared_task

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine from a sync Celery task context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("closed")
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@shared_task(
    bind=True,
    name="app.worker.tasks.process_document",
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def process_document(self, document_id: str) -> dict:
    """
    Async document processing pipeline.

    Steps:
      1. Load Document from DB
      2. Download file bytes from storage (local or GCS)
      3. parse_document() — DOCX/PDF parser
      4. run_ocr_if_needed() — GCV + Mathpix for scanned PDFs
      5. save_math_expressions() — persist to DB
      6. generate_ai_narrations() — Gemini batch narration
      7. update_document_after_parse() — set status='parsed'

    On failure: sets Document.parsing_status='failed', Document.error_code='PARSE_001'.
    """
    return _run_async(_process_document_async(self, document_id))


async def _process_document_async(task, document_id: str) -> dict:
    """Actual async implementation of the document processing task."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.core.database import async_session_maker
    from app.models.document import Document
    from app.services import document_service as svc
    from app.services.storage import storage
    from sqlalchemy import select

    doc_uuid = uuid.UUID(document_id)
    logger.info("[task] Starting process_document for %s", document_id)

    async with async_session_maker() as db:
        # 1. Load document
        result = await db.execute(select(Document).where(Document.id == doc_uuid))
        doc = result.scalar_one_or_none()
        if doc is None:
            logger.error("[task] Document %s not found", document_id)
            return {"status": "not_found", "document_id": document_id}

        doc.parsing_status = "processing"
        await db.flush()

        try:
            # 2. Download file bytes
            file_bytes = await storage.load(doc.original_file_path)
            file_type = doc.file_type

            # 3. Parse
            import asyncio as _asyncio
            loop = _asyncio.get_running_loop()
            parsed = await loop.run_in_executor(
                None, svc.parse_document, file_bytes, file_type, doc.title
            )

            # 4. OCR if needed
            parsed = await svc.run_ocr_if_needed(file_bytes, parsed, doc.title)

            # 5. Save math expressions
            saved_expressions = await svc.save_math_expressions(db, doc.id, parsed)

            # 6. AI narrations (best-effort)
            from app.core.config import settings
            ai_count = 0
            if saved_expressions and settings.GEMINI_API_KEY:
                try:
                    ai_count = await svc.generate_ai_narrations(db, doc.id, saved_expressions)
                except Exception as exc:
                    logger.warning("[task] AI narration failed (non-fatal): %s", exc)

            # 7. Update document
            await svc.update_document_after_parse(db, doc, parsed)
            await db.commit()

            logger.info(
                "[task] Done: doc=%s math=%d ai=%d ocr=%s",
                document_id, parsed.math_count, ai_count, parsed.ocr_used
            )
            return {
                "status": "done",
                "document_id": document_id,
                "math_count": parsed.math_count,
                "ai_count": ai_count,
                "ocr_used": parsed.ocr_used,
            }

        except Exception as exc:
            logger.error("[task] process_document failed for %s: %s", document_id, exc)
            doc.parsing_status = "failed"
            doc.error_code = "PARSE_001"
            await db.flush()
            await db.commit()

            # Retry up to max_retries
            raise task.retry(exc=exc)
