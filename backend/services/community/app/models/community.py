from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid

from shared.core.database import Base


class Quote(Base):
    """Quote model"""
    __tablename__ = "quotes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id"), nullable=False, index=True)

    content = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    memo = Column(Text, nullable=True)
    likes_count = Column(Integer, default=0)

    is_public = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class QuoteLike(Base):
    """Quote like model"""
    __tablename__ = "quote_likes"

    quote_id = Column(UUID(as_uuid=True), ForeignKey("quotes.id", ondelete="CASCADE"), primary_key=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True, nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class Review(Base):
    """Book review model"""
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id"), nullable=False, index=True)

    rating = Column(Float, nullable=False)  # 0.5 to 5
    content = Column(Text, nullable=False)
    has_spoiler = Column(Boolean, default=False)
    likes_count = Column(Integer, default=0)

    is_public = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReviewLike(Base):
    """Review like model"""
    __tablename__ = "review_likes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = Column(UUID(as_uuid=True), ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class Comment(Base):
    """Comment on reviews or quotes"""
    __tablename__ = "comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    parent_type = Column(String(50), nullable=False)  # review, quote
    parent_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    content = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
