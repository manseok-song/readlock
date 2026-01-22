from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid

from shared.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "body": self.body,
            "data": self.data,
            "is_read": self.is_read,
            "created_at": self.created_at,
        }


class NotificationSettings(Base):
    __tablename__ = "notification_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    push_enabled = Column(Boolean, default=True)
    reading_reminder = Column(Boolean, default=True)
    reading_reminder_time = Column(String(5), default="21:00")
    social_notifications = Column(Boolean, default=True)
    marketing_notifications = Column(Boolean, default=False)
    streak_reminder = Column(Boolean, default=True)
    goal_notifications = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "push_enabled": self.push_enabled,
            "reading_reminder": self.reading_reminder,
            "reading_reminder_time": self.reading_reminder_time,
            "social_notifications": self.social_notifications,
            "marketing_notifications": self.marketing_notifications,
            "streak_reminder": self.streak_reminder,
            "goal_notifications": self.goal_notifications,
        }


class DeviceToken(Base):
    __tablename__ = "device_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(500), unique=True, nullable=False)
    platform = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
