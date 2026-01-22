from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional

from shared.middleware.auth import get_current_user
from ..schemas.user_schemas import (
    UserResponse,
    UserUpdateRequest,
    UserSearchResponse,
)
from ..services.user_service import UserService

router = APIRouter()


def get_user_service() -> UserService:
    return UserService()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Get current user's full profile"""
    user = await user_service.get_user_with_profile(current_user.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    data: UserUpdateRequest,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Update current user's profile"""
    user = await user_service.update_user(current_user.user_id, data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.get("/search", response_model=UserSearchResponse)
async def search_users(
    query: str = Query(..., min_length=1, max_length=50),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Search users by nickname"""
    return await user_service.search_users(
        query=query,
        page=page,
        page_size=page_size,
        current_user_id=current_user.user_id,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Get user by ID (public profile view)"""
    user = await user_service.get_public_profile(
        user_id=user_id,
        viewer_id=current_user.user_id,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user
