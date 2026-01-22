from typing import Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field


# Quote schemas
class QuoteCreateRequest(BaseModel):
    """Create quote request"""
    book_id: str
    content: str = Field(..., min_length=1, max_length=1000)
    page_number: Optional[int] = Field(None, ge=1)
    thought: Optional[str] = Field(None, max_length=500)
    background_color: Optional[str] = Field(None, max_length=7)  # hex color
    is_public: bool = True


class QuoteUpdateRequest(BaseModel):
    """Update quote request"""
    content: Optional[str] = Field(None, min_length=1, max_length=1000)
    thought: Optional[str] = Field(None, max_length=500)
    background_color: Optional[str] = None
    is_public: Optional[bool] = None


class QuoteAuthor(BaseModel):
    """Quote author info"""
    id: str
    nickname: str
    avatar_url: Optional[str] = None
    level: int


class QuoteBook(BaseModel):
    """Quote book info"""
    id: str
    title: str
    author: str
    cover_image_url: Optional[str] = None


class QuoteResponse(BaseModel):
    """Quote response"""
    id: str
    content: str
    page_number: Optional[int] = None
    thought: Optional[str] = None
    background_color: Optional[str] = None
    is_public: bool
    author: QuoteAuthor
    book: QuoteBook
    likes_count: int = 0
    is_liked: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class QuoteListResponse(BaseModel):
    """Quote list response"""
    items: List[QuoteResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# Review schemas
class ReviewCreateRequest(BaseModel):
    """Create review request"""
    book_id: str
    rating: float = Field(..., ge=0.5, le=5)
    title: Optional[str] = Field(None, max_length=100)
    content: str = Field(..., min_length=10, max_length=5000)
    contains_spoiler: bool = False
    is_public: bool = True


class ReviewUpdateRequest(BaseModel):
    """Update review request"""
    rating: Optional[float] = Field(None, ge=0.5, le=5)
    title: Optional[str] = Field(None, max_length=100)
    content: Optional[str] = Field(None, min_length=10, max_length=5000)
    contains_spoiler: Optional[bool] = None
    is_public: Optional[bool] = None


class ReviewResponse(BaseModel):
    """Review response"""
    id: str
    rating: float
    title: Optional[str] = None
    content: str
    contains_spoiler: bool
    is_public: bool
    author: QuoteAuthor
    book: QuoteBook
    likes_count: int = 0
    comments_count: int = 0
    is_liked: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReviewListResponse(BaseModel):
    """Review list response"""
    items: List[ReviewResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class CommentResponse(BaseModel):
    """Comment response"""
    id: str
    content: str
    author: QuoteAuthor
    created_at: datetime


# Feed schemas
class FeedItem(BaseModel):
    """Feed item (can be quote or review)"""
    id: str
    type: Literal["quote", "review"]
    content: str
    author: QuoteAuthor
    book: QuoteBook
    rating: Optional[float] = None  # Only for reviews
    page_number: Optional[int] = None  # Only for quotes
    background_color: Optional[str] = None  # Only for quotes
    likes_count: int = 0
    comments_count: int = 0
    is_liked: bool = False
    created_at: datetime


class FeedResponse(BaseModel):
    """Feed response"""
    items: List[FeedItem]
    total: int
    page: int
    page_size: int
    has_more: bool
