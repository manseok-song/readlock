from fastapi import APIRouter, Depends, Query
from typing import Optional

from shared.middleware.auth import get_current_user
from ..schemas.community_schemas import FeedResponse, FeedItem
from ..services.feed_service import FeedService

router = APIRouter()


def get_feed_service() -> FeedService:
    return FeedService()


@router.get("/", response_model=FeedResponse)
async def get_feed(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    feed_service: FeedService = Depends(get_feed_service),
):
    """Get personalized feed from followed users"""
    return await feed_service.get_feed(
        user_id=current_user.user_id,
        page=page,
        page_size=page_size,
    )


@router.get("/discover", response_model=FeedResponse)
async def get_discover_feed(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    feed_service: FeedService = Depends(get_feed_service),
):
    """Get discover feed with popular content"""
    return await feed_service.get_discover_feed(
        user_id=current_user.user_id,
        page=page,
        page_size=page_size,
    )


@router.get("/trending", response_model=FeedResponse)
async def get_trending(
    period: str = Query("week", pattern="^(day|week|month)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    feed_service: FeedService = Depends(get_feed_service),
):
    """Get trending content"""
    return await feed_service.get_trending(
        period=period,
        user_id=current_user.user_id,
        page=page,
        page_size=page_size,
    )


@router.get("/book/{book_id}", response_model=FeedResponse)
async def get_book_feed(
    book_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    feed_service: FeedService = Depends(get_feed_service),
):
    """Get feed for a specific book (quotes and reviews)"""
    return await feed_service.get_book_feed(
        book_id=book_id,
        user_id=current_user.user_id,
        page=page,
        page_size=page_size,
    )


@router.get("/user/{user_id}", response_model=FeedResponse)
async def get_user_feed(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    feed_service: FeedService = Depends(get_feed_service),
):
    """Get feed from a specific user"""
    return await feed_service.get_user_feed(
        target_user_id=user_id,
        viewer_id=current_user.user_id,
        page=page,
        page_size=page_size,
    )
