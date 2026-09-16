"""
Document-related models: Document, MathExpression, LearningModule.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)
    original_file_path: Mapped[str] = mapped_column(Text, nullable=False)
    parsing_status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, index=True
    )
    ocr_used: Mapped[str] = mapped_column(String(20), default="none", nullable=False)
    raw_structure: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    teacher = relationship("User", back_populates="documents")
    math_expressions = relationship(
        "MathExpression", back_populates="document", cascade="all, delete-orphan"
    )
    learning_module = relationship(
        "LearningModule", back_populates="document", uselist=False
    )


class MathExpression(Base):
    __tablename__ = "math_expressions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True
    )
    original_notation: Mapped[str] = mapped_column(Text, nullable=False)
    latex_representation: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_narration: Mapped[str | None] = mapped_column(Text, nullable=True)
    teacher_narration: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, index=True
    )
    position_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), server_default=func.now()
    )

    # Relationships
    document = relationship("Document", back_populates="math_expressions")


class LearningModule(Base):
    __tablename__ = "learning_modules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        unique=True,
        nullable=False,
    )
    html_content: Mapped[str] = mapped_column(Text, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Relationships
    document = relationship("Document", back_populates="learning_module")
    tutor_sessions = relationship("TutorSession", back_populates="module")
