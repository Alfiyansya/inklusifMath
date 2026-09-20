"""
Tests for real RBAC enforcement in get_current_user and require_role.

Strategy:
  - get_current_user: mock verify_firebase_token + db.execute to test DB lookup.
  - require_role: call the returned _check_role coroutine directly with a user dict.
  - Endpoint-level tests: inject pre-built user dicts, no DI needed.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.core.dependencies import require_role


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_user(role: str = "teacher") -> MagicMock:
    """Return a mock User ORM object with the given role."""
    user = MagicMock()
    user.id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    user.email = "test@example.com"
    user.firebase_uid = "uid123"
    user.role = role
    user.full_name = "Test User"
    return user


def _make_db(user: MagicMock | None) -> AsyncMock:
    """Build a mock AsyncSession where db.execute returns the given user."""
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    db.execute = AsyncMock(return_value=result)
    return db


def _make_creds(token: str = "valid-token") -> MagicMock:
    """Build a mock HTTPAuthorizationCredentials."""
    creds = MagicMock()
    creds.credentials = token
    return creds


async def check_role(roles_factory, user_dict: dict) -> dict:
    """Call require_role(...)._check_role directly with a pre-built user dict."""
    # require_role() returns _check_role (the closure), which takes current_user
    return await roles_factory(current_user=user_dict)


def make_user_dict(role: str) -> dict:
    return {
        "user_id": str(uuid.uuid4()),
        "email": f"{role}@test.com",
        "firebase_uid": f"uid-{role}",
        "role": role,
        "full_name": f"{role.title()} User",
    }


# ── Task 1 & 2: get_current_user ─────────────────────────────────────────────

class TestGetCurrentUser:
    @pytest.mark.asyncio
    async def test_returns_role_from_db(self):
        """get_current_user includes role fetched from DB, not from token."""
        from app.core.dependencies import get_current_user

        teacher = make_user(role="teacher")
        db = _make_db(teacher)

        with patch(
            "app.core.dependencies.verify_firebase_token",
            return_value={"uid": "uid123", "email": "test@example.com"},
        ):
            result = await get_current_user(credentials=_make_creds(), db=db)

        assert result["role"] == "teacher"
        assert result["firebase_uid"] == "uid123"
        assert result["email"] == "test@example.com"
        assert result["full_name"] == "Test User"
        assert result["user_id"] == str(teacher.id)

    @pytest.mark.asyncio
    async def test_raises_401_when_user_not_in_db(self):
        """get_current_user raises 401 if firebase_uid has no matching DB row."""
        from app.core.dependencies import get_current_user

        db = _make_db(None)  # user missing from DB

        with patch(
            "app.core.dependencies.verify_firebase_token",
            return_value={"uid": "ghost-uid"},
        ):
            with pytest.raises(HTTPException) as exc:
                await get_current_user(credentials=_make_creds(), db=db)

        assert exc.value.status_code == 401
        assert "tidak ditemukan" in exc.value.detail

    @pytest.mark.asyncio
    async def test_raises_401_on_expired_token(self):
        """Expired Firebase token raises 401 with 'kedaluwarsa' message."""
        from firebase_admin import auth as firebase_auth
        from app.core.dependencies import get_current_user

        db = _make_db(make_user())

        with patch(
            "app.core.dependencies.verify_firebase_token",
            side_effect=firebase_auth.ExpiredIdTokenError("expired", None),
        ):
            with pytest.raises(HTTPException) as exc:
                await get_current_user(credentials=_make_creds("expired"), db=db)

        assert exc.value.status_code == 401
        assert "kedaluwarsa" in exc.value.detail

    @pytest.mark.asyncio
    async def test_student_role_returned_correctly(self):
        """get_current_user correctly returns 'student' role from DB."""
        from app.core.dependencies import get_current_user

        student = make_user(role="student")
        db = _make_db(student)

        with patch(
            "app.core.dependencies.verify_firebase_token",
            return_value={"uid": "uid123"},
        ):
            result = await get_current_user(credentials=_make_creds(), db=db)

        assert result["role"] == "student"


# ── Task 2: require_role ──────────────────────────────────────────────────────

class TestRequireRole:
    @pytest.mark.asyncio
    async def test_allows_teacher_role(self):
        """require_role('teacher') passes through for teacher user."""
        user = make_user_dict("teacher")
        result = await check_role(require_role("teacher"), user)
        assert result["role"] == "teacher"

    @pytest.mark.asyncio
    async def test_blocks_student_from_teacher_role_403(self):
        """require_role('teacher') raises 403 for student."""
        user = make_user_dict("student")
        with pytest.raises(HTTPException) as exc:
            await check_role(require_role("teacher"), user)
        assert exc.value.status_code == 403
        assert "Akses ditolak" in exc.value.detail

    @pytest.mark.asyncio
    async def test_blocks_teacher_from_admin_only_403(self):
        """require_role('admin') raises 403 for teacher."""
        user = make_user_dict("teacher")
        with pytest.raises(HTTPException) as exc:
            await check_role(require_role("admin"), user)
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_allows_teacher_in_multi_role(self):
        """require_role('teacher', 'admin') allows teacher."""
        user = make_user_dict("teacher")
        result = await check_role(require_role("teacher", "admin"), user)
        assert result["role"] == "teacher"

    @pytest.mark.asyncio
    async def test_allows_admin_in_multi_role(self):
        """require_role('teacher', 'admin') allows admin."""
        user = make_user_dict("admin")
        result = await check_role(require_role("teacher", "admin"), user)
        assert result["role"] == "admin"

    @pytest.mark.asyncio
    async def test_blocks_absent_role_key(self):
        """require_role raises 403 when 'role' key is missing from user dict."""
        user = {"user_id": "u1", "email": "x@t.com", "firebase_uid": "uid1", "full_name": "X"}
        with pytest.raises(HTTPException) as exc:
            await check_role(require_role("teacher"), user)
        assert exc.value.status_code == 403


# ── Task 3: Document upload RBAC (teacher/admin only) ─────────────────────────

class TestDocumentUploadRBAC:
    @pytest.mark.asyncio
    async def test_teacher_passes_require_role_for_upload(self):
        """Teacher role satisfies require_role('teacher', 'admin')."""
        user = make_user_dict("teacher")
        result = await check_role(require_role("teacher", "admin"), user)
        assert result["role"] == "teacher"

    @pytest.mark.asyncio
    async def test_student_blocked_from_upload_403(self):
        """Student role is rejected by require_role('teacher', 'admin')."""
        user = make_user_dict("student")
        with pytest.raises(HTTPException) as exc:
            await check_role(require_role("teacher", "admin"), user)
        assert exc.value.status_code == 403


# ── Task 3: Tutor RBAC (student/admin only) ───────────────────────────────────

class TestTutorRBAC:
    @pytest.mark.asyncio
    async def test_student_can_access_tutor(self):
        """Student role satisfies require_role('student', 'admin')."""
        user = make_user_dict("student")
        result = await check_role(require_role("student", "admin"), user)
        assert result["role"] == "student"

    @pytest.mark.asyncio
    async def test_teacher_blocked_from_tutor_403(self):
        """Teacher role is rejected by require_role('student', 'admin')."""
        user = make_user_dict("teacher")
        with pytest.raises(HTTPException) as exc:
            await check_role(require_role("student", "admin"), user)
        assert exc.value.status_code == 403
        assert "Akses ditolak" in exc.value.detail


# ── Task 3: Modules endpoint (any authenticated user) ─────────────────────────

class TestModulesRBAC:
    @pytest.mark.asyncio
    async def test_teacher_can_list_modules(self):
        """Teacher can call list_modules (uses get_current_user, no role restriction)."""
        from app.services import module_service as svc
        from app.api.v1.endpoints.modules import list_modules
        from starlette.requests import Request

        teacher_user = make_user_dict("teacher")
        mock_db = AsyncMock()
        scope = {
            "type": "http", "method": "GET", "path": "/modules",
            "query_string": b"", "headers": [], "client": ("127.0.0.1", 9999),
        }
        with patch.object(svc, "list_published_modules", AsyncMock(return_value=[])):
            response = await list_modules(
                request=Request(scope), current_user=teacher_user, db=mock_db
            )
        assert response.modules == []

    @pytest.mark.asyncio
    async def test_student_can_list_modules(self):
        """Student can call list_modules (uses get_current_user, no role restriction)."""
        from app.services import module_service as svc
        from app.api.v1.endpoints.modules import list_modules
        from starlette.requests import Request

        student_user = make_user_dict("student")
        mock_db = AsyncMock()
        scope = {
            "type": "http", "method": "GET", "path": "/modules",
            "query_string": b"", "headers": [], "client": ("127.0.0.1", 9999),
        }
        with patch.object(svc, "list_published_modules", AsyncMock(return_value=[])):
            response = await list_modules(
                request=Request(scope), current_user=student_user, db=mock_db
            )
        assert response.modules == []
