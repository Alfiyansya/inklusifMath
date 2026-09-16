"""
Pydantic schemas for learning module endpoints.
"""

from pydantic import BaseModel

from app.schemas.document import MathExpressionResponse


class ModuleListItem(BaseModel):
    id: str
    title: str
    published_at: str


class ModuleListResponse(BaseModel):
    modules: list[ModuleListItem]


class ModuleDetailResponse(BaseModel):
    id: str
    title: str
    html_content: str
    math_expressions: list[MathExpressionResponse]
