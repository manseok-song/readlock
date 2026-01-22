from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Optional

from shared.middleware.auth import get_current_user
from ..schemas.notification_schemas import (
    NotificationListResponse,
    NotificationSettingsResponse,
    NotificationSettingsUpdate,
    DeviceTokenRequest,
)
from ..services.notification_service import NotificationService

router = APIRouter()


def get_notification_service() -> NotificationService:
    return NotificationService()


@router.get("/", response_model=NotificationListResponse)
async def get_notifications(
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Get user's notifications"""
    return await service.get_notifications(
        user_id=current_user.user_id,
        unread_only=unread_only,
        page=page,
        page_size=page_size,
    )


@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Mark a notification as read"""
    success = await service.mark_as_read(
        notification_id=notification_id,
        user_id=current_user.user_id,
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return {"status": "read"}


@router.post("/read-all")
async def mark_all_as_read(
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Mark all notifications as read"""
    count = await service.mark_all_as_read(user_id=current_user.user_id)
    return {"marked_count": count}


@router.get("/unread-count")
async def get_unread_count(
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Get unread notification count"""
    count = await service.get_unread_count(user_id=current_user.user_id)
    return {"count": count}


@router.get("/settings", response_model=NotificationSettingsResponse)
async def get_settings(
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Get notification settings"""
    return await service.get_settings(user_id=current_user.user_id)


@router.put("/settings", response_model=NotificationSettingsResponse)
async def update_settings(
    data: NotificationSettingsUpdate,
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Update notification settings"""
    return await service.update_settings(user_id=current_user.user_id, data=data)


@router.post("/device")
async def register_device(
    data: DeviceTokenRequest,
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Register device for push notifications"""
    await service.register_device(
        user_id=current_user.user_id,
        token=data.token,
        platform=data.platform,
    )
    return {"status": "registered"}


@router.delete("/device")
async def unregister_device(
    token: str = Query(...),
    current_user: dict = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Unregister device from push notifications"""
    await service.unregister_device(user_id=current_user.user_id, token=token)
    return {"status": "unregistered"}
