from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class BadgeResponse(BaseModel):
    id: str
    name: str
    description: str
    icon_url: str
    category: str
    tier: str  # bronze, silver, gold, platinum
    requirements: dict
    exp_reward: int
    coin_reward: int


class UserBadgeResponse(BaseModel):
    badge_id: str
    badge: BadgeResponse
    earned_at: datetime


class BadgeProgressResponse(BaseModel):
    badge_id: str
    badge: BadgeResponse
    current_progress: int
    required_progress: int
    progress_percent: float
    is_earned: bool


class UserLevelResponse(BaseModel):
    level: int
    current_exp: int
    exp_to_next_level: int
    total_exp: int
    progress_percent: float
    title: str


class LevelConfigResponse(BaseModel):
    level: int
    required_exp: int
    title: str
    rewards: Optional[dict] = None


class ExpHistoryResponse(BaseModel):
    id: str
    amount: int
    source: str
    description: str
    created_at: datetime


class ShopItemResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str  # avatar, room, theme, effect
    subcategory: Optional[str] = None
    price_coins: int
    price_real: Optional[float] = None
    preview_url: str
    is_limited: bool = False
    available_until: Optional[datetime] = None
    required_level: int = 1


class UserInventoryResponse(BaseModel):
    id: str
    item: ShopItemResponse
    purchased_at: datetime
    is_equipped: bool


class CoinBalanceResponse(BaseModel):
    balance: int
    lifetime_earned: int
    lifetime_spent: int


class CoinHistoryResponse(BaseModel):
    id: str
    amount: int
    balance_after: int
    transaction_type: str  # earn, spend, bonus
    source: str
    description: str
    created_at: datetime


class PurchaseRequest(BaseModel):
    item_id: str


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    username: str
    avatar_url: Optional[str] = None
    level: int
    score: int
    is_current_user: bool = False


class LeaderboardResponse(BaseModel):
    leaderboard_type: str
    period: str
    entries: List[LeaderboardEntry]
    user_rank: Optional[int] = None
    user_score: Optional[int] = None
    total_participants: int
