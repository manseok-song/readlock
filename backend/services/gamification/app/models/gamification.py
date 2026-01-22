from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, JSON, Float, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid

from shared.core.database import Base


class Badge(Base):
    __tablename__ = "badges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    icon_url = Column(String(500), nullable=False)
    category = Column(String(50), nullable=False)  # reading, social, streak, achievement
    tier = Column(String(20), nullable=False)  # bronze, silver, gold, platinum
    requirements = Column(JSON, nullable=False)
    exp_reward = Column(Integer, default=0)
    coin_reward = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon_url": self.icon_url,
            "category": self.category,
            "tier": self.tier,
            "requirements": self.requirements,
            "exp_reward": self.exp_reward,
            "coin_reward": self.coin_reward,
        }


class UserBadge(Base):
    __tablename__ = "user_badges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    badge_id = Column(UUID(as_uuid=True), ForeignKey("badges.id"), nullable=False)
    earned_at = Column(DateTime, default=datetime.utcnow)


class UserLevel(Base):
    __tablename__ = "user_levels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    level = Column(Integer, default=1)
    current_exp = Column(Integer, default=0)
    total_exp = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LevelConfig(Base):
    __tablename__ = "level_configs"

    level = Column(Integer, primary_key=True)
    required_exp = Column(Integer, nullable=False)
    title = Column(String(100), nullable=False)
    rewards = Column(JSON, nullable=True)


class ExpHistory(Base):
    __tablename__ = "exp_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)
    source = Column(String(50), nullable=False)  # reading, badge, quest, bonus
    description = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ShopItem(Base):
    __tablename__ = "shop_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)  # avatar, room, theme, effect
    subcategory = Column(String(50), nullable=True)
    price_coins = Column(Integer, nullable=False)
    price_real = Column(Float, nullable=True)
    preview_url = Column(String(500), nullable=False)
    asset_data = Column(JSON, nullable=True)
    is_limited = Column(Boolean, default=False)
    available_until = Column(DateTime, nullable=True)
    required_level = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "subcategory": self.subcategory,
            "price_coins": self.price_coins,
            "price_real": self.price_real,
            "preview_url": self.preview_url,
            "is_limited": self.is_limited,
            "available_until": self.available_until,
            "required_level": self.required_level,
        }


class UserInventory(Base):
    __tablename__ = "user_inventory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    item_id = Column(UUID(as_uuid=True), ForeignKey("shop_items.id"), nullable=False)
    purchased_at = Column(DateTime, default=datetime.utcnow)
    is_equipped = Column(Boolean, default=False)


class UserCoins(Base):
    __tablename__ = "user_coins"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    balance = Column(Integer, default=0)
    lifetime_earned = Column(Integer, default=0)
    lifetime_spent = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CoinTransaction(Base):
    __tablename__ = "coin_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    transaction_type = Column(String(20), nullable=False)  # earn, spend, bonus
    source = Column(String(50), nullable=False)
    description = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
