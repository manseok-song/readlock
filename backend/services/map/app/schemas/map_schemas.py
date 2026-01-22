from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class Location(BaseModel):
    """Geographic location"""
    latitude: float
    longitude: float


class BookstoreResponse(BaseModel):
    """Bookstore response"""
    id: str
    name: str
    address: str
    description: Optional[str] = None
    location: Location
    distance_km: Optional[float] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    opening_hours: Optional[dict] = None
    rating: float = 0.0
    review_count: int = 0
    checkin_count: int = 0
    is_favorite: bool = False
    image_url: Optional[str] = None
    image_urls: List[str] = []
    features: List[str] = []  # cafe, events, rare_books, etc.

    class Config:
        from_attributes = True


class BookstoreListResponse(BaseModel):
    """Bookstore list response"""
    items: List[BookstoreResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class BookstoreDetailResponse(BookstoreResponse):
    """Detailed bookstore response"""
    recent_checkins: List[dict] = []
    recent_reviews: List[dict] = []


class BookstoreReviewCreateRequest(BaseModel):
    """Create bookstore review request"""
    rating: float = Field(..., ge=1, le=5)
    content: str = Field(..., min_length=10, max_length=1000)


class BookstoreReviewResponse(BaseModel):
    """Bookstore review response"""
    id: str
    user_id: str
    user_nickname: str
    user_avatar: Optional[str] = None
    rating: float
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class CheckinCreateRequest(BaseModel):
    """Create check-in request"""
    bookstore_id: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class CheckinResponse(BaseModel):
    """Check-in response"""
    id: str
    user_id: str
    bookstore_id: str
    bookstore_name: str
    coins_earned: int = 0
    exp_earned: int = 0
    is_first_visit: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class CheckinListResponse(BaseModel):
    """Check-in list response"""
    items: List[CheckinResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
