"""
Application configuration loaded from environment variables.
"""

import json
import os
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application
    APP_NAME: str = "InklusifMath API"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/inklusifmath"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT (kept for backward compatibility, not actively used with Firebase)
    JWT_SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION-use-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Firebase
    FIREBASE_PROJECT_ID: str = ""

    # CORS
    CORS_ORIGINS: str | list[str] = ["http://localhost:3000"]

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 20
    UPLOAD_DIR: str = "uploads"

    # AI Services
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # STT
    WHISPER_API_KEY: str = ""

    # OCR
    GOOGLE_CLOUD_VISION_CREDENTIALS: str = ""
    MATHPIX_APP_ID: str = ""
    MATHPIX_APP_KEY: str = ""
    MATH_OCR_ENGINE: str = "pix2tex"  # "pix2tex" (free) | "mathpix" (paid) | "auto"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # GCS
    GCS_ENABLED: bool = False
    GCS_BUCKET_NAME: str = "inklusifmath-uploads"

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if not v or not v.strip() or "${{" in v:
            pghost = os.getenv("PGHOST")
            if pghost:
                pguser = os.getenv("PGUSER", "postgres")
                pgpassword = os.getenv("PGPASSWORD", "")
                pgport = os.getenv("PGPORT", "5432")
                pgdatabase = os.getenv("PGDATABASE", "railway")
                auth_part = f"{pguser}:{pgpassword}@" if pgpassword else f"{pguser}@"
                return f"postgresql+asyncpg://{auth_part}{pghost}:{pgport}/{pgdatabase}"
            for fallback_var in ["DATABASE_PRIVATE_URL", "DATABASE_PUBLIC_URL", "POSTGRES_URL"]:
                fallback_val = os.getenv(fallback_var)
                if fallback_val and "${{" not in fallback_val:
                    return cls.assemble_db_connection(fallback_val)
            raise ValueError(
                f"DATABASE_URL tidak valid atau template belum ter-resolve oleh Railway: {v!r}. "
                f"Pastikan nama service PostgreSQL di Railway sesuai dengan referensi "
                f"(misal jika nama service database Anda adalah 'PostgreSQL', gunakan ${{PostgreSQL.DATABASE_URL}} "
                f"atau pilih via tombol 'Add Reference' di tab Variables)."
            )
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @field_validator("REDIS_URL", mode="after")
    @classmethod
    def assemble_redis_connection(cls, v: str) -> str:
        if not v or not v.strip() or "${{" in v:
            for fallback_var in ["REDIS_PRIVATE_URL", "REDIS_PUBLIC_URL", "REDISURL"]:
                fallback_val = os.getenv(fallback_var)
                if fallback_val and "${{" not in fallback_val:
                    return fallback_val
            redishost = os.getenv("REDISHOST")
            if redishost:
                redisport = os.getenv("REDISPORT", "6379")
                redisuser = os.getenv("REDISUSER", "default")
                redispass = os.getenv("REDISPASSWORD", "")
                auth_part = f"{redisuser}:{redispass}@" if redispass else ""
                return f"redis://{auth_part}{redishost}:{redisport}/0"
            return "redis://localhost:6379/0"
        return v

    @field_validator("CELERY_BROKER_URL", "CELERY_RESULT_BACKEND", mode="after")
    @classmethod
    def assemble_celery_urls(cls, v: str) -> str:
        if not v or not v.strip() or "${{" in v:
            for fallback_var in ["REDIS_PRIVATE_URL", "REDIS_PUBLIC_URL", "REDIS_URL"]:
                fallback_val = os.getenv(fallback_var)
                if fallback_val and "${{" not in fallback_val:
                    return fallback_val
            return "redis://localhost:6379/0"
        return v

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            v_trimmed = v.strip()
            if v_trimmed.startswith("[") and v_trimmed.endswith("]"):
                try:
                    parsed = json.loads(v_trimmed)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except Exception:
                    pass
            return [origin.strip() for origin in v_trimmed.split(",") if origin.strip()]
        if isinstance(v, list):
            return [str(item).strip() for item in v if str(item).strip()]
        return ["http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
