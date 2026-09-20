"""
Pydantic schemas for authentication endpoints.
"""

from pydantic import BaseModel, Field


class ProfileCreateRequest(BaseModel):
    """Request to create a user profile after Firebase registration."""
    full_name: str = Field(min_length=1, max_length=255)
    role: str = Field(pattern="^(teacher|student|admin)$")
    student_level: str | None = Field(
        default=None, pattern="^(SD|SMP|SMA)$"
    )


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    full_name: str
    student_level: str | None = None
    firebase_uid: str

    model_config = {"from_attributes": True}
