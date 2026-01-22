from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
import uuid

from shared.core.database import Base


class ReadingSession(Base):
    """Reading session model"""
    __tablename__ = "reading_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_book_id = Column(UUID(as_uuid=True), ForeignKey("user_books.id"), nullable=False, index=True)

    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    duration_sec = Column(Integer, default=0)  # seconds
    pages_read = Column(Integer, default=0)

    was_locked = Column(Boolean, default=False)
    platform = Column(String(50), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_book_id": self.user_book_id,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_sec": self.duration_sec,
            "pages_read": self.pages_read,
            "was_locked": self.was_locked,
            "platform": self.platform,
            "created_at": self.created_at,
        }


class ReadingStreak(Base):
    """User reading streak tracking"""
    __tablename__ = "reading_streaks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)

    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_reading_date = Column(Date, nullable=True)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
