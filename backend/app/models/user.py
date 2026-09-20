"""
User model — represents teachers, students, and admins.
Linked to Firebase Auth via firebase_uid.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    firebase_uid: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # Kept for backward compatibility, no longer used with Firebase
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    student_level: Mapped[str | None] = mapped_column(
        String(10), nullable=True, default=None
    )  # 'SD' | 'SMP' | 'SMA' — only for role='student'
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    documents = relationship("Document", back_populates="teacher")
    tutor_sessions = relationship("TutorSession", back_populates="student")
