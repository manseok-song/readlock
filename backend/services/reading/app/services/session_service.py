from typing import Optional
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select, and_

from shared.core.database import get_db_session
from shared.core.redis import cache_service
from ..models.reading import ReadingSession
from ..schemas.reading_schemas import SessionSyncRequest
from .reward_service import RewardService


class SessionService:
    """Service for reading session management"""

    def __init__(self):
        self.reward_service = RewardService()

    async def start_session(
        self,
        user_id: str,
        user_book_id: str,
        start_page: Optional[int] = None,
    ) -> dict:
        """Start a new reading session"""
        async with get_db_session() as session:
            # Get current page from user_book if not provided
            if start_page is None:
                # TODO: Fetch from book service
                start_page = 0

            reading_session = ReadingSession(
                id=str(uuid4()),
                user_id=user_id,
                user_book_id=user_book_id,
                start_time=datetime.utcnow(),
                start_page=start_page,
                is_active=True,
            )
            session.add(reading_session)
            await session.commit()
            await session.refresh(reading_session)

            # Cache active session
            await cache_service.set(
                f"active_session:{user_id}",
                reading_session.id,
                ttl=86400,  # 24 hours
            )

            return reading_session.to_dict()

    async def get_active_session(self, user_id: str) -> Optional[dict]:
        """Get user's active reading session"""
        # Check cache first
        cached_id = await cache_service.get(f"active_session:{user_id}")
        if cached_id:
            async with get_db_session() as session:
                result = await session.execute(
                    select(ReadingSession).where(
                        ReadingSession.id == cached_id,
                        ReadingSession.is_active == True,
                    )
                )
                reading_session = result.scalar_one_or_none()
                if reading_session:
                    return reading_session.to_dict()

        # Fallback to database query
        async with get_db_session() as session:
            result = await session.execute(
                select(ReadingSession).where(
                    ReadingSession.user_id == user_id,
                    ReadingSession.is_active == True,
                )
            )
            reading_session = result.scalar_one_or_none()
            return reading_session.to_dict() if reading_session else None

    async def end_session(
        self,
        session_id: str,
        user_id: str,
        end_page: int,
        focus_score: Optional[int] = None,
    ) -> Optional[dict]:
        """End a reading session and calculate rewards"""
        async with get_db_session() as db:
            result = await db.execute(
                select(ReadingSession).where(
                    ReadingSession.id == session_id,
                    ReadingSession.user_id == user_id,
                )
            )
            reading_session = result.scalar_one_or_none()
            if not reading_session:
                return None

            # Calculate duration
            end_time = datetime.utcnow()
            duration = int((end_time - reading_session.start_time).total_seconds())

            # Subtract paused time if any
            if reading_session.total_pause_duration:
                duration -= reading_session.total_pause_duration

            # Update session
            reading_session.end_time = end_time
            reading_session.end_page = end_page
            reading_session.duration = max(0, duration)
            reading_session.focus_score = focus_score
            reading_session.is_active = False
            reading_session.is_paused = False

            await db.commit()

            # Clear cache
            await cache_service.delete(f"active_session:{user_id}")

            # Calculate rewards
            pages_read = max(0, end_page - reading_session.start_page)
            rewards = await self.reward_service.calculate_rewards(
                user_id=user_id,
                duration=duration,
                pages_read=pages_read,
                focus_score=focus_score,
            )

            # Get streak
            streak_days = await self._get_streak_days(user_id)

            return {
                "session_id": session_id,
                "duration": duration,
                "pages_read": pages_read,
                "streak_days": streak_days,
                "rewards": rewards,
                "level_up": rewards.get("level_up", False),
                "new_level": rewards.get("new_level"),
                "badges_earned": rewards.get("badges", []),
            }

    async def pause_session(self, session_id: str, user_id: str) -> bool:
        """Pause a reading session"""
        async with get_db_session() as session:
            result = await session.execute(
                select(ReadingSession).where(
                    ReadingSession.id == session_id,
                    ReadingSession.user_id == user_id,
                    ReadingSession.is_active == True,
                )
            )
            reading_session = result.scalar_one_or_none()
            if not reading_session:
                return False

            reading_session.is_paused = True
            reading_session.paused_at = datetime.utcnow()
            await session.commit()
            return True

    async def resume_session(self, session_id: str, user_id: str) -> bool:
        """Resume a paused reading session"""
        async with get_db_session() as session:
            result = await session.execute(
                select(ReadingSession).where(
                    ReadingSession.id == session_id,
                    ReadingSession.user_id == user_id,
                    ReadingSession.is_paused == True,
                )
            )
            reading_session = result.scalar_one_or_none()
            if not reading_session:
                return False

            # Calculate pause duration
            if reading_session.paused_at:
                pause_duration = int(
                    (datetime.utcnow() - reading_session.paused_at).total_seconds()
                )
                reading_session.total_pause_duration = (
                    reading_session.total_pause_duration or 0
                ) + pause_duration

            reading_session.is_paused = False
            reading_session.paused_at = None
            await session.commit()
            return True

    async def get_sessions(
        self,
        user_id: str,
        user_book_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """Get reading session history"""
        async with get_db_session() as session:
            query = select(ReadingSession).where(
                ReadingSession.user_id == user_id,
                ReadingSession.is_active == False,
            )

            if user_book_id:
                query = query.where(ReadingSession.user_book_id == user_book_id)

            if start_date:
                start = datetime.fromisoformat(start_date)
                query = query.where(ReadingSession.start_time >= start)

            if end_date:
                end = datetime.fromisoformat(end_date)
                query = query.where(ReadingSession.start_time <= end)

            # Count total
            count_query = select(ReadingSession.id).where(
                ReadingSession.user_id == user_id,
                ReadingSession.is_active == False,
            )
            count_result = await session.execute(count_query)
            total = len(count_result.all())

            # Paginate
            query = query.order_by(ReadingSession.start_time.desc())
            query = query.offset((page - 1) * page_size).limit(page_size)

            result = await session.execute(query)
            sessions = result.scalars().all()

            return {
                "items": [s.to_dict() for s in sessions],
                "total": total,
                "page": page,
                "page_size": page_size,
                "has_more": page * page_size < total,
            }

    async def sync_offline_session(
        self,
        user_id: str,
        data: SessionSyncRequest,
    ) -> dict:
        """Sync an offline reading session"""
        async with get_db_session() as session:
            duration = int((data.end_time - data.start_time).total_seconds())

            reading_session = ReadingSession(
                id=str(uuid4()),
                user_id=user_id,
                user_book_id=data.user_book_id,
                start_time=data.start_time,
                end_time=data.end_time,
                start_page=data.start_page,
                end_page=data.end_page,
                duration=duration,
                focus_score=data.focus_score,
                is_active=False,
                is_offline_sync=True,
            )
            session.add(reading_session)
            await session.commit()
            await session.refresh(reading_session)

            return reading_session.to_dict()

    async def _get_streak_days(self, user_id: str) -> int:
        """Get current reading streak days"""
        # TODO: Implement streak calculation
        return 0
