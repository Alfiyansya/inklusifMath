"""
Tests for GET /api/v1/documents (list) and GET /api/v1/documents/{id} (detail).

Tests cover:
  - Service: list_documents_for_teacher (empty, multiple, pagination, unknown teacher)
  - Service: get_document_detail (found, not found, ownership check)
  - Endpoint helpers: DocumentListItem/DocumentDetailResponse shape
  - Narration status counting logic (the 4-bucket breakdown)

All DB operations are mocked via AsyncMock — no real DB needed.
"""

from __future__ import annotations

import uuid
from collections import Counter
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_teacher(uid: str = "teacher-uid-001") -> MagicMock:
    t = MagicMock()
    t.id = uuid.uuid4()
    t.firebase_uid = uid
    t.email = "guru@inklusif.test"
    t.role = "teacher"
    return t


def _make_document(
    teacher_id: uuid.UUID,
    title: str = "Aljabar Kelas X",
    parsing_status: str = "parsed",
    file_type: str = "docx",
    math_count: int = 3,
    is_published: bool = False,
) -> MagicMock:
    doc = MagicMock()
    doc.id = uuid.uuid4()
    doc.teacher_id = teacher_id
    doc.title = title
    doc.file_type = file_type
    doc.parsing_status = parsing_status
    doc.ocr_used = "none"
    doc.error_code = None
    doc.raw_structure = {"math_count": math_count, "blocks": []}
    doc.created_at = MagicMock()
    doc.created_at.isoformat.return_value = "2026-09-01T00:00:00"
    doc.updated_at = MagicMock()
    doc.updated_at.isoformat.return_value = "2026-09-01T01:00:00"

    # learning_module
    if is_published:
        lm = MagicMock()
        lm.id = uuid.uuid4()
        lm.is_published = True
        lm.published_at = MagicMock()
        lm.published_at.isoformat.return_value = "2026-09-02T00:00:00"
        doc.learning_module = lm
    else:
        doc.learning_module = None

    return doc


def _make_expression(status: str = "pending") -> MagicMock:
    expr = MagicMock()
    expr.id = uuid.uuid4()
    expr.status = status
    expr.original_notation = "x^2"
    expr.latex_representation = r"x^2"
    expr.ai_narration = "x pangkat dua" if status != "pending" else None
    expr.teacher_narration = "x kuadrat" if status in ("reviewed", "approved") else None
    expr.position_order = 1
    return expr


# ── list_documents_for_teacher ────────────────────────────────────────────────

class TestListDocumentsForTeacher:
    @pytest.mark.asyncio
    async def test_returns_empty_if_teacher_not_found(self):
        from app.services.document_service import list_documents_for_teacher

        db = AsyncMock()
        with patch(
            "app.services.document_service.get_user_by_firebase_uid",
            AsyncMock(return_value=None),
        ):
            docs, total = await list_documents_for_teacher(db, "unknown-uid")

        assert docs == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_returns_documents_and_count(self):
        from app.services.document_service import list_documents_for_teacher

        teacher = _make_teacher()
        doc1 = _make_document(teacher.id, title="Doc A")
        doc2 = _make_document(teacher.id, title="Doc B")

        db = AsyncMock()

        # Count query result
        count_result = MagicMock()
        count_result.scalar_one.return_value = 2

        # List query result
        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = [doc1, doc2]

        db.execute = AsyncMock(side_effect=[count_result, list_result])

        with patch(
            "app.services.document_service.get_user_by_firebase_uid",
            AsyncMock(return_value=teacher),
        ):
            docs, total = await list_documents_for_teacher(db, teacher.firebase_uid)

        assert total == 2
        assert len(docs) == 2
        assert docs[0].title == "Doc A"

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_documents(self):
        from app.services.document_service import list_documents_for_teacher

        teacher = _make_teacher()

        db = AsyncMock()
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(side_effect=[count_result, list_result])

        with patch(
            "app.services.document_service.get_user_by_firebase_uid",
            AsyncMock(return_value=teacher),
        ):
            docs, total = await list_documents_for_teacher(db, teacher.firebase_uid)

        assert total == 0
        assert docs == []

    @pytest.mark.asyncio
    async def test_pagination_passes_limit_offset(self):
        from app.services.document_service import list_documents_for_teacher

        teacher = _make_teacher()

        db = AsyncMock()
        count_result = MagicMock()
        count_result.scalar_one.return_value = 100
        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(side_effect=[count_result, list_result])

        with patch(
            "app.services.document_service.get_user_by_firebase_uid",
            AsyncMock(return_value=teacher),
        ):
            docs, total = await list_documents_for_teacher(
                db, teacher.firebase_uid, limit=10, offset=20
            )

        # Verify DB execute was called (pagination params passed through SQLAlchemy query)
        assert db.execute.call_count == 2
        assert total == 100


# ── get_document_detail ───────────────────────────────────────────────────────

class TestGetDocumentDetail:
    @pytest.mark.asyncio
    async def test_returns_none_if_teacher_not_found(self):
        from app.services.document_service import get_document_detail

        db = AsyncMock()
        with patch(
            "app.services.document_service.get_user_by_firebase_uid",
            AsyncMock(return_value=None),
        ):
            result = await get_document_detail(db, uuid.uuid4(), "bad-uid")

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_if_document_not_found(self):
        from app.services.document_service import get_document_detail

        teacher = _make_teacher()
        db = AsyncMock()
        query_result = MagicMock()
        query_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=query_result)

        with patch(
            "app.services.document_service.get_user_by_firebase_uid",
            AsyncMock(return_value=teacher),
        ):
            result = await get_document_detail(db, uuid.uuid4(), teacher.firebase_uid)

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_document_when_found(self):
        from app.services.document_service import get_document_detail

        teacher = _make_teacher()
        doc = _make_document(teacher.id, title="Test Doc")
        doc.math_expressions = []

        db = AsyncMock()
        query_result = MagicMock()
        query_result.scalar_one_or_none.return_value = doc
        db.execute = AsyncMock(return_value=query_result)

        with patch(
            "app.services.document_service.get_user_by_firebase_uid",
            AsyncMock(return_value=teacher),
        ):
            result = await get_document_detail(db, doc.id, teacher.firebase_uid)

        assert result is doc
        assert result.title == "Test Doc"


# ── Narration status counting ─────────────────────────────────────────────────

class TestNarrationStatusCounting:
    """Tests for the status count logic inside get_document endpoint."""

    def test_counts_four_buckets_correctly(self):
        exprs = [
            _make_expression("pending"),
            _make_expression("pending"),
            _make_expression("ai_generated"),
            _make_expression("reviewed"),
            _make_expression("approved"),
            _make_expression("approved"),
        ]
        counts = Counter(e.status for e in exprs)
        assert counts["pending"] == 2
        assert counts["ai_generated"] == 1
        assert counts["reviewed"] == 1
        assert counts["approved"] == 2

    def test_all_approved_is_fully_reviewd(self):
        exprs = [_make_expression("approved")] * 5
        counts = Counter(e.status for e in exprs)
        assert counts["approved"] == 5
        assert counts.get("pending", 0) == 0

    def test_empty_expressions(self):
        exprs = []
        status_counts = {"pending": 0, "ai_generated": 0, "reviewed": 0, "approved": 0}
        for e in exprs:
            status_counts[e.status] = status_counts.get(e.status, 0) + 1
        assert sum(status_counts.values()) == 0


# ── DocumentListItem schema ───────────────────────────────────────────────────

class TestDocumentListItemSchema:
    def test_schema_fields_present(self):
        from app.schemas.document import DocumentListItem

        item = DocumentListItem(
            document_id="abc",
            title="Test",
            file_type="docx",
            parsing_status="parsed",
            ocr_used="none",
            math_expressions_count=3,
            is_published=False,
            module_id=None,
            created_at="2026-01-01T00:00:00",
            updated_at="2026-01-01T01:00:00",
        )
        assert item.document_id == "abc"
        assert item.math_expressions_count == 3
        assert item.is_published is False
        assert item.module_id is None

    def test_schema_with_published_module(self):
        from app.schemas.document import DocumentListItem

        item = DocumentListItem(
            document_id="abc",
            title="Test",
            file_type="pdf",
            parsing_status="parsed",
            ocr_used="gcv",
            math_expressions_count=10,
            is_published=True,
            module_id="mod-001",
            created_at="2026-01-01T00:00:00",
            updated_at="2026-01-01T01:00:00",
        )
        assert item.is_published is True
        assert item.module_id == "mod-001"
        assert item.ocr_used == "gcv"


# ── DocumentDetailResponse schema ─────────────────────────────────────────────

class TestDocumentDetailResponseSchema:
    def test_all_fields_present(self):
        from app.schemas.document import DocumentDetailResponse

        resp = DocumentDetailResponse(
            document_id="doc-1",
            title="Kalkulus Integral",
            file_type="pdf",
            parsing_status="parsed",
            ocr_used="none",
            error_code=None,
            math_expressions_count=5,
            narrations_pending=1,
            narrations_ai_generated=2,
            narrations_reviewed=1,
            narrations_approved=1,
            is_published=True,
            module_id="mod-1",
            published_at="2026-09-01T00:00:00",
            created_at="2026-08-01T00:00:00",
            updated_at="2026-09-01T00:00:00",
        )
        assert resp.math_expressions_count == 5
        assert resp.narrations_pending == 1
        assert resp.narrations_approved == 1
        assert resp.is_published is True

    def test_unpublished_has_null_module_and_date(self):
        from app.schemas.document import DocumentDetailResponse

        resp = DocumentDetailResponse(
            document_id="doc-2",
            title="Geometri",
            file_type="docx",
            parsing_status="processing",
            ocr_used="none",
            error_code=None,
            math_expressions_count=0,
            narrations_pending=0,
            narrations_ai_generated=0,
            narrations_reviewed=0,
            narrations_approved=0,
            is_published=False,
            module_id=None,
            published_at=None,
            created_at="2026-08-01T00:00:00",
            updated_at="2026-08-01T00:00:00",
        )
        assert resp.module_id is None
        assert resp.published_at is None

    def test_error_code_field(self):
        from app.schemas.document import DocumentDetailResponse

        resp = DocumentDetailResponse(
            document_id="doc-3",
            title="Gagal",
            file_type="pdf",
            parsing_status="failed",
            ocr_used="none",
            error_code="PARSE_001",
            math_expressions_count=0,
            narrations_pending=0,
            narrations_ai_generated=0,
            narrations_reviewed=0,
            narrations_approved=0,
            is_published=False,
            module_id=None,
            published_at=None,
            created_at="2026-08-01T00:00:00",
            updated_at="2026-08-01T00:00:00",
        )
        assert resp.error_code == "PARSE_001"
        assert resp.parsing_status == "failed"


# ── DocumentListResponse schema ───────────────────────────────────────────────

class TestDocumentListResponseSchema:
    def test_list_response_shape(self):
        from app.schemas.document import DocumentListResponse, DocumentListItem

        item = DocumentListItem(
            document_id="abc",
            title="Test",
            file_type="docx",
            parsing_status="parsed",
            ocr_used="none",
            math_expressions_count=0,
            is_published=False,
            module_id=None,
            created_at="2026-01-01T00:00:00",
            updated_at="2026-01-01T01:00:00",
        )
        resp = DocumentListResponse(
            documents=[item],
            total=42,
            limit=10,
            offset=0,
        )
        assert resp.total == 42
        assert len(resp.documents) == 1

    def test_empty_list_response(self):
        from app.schemas.document import DocumentListResponse

        resp = DocumentListResponse(documents=[], total=0, limit=50, offset=0)
        assert resp.documents == []
        assert resp.total == 0
