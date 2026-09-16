"""
Pydantic schemas for tutor endpoints.
"""

from pydantic import BaseModel, Field


class TutorAskRequest(BaseModel):
    module_id: str
    context_element_id: str
    transcript_text: str = Field(min_length=1, max_length=2000)


class TutorAskResponse(BaseModel):
    session_id: str
    answer_text: str
    follow_up_hint: str | None = None
