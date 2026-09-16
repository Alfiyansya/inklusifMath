"""
API v1 router — aggregates all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, documents, modules, tutor

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(modules.router, prefix="/modules", tags=["Modules"])
api_router.include_router(tutor.router, prefix="/tutor", tags=["Tutor"])
