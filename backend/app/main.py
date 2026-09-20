"""
InklusifMath Platform — FastAPI Application Entry Point

This is the main FastAPI application that serves as the backend for the
InklusifMath accessible mathematics e-learning platform.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.rate_limiter import limiter
from app.core.firebase import init_firebase
from app.core.errors import AppError, app_error_handler
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    init_firebase()
    yield
    # Shutdown


app = FastAPI(
    title="InklusifMath API",
    description=(
        "Backend API untuk platform e-learning matematika aksesibel "
        "bagi siswa tunanetra dan low vision."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Structured error handler (DOC_xxx, AI_xxx, STT_xxx, etc.)
app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "inklusifmath-api"}
