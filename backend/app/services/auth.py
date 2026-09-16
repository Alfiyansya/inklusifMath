"""
Authentication service — register, login, and token management.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models import User


class AuthService:
    """Handles user registration, login, and token refresh."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(
        self, email: str, password: str, full_name: str, role: str
    ) -> User:
        """Register a new user. Raises ValueError if email already exists."""
        # Check if email already exists
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise ValueError("Email sudah terdaftar")

        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role=role,
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def authenticate(self, email: str, password: str) -> User | None:
        """Verify credentials and return user if valid, None otherwise."""
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.password_hash):
            return None

        return user

    @staticmethod
    def create_tokens(user: User) -> dict:
        """Generate access and refresh tokens for a user."""
        access_token = create_access_token(str(user.id), user.role)
        refresh_token = create_refresh_token(str(user.id))
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Find a user by their UUID."""
        stmt = select(User).where(User.id == uuid.UUID(user_id))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
