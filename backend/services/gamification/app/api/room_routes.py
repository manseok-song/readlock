from fastapi import APIRouter, Depends

from shared.middleware.auth import get_current_user
from ..schemas.gamification_schemas import (
    RoomLayoutResponse,
    RoomLayoutUpdateRequest,
    BookshelfUpdateRequest,
)
from ..services.room_service import RoomService

router = APIRouter()


def get_room_service() -> RoomService:
    return RoomService()


@router.get("/layout", response_model=RoomLayoutResponse)
async def get_room_layout(
    current_user: dict = Depends(get_current_user),
    service: RoomService = Depends(get_room_service),
):
    """Get user's room layout"""
    return await service.get_room_layout(user_id=current_user.user_id)


@router.put("/layout", response_model=RoomLayoutResponse)
async def update_room_layout(
    data: RoomLayoutUpdateRequest,
    current_user: dict = Depends(get_current_user),
    service: RoomService = Depends(get_room_service),
):
    """Update user's room layout"""
    return await service.update_room_layout(
        user_id=current_user.user_id,
        background_item_id=data.background_item_id,
        layout_data=data.layout_data,
    )


@router.put("/bookshelf", response_model=RoomLayoutResponse)
async def update_bookshelf(
    data: BookshelfUpdateRequest,
    current_user: dict = Depends(get_current_user),
    service: RoomService = Depends(get_room_service),
):
    """Update books displayed on the bookshelf"""
    return await service.update_bookshelf(
        user_id=current_user.user_id,
        book_ids=data.book_ids,
    )
