"""
Authentication endpoint tests.
Tests register, login, refresh, and logout flows.

All tests use the session-scoped `client` fixture from conftest.py
to share a single AsyncClient and event loop, preventing asyncpg
'Event loop is closed' errors.
"""

import pytest

BASE = "/api/v1/auth"


# ─── Register ───


async def test_register_teacher(client):
    """Test successful teacher registration."""
    response = await client.post(
        f"{BASE}/register",
        json={
            "email": "guru_test_1@sekolah.id",
            "password": "SecureP@ss123",
            "full_name": "Budi Hartono",
            "role": "teacher",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "guru_test_1@sekolah.id"
    assert data["role"] == "teacher"
    assert data["full_name"] == "Budi Hartono"
    assert "id" in data


async def test_register_student(client):
    """Test successful student registration."""
    response = await client.post(
        f"{BASE}/register",
        json={
            "email": "siswa_test_1@sekolah.id",
            "password": "SecureP@ss123",
            "full_name": "Ani Wulandari",
            "role": "student",
        },
    )
    assert response.status_code == 201
    assert response.json()["role"] == "student"


async def test_register_duplicate_email(client):
    """Test that duplicate email returns 409."""
    # Register first
    await client.post(
        f"{BASE}/register",
        json={
            "email": "duplicate_test@sekolah.id",
            "password": "SecureP@ss123",
            "full_name": "User One",
            "role": "teacher",
        },
    )
    # Duplicate
    response = await client.post(
        f"{BASE}/register",
        json={
            "email": "duplicate_test@sekolah.id",
            "password": "DifferentP@ss",
            "full_name": "User Two",
            "role": "student",
        },
    )
    assert response.status_code == 409


async def test_register_invalid_role(client):
    """Test that invalid role returns 422."""
    response = await client.post(
        f"{BASE}/register",
        json={
            "email": "bad_role@sekolah.id",
            "password": "SecureP@ss123",
            "full_name": "Bad Role",
            "role": "superadmin",
        },
    )
    assert response.status_code == 422


async def test_register_short_password(client):
    """Test that password < 8 chars returns 422."""
    response = await client.post(
        f"{BASE}/register",
        json={
            "email": "short_pw@sekolah.id",
            "password": "short",
            "full_name": "Short PW",
            "role": "teacher",
        },
    )
    assert response.status_code == 422


# ─── Login ───


async def test_login_success(client):
    """Test successful login returns access token and sets cookie."""
    # Register first
    await client.post(
        f"{BASE}/register",
        json={
            "email": "login_test@sekolah.id",
            "password": "SecureP@ss123",
            "full_name": "Login Test",
            "role": "teacher",
        },
    )
    # Login
    response = await client.post(
        f"{BASE}/login",
        json={
            "email": "login_test@sekolah.id",
            "password": "SecureP@ss123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 900

    # Check refresh token cookie is set
    assert "refresh_token" in response.cookies


async def test_login_wrong_password(client):
    """Test login with wrong password returns 401."""
    # Register first
    await client.post(
        f"{BASE}/register",
        json={
            "email": "wrong_pw_test@sekolah.id",
            "password": "SecureP@ss123",
            "full_name": "Wrong PW",
            "role": "teacher",
        },
    )
    # Login with wrong password
    response = await client.post(
        f"{BASE}/login",
        json={
            "email": "wrong_pw_test@sekolah.id",
            "password": "WrongPassword",
        },
    )
    assert response.status_code == 401


async def test_login_nonexistent_email(client):
    """Test login with non-existent email returns 401."""
    response = await client.post(
        f"{BASE}/login",
        json={
            "email": "nobody@nowhere.id",
            "password": "SecureP@ss123",
        },
    )
    assert response.status_code == 401


# ─── Protected Endpoint Access ───


async def test_protected_endpoint_with_token(client):
    """Test that a valid token grants access to protected endpoints."""
    # Register + login
    await client.post(
        f"{BASE}/register",
        json={
            "email": "protected_test@sekolah.id",
            "password": "SecureP@ss123",
            "full_name": "Protected Test",
            "role": "student",
        },
    )
    login_resp = await client.post(
        f"{BASE}/login",
        json={
            "email": "protected_test@sekolah.id",
            "password": "SecureP@ss123",
        },
    )
    token = login_resp.json()["access_token"]

    # Access modules list (requires any authenticated user)
    response = await client.get(
        "/api/v1/modules",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


async def test_protected_endpoint_without_token(client):
    """Test that missing token returns 401."""
    response = await client.get("/api/v1/modules")
    assert response.status_code == 401


# ─── Logout ───


async def test_logout(client):
    """Test logout clears the refresh token cookie."""
    response = await client.post(f"{BASE}/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "Berhasil logout"
