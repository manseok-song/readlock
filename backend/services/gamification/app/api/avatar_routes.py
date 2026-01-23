from fastapi import APIRouter, Depends

from shared.middleware.auth import get_current_user
from ..schemas.gamification_schemas import (
    AvatarConfigResponse,
    AvatarConfigUpdateRequest,
)
from ..services.avatar_service import AvatarService

router = APIRouter()


def get_avatar_service() -> AvatarService:
    return AvatarService()


@router.get("/config", response_model=AvatarConfigResponse)
async def get_avatar_config(
    current_user: dict = Depends(get_current_user),
    service: AvatarService = Depends(get_avatar_service),
):
    """Get user's avatar configuration"""
    return await service.get_avatar_config(user_id=current_user.user_id)


@router.put("/config", response_model=AvatarConfigResponse)
async def update_avatar_config(
    data: AvatarConfigUpdateRequest,
    current_user: dict = Depends(get_current_user),
    service: AvatarService = Depends(get_avatar_service),
):
    """Update user's avatar configuration"""
    return await service.update_avatar_config(
        user_id=current_user.user_id,
        face_item_id=data.face_item_id,
        hair_item_id=data.hair_item_id,
        outfit_item_id=data.outfit_item_id,
        accessory_item_id=data.accessory_item_id,
        skin_color=data.skin_color,
    )
