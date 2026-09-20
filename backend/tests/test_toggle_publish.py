"""
Tests for toggle_module_publish service function and ModulePublish schemas.

Strategy:
  - Service tests use AsyncMock + MagicMock (no real DB).
  - Schema tests validate Pydantic field defaults, types, and serialisation.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.module import ModulePublishRequest, ModulePublishResponse


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_teacher(uid: str = "teacher-uid-1") -> MagicMock:
    """Return a mock User record."""
    t = MagicMock()
    t.id = uuid.uuid4()
    t.firebase_uid = uid
    return t


def _make_module(
    teacher: MagicMock,
    is_published: bool = False,
    published_at: datetime | None = None,
) -> MagicMock:
    """Return a mock LearningModule with a linked Document owned by teacher."""
    m = MagicMock()
    m.id = uuid.uuid4()
    m.is_published = is_published
    m.published_at = published_at
    doc = MagicMock()
    doc.teacher_id = teacher.id
    m.document = doc
    return m


def _db_returning(module: MagicMock | None, teacher: MagicMock | None) -> AsyncMock:
    """
    Build a mock AsyncSession where:
      - First execute() (teacher lookup) returns teacher via scalar_one_or_none
      - Second execute() (module lookup) returns module via scalar_one_or_none
    """
    db = AsyncMock()
    db.flush = AsyncMock()

    teacher_result = MagicMock()
    teacher_result.scalar_one_or_none.return_value = teacher

    module_result = MagicMock()
    module_result.scalar_one_or_none.return_value = module

    db.execute = AsyncMock(side_effect=[teacher_result, module_result])
    return db


# ── toggle_module_publish service tests ──────────────────────────────────────

class TestToggleModulePublish:
    """Unit tests for document_service.toggle_module_publish."""

    @pytest.mark.asyncio
    async def test_publish_sets_is_published_true_and_published_at(self):
        """Publishing a module sets is_published=True and published_at to now."""
        from app.services.document_service import toggle_module_publish

        teacher = _make_teacher()
        module = _make_module(teacher, is_published=False)
        db = _db_returning(module, teacher)

        result = await toggle_module_publish(
            db=db,
            module_id=module.id,
            teacher_firebase_uid=teacher.firebase_uid,
            publish=True,
        )

        assert result is module
        assert module.is_published is True
        assert module.published_at is not None
        db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_unpublish_sets_is_published_false_and_clears_published_at(self):
        """Unpublishing sets is_published=False and published_at=None."""
        from app.services.document_service import toggle_module_publish

        teacher = _make_teacher()
        now = datetime.now(timezone.utc)
        module = _make_module(teacher, is_published=True, published_at=now)
        db = _db_returning(module, teacher)

        result = await toggle_module_publish(
            db=db,
            module_id=module.id,
            teacher_firebase_uid=teacher.firebase_uid,
            publish=False,
        )

        assert result is module
        assert module.is_published is False
        assert module.published_at is None
        db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_module_not_found(self):
        """Returns None when the module_id does not exist."""
        from app.services.document_service import toggle_module_publish

        teacher = _make_teacher()
        db = _db_returning(None, teacher)

        result = await toggle_module_publish(
            db=db,
            module_id=uuid.uuid4(),
            teacher_firebase_uid=teacher.firebase_uid,
            publish=True,
        )

        assert result is None
        db.flush.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_none_when_wrong_teacher(self):
        """Returns None when module is owned by a different teacher."""
        from app.services.document_service import toggle_module_publish

        owner = _make_teacher("owner-uid")
        other = _make_teacher("other-uid")
        # Module belongs to owner, but 'other' teacher is requesting
        module = _make_module(owner, is_published=False)
        db = _db_returning(module, other)

        result = await toggle_module_publish(
            db=db,
            module_id=module.id,
            teacher_firebase_uid=other.firebase_uid,
            publish=True,
        )

        assert result is None
        db.flush.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_none_when_teacher_not_found(self):
        """Returns None when firebase_uid does not match any User record."""
        from app.services.document_service import toggle_module_publish

        db = AsyncMock()
        db.flush = AsyncMock()
        no_teacher_result = MagicMock()
        no_teacher_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=no_teacher_result)

        result = await toggle_module_publish(
            db=db,
            module_id=uuid.uuid4(),
            teacher_firebase_uid="nonexistent-uid",
            publish=True,
        )

        assert result is None
        db.flush.assert_not_called()

    @pytest.mark.asyncio
    async def test_published_at_is_timezone_aware(self):
        """published_at must be timezone-aware when publishing."""
        from app.services.document_service import toggle_module_publish

        teacher = _make_teacher()
        module = _make_module(teacher)
        db = _db_returning(module, teacher)

        await toggle_module_publish(
            db=db,
            module_id=module.id,
            teacher_firebase_uid=teacher.firebase_uid,
            publish=True,
        )

        assert module.published_at.tzinfo is not None


# ── ModulePublishRequest schema tests ─────────────────────────────────────────

class TestModulePublishRequest:
    def test_default_is_published_is_true(self):
        req = ModulePublishRequest()
        assert req.is_published is True

    def test_can_set_is_published_false(self):
        req = ModulePublishRequest(is_published=False)
        assert req.is_published is False

    def test_accepts_bool_coercion(self):
        """Pydantic coerces 1 -> True."""
        req = ModulePublishRequest(is_published=1)
        assert req.is_published is True


# ── ModulePublishResponse schema tests ────────────────────────────────────────

class TestModulePublishResponse:
    def test_fields_present(self):
        resp = ModulePublishResponse(
            module_id="abc-123",
            is_published=True,
            published_at="2026-09-20T12:00:00+00:00",
        )
        assert resp.module_id == "abc-123"
        assert resp.is_published is True
        assert "2026" in resp.published_at

    def test_published_at_can_be_none(self):
        resp = ModulePublishResponse(
            module_id="abc-123",
            is_published=False,
            published_at=None,
        )
        assert resp.published_at is None

    def test_serialises_to_dict(self):
        resp = ModulePublishResponse(
            module_id="x",
            is_published=True,
            published_at="2026-01-01T00:00:00Z",
        )
        d = resp.model_dump()
        assert d["module_id"] == "x"
        assert d["is_published"] is True


# ── publish_module endpoint tests ─────────────────────────────────────────────

def _mock_request():
    from starlette.requests import Request
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/test",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 9999),
    }
    return Request(scope)


class TestPublishModuleEndpoint:
    """Tests for the POST /modules/{module_id}/publish endpoint function."""

    @pytest.mark.asyncio
    async def test_returns_publish_response_on_success(self):
        from app.services import document_service as doc_svc
        from app.api.v1.endpoints.modules import publish_module

        module_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        mock_module = MagicMock()
        mock_module.id = module_id
        mock_module.is_published = True
        mock_module.published_at = now

        mock_db = AsyncMock()
        fake_user = {"firebase_uid": "teacher-uid", "user_id": "teacher-uid"}

        with patch.object(
            doc_svc, "toggle_module_publish", AsyncMock(return_value=mock_module)
        ):
            response = await publish_module(
                request=_mock_request(),
                module_id=str(module_id),
                body=ModulePublishRequest(is_published=True),
                current_user=fake_user,
                db=mock_db,
            )

        assert response.module_id == str(module_id)
        assert response.is_published is True
        assert response.published_at is not None

    @pytest.mark.asyncio
    async def test_raises_404_when_invalid_uuid(self):
        from fastapi import HTTPException
        from app.api.v1.endpoints.modules import publish_module

        mock_db = AsyncMock()
        fake_user = {"firebase_uid": "uid", "user_id": "uid"}

        with pytest.raises(HTTPException) as exc:
            await publish_module(
                request=_mock_request(),
                module_id="not-a-valid-uuid",
                body=ModulePublishRequest(),
                current_user=fake_user,
                db=mock_db,
            )
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_404_when_service_returns_none(self):
        from fastapi import HTTPException
        from app.services import document_service as doc_svc
        from app.api.v1.endpoints.modules import publish_module

        mock_db = AsyncMock()
        fake_user = {"firebase_uid": "uid", "user_id": "uid"}

        with patch.object(
            doc_svc, "toggle_module_publish", AsyncMock(return_value=None)
        ):
            with pytest.raises(HTTPException) as exc:
                await publish_module(
                    request=_mock_request(),
                    module_id=str(uuid.uuid4()),
                    body=ModulePublishRequest(),
                    current_user=fake_user,
                    db=mock_db,
                )
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_unpublish_returns_none_published_at(self):
        from app.services import document_service as doc_svc
        from app.api.v1.endpoints.modules import publish_module

        module_id = uuid.uuid4()
        mock_module = MagicMock()
        mock_module.id = module_id
        mock_module.is_published = False
        mock_module.published_at = None

        mock_db = AsyncMock()
        fake_user = {"firebase_uid": "uid", "user_id": "uid"}

        with patch.object(
            doc_svc, "toggle_module_publish", AsyncMock(return_value=mock_module)
        ):
            response = await publish_module(
                request=_mock_request(),
                module_id=str(module_id),
                body=ModulePublishRequest(is_published=False),
                current_user=fake_user,
                db=mock_db,
            )

        assert response.is_published is False
        assert response.published_at is None

    @pytest.mark.asyncio
    async def test_default_body_publishes(self):
        """When body=None is passed, endpoint defaults to is_published=True."""
        from app.services import document_service as doc_svc
        from app.api.v1.endpoints.modules import publish_module

        module_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        mock_module = MagicMock()
        mock_module.id = module_id
        mock_module.is_published = True
        mock_module.published_at = now

        mock_db = AsyncMock()
        fake_user = {"firebase_uid": "uid", "user_id": "uid"}

        captured = {}

        async def _fake_toggle(db, module_id, teacher_firebase_uid, publish):
            captured["publish"] = publish
            return mock_module

        with patch.object(doc_svc, "toggle_module_publish", _fake_toggle):
            await publish_module(
                request=_mock_request(),
                module_id=str(module_id),
                body=None,  # no body → should default to True
                current_user=fake_user,
                db=mock_db,
            )

        assert captured["publish"] is True
