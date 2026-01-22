from typing import List, Optional
from datetime import datetime, timedelta

from sqlalchemy import select, func, and_

from shared.core.database import get_db_session
from ..models.gamification import UserLevel


class LeaderboardService:
    """Service for leaderboard management"""

    async def get_leaderboard(
        self,
        user_id: str,
        leaderboard_type: str,
        period: str,
        limit: int,
    ) -> dict:
        """Get leaderboard data"""
        # TODO: Implement actual leaderboard queries
        # This is a placeholder implementation

        entries = await self._get_leaderboard_entries(leaderboard_type, period, limit)
        user_rank, user_score = await self._get_user_rank(user_id, leaderboard_type, period)

        for i, entry in enumerate(entries):
            entry["is_current_user"] = entry["user_id"] == user_id

        return {
            "leaderboard_type": leaderboard_type,
            "period": period,
            "entries": entries,
            "user_rank": user_rank,
            "user_score": user_score,
            "total_participants": len(entries),
        }

    async def get_friends_leaderboard(
        self,
        user_id: str,
        leaderboard_type: str,
        period: str,
    ) -> dict:
        """Get leaderboard among friends"""
        # TODO: Get actual friend IDs from user service
        friend_ids = await self._get_friend_ids(user_id)

        entries = await self._get_friends_entries(
            user_id,
            friend_ids,
            leaderboard_type,
            period,
        )
        user_rank, user_score = await self._get_user_rank(user_id, leaderboard_type, period)

        for i, entry in enumerate(entries):
            entry["is_current_user"] = entry["user_id"] == user_id

        return {
            "leaderboard_type": leaderboard_type,
            "period": period,
            "entries": entries,
            "user_rank": user_rank,
            "user_score": user_score,
            "total_participants": len(entries),
        }

    async def _get_leaderboard_entries(
        self,
        leaderboard_type: str,
        period: str,
        limit: int,
    ) -> List[dict]:
        """Get leaderboard entries based on type and period"""
        # TODO: Implement actual queries based on leaderboard_type
        # - reading_time: Sum of reading minutes in period
        # - books_completed: Count of books completed in period
        # - streak: Current streak length
        # - level: User level

        if leaderboard_type == "level":
            return await self._get_level_leaderboard(limit)

        # Placeholder data
        return [
            {
                "rank": i + 1,
                "user_id": f"user_{i}",
                "username": f"Reader{i+1}",
                "avatar_url": None,
                "level": 10 - i,
                "score": 1000 - (i * 100),
                "is_current_user": False,
            }
            for i in range(min(limit, 10))
        ]

    async def _get_level_leaderboard(self, limit: int) -> List[dict]:
        """Get leaderboard by level"""
        async with get_db_session() as session:
            result = await session.execute(
                select(UserLevel)
                .order_by(UserLevel.level.desc(), UserLevel.total_exp.desc())
                .limit(limit)
            )
            user_levels = result.scalars().all()

            return [
                {
                    "rank": i + 1,
                    "user_id": ul.user_id,
                    "username": f"User {ul.user_id[:8]}",  # TODO: Join with user table
                    "avatar_url": None,
                    "level": ul.level,
                    "score": ul.total_exp,
                    "is_current_user": False,
                }
                for i, ul in enumerate(user_levels)
            ]

    async def _get_user_rank(
        self,
        user_id: str,
        leaderboard_type: str,
        period: str,
    ) -> tuple:
        """Get user's rank and score"""
        # TODO: Implement actual rank calculation
        return 15, 500

    async def _get_friend_ids(self, user_id: str) -> List[str]:
        """Get list of friend user IDs"""
        # TODO: Call user service to get friends
        return []

    async def _get_friends_entries(
        self,
        user_id: str,
        friend_ids: List[str],
        leaderboard_type: str,
        period: str,
    ) -> List[dict]:
        """Get leaderboard entries for friends only"""
        all_ids = [user_id] + friend_ids

        # TODO: Implement actual query filtered by friend_ids
        return [
            {
                "rank": 1,
                "user_id": user_id,
                "username": "You",
                "avatar_url": None,
                "level": 5,
                "score": 500,
                "is_current_user": True,
            }
        ]

    def _get_period_start(self, period: str) -> datetime:
        """Get start datetime for period"""
        now = datetime.utcnow()

        if period == "daily":
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "weekly":
            days_since_monday = now.weekday()
            return (now - timedelta(days=days_since_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        elif period == "monthly":
            return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:  # all_time
            return datetime(2020, 1, 1)
