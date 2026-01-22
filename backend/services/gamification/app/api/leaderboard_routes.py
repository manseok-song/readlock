from fastapi import APIRouter, Depends, Query
from typing import Optional

from shared.middleware.auth import get_current_user
from ..schemas.gamification_schemas import LeaderboardResponse
from ..services.leaderboard_service import LeaderboardService

router = APIRouter()


def get_leaderboard_service() -> LeaderboardService:
    return LeaderboardService()


@router.get("/reading-time", response_model=LeaderboardResponse)
async def get_reading_time_leaderboard(
    period: str = Query("weekly", pattern="^(daily|weekly|monthly|all_time)$"),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    service: LeaderboardService = Depends(get_leaderboard_service),
):
    """Get leaderboard by reading time"""
    return await service.get_leaderboard(
        user_id=current_user.user_id,
        leaderboard_type="reading_time",
        period=period,
        limit=limit,
    )


@router.get("/books-completed", response_model=LeaderboardResponse)
async def get_books_completed_leaderboard(
    period: str = Query("weekly", pattern="^(daily|weekly|monthly|all_time)$"),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    service: LeaderboardService = Depends(get_leaderboard_service),
):
    """Get leaderboard by books completed"""
    return await service.get_leaderboard(
        user_id=current_user.user_id,
        leaderboard_type="books_completed",
        period=period,
        limit=limit,
    )


@router.get("/streak", response_model=LeaderboardResponse)
async def get_streak_leaderboard(
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    service: LeaderboardService = Depends(get_leaderboard_service),
):
    """Get leaderboard by reading streak"""
    return await service.get_leaderboard(
        user_id=current_user.user_id,
        leaderboard_type="streak",
        period="all_time",
        limit=limit,
    )


@router.get("/level", response_model=LeaderboardResponse)
async def get_level_leaderboard(
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    service: LeaderboardService = Depends(get_leaderboard_service),
):
    """Get leaderboard by level"""
    return await service.get_leaderboard(
        user_id=current_user.user_id,
        leaderboard_type="level",
        period="all_time",
        limit=limit,
    )


@router.get("/friends", response_model=LeaderboardResponse)
async def get_friends_leaderboard(
    leaderboard_type: str = Query("reading_time", pattern="^(reading_time|books_completed|streak|level)$"),
    period: str = Query("weekly", pattern="^(daily|weekly|monthly|all_time)$"),
    current_user: dict = Depends(get_current_user),
    service: LeaderboardService = Depends(get_leaderboard_service),
):
    """Get leaderboard among friends"""
    return await service.get_friends_leaderboard(
        user_id=current_user.user_id,
        leaderboard_type=leaderboard_type,
        period=period,
    )
