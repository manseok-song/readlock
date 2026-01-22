from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from shared.core.database import Base


class User(Base):
    """User model (shared with auth service)"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Null for OAuth users
    provider = Column(String(50), nullable=True)
    provider_id = Column(String(255), nullable=True)
    fcm_token = Column(String(500), nullable=True)
    status = Column(String(20), default="active")
    last_login_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "status": self.status,
            "provider": self.provider,
            "created_at": self.created_at,
        }


class UserProfile(Base):
    """User profile with detailed info"""
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)

    nickname = Column(String(50), nullable=False, index=True)
    bio = Column(Text, nullable=True)
    profile_image = Column(String(500), nullable=True)
    reading_goal_min = Column(Integer, default=30)
    is_public = Column(Boolean, default=True)

    # Gamification
    level = Column(Integer, default=1)
    exp = Column(Integer, default=0)
    coins = Column(Integer, default=0)

    # Subscription
    premium_until = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="profile")

    def to_dict(self) -> dict:
        return {
            "user_id": str(self.user_id) if self.user_id else None,
            "nickname": self.nickname,
            "bio": self.bio,
            "avatar_url": self.profile_image,  # Map for schema compatibility
            "level": self.level,
            "exp": self.exp,
            "coins": self.coins,
            "is_public": self.is_public,
            "is_premium": self.premium_until is not None and self.premium_until > datetime.utcnow(),
            "created_at": self.created_at,
        }


class Follow(Base):
    """Follow relationship between users"""
    __tablename__ = "follows"

    follower_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True, nullable=False, index=True)
    following_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True, nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class ReadingGoal(Base):
    """User's reading goals"""
    __tablename__ = "reading_goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    goal_type = Column(String(50), nullable=False)  # daily_minutes, daily_pages, monthly_books, yearly_books
    target = Column(Integer, default=0)
    current = Column(Integer, default=0)
    year = Column(Integer, nullable=True)
    month = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
