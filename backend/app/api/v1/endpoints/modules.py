"""
Learning module endpoints: list published modules, get module detail, toggle publish.

Rate limits (TDD Section 1.11):
  GET  /modules        — 60/minute  (student listing page, frequent)
  GET  /modules/{id}   — 120/minute (content reading, screen reader page)
  POST /modules/{id}/publish — 10/hour (teacher publish/unpublish action)
"""

from __future__ import annotations

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.core.rate_limiter import limiter
from app.schemas.module import (
    ModuleDetailResponse,
    ModuleListItem,
    ModuleListResponse,
    ModulePublishRequest,
    ModulePublishResponse,
)
from app.schemas.document import MathExpressionResponse
from app.services import module_service as svc
from app.services import document_service as doc_svc

logger = logging.getLogger(__name__)

router = APIRouter()


# ── GET /modules ──────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=ModuleListResponse,
    summary="List all published learning modules",
)
@limiter.limit("60/minute")
async def list_modules(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    List all published learning modules available to students.
    Returns newest first.

    Rate limited: 60/minute.
    """
    modules = await svc.list_published_modules(db)

    return ModuleListResponse(
        modules=[
            ModuleListItem(
                id=str(m.id),
                title=m.document.title if m.document else "Tanpa Judul",
                published_at=m.published_at.isoformat() if m.published_at else "",
            )
            for m in modules
        ]
    )


# ── GET /modules/{module_id} ──────────────────────────────────────────────────

@router.get(
    "/{module_id}",
    response_model=ModuleDetailResponse,
    summary="Get full module content with math expressions",
)
@limiter.limit("120/minute")
async def get_module(
    request: Request,
    module_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    Get full module content with its math expressions.
    Only published modules are accessible.

    Rate limited: 120/minute (screen reader content reading).
    """
    try:
        module_uuid = uuid.UUID(module_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modul tidak ditemukan.",
        )

    module, expressions = await svc.get_module_with_expressions(db, module_uuid)

    if module is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modul tidak ditemukan atau belum dipublikasikan.",
        )

    return ModuleDetailResponse(
        id=str(module.id),
        title=module.document.title if module.document else "Tanpa Judul",
        html_content=module.html_content,
        math_expressions=[
            MathExpressionResponse(
                id=str(e.id),
                original_notation=e.original_notation,
                latex=e.latex_representation,
                ai_narration=e.ai_narration,
                teacher_narration=e.teacher_narration,
                status=e.status,
                position_order=e.position_order,
            )
            for e in expressions
        ],
    )


# ── POST /modules/{module_id}/publish ─────────────────────────────────────────

@router.post(
    "/{module_id}/publish",
    response_model=ModulePublishResponse,
    summary="Toggle publish status of a learning module",
)
@limiter.limit("10/hour")
async def publish_module(
    request: Request,
    module_id: str,
    body: ModulePublishRequest = None,
    current_user: Annotated[dict, Depends(require_role("teacher", "admin"))] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Publish or unpublish a learning module.

    - Requires 'teacher' or 'admin' role.
    - Verifies ownership: the requesting teacher must own the linked document.
    - Accepts optional JSON body: { "is_published": bool } (default: true).
    - If publishing: sets published_at = now().
    - If unpublishing: sets published_at = None.

    Returns 404 if module is not found or not owned by the requesting teacher.
    Rate limited: 10/hour.
    """
    if body is None:
        body = ModulePublishRequest()

    try:
        module_uuid = uuid.UUID(module_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modul tidak ditemukan.",
        )

    module = await doc_svc.toggle_module_publish(
        db=db,
        module_id=module_uuid,
        teacher_firebase_uid=current_user["firebase_uid"],
        publish=body.is_published,
    )

    if module is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modul tidak ditemukan atau tidak memiliki akses.",
        )

    return ModulePublishResponse(
        module_id=str(module.id),
        is_published=module.is_published,
        published_at=module.published_at.isoformat() if module.published_at else None,
    )
