from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional

from shared.middleware.auth import get_current_user
from ..schemas.map_schemas import (
    CheckinCreateRequest,
    CheckinResponse,
    CheckinListResponse,
)
from ..services.checkin_service import CheckinService

router = APIRouter()


def get_checkin_service() -> CheckinService:
    return CheckinService()


@router.post("/", response_model=CheckinResponse, status_code=status.HTTP_201_CREATED)
async def create_checkin(
    data: CheckinCreateRequest,
    current_user: dict = Depends(get_current_user),
    checkin_service: CheckinService = Depends(get_checkin_service),
):
    """Check in at a bookstore"""
    checkin = await checkin_service.create_checkin(
        user_id=current_user.user_id,
        data=data,
    )
    if not checkin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot check in. Too far from bookstore or already checked in today.",
        )
    return checkin


@router.get("/my", response_model=CheckinListResponse)
async def get_my_checkins(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    checkin_service: CheckinService = Depends(get_checkin_service),
):
    """Get current user's check-in history"""
    return await checkin_service.get_user_checkins(
        user_id=current_user.user_id,
        page=page,
        page_size=page_size,
    )


@router.get("/bookstore/{bookstore_id}", response_model=CheckinListResponse)
async def get_bookstore_checkins(
    bookstore_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    checkin_service: CheckinService = Depends(get_checkin_service),
):
    """Get check-ins at a bookstore"""
    return await checkin_service.get_bookstore_checkins(
        bookstore_id=bookstore_id,
        page=page,
        page_size=page_size,
    )


@router.get("/stats")
async def get_checkin_stats(
    current_user: dict = Depends(get_current_user),
    checkin_service: CheckinService = Depends(get_checkin_service),
):
    """Get user's check-in statistics"""
    return await checkin_service.get_user_stats(current_user.user_id)
