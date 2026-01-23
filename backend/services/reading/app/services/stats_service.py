from typing import Optional, List
from datetime import datetime, timedelta

from sqlalchemy import select, func, and_

from shared.core.database import get_db_session
from shared.core.redis import cache_service
from ..models.reading import ReadingSession, ReadingStreak


class StatsService:
    """Service for reading statistics"""

    async def get_stats(
        self,
        user_id: str,
        period: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        """Get reading statistics for a period"""
        # Calculate date range based on period
        now = datetime.utcnow()
        if period == "day":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif period == "week":
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif period == "month":
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif period == "year":
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now
        else:
            start = now - timedelta(days=7)
            end = now

        # Override with custom dates if provided
        if start_date:
            start = datetime.fromisoformat(start_date)
        if end_date:
            end = datetime.fromisoformat(end_date)

        # Import UserBook model for the join
        from services.book.app.models.book import UserBook

        async with get_db_session() as session:
            # Get aggregated stats - join with user_books to filter by user_id
            result = await session.execute(
                select(
                    func.sum(ReadingSession.duration).label("total_time"),
                    func.sum(ReadingSession.end_page - ReadingSession.start_page).label("total_pages"),
                    func.count(ReadingSession.id).label("session_count"),
                    func.avg(ReadingSession.duration).label("avg_duration"),
                ).select_from(ReadingSession).join(
                    UserBook, ReadingSession.user_book_id == UserBook.id
                ).where(
                    UserBook.user_id == user_id,
                    ReadingSession.end_time.isnot(None),
                    ReadingSession.start_time >= start,
                    ReadingSession.start_time <= end,
                )
            )
            row = result.first()

            total_time = int(row.total_time or 0)
            total_pages = int(row.total_pages or 0)
            session_count = int(row.session_count or 0)
            avg_duration = int(row.avg_duration or 0)

            # Get unique reading days
            days_result = await session.execute(
                select(func.count(func.distinct(func.date(ReadingSession.start_time)))).select_from(
                    ReadingSession
                ).join(
                    UserBook, ReadingSession.user_book_id == UserBook.id
                ).where(
                    UserBook.user_id == user_id,
                    ReadingSession.end_time.isnot(None),
                    ReadingSession.start_time >= start,
                    ReadingSession.start_time <= end,
                )
            )
            reading_days = days_result.scalar() or 0

            # Get unique books
            books_result = await session.execute(
                select(func.count(func.distinct(ReadingSession.user_book_id))).select_from(
                    ReadingSession
                ).join(
                    UserBook, ReadingSession.user_book_id == UserBook.id
                ).where(
                    UserBook.user_id == user_id,
                    ReadingSession.end_time.isnot(None),
                    ReadingSession.start_time >= start,
                    ReadingSession.start_time <= end,
                )
            )
            total_books = books_result.scalar() or 0

            return {
                "total_time": total_time,
                "total_pages": total_pages,
                "total_books": total_books,
                "completed_books": 0,  # TODO: Get from book service
                "avg_session_time": avg_duration,
                "avg_pages_per_session": total_pages / session_count if session_count > 0 else 0,
                "favorite_genre": None,  # TODO: Implement
                "reading_days": reading_days,
            }

    async def get_reading_profile(self, user_id: str) -> dict:
        """Get comprehensive reading profile"""
        from services.book.app.models.book import UserBook

        async with get_db_session() as session:
            # Total stats
            result = await session.execute(
                select(
                    func.sum(ReadingSession.duration).label("total_time"),
                    func.sum(ReadingSession.end_page - ReadingSession.start_page).label("total_pages"),
                    func.min(ReadingSession.start_time).label("first_reading"),
                ).select_from(ReadingSession).join(
                    UserBook, ReadingSession.user_book_id == UserBook.id
                ).where(
                    UserBook.user_id == user_id,
                    ReadingSession.end_time.isnot(None),
                )
            )
            row = result.first()

            total_time = int(row.total_time or 0) // 60  # Convert to minutes
            total_pages = int(row.total_pages or 0)
            first_reading = row.first_reading

            # Get streaks
            streak = await self.get_streak(user_id)

            # Calculate reading speed (pages per hour)
            hours = total_time / 60 if total_time > 0 else 0
            reading_speed = total_pages / hours if hours > 0 else 0

            return {
                "total_reading_time": total_time,
                "total_books_read": 0,  # TODO: Get from book service
                "total_pages_read": total_pages,
                "current_streak": streak["current_streak"],
                "longest_streak": streak["longest_streak"],
                "avg_reading_speed": round(reading_speed, 1),
                "favorite_reading_time": await self._get_favorite_reading_time(user_id),
                "top_genres": [],  # TODO: Implement
                "monthly_books": [0] * 12,  # TODO: Implement
                "reading_since": first_reading,
            }

    async def get_streak(self, user_id: str) -> dict:
        """Get current reading streak"""
        # Check cache first
        cached = await cache_service.get(f"streak:{user_id}")
        if cached:
            return cached

        async with get_db_session() as session:
            # Get streak record
            result = await session.execute(
                select(ReadingStreak).where(ReadingStreak.user_id == user_id)
            )
            streak = result.scalar_one_or_none()

            if not streak:
                return {
                    "current_streak": 0,
                    "longest_streak": 0,
                    "last_reading_date": None,
                    "streak_maintained_today": False,
                }

            # Check if streak is maintained today
            today = datetime.utcnow().date()
            streak_maintained = False
            if streak.last_reading_date:
                last_date = streak.last_reading_date.date() if isinstance(
                    streak.last_reading_date, datetime
                ) else streak.last_reading_date
                days_diff = (today - last_date).days

                if days_diff == 0:
                    streak_maintained = True
                elif days_diff > 1:
                    # Streak broken
                    streak.current_streak = 0
                    await session.commit()

            result_data = {
                "current_streak": streak.current_streak,
                "longest_streak": streak.longest_streak,
                "last_reading_date": str(streak.last_reading_date) if streak.last_reading_date else None,
                "streak_maintained_today": streak_maintained,
            }

            # Cache for 1 hour
            await cache_service.set(f"streak:{user_id}", result_data, ttl=3600)

            return result_data

    async def get_daily_stats(self, user_id: str, days: int) -> dict:
        """Get daily reading stats for chart"""
        from services.book.app.models.book import UserBook

        async with get_db_session() as session:
            start_date = datetime.utcnow() - timedelta(days=days)

            # Get daily aggregates
            result = await session.execute(
                select(
                    func.date(ReadingSession.start_time).label("date"),
                    func.sum(ReadingSession.duration).label("duration"),
                    func.sum(ReadingSession.end_page - ReadingSession.start_page).label("pages"),
                    func.count(ReadingSession.id).label("sessions"),
                ).select_from(ReadingSession).join(
                    UserBook, ReadingSession.user_book_id == UserBook.id
                ).where(
                    UserBook.user_id == user_id,
                    ReadingSession.end_time.isnot(None),
                    ReadingSession.start_time >= start_date,
                ).group_by(
                    func.date(ReadingSession.start_time)
                ).order_by(
                    func.date(ReadingSession.start_time)
                )
            )

            rows = result.all()

            # Build daily stats
            daily_stats = []
            total_minutes = 0
            total_pages = 0

            for row in rows:
                minutes = (row.duration or 0) // 60
                pages = row.pages or 0
                daily_stats.append({
                    "date": str(row.date),
                    "minutes": minutes,
                    "pages": pages,
                    "sessions": row.sessions or 0,
                })
                total_minutes += minutes
                total_pages += pages

            return {
                "days": daily_stats,
                "total_minutes": total_minutes,
                "total_pages": total_pages,
                "avg_minutes": total_minutes / len(daily_stats) if daily_stats else 0,
            }

    async def _get_favorite_reading_time(self, user_id: str) -> Optional[str]:
        """Determine user's favorite reading time"""
        from services.book.app.models.book import UserBook

        async with get_db_session() as session:
            result = await session.execute(
                select(
                    func.extract("hour", ReadingSession.start_time).label("hour"),
                    func.count(ReadingSession.id).label("count"),
                ).select_from(ReadingSession).join(
                    UserBook, ReadingSession.user_book_id == UserBook.id
                ).where(
                    UserBook.user_id == user_id,
                    ReadingSession.end_time.isnot(None),
                ).group_by(
                    func.extract("hour", ReadingSession.start_time)
                ).order_by(
                    func.count(ReadingSession.id).desc()
                ).limit(1)
            )

            row = result.first()
            if not row:
                return None

            hour = int(row.hour)
            if 5 <= hour < 12:
                return "morning"
            elif 12 <= hour < 17:
                return "afternoon"
            elif 17 <= hour < 21:
                return "evening"
            else:
                return "night"
