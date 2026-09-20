"""
FastAPI dependency injection for authentication and authorization.
Uses Firebase Admin SDK to verify ID tokens.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_auth

from app.core.firebase import verify_firebase_token

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> dict:
    """Extract and validate the current user from Firebase ID token."""
    try:
        decoded = verify_firebase_token(credentials.credentials)
        return {
            "user_id": decoded["uid"],
            "email": decoded.get("email", ""),
            "firebase_uid": decoded["uid"],
        }
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


def require_role(*roles: str):
    """Dependency factory that restricts access to specific roles.

    Note: Role is stored in our backend DB, not in Firebase token.
    This dependency requires the caller to also look up the user profile.
    """
    async def _check_role(
        current_user: Annotated[dict, Depends(get_current_user)],
    ) -> dict:
        # For role checking, we'd need to look up the user in our DB
        # This is a placeholder — callers should verify role from DB profile
        if current_user.get("role") and current_user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return _check_role
