from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field


class BookResponse(BaseModel):
    """Book response schema"""
    id: str
    isbn: Optional[str] = None
    title: str
    author: Optional[str] = None
    publisher: Optional[str] = None
    published_date: Optional[date] = None
    description: Optional[str] = None
    cover_image: Optional[str] = None
    category: Optional[str] = None
    page_count: Optional[int] = None
    naver_link: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BookSearchItem(BaseModel):
    """Book search result item"""
    id: Optional[str] = None
    isbn: Optional[str] = None
    title: str
    author: Optional[str] = None
    publisher: Optional[str] = None
    published_date: Optional[date] = None
    description: Optional[str] = None
    cover_image: Optional[str] = None
    category: Optional[str] = None


class BookSearchResponse(BaseModel):
    """Book search response"""
    items: List[BookSearchItem]
    total: int
    page: int
    page_size: int
    has_more: bool


class UserBookCreate(BaseModel):
    """Create user book request"""
    book_id: str
    status: str = Field(default="wishlist", pattern="^(wishlist|reading|completed|dropped)$")


class UserBookUpdate(BaseModel):
    """Update user book request"""
    status: Optional[str] = Field(None, pattern="^(wishlist|reading|completed|dropped)$")
    current_page: Optional[int] = Field(None, ge=0)
    total_pages: Optional[int] = Field(None, ge=0)


class UserBookResponse(BaseModel):
    """User book response"""
    id: str
    user_id: str
    book_id: str
    book: BookResponse
    status: str
    current_page: int = 0
    total_pages: Optional[int] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserBooksListResponse(BaseModel):
    """User books list response"""
    items: List[UserBookResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
