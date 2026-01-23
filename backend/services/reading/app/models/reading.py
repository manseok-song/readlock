from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
import uuid

from shared.core.database import Base


class ReadingSession(Base):
    """Reading session model"""
    __tablename__ = "reading_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    user_book_id = Column(UUID(as_uuid=True), ForeignKey("user_books.id"), nullable=False, index=True)

    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    start_page = Column(Integer, default=0)
    end_page = Column(Integer, nullable=True)
    duration = Column(Integer, default=0)  # seconds

    focus_score = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    is_paused = Column(Boolean, default=False)
    paused_at = Column(DateTime, nullable=True)
    total_pause_duration = Column(Integer, default=0)
    is_offline_sync = Column(Boolean, default=False)

    was_locked = Column(Boolean, default=False)
    platform = Column(String(50), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id) if self.id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "user_book_id": str(self.user_book_id) if self.user_book_id else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "start_page": self.start_page,
            "end_page": self.end_page,
            "duration": self.duration,
            "focus_score": self.focus_score,
            "is_active": self.is_active,
            "is_paused": self.is_paused,
            "was_locked": self.was_locked,
            "platform": self.platform,
            "created_at": self.created_at.isoformat() if self.created_at else None,
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
