"""
Module service layer.

Handles business logic for LearningModule:
  - Listing all published modules for a student
  - Fetching module detail with math expressions
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.document import LearningModule, MathExpression

logger = logging.getLogger(__name__)


async def list_published_modules(db: AsyncSession) -> list[LearningModule]:
    """Return all published LearningModule rows, newest first."""
    result = await db.execute(
        select(LearningModule)
        .where(LearningModule.is_published == True)  # noqa: E712
        .order_by(LearningModule.published_at.desc())
        .options(selectinload(LearningModule.document))
    )
    return list(result.scalars().all())


async def get_module_with_expressions(
    db: AsyncSession,
    module_id: uuid.UUID,
) -> tuple[LearningModule | None, list[MathExpression]]:
    """
    Fetch a published module by ID with its related math expressions.

    Returns:
        (module, expressions) — module is None if not found or not published.
    """
    result = await db.execute(
        select(LearningModule)
        .where(
            LearningModule.id == module_id,
            LearningModule.is_published == True,  # noqa: E712
        )
        .options(selectinload(LearningModule.document))
    )
    module = result.scalar_one_or_none()
    if module is None:
        return None, []

    # Fetch math expressions via document relationship
    expr_result = await db.execute(
        select(MathExpression)
        .where(MathExpression.document_id == module.document_id)
        .order_by(MathExpression.position_order)
    )
    expressions = list(expr_result.scalars().all())
    return module, expressions
