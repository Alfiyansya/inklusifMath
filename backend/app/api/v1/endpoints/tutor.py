"""
Socratic tutor endpoint: process student questions contextually.
"""

from __future__ import annotations

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.rate_limiter import limiter
from app.schemas.tutor import TutorAskRequest, TutorAskResponse
from app.services import tutor_service as svc

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/ask",
    response_model=TutorAskResponse,
    summary="Ask the Socratic tutor a math question",
)
@limiter.limit("30/hour")
async def ask_tutor(
    request: Request,
    body: TutorAskRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    Send a student question to the Socratic AI tutor.

    The tutor NEVER gives direct answers — it guides students with questions
    (Socratic method). Responses are in Bahasa Indonesia, 2-4 sentences max
    (screen reader optimized).

    Rate limited: 30 requests/hour per student.
    """
    if not body.transcript_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "TUTOR_001",
                "message": "Pertanyaan tidak boleh kosong.",
            },
        )

    answer_text, follow_up_hint = await svc.ask_tutor(
        question=body.transcript_text,
        module_id=body.module_id,
        context_element_id=body.context_element_id,
    )

    session_id = str(uuid.uuid4())

    logger.info(
        "[tutor] user=%s module=%s context=%s",
        current_user.get("user_id", "?"),
        body.module_id,
        body.context_element_id,
    )

    return TutorAskResponse(
        session_id=session_id,
        answer_text=answer_text,
        follow_up_hint=follow_up_hint,
    )
