"""
Unit tests for bulk update narrations: PUT /api/v1/documents/{document_id}/narrations
Tests service layer (update_narrations_bulk), schemas, and endpoint behavior.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.dependencies import get_current_user, get_db
from app.schemas.document import (
    BulkNarrationItem,
    BulkNarrationUpdateRequest,
    BulkNarrationUpdateResponse,
)
from app.services import document_service as svc


# ── Fixtures & Helpers ────────────────────────────────────────────────────────

def _make_expression(doc_id: uuid.UUID, expr_id: uuid.UUID | None = None) -> MagicMock:
    expr = MagicMock()
    expr.id = expr_id or uuid.uuid4()
    expr.document_id = doc_id
    expr.original_notation = "a/b"
    expr.latex_representation = "\\frac{a}{b}"
    expr.ai_narration = "Pecahan a per b"
    expr.teacher_narration = None
    expr.status = "ai_generated"
    expr.position_order = 1
    return expr


def _make_doc(teacher_id: uuid.UUID, doc_id: uuid.UUID | None = None) -> MagicMock:
    doc = MagicMock()
    doc.id = doc_id or uuid.uuid4()
    doc.teacher_id = teacher_id
    doc.title = "Matematika Dasar"
    doc.math_expressions = []
    return doc


# ── Schema Tests ──────────────────────────────────────────────────────────────

def test_bulk_narration_schemas():
    expr_id = str(uuid.uuid4())
    item = BulkNarrationItem(id=expr_id, teacher_narration="Narasi guru yang diedit")
    assert item.id == expr_id
    assert item.teacher_narration == "Narasi guru yang diedit"

    req = BulkNarrationUpdateRequest(narrations=[item])
    assert len(req.narrations) == 1

    resp = BulkNarrationUpdateResponse(
        document_id=str(uuid.uuid4()),
        updated_count=1,
        narrations=[{"id": expr_id, "status": "reviewed", "teacher_narration": "Narasi baru"}],
    )
    assert resp.updated_count == 1
    assert resp.narrations[0].status == "reviewed"


# ── Service Layer Tests ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_narrations_bulk_success():
    teacher_uid = "teacher-123"
    doc_id = uuid.uuid4()
    teacher_id = uuid.uuid4()

    doc = _make_doc(teacher_id, doc_id)
    expr1 = _make_expression(doc_id)
    expr2 = _make_expression(doc_id)
    doc.math_expressions = [expr1, expr2]

    db = AsyncMock()

    with patch("app.services.document_service.get_document_by_id", new_callable=AsyncMock) as mock_get_doc:
        mock_get_doc.return_value = doc

        items = [
            {"id": str(expr1.id), "teacher_narration": "Narasi guru ekspresi 1"},
            {"id": str(expr2.id), "teacher_narration": "Narasi guru ekspresi 2"},
        ]

        returned_doc, updated = await svc.update_narrations_bulk(
            db=db,
            document_id=doc_id,
            items=items,
            teacher_firebase_uid=teacher_uid,
        )

        assert returned_doc == doc
        assert len(updated) == 2
        assert expr1.teacher_narration == "Narasi guru ekspresi 1"
        assert expr1.status == "reviewed"
        assert expr2.teacher_narration == "Narasi guru ekspresi 2"
        assert expr2.status == "reviewed"
        db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_narrations_bulk_partial_match():
    teacher_uid = "teacher-123"
    doc_id = uuid.uuid4()
    teacher_id = uuid.uuid4()

    doc = _make_doc(teacher_id, doc_id)
    expr1 = _make_expression(doc_id)
    doc.math_expressions = [expr1]

    db = AsyncMock()

    with patch("app.services.document_service.get_document_by_id", new_callable=AsyncMock) as mock_get_doc:
        mock_get_doc.return_value = doc

        items = [
            {"id": str(expr1.id), "teacher_narration": "Narasi guru cocok"},
            {"id": str(uuid.uuid4()), "teacher_narration": "ID ini tidak ada di dokumen"},
        ]

        returned_doc, updated = await svc.update_narrations_bulk(
            db=db,
            document_id=doc_id,
            items=items,
            teacher_firebase_uid=teacher_uid,
        )

        assert returned_doc == doc
        assert len(updated) == 1
        assert updated[0] == expr1
        assert expr1.teacher_narration == "Narasi guru cocok"


@pytest.mark.asyncio
async def test_update_narrations_bulk_doc_not_found():
    teacher_uid = "teacher-123"
    doc_id = uuid.uuid4()
    db = AsyncMock()

    with patch("app.services.document_service.get_document_by_id", new_callable=AsyncMock) as mock_get_doc:
        mock_get_doc.return_value = None

        returned_doc, updated = await svc.update_narrations_bulk(
            db=db,
            document_id=doc_id,
            items=[{"id": str(uuid.uuid4()), "teacher_narration": "Test"}],
            teacher_firebase_uid=teacher_uid,
        )

        assert returned_doc is None
        assert updated == []
        db.flush.assert_not_called()


# ── Endpoint Tests ────────────────────────────────────────────────────────────

def test_endpoint_bulk_update_success():
    doc_id = uuid.uuid4()
    expr_id = uuid.uuid4()

    mock_user = {
        "uid": "teacher-uid",
        "firebase_uid": "teacher-uid",
        "email": "guru@inklusifmath.id",
        "role": "teacher",
    }

    mock_doc = MagicMock()
    mock_doc.id = doc_id

    mock_expr = MagicMock()
    mock_expr.id = expr_id
    mock_expr.status = "reviewed"
    mock_expr.teacher_narration = "Narasi baru hasil bulk"

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: AsyncMock()

    try:
        with patch("app.services.document_service.update_narrations_bulk", new_callable=AsyncMock) as mock_svc:
            mock_svc.return_value = (mock_doc, [mock_expr])

            client = TestClient(app)
            payload = {
                "narrations": [
                    {"id": str(expr_id), "teacher_narration": "Narasi baru hasil bulk"}
                ]
            }
            resp = client.put(f"/api/v1/documents/{doc_id}/narrations", json=payload)

            assert resp.status_code == 200
            data = resp.json()
            assert data["document_id"] == str(doc_id)
            assert data["updated_count"] == 1
            assert len(data["narrations"]) == 1
            assert data["narrations"][0]["id"] == str(expr_id)
            assert data["narrations"][0]["teacher_narration"] == "Narasi baru hasil bulk"
    finally:
        app.dependency_overrides.clear()


def test_endpoint_bulk_update_not_found():
    doc_id = uuid.uuid4()
    mock_user = {
        "uid": "teacher-uid",
        "firebase_uid": "teacher-uid",
        "email": "guru@inklusifmath.id",
        "role": "teacher",
    }

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: AsyncMock()

    try:
        with patch("app.services.document_service.update_narrations_bulk", new_callable=AsyncMock) as mock_svc:
            mock_svc.return_value = (None, [])

            client = TestClient(app)
            payload = {
                "narrations": [
                    {"id": str(uuid.uuid4()), "teacher_narration": "Narasi baru"}
                ]
            }
            resp = client.put(f"/api/v1/documents/{doc_id}/narrations", json=payload)
            assert resp.status_code == 404
            assert "tidak ditemukan" in resp.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_endpoint_bulk_update_invalid_uuid():
    mock_user = {
        "uid": "teacher-uid",
        "firebase_uid": "teacher-uid",
        "email": "guru@inklusifmath.id",
        "role": "teacher",
    }
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: AsyncMock()

    try:
        client = TestClient(app)
        payload = {
            "narrations": [
                {"id": str(uuid.uuid4()), "teacher_narration": "Narasi baru"}
            ]
        }
        resp = client.put("/api/v1/documents/not-a-valid-uuid/narrations", json=payload)
        assert resp.status_code == 404
        assert "tidak ditemukan" in resp.json()["detail"]
    finally:
        app.dependency_overrides.clear()
