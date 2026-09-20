"""
Application configuration loaded from environment variables.
"""

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
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

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

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
