from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class SessionStartRequest(BaseModel):
    """Start session request"""
    user_book_id: str
    start_page: Optional[int] = Field(None, ge=0)


class SessionEndRequest(BaseModel):
    """End session request"""
    end_page: int = Field(..., ge=0)
    focus_score: Optional[int] = Field(None, ge=0, le=100)


class SessionSyncRequest(BaseModel):
    """Sync offline session request"""
    user_book_id: str
    start_time: datetime
    end_time: datetime
    start_page: int = Field(..., ge=0)
    end_page: int = Field(..., ge=0)
    focus_score: Optional[int] = Field(None, ge=0, le=100)


class SessionResponse(BaseModel):
    """Reading session response"""
    id: str
    user_id: str
    user_book_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    start_page: int
    end_page: Optional[int] = None
    duration: int = 0  # seconds
    focus_score: Optional[int] = None
    is_active: bool = False
    is_paused: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class RewardsResponse(BaseModel):
    """Session rewards"""
    coins_earned: int
    exp_earned: int
    bonus_coins: int = 0
    bonus_exp: int = 0
    streak_bonus: bool = False
    daily_goal_bonus: bool = False


class SessionResultResponse(BaseModel):
    """Session end result"""
    session_id: str
    duration: int  # seconds
    pages_read: int
    streak_days: int
    rewards: RewardsResponse
    level_up: bool = False
    new_level: Optional[int] = None
    badges_earned: List[str] = []


class SessionListResponse(BaseModel):
    """Session list response"""
    items: List[SessionResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class ReadingStatsResponse(BaseModel):
    """Reading statistics"""
    total_time: int  # seconds
    total_pages: int
    total_books: int
    completed_books: int
    avg_session_time: int  # seconds
    avg_pages_per_session: float
    favorite_genre: Optional[str] = None
    reading_days: int


class DailyStat(BaseModel):
    """Single day stat"""
    date: str  # YYYY-MM-DD
    minutes: int
    pages: int
    sessions: int


class DailyStatsResponse(BaseModel):
    """Daily stats for chart"""
    days: List[DailyStat]
    total_minutes: int
    total_pages: int
    avg_minutes: float


class StreakResponse(BaseModel):
    """Reading streak info"""
    current_streak: int
    longest_streak: int
    last_reading_date: Optional[str] = None
    streak_maintained_today: bool = False


class GenreStat(BaseModel):
    """Genre statistics"""
    genre: str
    books_count: int
    pages_count: int
    time_minutes: int
    percentage: float


class ReadingProfileResponse(BaseModel):
    """Comprehensive reading profile"""
    total_reading_time: int  # minutes
    total_books_read: int
    total_pages_read: int
    current_streak: int
    longest_streak: int
    avg_reading_speed: float  # pages per hour
    favorite_reading_time: Optional[str] = None  # morning, afternoon, evening, night
    top_genres: List[GenreStat]
    monthly_books: List[int]  # Last 12 months
    reading_since: Optional[datetime] = None
