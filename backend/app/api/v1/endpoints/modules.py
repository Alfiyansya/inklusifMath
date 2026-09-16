"""
Learning module endpoints: list published modules, get module detail.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.schemas.module import ModuleDetailResponse, ModuleListResponse

router = APIRouter()


@router.get("", response_model=ModuleListResponse)
async def list_modules(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """List all published learning modules."""
    # TODO: Implement
    return ModuleListResponse(modules=[])


@router.get("/{module_id}", response_model=ModuleDetailResponse)
async def get_module(
    module_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get full module content with math expressions."""
    # TODO: Implement
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not yet implemented",
    )
