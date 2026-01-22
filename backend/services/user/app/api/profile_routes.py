from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import Optional

from shared.middleware.auth import get_current_user
from ..schemas.user_schemas import (
    ProfileUpdateRequest,
    ProfileResponse,
    AvatarUpdateRequest,
    AvatarResponse,
    ReadingGoalRequest,
    ReadingGoalResponse,
)
from ..services.profile_service import ProfileService

router = APIRouter()


def get_profile_service() -> ProfileService:
    return ProfileService()


@router.get("/", response_model=ProfileResponse)
async def get_profile(
    current_user: dict = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service),
):
    """Get current user's profile details"""
    profile = await profile_service.get_profile(current_user.user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    return profile


@router.patch("/", response_model=ProfileResponse)
async def update_profile(
    data: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service),
):
    """Update profile details"""
    profile = await profile_service.update_profile(current_user.user_id, data)
    return profile


@router.post("/avatar", response_model=AvatarResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service),
):
    """Upload profile avatar image"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image",
        )

    # Max 5MB
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large (max 5MB)",
        )

    avatar_url = await profile_service.upload_avatar(
        user_id=current_user.user_id,
        file_content=contents,
        content_type=file.content_type,
    )
    return {"avatar_url": avatar_url}


@router.put("/avatar/customize", response_model=AvatarResponse)
async def customize_avatar(
    data: AvatarUpdateRequest,
    current_user: dict = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service),
):
    """Customize virtual avatar"""
    avatar = await profile_service.update_avatar_customization(
        user_id=current_user.user_id,
        customization=data,
    )
    return avatar


@router.get("/reading-goal", response_model=ReadingGoalResponse)
async def get_reading_goal(
    current_user: dict = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service),
):
    """Get user's reading goal"""
    return await profile_service.get_reading_goal(current_user.user_id)


@router.put("/reading-goal", response_model=ReadingGoalResponse)
async def set_reading_goal(
    data: ReadingGoalRequest,
    current_user: dict = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service),
):
    """Set user's reading goal"""
    return await profile_service.set_reading_goal(
        user_id=current_user.user_id,
        data=data,
    )
