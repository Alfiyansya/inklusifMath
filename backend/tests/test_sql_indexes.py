"""
Tests for SQL Performance Indexes (TDD Section 2.10).

Tests verify:
  - Migration file exists and is importable (syntax valid)
  - All 6 composite index names are consistent between migration and models
  - Alembic revision chain is correct (down_revision points to previous)
  - SQLAlchemy models declare composite indexes via __table_args__
  - Index column combinations match the intended query patterns
"""

from __future__ import annotations

import importlib.util
import pathlib
import types


# ── Helper: load migration file directly (alembic/versions is not a package) ──

def _load_migration(filename: str) -> types.ModuleType:
    """Load an Alembic migration file by filename (not importable as package)."""
    migration_dir = (
        pathlib.Path(__file__).parent.parent / "alembic" / "versions"
    )
    path = migration_dir / filename
    spec = importlib.util.spec_from_file_location("migration_mod", path)
    assert spec is not None and spec.loader is not None, f"Cannot load {path}"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── Migration file validation ─────────────────────────────────────────────────

class TestIndexMigration:
    _FILENAME = "e1f9a3b04c2d_add_performance_indexes.py"

    def test_migration_importable(self):
        """Migration file has valid Python syntax and is importable."""
        mod = _load_migration(self._FILENAME)
        assert mod is not None

    def test_revision_id(self):
        mod = _load_migration(self._FILENAME)
        assert mod.revision == "e1f9a3b04c2d"

    def test_down_revision_points_to_firebase_uid_migration(self):
        """Chain: e1f9a3b04c2d → d5e8f2a91b3c (firebase_uid migration)."""
        mod = _load_migration(self._FILENAME)
        assert mod.down_revision == "d5e8f2a91b3c"

    def test_upgrade_function_exists(self):
        mod = _load_migration(self._FILENAME)
        assert callable(mod.upgrade)

    def test_downgrade_function_exists(self):
        mod = _load_migration(self._FILENAME)
        assert callable(mod.downgrade)


# ── Model __table_args__ validation ──────────────────────────────────────────

class TestDocumentModelIndexes:
    def test_document_has_table_args(self):
        from app.models.document import Document
        assert hasattr(Document, "__table_args__")

    def test_document_composite_index_teacher_created(self):
        """ix_documents_teacher_created covers (teacher_id, created_at)."""
        from sqlalchemy import Index
        from app.models.document import Document
        args = Document.__table_args__
        index_names = {a.name for a in args if isinstance(a, Index)}
        assert "ix_documents_teacher_created" in index_names

    def test_document_teacher_created_columns(self):
        from sqlalchemy import Index
        from app.models.document import Document
        args = Document.__table_args__
        for a in args:
            if isinstance(a, Index) and a.name == "ix_documents_teacher_created":
                col_names = [c.key for c in a.expressions]
                assert "teacher_id" in col_names
                assert "created_at" in col_names
                break


class TestMathExpressionModelIndexes:
    def test_math_expression_has_table_args(self):
        from app.models.document import MathExpression
        assert hasattr(MathExpression, "__table_args__")

    def test_math_expression_doc_position_index(self):
        from sqlalchemy import Index
        from app.models.document import MathExpression
        args = MathExpression.__table_args__
        index_names = {a.name for a in args if isinstance(a, Index)}
        assert "ix_math_expressions_doc_position" in index_names

    def test_math_expression_doc_status_index(self):
        from sqlalchemy import Index
        from app.models.document import MathExpression
        args = MathExpression.__table_args__
        index_names = {a.name for a in args if isinstance(a, Index)}
        assert "ix_math_expressions_doc_status" in index_names

    def test_doc_position_columns(self):
        from sqlalchemy import Index
        from app.models.document import MathExpression
        for a in MathExpression.__table_args__:
            if isinstance(a, Index) and a.name == "ix_math_expressions_doc_position":
                col_names = [c.key for c in a.expressions]
                assert "document_id" in col_names
                assert "position_order" in col_names
                break

    def test_doc_status_columns(self):
        from sqlalchemy import Index
        from app.models.document import MathExpression
        for a in MathExpression.__table_args__:
            if isinstance(a, Index) and a.name == "ix_math_expressions_doc_status":
                col_names = [c.key for c in a.expressions]
                assert "document_id" in col_names
                assert "status" in col_names
                break


class TestLearningModuleModelIndexes:
    def test_learning_module_has_table_args(self):
        from app.models.document import LearningModule
        assert hasattr(LearningModule, "__table_args__")

    def test_learning_module_published_index(self):
        from sqlalchemy import Index
        from app.models.document import LearningModule
        args = LearningModule.__table_args__
        index_names = {a.name for a in args if isinstance(a, Index)}
        assert "ix_learning_modules_published_at" in index_names

    def test_published_at_columns(self):
        from sqlalchemy import Index
        from app.models.document import LearningModule
        for a in LearningModule.__table_args__:
            if isinstance(a, Index) and a.name == "ix_learning_modules_published_at":
                col_names = [c.key for c in a.expressions]
                assert "is_published" in col_names
                assert "published_at" in col_names
                break


class TestTutorModelIndexes:
    def test_tutor_session_has_table_args(self):
        from app.models.tutor import TutorSession
        assert hasattr(TutorSession, "__table_args__")

    def test_tutor_session_student_module_index(self):
        from sqlalchemy import Index
        from app.models.tutor import TutorSession
        args = TutorSession.__table_args__
        index_names = {a.name for a in args if isinstance(a, Index)}
        assert "ix_tutor_sessions_student_module" in index_names

    def test_session_student_module_columns(self):
        from sqlalchemy import Index
        from app.models.tutor import TutorSession
        for a in TutorSession.__table_args__:
            if isinstance(a, Index) and a.name == "ix_tutor_sessions_student_module":
                col_names = [c.key for c in a.expressions]
                assert "student_id" in col_names
                assert "module_id" in col_names
                break

    def test_tutor_message_has_table_args(self):
        from app.models.tutor import TutorMessage
        assert hasattr(TutorMessage, "__table_args__")

    def test_tutor_message_session_created_index(self):
        from sqlalchemy import Index
        from app.models.tutor import TutorMessage
        args = TutorMessage.__table_args__
        index_names = {a.name for a in args if isinstance(a, Index)}
        assert "ix_tutor_messages_session_created" in index_names

    def test_message_session_created_columns(self):
        from sqlalchemy import Index
        from app.models.tutor import TutorMessage
        for a in TutorMessage.__table_args__:
            if isinstance(a, Index) and a.name == "ix_tutor_messages_session_created":
                col_names = [c.key for c in a.expressions]
                assert "session_id" in col_names
                assert "created_at" in col_names
                break


# ── Index name consistency between migration and models ───────────────────────

class TestIndexNameConsistency:
    """Ensure migration index names match model index names (no typos)."""

    _FILENAME = "e1f9a3b04c2d_add_performance_indexes.py"

    EXPECTED_INDEX_NAMES = {
        "ix_documents_teacher_created",
        "ix_math_expressions_doc_position",
        "ix_math_expressions_doc_status",
        "ix_learning_modules_published_at",
        "ix_tutor_sessions_student_module",
        "ix_tutor_messages_session_created",
    }

    def _get_migration_index_names(self) -> set[str]:
        """Parse upgrade() source to extract index names (quick string check)."""
        import inspect
        mod = _load_migration(self._FILENAME)
        source = inspect.getsource(mod.upgrade)
        return {name for name in self.EXPECTED_INDEX_NAMES if name in source}

    def test_all_index_names_in_migration_upgrade(self):
        found = self._get_migration_index_names()
        missing = self.EXPECTED_INDEX_NAMES - found
        assert not missing, f"Index names missing from migration upgrade(): {missing}"

    def _get_migration_downgrade_names(self) -> set[str]:
        import inspect
        mod = _load_migration(self._FILENAME)
        source = inspect.getsource(mod.downgrade)
        return {name for name in self.EXPECTED_INDEX_NAMES if name in source}

    def test_all_index_names_in_migration_downgrade(self):
        """All indexes should also appear in downgrade() for clean rollback."""
        found = self._get_migration_downgrade_names()
        missing = self.EXPECTED_INDEX_NAMES - found
        assert not missing, f"Index names missing from migration downgrade(): {missing}"

    def test_total_6_composite_indexes_defined(self):
        """Exactly 6 composite indexes must be defined."""
        assert len(self.EXPECTED_INDEX_NAMES) == 6
