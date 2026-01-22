from fastapi import APIRouter, Depends, Query
from typing import Optional

from shared.middleware.auth import get_current_user
from ..schemas.reading_schemas import (
    ReadingStatsResponse,
    ReadingProfileResponse,
    StreakResponse,
    DailyStatsResponse,
)
from ..services.stats_service import StatsService

router = APIRouter()


def get_stats_service() -> StatsService:
    return StatsService()


@router.get("/stats", response_model=ReadingStatsResponse)
async def get_reading_stats(
    period: str = Query("week", pattern="^(day|week|month|year)$"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    stats_service: StatsService = Depends(get_stats_service),
):
    """Get reading statistics for a period"""
    return await stats_service.get_stats(
        user_id=current_user.user_id,
        period=period,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/profile", response_model=ReadingProfileResponse)
async def get_reading_profile(
    current_user: dict = Depends(get_current_user),
    stats_service: StatsService = Depends(get_stats_service),
):
    """Get comprehensive reading profile"""
    return await stats_service.get_reading_profile(current_user.user_id)


@router.get("/streak", response_model=StreakResponse)
async def get_reading_streak(
    current_user: dict = Depends(get_current_user),
    stats_service: StatsService = Depends(get_stats_service),
):
    """Get current reading streak"""
    return await stats_service.get_streak(current_user.user_id)


@router.get("/daily", response_model=DailyStatsResponse)
async def get_daily_stats(
    days: int = Query(7, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
    stats_service: StatsService = Depends(get_stats_service),
):
    """Get daily reading stats for chart"""
    return await stats_service.get_daily_stats(
        user_id=current_user.user_id,
        days=days,
    )
