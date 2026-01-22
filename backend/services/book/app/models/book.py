from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from shared.core.database import Base


class Book(Base):
    """Book model"""
    __tablename__ = "books"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    isbn = Column(String(20), unique=True, index=True, nullable=True)
    title = Column(String(500), nullable=False, index=True)
    author = Column(String(500), nullable=True)
    publisher = Column(String(200), nullable=True)
    published_date = Column(Date, nullable=True)
    description = Column(Text, nullable=True)
    cover_image = Column(String(500), nullable=True)
    category = Column(String(100), nullable=True)
    page_count = Column(Integer, nullable=True)
    naver_link = Column(String(500), nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user_books = relationship("UserBook", back_populates="book")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "isbn": self.isbn,
            "title": self.title,
            "author": self.author,
            "publisher": self.publisher,
            "published_date": self.published_date,
            "description": self.description,
            "cover_image": self.cover_image,
            "category": self.category,
            "page_count": self.page_count,
            "naver_link": self.naver_link,
            "created_at": self.created_at,
        }


class UserBook(Base):
    """User's book in their library"""
    __tablename__ = "user_books"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id"), nullable=False, index=True)

    status = Column(String(20), default="wishlist")  # wishlist, reading, completed, dropped
    current_page = Column(Integer, default=0)
    total_pages = Column(Integer, nullable=True)

    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    book = relationship("Book", back_populates="user_books")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "book_id": str(self.book_id),
            "book": self.book.to_dict() if self.book else None,
            "status": self.status,
            "current_page": self.current_page,
            "total_pages": self.total_pages,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
