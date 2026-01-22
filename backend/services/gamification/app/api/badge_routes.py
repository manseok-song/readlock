from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from shared.middleware.auth import get_current_user
from ..schemas.gamification_schemas import (
    BadgeResponse,
    UserBadgeResponse,
    BadgeProgressResponse,
)
from ..services.badge_service import BadgeService

router = APIRouter()


def get_badge_service() -> BadgeService:
    return BadgeService()


@router.get("/", response_model=List[BadgeResponse])
async def get_all_badges(
    service: BadgeService = Depends(get_badge_service),
):
    """Get all available badges"""
    return await service.get_all_badges()


@router.get("/me", response_model=List[UserBadgeResponse])
async def get_my_badges(
    current_user: dict = Depends(get_current_user),
    service: BadgeService = Depends(get_badge_service),
):
    """Get current user's earned badges"""
    return await service.get_user_badges(user_id=current_user.user_id)


@router.get("/progress", response_model=List[BadgeProgressResponse])
async def get_badge_progress(
    current_user: dict = Depends(get_current_user),
    service: BadgeService = Depends(get_badge_service),
):
    """Get progress towards all badges"""
    return await service.get_badge_progress(user_id=current_user.user_id)


@router.post("/{badge_id}/claim")
async def claim_badge(
    badge_id: str,
    current_user: dict = Depends(get_current_user),
    service: BadgeService = Depends(get_badge_service),
):
    """Claim a badge if requirements are met"""
    result = await service.claim_badge(
        user_id=current_user.user_id,
        badge_id=badge_id,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Badge requirements not met or already claimed",
        )
    return {"status": "claimed", "badge_id": badge_id}
