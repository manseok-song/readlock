from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class ProfileResponse(BaseModel):
    """User profile response"""
    user_id: str
    nickname: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    level: int = 1
    exp: int = 0
    coins: int = 0
    is_premium: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """Full user response"""
    id: str
    email: EmailStr
    profile: ProfileResponse
    followers_count: int = 0
    following_count: int = 0
    books_count: int = 0
    completed_books_count: int = 0
    is_following: Optional[bool] = None  # Only for other users
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    """Update user request"""
    nickname: Optional[str] = Field(None, min_length=2, max_length=20)
    bio: Optional[str] = Field(None, max_length=200)


class ProfileUpdateRequest(BaseModel):
    """Update profile request"""
    nickname: Optional[str] = Field(None, min_length=2, max_length=20)
    bio: Optional[str] = Field(None, max_length=200)
    notification_enabled: Optional[bool] = None
    reading_reminder_time: Optional[str] = None  # HH:MM format


class AvatarUpdateRequest(BaseModel):
    """Avatar customization request"""
    face_type: Optional[str] = None
    hair_type: Optional[str] = None
    hair_color: Optional[str] = None
    outfit_type: Optional[str] = None
    outfit_color: Optional[str] = None
    accessory_type: Optional[str] = None


class AvatarResponse(BaseModel):
    """Avatar response"""
    avatar_url: Optional[str] = None
    customization: Optional[dict] = None


class ReadingGoalRequest(BaseModel):
    """Reading goal request"""
    daily_minutes: Optional[int] = Field(None, ge=0, le=480)
    daily_pages: Optional[int] = Field(None, ge=0, le=500)
    monthly_books: Optional[int] = Field(None, ge=0, le=100)
    yearly_books: Optional[int] = Field(None, ge=0, le=500)


class ReadingGoalResponse(BaseModel):
    """Reading goal response"""
    daily_minutes: int = 30
    daily_pages: int = 0
    monthly_books: int = 0
    yearly_books: int = 0
    today_minutes: int = 0
    today_pages: int = 0
    month_books: int = 0
    year_books: int = 0


class UserSearchItem(BaseModel):
    """User search result item"""
    id: str
    nickname: str
    avatar_url: Optional[str] = None
    level: int
    is_following: bool = False


class UserSearchResponse(BaseModel):
    """User search response"""
    items: List[UserSearchItem]
    total: int
    page: int
    page_size: int
    has_more: bool


class FollowResponse(BaseModel):
    """Follow action response"""
    follower_id: str
    following_id: str
    created_at: datetime


class FollowUserItem(BaseModel):
    """User item in followers/following list"""
    id: str
    nickname: str
    avatar_url: Optional[str] = None
    level: int
    bio: Optional[str] = None
    is_following: bool = False
    is_follower: bool = False


class FollowersListResponse(BaseModel):
    """Followers list response"""
    items: List[FollowUserItem]
    total: int
    page: int
    page_size: int
    has_more: bool


class FollowingListResponse(BaseModel):
    """Following list response"""
    items: List[FollowUserItem]
    total: int
    page: int
    page_size: int
    has_more: bool
