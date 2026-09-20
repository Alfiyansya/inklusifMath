"""
Authentication endpoint tests with mocked Firebase Auth.
Tests profile creation, user lookup, and logout flows.
"""

import uuid
from unittest.mock import patch

import pytest

BASE = "/api/v1/auth"

# Mock Firebase UID for testing
MOCK_FIREBASE_UID = "firebase_test_uid_12345"
MOCK_FIREBASE_UID_2 = "firebase_test_uid_67890"


def _mock_verify_token(uid: str, email: str = "test@sekolah.id"):
    """Create a mock for verify_firebase_token that returns a fixed decoded token."""
    return {
        "uid": uid,
        "email": email,
        "email_verified": True,
    }


# ─── Profile Creation ───


async def test_create_profile_teacher(client):
    """Test creating a teacher profile after Firebase signup."""
    with patch(
        "app.core.dependencies.verify_firebase_token",
        return_value=_mock_verify_token(MOCK_FIREBASE_UID, "guru_test@sekolah.id"),
    ):
        response = await client.post(
            f"{BASE}/profile",
            json={
                "full_name": "Budi Hartono",
                "role": "teacher",
            },
            headers={"Authorization": "Bearer fake-firebase-token"},
        )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "guru_test@sekolah.id"
    assert data["role"] == "teacher"
    assert data["full_name"] == "Budi Hartono"
    assert data["firebase_uid"] == MOCK_FIREBASE_UID
    assert "id" in data


async def test_create_profile_student_with_level(client):
    """Test creating a student profile with student_level."""
    with patch(
        "app.core.dependencies.verify_firebase_token",
        return_value=_mock_verify_token(MOCK_FIREBASE_UID_2, "siswa_test@sekolah.id"),
    ):
        response = await client.post(
            f"{BASE}/profile",
            json={
                "full_name": "Ani Wulandari",
                "role": "student",
                "student_level": "SMP",
            },
            headers={"Authorization": "Bearer fake-firebase-token"},
        )
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "student"
    assert data["student_level"] == "SMP"


async def test_create_profile_duplicate(client):
    """Test that creating a duplicate profile returns 409."""
    uid = f"firebase_dup_{uuid.uuid4().hex[:8]}"
    with patch(
        "app.core.dependencies.verify_firebase_token",
        return_value=_mock_verify_token(uid, "dup@sekolah.id"),
    ):
        # Create first
        await client.post(
            f"{BASE}/profile",
            json={"full_name": "User One", "role": "teacher"},
            headers={"Authorization": "Bearer fake-firebase-token"},
        )
        # Duplicate
        response = await client.post(
            f"{BASE}/profile",
            json={"full_name": "User Two", "role": "student"},
            headers={"Authorization": "Bearer fake-firebase-token"},
        )
    assert response.status_code == 409


async def test_create_profile_invalid_role(client):
    """Test that invalid role returns 422."""
    uid = f"firebase_invalid_{uuid.uuid4().hex[:8]}"
    with patch(
        "app.core.dependencies.verify_firebase_token",
        return_value=_mock_verify_token(uid),
    ):
        response = await client.post(
            f"{BASE}/profile",
            json={"full_name": "Bad Role", "role": "superadmin"},
            headers={"Authorization": "Bearer fake-firebase-token"},
        )
    assert response.status_code == 422


# ─── Get Profile ───


async def test_get_me(client):
    """Test getting current user's profile."""
    with patch(
        "app.core.dependencies.verify_firebase_token",
        return_value=_mock_verify_token(MOCK_FIREBASE_UID, "guru_test@sekolah.id"),
    ):
        response = await client.get(
            f"{BASE}/me",
            headers={"Authorization": "Bearer fake-firebase-token"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Budi Hartono"
    assert data["role"] == "teacher"


async def test_get_me_no_profile(client):
    """Test getting profile for user that has no profile returns 404."""
    uid = f"firebase_noprofile_{uuid.uuid4().hex[:8]}"
    with patch(
        "app.core.dependencies.verify_firebase_token",
        return_value=_mock_verify_token(uid),
    ):
        response = await client.get(
            f"{BASE}/me",
            headers={"Authorization": "Bearer fake-firebase-token"},
        )
    assert response.status_code == 404


# ─── Protected Endpoint ───


async def test_protected_endpoint_without_token(client):
    """Test that missing token returns 401/403."""
    response = await client.get("/api/v1/modules")
    # FastAPI HTTPBearer returns 403 when no credentials provided
    assert response.status_code in (401, 403)


# ─── Logout ───


async def test_logout(client):
    """Test logout returns success message."""
    response = await client.post(f"{BASE}/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "Berhasil logout"
