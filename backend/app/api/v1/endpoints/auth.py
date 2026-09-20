"""
Authentication endpoints for Firebase Auth integration.

Firebase handles email/password auth directly on the client.
Backend manages user profiles (role, student_level, full_name).

Rate limits (TDD Section 1.11):
  POST /profile   — 5/hour   (one-time registration)
  GET  /me        — 60/minute (frequent session check)
  POST /logout    — 10/minute (normal logout usage)
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_firebase_user
from app.core.rate_limiter import limiter
from app.models.user import User
from app.schemas.auth import ProfileCreateRequest, UserResponse

router = APIRouter()


@router.post(
    "/profile", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
@limiter.limit("5/hour")
async def create_profile(
    request: Request,
    body: ProfileCreateRequest,
    current_user: Annotated[dict, Depends(get_firebase_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a user profile after Firebase registration.

    Called by the frontend after createUserWithEmailAndPassword succeeds.
    The Firebase ID token is used to identify the user.

    Rate limited: 5/hour (one-time registration flow).
    """
    firebase_uid = current_user["firebase_uid"]
    email = current_user.get("email", "")

    # Check if profile already exists
    stmt = select(User).where(User.firebase_uid == firebase_uid)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profil sudah dibuat",
        )

    user = User(
        firebase_uid=firebase_uid,
        email=email,
        full_name=body.full_name,
        role=body.role,
        student_level=body.student_level if body.role == "student" else None,
    )
    db.add(user)
    await db.flush()

    return UserResponse(
        id=str(user.id),
        email=user.email,
        role=user.role,
        full_name=user.full_name,
        student_level=user.student_level,
        firebase_uid=user.firebase_uid,
    )


@router.get("/me", response_model=UserResponse)
@limiter.limit("60/minute")
async def get_me(
    request: Request,
    current_user: Annotated[dict, Depends(get_firebase_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get the current user's profile.

    Rate limited: 60/minute (frequent session checks).
    """
    firebase_uid = current_user["firebase_uid"]

    stmt = select(User).where(User.firebase_uid == firebase_uid)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil tidak ditemukan",
        )

    return UserResponse(
        id=str(user.id),
        email=user.email,
        role=user.role,
        full_name=user.full_name,
        student_level=user.student_level,
        firebase_uid=user.firebase_uid,
    )


@router.post("/logout")
@limiter.limit("10/minute")
async def logout(request: Request):
    """Logout endpoint (client-side Firebase signOut handles the actual logout).

    This endpoint exists for API compatibility.
    Rate limited: 10/minute.
    """
    return {"message": "Berhasil logout"}
