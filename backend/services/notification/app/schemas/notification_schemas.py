from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    body: str
    data: Optional[dict] = None
    is_read: bool = False
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int
    has_more: bool


class NotificationSettingsResponse(BaseModel):
    push_enabled: bool = True
    reading_reminder: bool = True
    reading_reminder_time: Optional[str] = "21:00"
    social_notifications: bool = True
    marketing_notifications: bool = False
    streak_reminder: bool = True
    goal_notifications: bool = True


class NotificationSettingsUpdate(BaseModel):
    push_enabled: Optional[bool] = None
    reading_reminder: Optional[bool] = None
    reading_reminder_time: Optional[str] = None
    social_notifications: Optional[bool] = None
    marketing_notifications: Optional[bool] = None
    streak_reminder: Optional[bool] = None
    goal_notifications: Optional[bool] = None


class DeviceTokenRequest(BaseModel):
    token: str
    platform: str = Field(..., pattern="^(ios|android|web)$")
