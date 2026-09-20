"""
Tests for StorageService (local disk + GCS path detection).
"""
from __future__ import annotations

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestStorageServiceIsGcsPath:
    def test_gs_prefix_is_gcs(self):
        from app.services.storage import StorageService
        svc = StorageService()
        assert svc.is_gcs_path("gs://bucket/file.docx") is True

    def test_local_path_is_not_gcs(self):
        from app.services.storage import StorageService
        svc = StorageService()
        assert svc.is_gcs_path("/app/uploads/file.docx") is False

    def test_http_is_not_gcs(self):
        from app.services.storage import StorageService
        svc = StorageService()
        assert svc.is_gcs_path("https://storage.googleapis.com/bucket/file") is False


class TestStorageServiceLocal:
    @pytest.mark.asyncio
    async def test_save_creates_file(self):
        from app.services.storage import StorageService
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("app.services.storage.settings") as mock_settings:
                mock_settings.GCS_ENABLED = False
                mock_settings.UPLOAD_DIR = tmpdir

                svc = StorageService()
                path = await svc.save(b"hello docx content", "test.docx")

            # Assertions inside the tempdir context so the dir still exists
            assert path.endswith(".docx")
            assert os.path.exists(path)

    @pytest.mark.asyncio
    async def test_save_generates_unique_names(self):
        from app.services.storage import StorageService

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("app.services.storage.settings") as mock_settings:
                mock_settings.GCS_ENABLED = False
                mock_settings.UPLOAD_DIR = tmpdir

                svc = StorageService()
                path1 = await svc.save(b"content A", "file.pdf")
                path2 = await svc.save(b"content B", "file.pdf")

        assert path1 != path2

    @pytest.mark.asyncio
    async def test_load_reads_file(self):
        from app.services.storage import StorageService

        with tempfile.TemporaryDirectory() as tmpdir:
            # Write a file directly
            test_path = os.path.join(tmpdir, "test.bin")
            with open(test_path, "wb") as f:
                f.write(b"test bytes 1234")

            with patch("app.services.storage.settings") as mock_settings:
                mock_settings.GCS_ENABLED = False
                mock_settings.UPLOAD_DIR = tmpdir

                svc = StorageService()
                data = await svc.load(test_path)

        assert data == b"test bytes 1234"

    @pytest.mark.asyncio
    async def test_save_preserves_extension(self):
        from app.services.storage import StorageService

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("app.services.storage.settings") as mock_settings:
                mock_settings.GCS_ENABLED = False
                mock_settings.UPLOAD_DIR = tmpdir

                svc = StorageService()
                path = await svc.save(b"pdf bytes", "document.pdf")

        assert path.endswith(".pdf")


class TestStorageServiceGcsPath:
    @pytest.mark.asyncio
    async def test_save_gcs_returns_gs_uri(self):
        from app.services.storage import StorageService

        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_client.return_value.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        with patch("app.services.storage.settings") as mock_settings:
            mock_settings.GCS_ENABLED = True
            mock_settings.GCS_BUCKET_NAME = "test-bucket"

            with patch("google.cloud.storage.Client", mock_client):
                svc = StorageService()
                path = await svc.save(b"content", "file.docx")

        assert path.startswith("gs://test-bucket/uploads/")
        assert path.endswith(".docx")

    @pytest.mark.asyncio
    async def test_load_gcs_calls_download(self):
        from app.services.storage import StorageService

        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_blob.download_as_bytes.return_value = b"gcs file content"
        mock_client.return_value.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        with patch("app.services.storage.settings") as mock_settings:
            mock_settings.GCS_ENABLED = True
            mock_settings.GCS_BUCKET_NAME = "test-bucket"

            with patch("google.cloud.storage.Client", mock_client):
                svc = StorageService()
                data = await svc.load("gs://test-bucket/uploads/file.docx")

        assert data == b"gcs file content"
        mock_bucket.blob.assert_called_once_with("uploads/file.docx")


class TestCeleryAppConfig:
    def test_celery_app_importable(self):
        from app.worker.celery_app import celery_app
        assert celery_app.main == "inklusifmath"

    def test_celery_app_includes_tasks(self):
        from app.worker.celery_app import celery_app
        assert "app.worker.tasks" in celery_app.conf.include

    def test_celery_serializer_is_json(self):
        from app.worker.celery_app import celery_app
        assert celery_app.conf.task_serializer == "json"


class TestProcessDocumentTask:
    def test_task_registered(self):
        from app.worker.celery_app import celery_app
        from app.worker import tasks  # noqa: F401 — trigger autodiscover
        assert "app.worker.tasks.process_document" in celery_app.tasks

    def test_task_has_retry_config(self):
        from app.worker.tasks import process_document
        assert process_document.max_retries == 3
        assert process_document.default_retry_delay == 30
