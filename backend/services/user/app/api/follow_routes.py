from fastapi import APIRouter, Depends, HTTPException, status, Query

from shared.middleware.auth import get_current_user
from ..schemas.user_schemas import (
    FollowResponse,
    FollowersListResponse,
    FollowingListResponse,
)
from ..services.follow_service import FollowService

router = APIRouter()


def get_follow_service() -> FollowService:
    return FollowService()


@router.post("/follow/{user_id}", response_model=FollowResponse)
async def follow_user(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    follow_service: FollowService = Depends(get_follow_service),
):
    """Follow a user"""
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot follow yourself",
        )

    result = await follow_service.follow_user(
        follower_id=current_user.user_id,
        following_id=user_id,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return result


@router.delete("/follow/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_user(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    follow_service: FollowService = Depends(get_follow_service),
):
    """Unfollow a user"""
    success = await follow_service.unfollow_user(
        follower_id=current_user.user_id,
        following_id=user_id,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Follow relationship not found",
        )


@router.get("/followers", response_model=FollowersListResponse)
async def get_followers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    follow_service: FollowService = Depends(get_follow_service),
):
    """Get current user's followers"""
    return await follow_service.get_followers(
        user_id=current_user.user_id,
        page=page,
        page_size=page_size,
    )


@router.get("/followers/{user_id}", response_model=FollowersListResponse)
async def get_user_followers(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    follow_service: FollowService = Depends(get_follow_service),
):
    """Get a user's followers"""
    return await follow_service.get_followers(
        user_id=user_id,
        page=page,
        page_size=page_size,
        viewer_id=current_user.user_id,
    )


@router.get("/following", response_model=FollowingListResponse)
async def get_following(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    follow_service: FollowService = Depends(get_follow_service),
):
    """Get users current user is following"""
    return await follow_service.get_following(
        user_id=current_user.user_id,
        page=page,
        page_size=page_size,
    )


@router.get("/following/{user_id}", response_model=FollowingListResponse)
async def get_user_following(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    follow_service: FollowService = Depends(get_follow_service),
):
    """Get users a user is following"""
    return await follow_service.get_following(
        user_id=user_id,
        page=page,
        page_size=page_size,
        viewer_id=current_user.user_id,
    )


@router.get("/check/{user_id}", response_model=dict)
async def check_follow_status(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    follow_service: FollowService = Depends(get_follow_service),
):
    """Check if current user follows a user"""
    is_following = await follow_service.is_following(
        follower_id=current_user.user_id,
        following_id=user_id,
    )
    is_follower = await follow_service.is_following(
        follower_id=user_id,
        following_id=current_user.user_id,
    )
    return {
        "is_following": is_following,
        "is_follower": is_follower,
    }
