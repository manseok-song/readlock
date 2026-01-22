from typing import List, Optional
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select

from shared.core.database import get_db_session
from ..models.gamification import UserLevel, LevelConfig, ExpHistory


class LevelService:
    """Service for level and exp management"""

    LEVEL_CONFIG = [
        {"level": 1, "required_exp": 0, "title": "Novice Reader"},
        {"level": 2, "required_exp": 100, "title": "Page Turner"},
        {"level": 3, "required_exp": 300, "title": "Book Lover"},
        {"level": 4, "required_exp": 600, "title": "Avid Reader"},
        {"level": 5, "required_exp": 1000, "title": "Bookworm"},
        {"level": 6, "required_exp": 1500, "title": "Literature Fan"},
        {"level": 7, "required_exp": 2100, "title": "Story Seeker"},
        {"level": 8, "required_exp": 2800, "title": "Word Wanderer"},
        {"level": 9, "required_exp": 3600, "title": "Chapter Champion"},
        {"level": 10, "required_exp": 4500, "title": "Reading Master"},
        {"level": 11, "required_exp": 5500, "title": "Book Sage"},
        {"level": 12, "required_exp": 6600, "title": "Literary Scholar"},
        {"level": 13, "required_exp": 7800, "title": "Tome Keeper"},
        {"level": 14, "required_exp": 9100, "title": "Library Guardian"},
        {"level": 15, "required_exp": 10500, "title": "Reading Legend"},
        {"level": 16, "required_exp": 12000, "title": "Book Oracle"},
        {"level": 17, "required_exp": 13600, "title": "Story Weaver"},
        {"level": 18, "required_exp": 15300, "title": "Word Wizard"},
        {"level": 19, "required_exp": 17100, "title": "Reading Grandmaster"},
        {"level": 20, "required_exp": 19000, "title": "Ultimate Bibliophile"},
    ]

    async def get_user_level(self, user_id: str) -> dict:
        """Get user's current level and exp"""
        async with get_db_session() as session:
            result = await session.execute(
                select(UserLevel).where(UserLevel.user_id == user_id)
            )
            user_level = result.scalar_one_or_none()

            if not user_level:
                return {
                    "level": 1,
                    "current_exp": 0,
                    "exp_to_next_level": self.LEVEL_CONFIG[1]["required_exp"],
                    "total_exp": 0,
                    "progress_percent": 0,
                    "title": self.LEVEL_CONFIG[0]["title"],
                }

            current_level = user_level.level
            current_config = self._get_level_config(current_level)
            next_config = self._get_level_config(current_level + 1)

            if next_config:
                exp_for_current = current_config["required_exp"]
                exp_for_next = next_config["required_exp"]
                exp_in_level = user_level.total_exp - exp_for_current
                exp_needed = exp_for_next - exp_for_current
                progress = (exp_in_level / exp_needed * 100) if exp_needed > 0 else 100
            else:
                exp_in_level = 0
                exp_needed = 0
                progress = 100

            return {
                "level": current_level,
                "current_exp": user_level.current_exp,
                "exp_to_next_level": exp_needed - exp_in_level if next_config else 0,
                "total_exp": user_level.total_exp,
                "progress_percent": min(100, progress),
                "title": current_config["title"],
            }

    async def get_level_config(self) -> List[dict]:
        """Get level configuration"""
        async with get_db_session() as session:
            result = await session.execute(
                select(LevelConfig).order_by(LevelConfig.level)
            )
            configs = result.scalars().all()

            if not configs:
                return self.LEVEL_CONFIG

            return [
                {
                    "level": c.level,
                    "required_exp": c.required_exp,
                    "title": c.title,
                    "rewards": c.rewards,
                }
                for c in configs
            ]

    async def get_exp_history(
        self,
        user_id: str,
        page: int,
        page_size: int,
    ) -> List[dict]:
        """Get exp gain history"""
        async with get_db_session() as session:
            result = await session.execute(
                select(ExpHistory)
                .where(ExpHistory.user_id == user_id)
                .order_by(ExpHistory.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            history = result.scalars().all()

            return [
                {
                    "id": h.id,
                    "amount": h.amount,
                    "source": h.source,
                    "description": h.description or "",
                    "created_at": h.created_at,
                }
                for h in history
            ]

    async def add_exp(
        self,
        user_id: str,
        amount: int,
        source: str,
        description: str = None,
    ) -> dict:
        """Add exp to user and handle level ups"""
        async with get_db_session() as session:
            result = await session.execute(
                select(UserLevel).where(UserLevel.user_id == user_id)
            )
            user_level = result.scalar_one_or_none()

            if not user_level:
                user_level = UserLevel(
                    id=str(uuid4()),
                    user_id=user_id,
                    level=1,
                    current_exp=0,
                    total_exp=0,
                )
                session.add(user_level)

            old_level = user_level.level
            user_level.current_exp += amount
            user_level.total_exp += amount

            new_level = self._calculate_level(user_level.total_exp)
            level_up = new_level > old_level
            user_level.level = new_level

            exp_history = ExpHistory(
                id=str(uuid4()),
                user_id=user_id,
                amount=amount,
                source=source,
                description=description,
            )
            session.add(exp_history)

            await session.commit()

            return {
                "exp_added": amount,
                "new_total_exp": user_level.total_exp,
                "level": new_level,
                "level_up": level_up,
                "old_level": old_level if level_up else None,
            }

    def _calculate_level(self, total_exp: int) -> int:
        """Calculate level based on total exp"""
        current_level = 1
        for config in self.LEVEL_CONFIG:
            if total_exp >= config["required_exp"]:
                current_level = config["level"]
            else:
                break
        return current_level

    def _get_level_config(self, level: int) -> Optional[dict]:
        """Get config for a specific level"""
        for config in self.LEVEL_CONFIG:
            if config["level"] == level:
                return config
        return None
