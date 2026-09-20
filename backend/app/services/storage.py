"""
Storage service: local disk or Google Cloud Storage.

Usage:
    path = await storage.save(file_bytes, filename)  # returns gs:// or /local/path
    data = await storage.load(path)                  # handles both

Environment:
    GCS_ENABLED=true + GCS_BUCKET_NAME=<bucket>  → GCS mode
    GCS_ENABLED=false (default)                  → local disk mode
"""
from __future__ import annotations

import logging
import uuid
from pathlib import Path

import aiofiles

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Unified file storage: local disk or GCS."""

    def is_gcs_path(self, path: str) -> bool:
        return path.startswith("gs://")

    async def save(self, file_bytes: bytes, original_filename: str) -> str:
        """
        Save file bytes. Returns storage path (gs:// or absolute local path).
        Filename is prefixed with UUID to avoid collisions.
        """
        # Generate unique filename
        suffix = Path(original_filename).suffix.lower()
        unique_name = f"{uuid.uuid4().hex}{suffix}"

        if settings.GCS_ENABLED:
            return await self._save_gcs(file_bytes, unique_name)
        return await self._save_local(file_bytes, unique_name)

    async def load(self, path: str) -> bytes:
        """Load file bytes from storage path (gs:// or local)."""
        if self.is_gcs_path(path):
            return await self._load_gcs(path)
        return await self._load_local(path)

    async def _save_local(self, data: bytes, filename: str) -> str:
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        dest = upload_dir / filename
        async with aiofiles.open(dest, "wb") as f:
            await f.write(data)
        abs_path = str(dest.resolve())
        logger.info("Saved %d bytes to local: %s", len(data), abs_path)
        return abs_path

    async def _load_local(self, path: str) -> bytes:
        async with aiofiles.open(path, "rb") as f:
            return await f.read()

    async def _save_gcs(self, data: bytes, filename: str) -> str:
        import asyncio
        from google.cloud import storage as gcs

        blob_name = f"uploads/{filename}"
        gcs_path = f"gs://{settings.GCS_BUCKET_NAME}/{blob_name}"

        def _upload() -> None:
            client = gcs.Client()
            bucket = client.bucket(settings.GCS_BUCKET_NAME)
            blob = bucket.blob(blob_name)
            blob.upload_from_string(data)

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _upload)
        logger.info("Saved %d bytes to GCS: %s", len(data), gcs_path)
        return gcs_path

    async def _load_gcs(self, gcs_path: str) -> bytes:
        import asyncio
        from google.cloud import storage as gcs

        # Parse gs://bucket/blob
        without_prefix = gcs_path[5:]  # remove gs://
        bucket_name, _, blob_name = without_prefix.partition("/")

        def _download() -> bytes:
            client = gcs.Client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            return blob.download_as_bytes()

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _download)


# Module-level singleton
storage = StorageService()
