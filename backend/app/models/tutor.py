"""
Tutor-related models: TutorSession, TutorMessage.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TutorSession(Base):
    __tablename__ = "tutor_sessions"
    __table_args__ = (
        # Composite: student_id + module_id → session lookup per siswa×modul
        Index("ix_tutor_sessions_student_module", "student_id", "module_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    module_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("learning_modules.id"),
        nullable=False,
    )
    context_element_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    student = relationship("User", back_populates="tutor_sessions")
    module = relationship("LearningModule", back_populates="tutor_sessions")
    messages = relationship(
        "TutorMessage", back_populates="session", cascade="all, delete-orphan"
    )


class TutorMessage(Base):
    __tablename__ = "tutor_messages"
    __table_args__ = (
        # Composite: session_id + created_at → ordered chat history per session
        Index("ix_tutor_messages_session_created", "session_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tutor_sessions.id"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(10), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    # Relationships
    session = relationship("TutorSession", back_populates="messages")
