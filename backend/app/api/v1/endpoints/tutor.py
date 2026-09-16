"""
Socratic tutor endpoint: process student questions contextually.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.dependencies import get_current_user
from app.core.rate_limiter import limiter
from app.schemas.tutor import TutorAskRequest, TutorAskResponse

router = APIRouter()


@router.post("/ask", response_model=TutorAskResponse)
@limiter.limit("30/hour")
async def ask_tutor(
    request: Request,
    body: TutorAskRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Send a student question to the Socratic AI tutor.
    Rate limited: 30 requests/hour for students, 60/hour for teachers.
    """
    # TODO: Implement with Gemini API
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Tutor not yet implemented",
    )
