"""
FastAPI dependency injection for authentication and authorization.
Uses Firebase Admin SDK to verify ID tokens and DB lookup for role.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_auth
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.firebase import verify_firebase_token
from app.models.user import User

security = HTTPBearer()


async def get_firebase_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> dict:
    """Extract and validate the Firebase ID token without requiring a DB profile.

    Used during registration (create_profile) and initial profile checks (get_me).
    """
    try:
        decoded = verify_firebase_token(credentials.credentials)
    except firebase_auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sudah kedaluwarsa",
        )
    except firebase_auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autentikasi gagal",
        )

    return {
        "user_id": decoded["uid"],
        "email": decoded.get("email", ""),
        "firebase_uid": decoded["uid"],
    }


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Extract and validate the current user from Firebase ID token, then
    enrich with role and profile data from the database."""
    try:
        decoded = verify_firebase_token(credentials.credentials)
    except firebase_auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sudah kedaluwarsa",
        )
    except firebase_auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autentikasi gagal",
        )

    firebase_uid = decoded["uid"]

    # Look up the user in our DB to get the authoritative role
    result = await db.execute(select(User).where(User.firebase_uid == firebase_uid))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Pengguna tidak ditemukan dalam sistem",
        )

    return {
        "user_id": str(user.id),
        "email": user.email,
        "firebase_uid": user.firebase_uid,
        "role": user.role,
        "full_name": user.full_name,
    }


def require_role(*roles: str):
    """Dependency factory that restricts access to specific roles.

    Role is fetched from DB via get_current_user and strictly validated.
    Raises 403 if the authenticated user's role is not in the allowed list.
    """
    async def _check_role(
        current_user: Annotated[dict, Depends(get_current_user)],
    ) -> dict:
        user_role = current_user.get("role", "")
        if user_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Akses ditolak: dibutuhkan role {' atau '.join(roles)}",
            )
        return current_user
    return _check_role
