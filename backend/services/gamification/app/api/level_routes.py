from fastapi import APIRouter, Depends, Query
from typing import List

from shared.middleware.auth import get_current_user
from ..schemas.gamification_schemas import (
    UserLevelResponse,
    ExpHistoryResponse,
    LevelConfigResponse,
)
from ..services.level_service import LevelService

router = APIRouter()


def get_level_service() -> LevelService:
    return LevelService()


@router.get("/me", response_model=UserLevelResponse)
async def get_my_level(
    current_user: dict = Depends(get_current_user),
    service: LevelService = Depends(get_level_service),
):
    """Get current user's level and exp"""
    return await service.get_user_level(user_id=current_user.user_id)


@router.get("/config", response_model=List[LevelConfigResponse])
async def get_level_config(
    service: LevelService = Depends(get_level_service),
):
    """Get level configuration (exp requirements per level)"""
    return await service.get_level_config()


@router.get("/exp-history", response_model=List[ExpHistoryResponse])
async def get_exp_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    service: LevelService = Depends(get_level_service),
):
    """Get exp gain history"""
    return await service.get_exp_history(
        user_id=current_user.user_id,
        page=page,
        page_size=page_size,
    )


@router.post("/add-exp")
async def add_exp(
    amount: int = Query(..., ge=1),
    source: str = Query(...),
    current_user: dict = Depends(get_current_user),
    service: LevelService = Depends(get_level_service),
):
    """Add exp to user (internal use)"""
    result = await service.add_exp(
        user_id=current_user.user_id,
        amount=amount,
        source=source,
    )
    return result
