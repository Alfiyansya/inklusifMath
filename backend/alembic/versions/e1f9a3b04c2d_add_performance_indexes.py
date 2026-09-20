"""add performance indexes for common query patterns

Revision ID: e1f9a3b04c2d
Revises: d5e8f2a91b3c
Create Date: 2026-09-17 21:38:00.000000+07:00

Indexes target the six most common query patterns in InklusifMath:

1. documents(teacher_id, created_at DESC)
   → GET /documents — guru dashboard: "semua dokumen saya, terbaru dulu"
   → Composite because teacher_id is always first filter, then date sort

2. documents(parsing_status)
   → Polling & filtering by status (pending/processing/completed/failed)

3. math_expressions(document_id, position_order)
   → GET /documents/{id}/narrations — narasi ordered by position
   → position_order almost always used together with document_id

4. math_expressions(document_id, status)
   → COUNT of pending/approved expressions per document (publish gate)
   → Avoid full table scan for progress bar calculation

5. learning_modules(is_published, published_at DESC)
   → GET /modules (student facing) — published modules sorted newest first
   → Partial-like composite: is_published filtered first, then sort

6. tutor_sessions(student_id, module_id)
   → Lookup or create session for student×module pair
   → Also used for session history per module

7. tutor_messages(session_id, created_at)
   → Load chat history for a session, chronological order
   → session_id always present, created_at for ordering

Note: single-column indexes already created by SQLAlchemy via index=True in models:
  - users.firebase_uid (ix_users_firebase_uid, uq_users_firebase_uid)
  - users.email (unique constraint / ix_users_email)
  - documents.teacher_id (ix_documents_teacher_id)
  - documents.parsing_status (ix_documents_parsing_status)
  - math_expressions.document_id (ix_math_expressions_document_id)
  - math_expressions.status (ix_math_expressions_status)
  - learning_modules.is_published (ix_learning_modules_is_published)
  - tutor_sessions.student_id (ix_tutor_sessions_student_id)
  - tutor_messages.session_id (ix_tutor_messages_session_id)

This migration adds COMPOSITE indexes for multi-column query patterns.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "e1f9a3b04c2d"
down_revision: Union[str, None] = "d5e8f2a91b3c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. documents(teacher_id, created_at DESC) ─────────────────────────────
    # Guru dashboard: "semua dokumen saya, terbaru dulu"
    # Without this, Postgres scans all documents filtered by teacher_id then sorts.
    op.create_index(
        "ix_documents_teacher_created",
        "documents",
        ["teacher_id", "created_at"],
        postgresql_ops={"created_at": "DESC"},
    )

    # ── 2. math_expressions(document_id, position_order) ─────────────────────
    # Review narasi page: fetch expressions for a doc in display order.
    # Covers both: WHERE doc_id=X ORDER BY position_order
    op.create_index(
        "ix_math_expressions_doc_position",
        "math_expressions",
        ["document_id", "position_order"],
    )

    # ── 3. math_expressions(document_id, status) ─────────────────────────────
    # Progress bar: COUNT(*) WHERE document_id=X AND status='approved'
    # Avoids full scan of math_expressions table per document.
    op.create_index(
        "ix_math_expressions_doc_status",
        "math_expressions",
        ["document_id", "status"],
    )

    # ── 4. learning_modules(is_published, published_at DESC) ──────────────────
    # Student module listing: WHERE is_published=true ORDER BY published_at DESC
    # Without this: bitmap index scan on is_published + sort (slow at scale).
    op.create_index(
        "ix_learning_modules_published_at",
        "learning_modules",
        ["is_published", "published_at"],
        postgresql_ops={"published_at": "DESC"},
    )

    # ── 5. tutor_sessions(student_id, module_id) ──────────────────────────────
    # Lookup or create a tutor session for a specific student×module pair.
    # Also used for session history by module.
    op.create_index(
        "ix_tutor_sessions_student_module",
        "tutor_sessions",
        ["student_id", "module_id"],
    )

    # ── 6. tutor_messages(session_id, created_at) ─────────────────────────────
    # Load chat history: WHERE session_id=X ORDER BY created_at ASC
    # Single-column ix_tutor_messages_session_id exists but doesn't cover the sort.
    op.create_index(
        "ix_tutor_messages_session_created",
        "tutor_messages",
        ["session_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_tutor_messages_session_created", table_name="tutor_messages")
    op.drop_index("ix_tutor_sessions_student_module", table_name="tutor_sessions")
    op.drop_index("ix_learning_modules_published_at", table_name="learning_modules")
    op.drop_index("ix_math_expressions_doc_status", table_name="math_expressions")
    op.drop_index("ix_math_expressions_doc_position", table_name="math_expressions")
    op.drop_index("ix_documents_teacher_created", table_name="documents")
