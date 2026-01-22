from typing import Optional
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import select, func, and_

from shared.core.database import get_db_session
from ..models.map import Bookstore, Checkin
from ..schemas.map_schemas import CheckinCreateRequest


class CheckinService:
    """Service for check-in operations"""

    # Maximum distance for check-in (meters)
    MAX_CHECKIN_DISTANCE = 200

    # Rewards
    CHECKIN_COINS = 20
    CHECKIN_EXP = 30
    FIRST_VISIT_BONUS_COINS = 50
    FIRST_VISIT_BONUS_EXP = 50

    async def create_checkin(
        self,
        user_id: str,
        data: CheckinCreateRequest,
    ) -> Optional[dict]:
        """Create a check-in at a bookstore"""
        async with get_db_session() as session:
            # Get bookstore
            result = await session.execute(
                select(Bookstore).where(Bookstore.id == data.bookstore_id)
            )
            bookstore = result.scalar_one_or_none()
            if not bookstore:
                return None

            # Check distance
            distance = self._calculate_distance_meters(
                data.latitude, data.longitude,
                bookstore.latitude, bookstore.longitude
            )
            if distance > self.MAX_CHECKIN_DISTANCE:
                return None

            # Check if already checked in today
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            existing = await session.execute(
                select(Checkin).where(
                    Checkin.user_id == user_id,
                    Checkin.bookstore_id == data.bookstore_id,
                    Checkin.created_at >= today_start,
                )
            )
            if existing.scalar_one_or_none():
                return None

            # Check if first visit
            first_visit_check = await session.execute(
                select(Checkin).where(
                    Checkin.user_id == user_id,
                    Checkin.bookstore_id == data.bookstore_id,
                )
            )
            is_first_visit = first_visit_check.scalar_one_or_none() is None

            # Calculate rewards
            coins = self.CHECKIN_COINS
            exp = self.CHECKIN_EXP
            if is_first_visit:
                coins += self.FIRST_VISIT_BONUS_COINS
                exp += self.FIRST_VISIT_BONUS_EXP

            # Create check-in
            checkin = Checkin(
                id=str(uuid4()),
                user_id=user_id,
                bookstore_id=data.bookstore_id,
                latitude=data.latitude,
                longitude=data.longitude,
                note=data.note,
                photo_url=data.photo_url,
                coins_earned=coins,
                exp_earned=exp,
            )
            session.add(checkin)
            await session.commit()
            await session.refresh(checkin)

            # TODO: Update user's coins and exp in user service

            return {
                "id": checkin.id,
                "user_id": checkin.user_id,
                "bookstore_id": checkin.bookstore_id,
                "bookstore_name": bookstore.name,
                "note": checkin.note,
                "photo_url": checkin.photo_url,
                "coins_earned": coins,
                "exp_earned": exp,
                "is_first_visit": is_first_visit,
                "created_at": checkin.created_at,
            }

    async def get_user_checkins(
        self,
        user_id: str,
        page: int,
        page_size: int,
    ) -> dict:
        """Get user's check-in history"""
        async with get_db_session() as session:
            # Count total
            count_result = await session.execute(
                select(func.count()).where(Checkin.user_id == user_id)
            )
            total = count_result.scalar() or 0

            # Get check-ins with bookstore info
            result = await session.execute(
                select(Checkin, Bookstore.name)
                .join(Bookstore, Checkin.bookstore_id == Bookstore.id)
                .where(Checkin.user_id == user_id)
                .order_by(Checkin.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            checkins = result.all()

            items = [
                {
                    "id": c.id,
                    "user_id": c.user_id,
                    "bookstore_id": c.bookstore_id,
                    "bookstore_name": name,
                    "note": c.note,
                    "photo_url": c.photo_url,
                    "coins_earned": c.coins_earned,
                    "exp_earned": c.exp_earned,
                    "is_first_visit": False,
                    "created_at": c.created_at,
                }
                for c, name in checkins
            ]

            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "has_more": page * page_size < total,
            }

    async def get_bookstore_checkins(
        self,
        bookstore_id: str,
        page: int,
        page_size: int,
    ) -> dict:
        """Get check-ins at a bookstore"""
        async with get_db_session() as session:
            # Get bookstore name
            bookstore_result = await session.execute(
                select(Bookstore.name).where(Bookstore.id == bookstore_id)
            )
            bookstore_name = bookstore_result.scalar() or "Unknown"

            # Count total
            count_result = await session.execute(
                select(func.count()).where(Checkin.bookstore_id == bookstore_id)
            )
            total = count_result.scalar() or 0

            # Get check-ins
            result = await session.execute(
                select(Checkin)
                .where(Checkin.bookstore_id == bookstore_id)
                .order_by(Checkin.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            checkins = result.scalars().all()

            items = [
                {
                    "id": c.id,
                    "user_id": c.user_id,
                    "bookstore_id": c.bookstore_id,
                    "bookstore_name": bookstore_name,
                    "note": c.note,
                    "photo_url": c.photo_url,
                    "coins_earned": c.coins_earned,
                    "exp_earned": c.exp_earned,
                    "is_first_visit": False,
                    "created_at": c.created_at,
                }
                for c in checkins
            ]

            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "has_more": page * page_size < total,
            }

    async def get_user_stats(self, user_id: str) -> dict:
        """Get user's check-in statistics"""
        async with get_db_session() as session:
            # Total check-ins
            total_result = await session.execute(
                select(func.count()).where(Checkin.user_id == user_id)
            )
            total_checkins = total_result.scalar() or 0

            # Unique bookstores visited
            unique_result = await session.execute(
                select(func.count(func.distinct(Checkin.bookstore_id))).where(
                    Checkin.user_id == user_id
                )
            )
            unique_bookstores = unique_result.scalar() or 0

            # This month's check-ins
            month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_result = await session.execute(
                select(func.count()).where(
                    Checkin.user_id == user_id,
                    Checkin.created_at >= month_start,
                )
            )
            month_checkins = month_result.scalar() or 0

            # Total rewards earned
            rewards_result = await session.execute(
                select(
                    func.sum(Checkin.coins_earned),
                    func.sum(Checkin.exp_earned),
                ).where(Checkin.user_id == user_id)
            )
            row = rewards_result.first()
            total_coins = row[0] or 0
            total_exp = row[1] or 0

            # Most visited bookstore
            most_visited_result = await session.execute(
                select(
                    Checkin.bookstore_id,
                    func.count(Checkin.id).label("count")
                ).where(
                    Checkin.user_id == user_id
                ).group_by(
                    Checkin.bookstore_id
                ).order_by(
                    func.count(Checkin.id).desc()
                ).limit(1)
            )
            most_visited = most_visited_result.first()

            most_visited_name = None
            most_visited_count = 0
            if most_visited:
                bookstore_result = await session.execute(
                    select(Bookstore.name).where(Bookstore.id == most_visited[0])
                )
                most_visited_name = bookstore_result.scalar()
                most_visited_count = most_visited[1]

            return {
                "total_checkins": total_checkins,
                "unique_bookstores": unique_bookstores,
                "month_checkins": month_checkins,
                "total_coins_earned": total_coins,
                "total_exp_earned": total_exp,
                "most_visited_bookstore": most_visited_name,
                "most_visited_count": most_visited_count,
            }

    def _calculate_distance_meters(
        self,
        lat1: float, lon1: float,
        lat2: float, lon2: float,
    ) -> float:
        """Calculate distance in meters using Haversine formula"""
        import math

        R = 6371000  # Earth radius in meters

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c
