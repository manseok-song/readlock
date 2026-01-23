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
    asset_data: Optional[dict] = None
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


# Avatar schemas
class AvatarConfigResponse(BaseModel):
    id: Optional[str] = None
    user_id: str
    face_item_id: Optional[str] = None
    hair_item_id: Optional[str] = None
    outfit_item_id: Optional[str] = None
    accessory_item_id: Optional[str] = None
    skin_color: str = "#FFD5B8"
    face_item: Optional[ShopItemResponse] = None
    hair_item: Optional[ShopItemResponse] = None
    outfit_item: Optional[ShopItemResponse] = None
    accessory_item: Optional[ShopItemResponse] = None


class AvatarConfigUpdateRequest(BaseModel):
    face_item_id: Optional[str] = None
    hair_item_id: Optional[str] = None
    outfit_item_id: Optional[str] = None
    accessory_item_id: Optional[str] = None
    skin_color: Optional[str] = None


# Room schemas
class FurniturePosition(BaseModel):
    x: float
    y: float
    rotation: float = 0


class RoomLayoutResponse(BaseModel):
    id: Optional[str] = None
    user_id: str
    background_item_id: Optional[str] = None
    background_item: Optional[ShopItemResponse] = None
    layout_data: dict = {}
    furniture_items: List[ShopItemResponse] = []
    bookshelf_books: List[str] = []


class RoomLayoutUpdateRequest(BaseModel):
    background_item_id: Optional[str] = None
    layout_data: Optional[dict] = None


class BookshelfUpdateRequest(BaseModel):
    book_ids: List[str]
