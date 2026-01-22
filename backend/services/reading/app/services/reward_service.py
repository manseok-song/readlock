from typing import Optional, List
from datetime import datetime, timedelta

from sqlalchemy import select, func

from shared.core.database import get_db_session
from ..models.reading import ReadingSession, ReadingStreak


class RewardService:
    """Service for calculating reading rewards"""

    # Reward rates
    BASE_COIN_PER_MINUTE = 1
    BASE_EXP_PER_PAGE = 5
    FOCUS_BONUS_MULTIPLIER = 0.5  # 50% bonus for high focus
    STREAK_BONUS_PER_DAY = 0.1  # 10% bonus per streak day (max 100%)
    DAILY_GOAL_BONUS = 50  # Bonus for reaching daily goal

    # Level thresholds
    EXP_PER_LEVEL = 1000

    async def calculate_rewards(
        self,
        user_id: str,
        duration: int,  # seconds
        pages_read: int,
        focus_score: Optional[int] = None,
    ) -> dict:
        """Calculate rewards for a reading session"""
        minutes = duration // 60

        # Base rewards
        base_coins = minutes * self.BASE_COIN_PER_MINUTE
        base_exp = pages_read * self.BASE_EXP_PER_PAGE

        # Bonuses
        bonus_coins = 0
        bonus_exp = 0
        streak_bonus = False
        daily_goal_bonus = False

        # Focus score bonus (if focus > 80%)
        if focus_score and focus_score >= 80:
            focus_bonus_coins = int(base_coins * self.FOCUS_BONUS_MULTIPLIER)
            focus_bonus_exp = int(base_exp * self.FOCUS_BONUS_MULTIPLIER)
            bonus_coins += focus_bonus_coins
            bonus_exp += focus_bonus_exp

        # Streak bonus
        streak_days = await self._update_and_get_streak(user_id)
        if streak_days > 0:
            streak_multiplier = min(streak_days * self.STREAK_BONUS_PER_DAY, 1.0)
            streak_bonus_coins = int(base_coins * streak_multiplier)
            streak_bonus_exp = int(base_exp * streak_multiplier)
            bonus_coins += streak_bonus_coins
            bonus_exp += streak_bonus_exp
            streak_bonus = True

        # Daily goal bonus
        if await self._check_daily_goal_reached(user_id, duration):
            bonus_coins += self.DAILY_GOAL_BONUS
            bonus_exp += self.DAILY_GOAL_BONUS
            daily_goal_bonus = True

        # Total rewards
        total_coins = base_coins + bonus_coins
        total_exp = base_exp + bonus_exp

        # Apply rewards and check level up
        level_up, new_level = await self._apply_rewards(user_id, total_coins, total_exp)

        # Check for badge achievements
        badges = await self._check_badges(user_id, duration, pages_read, streak_days)

        return {
            "coins_earned": total_coins,
            "exp_earned": total_exp,
            "bonus_coins": bonus_coins,
            "bonus_exp": bonus_exp,
            "streak_bonus": streak_bonus,
            "daily_goal_bonus": daily_goal_bonus,
            "level_up": level_up,
            "new_level": new_level,
            "badges": badges,
        }

    async def _update_and_get_streak(self, user_id: str) -> int:
        """Update and return current streak"""
        async with get_db_session() as session:
            result = await session.execute(
                select(ReadingStreak).where(ReadingStreak.user_id == user_id)
            )
            streak = result.scalar_one_or_none()

            today = datetime.utcnow().date()

            if not streak:
                # Create new streak record
                from uuid import uuid4
                streak = ReadingStreak(
                    id=str(uuid4()),
                    user_id=user_id,
                    current_streak=1,
                    longest_streak=1,
                    last_reading_date=today,
                )
                session.add(streak)
                await session.commit()
                return 1

            last_date = streak.last_reading_date
            if isinstance(last_date, datetime):
                last_date = last_date.date()

            if last_date == today:
                # Already counted today
                return streak.current_streak

            days_diff = (today - last_date).days

            if days_diff == 1:
                # Consecutive day
                streak.current_streak += 1
            elif days_diff > 1:
                # Streak broken
                streak.current_streak = 1

            # Update longest streak
            if streak.current_streak > streak.longest_streak:
                streak.longest_streak = streak.current_streak

            streak.last_reading_date = today
            await session.commit()

            return streak.current_streak

    async def _check_daily_goal_reached(
        self,
        user_id: str,
        new_duration: int,
    ) -> bool:
        """Check if daily reading goal is reached with this session"""
        # TODO: Get user's daily goal from profile service
        daily_goal_minutes = 30  # Default 30 minutes

        async with get_db_session() as session:
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

            # Get today's total reading time before this session
            result = await session.execute(
                select(func.sum(ReadingSession.duration)).where(
                    ReadingSession.user_id == user_id,
                    ReadingSession.is_active == False,
                    ReadingSession.start_time >= today,
                )
            )
            previous_duration = result.scalar() or 0

            # Check if goal was not reached before but is now
            previous_minutes = previous_duration // 60
            new_total_minutes = (previous_duration + new_duration) // 60

            return previous_minutes < daily_goal_minutes <= new_total_minutes

    async def _apply_rewards(
        self,
        user_id: str,
        coins: int,
        exp: int,
    ) -> tuple[bool, Optional[int]]:
        """Apply rewards to user profile and check for level up"""
        # TODO: Update user profile in user service
        # For now, return no level up
        return False, None

    async def _check_badges(
        self,
        user_id: str,
        duration: int,
        pages_read: int,
        streak_days: int,
    ) -> List[str]:
        """Check and award badges for achievements"""
        badges = []

        # TODO: Implement badge checking logic
        # Examples:
        # - First book badge
        # - 10 hour reading badge
        # - 7 day streak badge
        # - 100 pages in one session badge

        return badges
