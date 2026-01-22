from typing import List, Optional
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select

from shared.core.database import get_db_session
from ..models.gamification import Badge, UserBadge, UserLevel, UserCoins, CoinTransaction, ExpHistory


class BadgeService:
    """Service for badge management"""

    BADGE_DEFINITIONS = [
        {
            "id": "first_book",
            "name": "First Step",
            "description": "Add your first book to the library",
            "icon_url": "/assets/badges/first_book.png",
            "category": "achievement",
            "tier": "bronze",
            "requirements": {"books_added": 1},
            "exp_reward": 50,
            "coin_reward": 10,
        },
        {
            "id": "bookworm_10",
            "name": "Bookworm",
            "description": "Complete 10 books",
            "icon_url": "/assets/badges/bookworm_10.png",
            "category": "reading",
            "tier": "silver",
            "requirements": {"books_completed": 10},
            "exp_reward": 200,
            "coin_reward": 50,
        },
        {
            "id": "streak_7",
            "name": "Week Warrior",
            "description": "Maintain a 7-day reading streak",
            "icon_url": "/assets/badges/streak_7.png",
            "category": "streak",
            "tier": "bronze",
            "requirements": {"streak_days": 7},
            "exp_reward": 100,
            "coin_reward": 25,
        },
        {
            "id": "streak_30",
            "name": "Month Master",
            "description": "Maintain a 30-day reading streak",
            "icon_url": "/assets/badges/streak_30.png",
            "category": "streak",
            "tier": "gold",
            "requirements": {"streak_days": 30},
            "exp_reward": 500,
            "coin_reward": 100,
        },
        {
            "id": "social_first_quote",
            "name": "Quoter",
            "description": "Share your first quote",
            "icon_url": "/assets/badges/first_quote.png",
            "category": "social",
            "tier": "bronze",
            "requirements": {"quotes_shared": 1},
            "exp_reward": 30,
            "coin_reward": 10,
        },
        {
            "id": "reading_1000_min",
            "name": "Time Traveler",
            "description": "Read for 1000 minutes total",
            "icon_url": "/assets/badges/time_1000.png",
            "category": "reading",
            "tier": "gold",
            "requirements": {"total_reading_minutes": 1000},
            "exp_reward": 300,
            "coin_reward": 75,
        },
    ]

    async def get_all_badges(self) -> List[dict]:
        """Get all available badges"""
        async with get_db_session() as session:
            result = await session.execute(select(Badge))
            badges = result.scalars().all()

            if not badges:
                return self.BADGE_DEFINITIONS

            return [b.to_dict() for b in badges]

    async def get_user_badges(self, user_id: str) -> List[dict]:
        """Get badges earned by user"""
        async with get_db_session() as session:
            result = await session.execute(
                select(UserBadge, Badge)
                .join(Badge, UserBadge.badge_id == Badge.id)
                .where(UserBadge.user_id == user_id)
                .order_by(UserBadge.earned_at.desc())
            )
            rows = result.all()

            return [
                {
                    "badge_id": ub.badge_id,
                    "badge": b.to_dict(),
                    "earned_at": ub.earned_at,
                }
                for ub, b in rows
            ]

    async def get_badge_progress(self, user_id: str) -> List[dict]:
        """Get progress for all badges"""
        all_badges = await self.get_all_badges()
        user_badges = await self.get_user_badges(user_id)
        earned_ids = {ub["badge_id"] for ub in user_badges}

        user_stats = await self._get_user_stats(user_id)

        progress_list = []
        for badge in all_badges:
            is_earned = badge["id"] in earned_ids
            current, required = self._calculate_progress(badge["requirements"], user_stats)

            progress_list.append({
                "badge_id": badge["id"],
                "badge": badge,
                "current_progress": current,
                "required_progress": required,
                "progress_percent": min(100, (current / required * 100) if required > 0 else 0),
                "is_earned": is_earned,
            })

        return progress_list

    async def claim_badge(self, user_id: str, badge_id: str) -> bool:
        """Claim a badge if requirements are met"""
        async with get_db_session() as session:
            existing = await session.execute(
                select(UserBadge).where(
                    UserBadge.user_id == user_id,
                    UserBadge.badge_id == badge_id,
                )
            )
            if existing.scalar_one_or_none():
                return False

            badge_result = await session.execute(
                select(Badge).where(Badge.id == badge_id)
            )
            badge = badge_result.scalar_one_or_none()
            if not badge:
                badge_def = next((b for b in self.BADGE_DEFINITIONS if b["id"] == badge_id), None)
                if not badge_def:
                    return False
                badge = Badge(**badge_def)
                session.add(badge)

            user_stats = await self._get_user_stats(user_id)
            current, required = self._calculate_progress(badge.requirements, user_stats)
            if current < required:
                return False

            user_badge = UserBadge(
                id=str(uuid4()),
                user_id=user_id,
                badge_id=badge_id,
            )
            session.add(user_badge)

            if badge.exp_reward > 0:
                await self._add_exp(session, user_id, badge.exp_reward, "badge", f"Badge: {badge.name}")

            if badge.coin_reward > 0:
                await self._add_coins(session, user_id, badge.coin_reward, "badge", f"Badge: {badge.name}")

            await session.commit()
            return True

    async def _get_user_stats(self, user_id: str) -> dict:
        """Get user statistics for badge progress calculation"""
        # TODO: Fetch actual stats from reading service
        return {
            "books_added": 5,
            "books_completed": 3,
            "streak_days": 7,
            "quotes_shared": 2,
            "total_reading_minutes": 500,
            "reviews_written": 1,
            "followers_count": 10,
        }

    def _calculate_progress(self, requirements: dict, user_stats: dict) -> tuple:
        """Calculate current progress and required amount"""
        for key, required in requirements.items():
            current = user_stats.get(key, 0)
            return current, required
        return 0, 1

    async def _add_exp(self, session, user_id: str, amount: int, source: str, description: str):
        """Add exp to user"""
        result = await session.execute(
            select(UserLevel).where(UserLevel.user_id == user_id)
        )
        user_level = result.scalar_one_or_none()

        if not user_level:
            user_level = UserLevel(id=str(uuid4()), user_id=user_id)
            session.add(user_level)

        user_level.current_exp += amount
        user_level.total_exp += amount

        exp_history = ExpHistory(
            id=str(uuid4()),
            user_id=user_id,
            amount=amount,
            source=source,
            description=description,
        )
        session.add(exp_history)

    async def _add_coins(self, session, user_id: str, amount: int, source: str, description: str):
        """Add coins to user"""
        result = await session.execute(
            select(UserCoins).where(UserCoins.user_id == user_id)
        )
        user_coins = result.scalar_one_or_none()

        if not user_coins:
            user_coins = UserCoins(id=str(uuid4()), user_id=user_id)
            session.add(user_coins)

        user_coins.balance += amount
        user_coins.lifetime_earned += amount

        transaction = CoinTransaction(
            id=str(uuid4()),
            user_id=user_id,
            amount=amount,
            balance_after=user_coins.balance,
            transaction_type="earn",
            source=source,
            description=description,
        )
        session.add(transaction)
