"""
Tests for module service and module endpoints.

Tests use mocked AsyncSession to avoid requiring a real DB.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


from starlette.requests import Request
from starlette.datastructures import Headers


def _mock_request() -> Request:
    """Return a minimal real Starlette Request for rate-limited endpoint tests.
    slowapi requires isinstance(request, Request) — MagicMock won't work.
    """
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 9999),
    }
    return Request(scope)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_module(
    module_id: uuid.UUID | None = None,
    doc_title: str = "Aljabar Dasar",
    is_published: bool = True,
    html_content: str = "<h1>Aljabar</h1>",
) -> MagicMock:
    """Build a mock LearningModule ORM object."""
    m = MagicMock()
    m.id = module_id or uuid.uuid4()
    m.document_id = uuid.uuid4()
    m.html_content = html_content
    m.is_published = is_published
    m.published_at = datetime(2026, 9, 17, 12, 0, 0, tzinfo=timezone.utc)
    doc = MagicMock()
    doc.title = doc_title
    m.document = doc
    return m


def _make_expr(position_order: int = 1) -> MagicMock:
    """Build a mock MathExpression ORM object."""
    e = MagicMock()
    e.id = uuid.uuid4()
    e.document_id = uuid.uuid4()
    e.original_notation = f"x^{position_order}"
    e.latex_representation = f"x^{{{position_order}}}"
    e.ai_narration = f"x pangkat {position_order}"
    e.teacher_narration = None
    e.status = "ai_generated"
    e.position_order = position_order
    return e


# ── module_service.list_published_modules ─────────────────────────────────────

class TestListPublishedModules:
    @pytest.mark.asyncio
    async def test_returns_list_of_modules(self):
        from app.services.module_service import list_published_modules

        mock_db = AsyncMock()
        m1, m2 = _make_module(), _make_module()

        scalars_mock = MagicMock()
        scalars_mock.all.return_value = [m1, m2]
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        mock_db.execute = AsyncMock(return_value=result_mock)

        result = await list_published_modules(mock_db)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_modules(self):
        from app.services.module_service import list_published_modules

        mock_db = AsyncMock()
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = []
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        mock_db.execute = AsyncMock(return_value=result_mock)

        result = await list_published_modules(mock_db)
        assert result == []


# ── module_service.get_module_with_expressions ────────────────────────────────

class TestGetModuleWithExpressions:
    @pytest.mark.asyncio
    async def test_returns_module_and_expressions(self):
        from app.services.module_service import get_module_with_expressions

        mock_db = AsyncMock()
        module = _make_module()
        e1, e2 = _make_expr(1), _make_expr(2)

        # First execute: module query
        module_result = MagicMock()
        module_result.scalar_one_or_none.return_value = module

        # Second execute: expressions query
        expr_scalars = MagicMock()
        expr_scalars.all.return_value = [e1, e2]
        expr_result = MagicMock()
        expr_result.scalars.return_value = expr_scalars

        mock_db.execute = AsyncMock(side_effect=[module_result, expr_result])

        returned_module, expressions = await get_module_with_expressions(
            mock_db, module.id
        )
        assert returned_module is module
        assert len(expressions) == 2

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        from app.services.module_service import get_module_with_expressions

        mock_db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=result_mock)

        returned_module, expressions = await get_module_with_expressions(
            mock_db, uuid.uuid4()
        )
        assert returned_module is None
        assert expressions == []


# ── GET /modules endpoint ─────────────────────────────────────────────────────

class TestListModulesEndpoint:
    @pytest.mark.asyncio
    async def test_returns_published_modules(self):
        from app.services import module_service as svc

        mock_db = AsyncMock()
        m1 = _make_module(doc_title="Aljabar Dasar")
        m2 = _make_module(doc_title="Geometri")

        with patch.object(svc, "list_published_modules", AsyncMock(return_value=[m1, m2])):
            from app.api.v1.endpoints.modules import list_modules

            fake_user = {"user_id": "u1", "email": "t@test.com", "firebase_uid": "uid1"}
            response = await list_modules(request=_mock_request(), current_user=fake_user, db=mock_db)

        assert len(response.modules) == 2
        titles = [mod.title for mod in response.modules]
        assert "Aljabar Dasar" in titles
        assert "Geometri" in titles

    @pytest.mark.asyncio
    async def test_empty_list_when_none_published(self):
        from app.services import module_service as svc

        mock_db = AsyncMock()
        with patch.object(svc, "list_published_modules", AsyncMock(return_value=[])):
            from app.api.v1.endpoints.modules import list_modules

            fake_user = {"user_id": "u1", "email": "t@test.com", "firebase_uid": "uid1"}
            response = await list_modules(request=_mock_request(), current_user=fake_user, db=mock_db)

        assert response.modules == []

    @pytest.mark.asyncio
    async def test_module_has_required_fields(self):
        from app.services import module_service as svc

        mock_db = AsyncMock()
        m = _make_module(doc_title="Kalkulus")

        with patch.object(svc, "list_published_modules", AsyncMock(return_value=[m])):
            from app.api.v1.endpoints.modules import list_modules

            fake_user = {"user_id": "u1", "email": "t@test.com", "firebase_uid": "uid1"}
            response = await list_modules(request=_mock_request(), current_user=fake_user, db=mock_db)

        item = response.modules[0]
        assert item.id == str(m.id)
        assert item.title == "Kalkulus"
        assert "2026" in item.published_at


# ── GET /modules/{module_id} endpoint ────────────────────────────────────────

class TestGetModuleEndpoint:
    @pytest.mark.asyncio
    async def test_returns_module_detail(self):
        from app.services import module_service as svc

        mock_db = AsyncMock()
        module = _make_module(html_content="<h2>Bab 1</h2>")
        expressions = [_make_expr(1), _make_expr(2)]

        with patch.object(
            svc, "get_module_with_expressions",
            AsyncMock(return_value=(module, expressions))
        ):
            from app.api.v1.endpoints.modules import get_module

            fake_user = {"user_id": "u1", "email": "t@test.com", "firebase_uid": "uid1"}
            response = await get_module(
                request=_mock_request(),
                module_id=str(module.id),
                current_user=fake_user,
                db=mock_db,
            )

        assert response.id == str(module.id)
        assert response.html_content == "<h2>Bab 1</h2>"
        assert len(response.math_expressions) == 2

    @pytest.mark.asyncio
    async def test_raises_404_for_invalid_uuid(self):
        from fastapi import HTTPException
        from app.api.v1.endpoints.modules import get_module

        mock_db = AsyncMock()
        fake_user = {"user_id": "u1", "email": "t@test.com", "firebase_uid": "uid1"}

        with pytest.raises(HTTPException) as exc:
            await get_module(
                request=_mock_request(),
                module_id="not-a-uuid",
                current_user=fake_user,
                db=mock_db,
            )
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_404_when_not_found(self):
        from fastapi import HTTPException
        from app.services import module_service as svc

        mock_db = AsyncMock()
        with patch.object(
            svc, "get_module_with_expressions",
            AsyncMock(return_value=(None, []))
        ):
            from app.api.v1.endpoints.modules import get_module

            fake_user = {"user_id": "u1", "email": "t@test.com", "firebase_uid": "uid1"}
            with pytest.raises(HTTPException) as exc:
                await get_module(
                    request=_mock_request(),
                    module_id=str(uuid.uuid4()),
                    current_user=fake_user,
                    db=mock_db,
                )
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_math_expressions_include_narrations(self):
        from app.services import module_service as svc

        mock_db = AsyncMock()
        module = _make_module()
        expr = _make_expr(1)
        expr.ai_narration = "x pangkat satu"
        expr.teacher_narration = "x pangkat satu (diverifikasi)"

        with patch.object(
            svc, "get_module_with_expressions",
            AsyncMock(return_value=(module, [expr]))
        ):
            from app.api.v1.endpoints.modules import get_module

            fake_user = {"user_id": "u1", "email": "t@test.com", "firebase_uid": "uid1"}
            response = await get_module(
                request=_mock_request(),
                module_id=str(module.id),
                current_user=fake_user,
                db=mock_db,
            )

        e = response.math_expressions[0]
        assert e.ai_narration == "x pangkat satu"
        assert e.teacher_narration == "x pangkat satu (diverifikasi)"
