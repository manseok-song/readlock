from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

from shared.core.database import Base


class Bookstore(Base):
    """Bookstore model"""
    __tablename__ = "bookstores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, index=True)

    address = Column(String(500), nullable=False)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)

    phone = Column(String(50), nullable=True)
    website = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)

    opening_hours = Column(JSON, nullable=True)  # {mon: "09:00-21:00", ...}
    features = Column(JSON, nullable=True)  # ["cafe", "events", "rare_books"]
    image_urls = Column(JSON, nullable=True)  # List of photo URLs

    average_rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)

    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BookstoreReview(Base):
    """Bookstore review model"""
    __tablename__ = "bookstore_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bookstore_id = Column(UUID(as_uuid=True), ForeignKey("bookstores.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    rating = Column(Float, nullable=False)  # 1-5
    content = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BookstoreFavorite(Base):
    """User's favorite bookstores"""
    __tablename__ = "bookstore_favorites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bookstore_id = Column(UUID(as_uuid=True), ForeignKey("bookstores.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class Checkin(Base):
    """Bookstore check-in model"""
    __tablename__ = "checkins"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bookstore_id = Column(UUID(as_uuid=True), ForeignKey("bookstores.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    coins_earned = Column(Integer, default=0)
    exp_earned = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
