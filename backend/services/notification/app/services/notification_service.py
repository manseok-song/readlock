from typing import Optional, List
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select, func, update

from shared.core.database import get_db_session
from ..models.notification import Notification, NotificationSettings, DeviceToken
from ..schemas.notification_schemas import NotificationSettingsUpdate


class NotificationService:
    """Service for notifications"""

    async def get_notifications(
        self,
        user_id: str,
        unread_only: bool,
        page: int,
        page_size: int,
    ) -> dict:
        async with get_db_session() as session:
            query = select(Notification).where(Notification.user_id == user_id)
            if unread_only:
                query = query.where(Notification.is_read == False)

            count_result = await session.execute(
                select(func.count()).where(Notification.user_id == user_id)
            )
            total = count_result.scalar() or 0

            unread_result = await session.execute(
                select(func.count()).where(
                    Notification.user_id == user_id,
                    Notification.is_read == False,
                )
            )
            unread_count = unread_result.scalar() or 0

            query = query.order_by(Notification.created_at.desc())
            query = query.offset((page - 1) * page_size).limit(page_size)

            result = await session.execute(query)
            notifications = result.scalars().all()

            return {
                "items": [n.to_dict() for n in notifications],
                "total": total,
                "unread_count": unread_count,
                "page": page,
                "page_size": page_size,
                "has_more": page * page_size < total,
            }

    async def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        async with get_db_session() as session:
            result = await session.execute(
                select(Notification).where(
                    Notification.id == notification_id,
                    Notification.user_id == user_id,
                )
            )
            notification = result.scalar_one_or_none()
            if not notification:
                return False

            notification.is_read = True
            notification.read_at = datetime.utcnow()
            await session.commit()
            return True

    async def mark_all_as_read(self, user_id: str) -> int:
        async with get_db_session() as session:
            result = await session.execute(
                update(Notification)
                .where(
                    Notification.user_id == user_id,
                    Notification.is_read == False,
                )
                .values(is_read=True, read_at=datetime.utcnow())
            )
            await session.commit()
            return result.rowcount

    async def get_unread_count(self, user_id: str) -> int:
        async with get_db_session() as session:
            result = await session.execute(
                select(func.count()).where(
                    Notification.user_id == user_id,
                    Notification.is_read == False,
                )
            )
            return result.scalar() or 0

    async def get_settings(self, user_id: str) -> dict:
        async with get_db_session() as session:
            result = await session.execute(
                select(NotificationSettings).where(
                    NotificationSettings.user_id == user_id
                )
            )
            settings = result.scalar_one_or_none()

            if not settings:
                return {
                    "push_enabled": True,
                    "reading_reminder": True,
                    "reading_reminder_time": "21:00",
                    "social_notifications": True,
                    "marketing_notifications": False,
                    "streak_reminder": True,
                    "goal_notifications": True,
                }

            return settings.to_dict()

    async def update_settings(
        self,
        user_id: str,
        data: NotificationSettingsUpdate,
    ) -> dict:
        async with get_db_session() as session:
            result = await session.execute(
                select(NotificationSettings).where(
                    NotificationSettings.user_id == user_id
                )
            )
            settings = result.scalar_one_or_none()

            if not settings:
                settings = NotificationSettings(id=str(uuid4()), user_id=user_id)
                session.add(settings)

            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(settings, field, value)

            await session.commit()
            await session.refresh(settings)
            return settings.to_dict()

    async def register_device(
        self,
        user_id: str,
        token: str,
        platform: str,
    ) -> None:
        async with get_db_session() as session:
            existing = await session.execute(
                select(DeviceToken).where(DeviceToken.token == token)
            )
            device = existing.scalar_one_or_none()

            if device:
                device.user_id = user_id
                device.platform = platform
                device.updated_at = datetime.utcnow()
            else:
                device = DeviceToken(
                    id=str(uuid4()),
                    user_id=user_id,
                    token=token,
                    platform=platform,
                )
                session.add(device)

            await session.commit()

    async def unregister_device(self, user_id: str, token: str) -> None:
        async with get_db_session() as session:
            result = await session.execute(
                select(DeviceToken).where(
                    DeviceToken.user_id == user_id,
                    DeviceToken.token == token,
                )
            )
            device = result.scalar_one_or_none()
            if device:
                await session.delete(device)
                await session.commit()

    async def send_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        body: str,
        data: Optional[dict] = None,
    ) -> str:
        """Send notification to user (in-app and push)"""
        async with get_db_session() as session:
            notification = Notification(
                id=str(uuid4()),
                user_id=user_id,
                type=notification_type,
                title=title,
                body=body,
                data=data,
            )
            session.add(notification)
            await session.commit()

            # TODO: Send push notification via FCM/APNs
            await self._send_push(user_id, title, body, data)

            return notification.id

    async def _send_push(
        self,
        user_id: str,
        title: str,
        body: str,
        data: Optional[dict],
    ) -> None:
        """Send push notification via Firebase/APNs"""
        # TODO: Implement actual push notification
        pass
