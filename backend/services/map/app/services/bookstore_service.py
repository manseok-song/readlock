from typing import Optional, List
from datetime import datetime
from uuid import uuid4
import math

from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.orm import joinedload

from shared.core.database import get_db_session
from shared.core.redis import cache_service
from ..models.map import Bookstore, BookstoreReview, BookstoreFavorite, Checkin
from ..schemas.map_schemas import BookstoreReviewCreateRequest


class BookstoreService:
    """Service for bookstore operations"""

    # Earth radius in km
    EARTH_RADIUS = 6371

    async def get_nearby(
        self,
        latitude: float,
        longitude: float,
        radius_km: float,
        types: Optional[List[str]],
        user_id: str,
        page: int,
        page_size: int,
    ) -> dict:
        """Get nearby bookstores"""
        async with get_db_session() as session:
            # Bounding box filter for performance
            query = select(Bookstore).where(
                Bookstore.latitude.between(
                    latitude - (radius_km / 111),
                    latitude + (radius_km / 111)
                ),
                Bookstore.longitude.between(
                    longitude - (radius_km / (111 * math.cos(math.radians(latitude)))),
                    longitude + (radius_km / (111 * math.cos(math.radians(latitude))))
                ),
                Bookstore.is_active == True,
            )

            # Get all bookstores in bounding box
            all_results = await session.execute(query)
            all_bookstores = all_results.scalars().all()

            # Calculate distance and filter
            bookstores_with_distance = []
            for bookstore in all_bookstores:
                distance = self._calculate_distance(
                    latitude, longitude,
                    bookstore.latitude, bookstore.longitude
                )
                if distance <= radius_km:
                    bookstores_with_distance.append((bookstore, distance))

            # Sort by distance
            bookstores_with_distance.sort(key=lambda x: x[1])

            total = len(bookstores_with_distance)

            # Paginate
            start = (page - 1) * page_size
            end = start + page_size
            paginated = bookstores_with_distance[start:end]

            items = []
            for bookstore, distance in paginated:
                item = await self._bookstore_to_dict(session, bookstore, user_id)
                item["distance_km"] = round(distance, 2)
                items.append(item)

            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "has_more": end < total,
            }

    async def search(
        self,
        query: str,
        latitude: Optional[float],
        longitude: Optional[float],
        user_id: str,
        page: int,
        page_size: int,
    ) -> dict:
        """Search bookstores by name or address"""
        async with get_db_session() as session:
            search_query = select(Bookstore).where(
                Bookstore.is_active == True,
                or_(
                    Bookstore.name.ilike(f"%{query}%"),
                    Bookstore.address.ilike(f"%{query}%"),
                )
            )

            # Count total
            count_result = await session.execute(
                select(func.count()).select_from(search_query.subquery())
            )
            total = count_result.scalar() or 0

            # Paginate
            search_query = search_query.offset((page - 1) * page_size).limit(page_size)

            result = await session.execute(search_query)
            bookstores = result.scalars().all()

            items = []
            for bookstore in bookstores:
                item = await self._bookstore_to_dict(session, bookstore, user_id)
                # Calculate distance if location provided
                if latitude and longitude:
                    item["distance_km"] = self._calculate_distance(
                        latitude, longitude,
                        bookstore.latitude, bookstore.longitude
                    )
                items.append(item)

            # Sort by distance if available
            if latitude and longitude:
                items.sort(key=lambda x: x.get("distance_km", float("inf")))

            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "has_more": page * page_size < total,
            }

    async def get_by_id(self, bookstore_id: str, user_id: str) -> Optional[dict]:
        """Get bookstore by ID with details"""
        async with get_db_session() as session:
            result = await session.execute(
                select(Bookstore).where(Bookstore.id == bookstore_id)
            )
            bookstore = result.scalar_one_or_none()
            if not bookstore:
                return None

            item = await self._bookstore_to_dict(session, bookstore, user_id)

            # Get recent check-ins
            checkins_result = await session.execute(
                select(Checkin)
                .where(Checkin.bookstore_id == bookstore_id)
                .order_by(Checkin.created_at.desc())
                .limit(5)
            )
            item["recent_checkins"] = [
                {
                    "user_id": str(c.user_id),
                    "created_at": c.created_at,
                }
                for c in checkins_result.scalars().all()
            ]

            # Get recent reviews
            reviews_result = await session.execute(
                select(BookstoreReview)
                .where(BookstoreReview.bookstore_id == bookstore_id)
                .order_by(BookstoreReview.created_at.desc())
                .limit(5)
            )
            item["recent_reviews"] = [
                {
                    "id": r.id,
                    "user_id": r.user_id,
                    "rating": r.rating,
                    "content": r.content[:100] + "..." if len(r.content) > 100 else r.content,
                    "created_at": r.created_at,
                }
                for r in reviews_result.scalars().all()
            ]

            return item

    async def create_review(
        self,
        bookstore_id: str,
        user_id: str,
        data: BookstoreReviewCreateRequest,
    ) -> Optional[dict]:
        """Create a bookstore review"""
        async with get_db_session() as session:
            # Check bookstore exists
            bookstore = await session.execute(
                select(Bookstore).where(Bookstore.id == bookstore_id)
            )
            if not bookstore.scalar_one_or_none():
                return None

            review = BookstoreReview(
                bookstore_id=bookstore_id,
                user_id=user_id,
                rating=data.rating,
                content=data.content,
            )
            session.add(review)
            await session.commit()
            await session.refresh(review)

            return {
                "id": str(review.id),
                "user_id": str(review.user_id),
                "user_nickname": "User",  # TODO: Fetch from user service
                "user_avatar": None,
                "rating": review.rating,
                "content": review.content,
                "created_at": review.created_at,
            }

    async def get_reviews(
        self,
        bookstore_id: str,
        page: int,
        page_size: int,
    ) -> List[dict]:
        """Get bookstore reviews"""
        async with get_db_session() as session:
            result = await session.execute(
                select(BookstoreReview)
                .where(BookstoreReview.bookstore_id == bookstore_id)
                .order_by(BookstoreReview.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            reviews = result.scalars().all()

            return [
                {
                    "id": str(r.id),
                    "user_id": str(r.user_id),
                    "user_nickname": "User",
                    "user_avatar": None,
                    "rating": r.rating,
                    "content": r.content,
                    "created_at": r.created_at,
                }
                for r in reviews
            ]

    async def add_favorite(self, bookstore_id: str, user_id: str) -> bool:
        """Add bookstore to favorites"""
        async with get_db_session() as session:
            # Check bookstore exists
            bookstore = await session.execute(
                select(Bookstore).where(Bookstore.id == bookstore_id)
            )
            if not bookstore.scalar_one_or_none():
                return False

            # Check not already favorited
            existing = await session.execute(
                select(BookstoreFavorite).where(
                    BookstoreFavorite.bookstore_id == bookstore_id,
                    BookstoreFavorite.user_id == user_id,
                )
            )
            if existing.scalar_one_or_none():
                return True

            favorite = BookstoreFavorite(
                bookstore_id=bookstore_id,
                user_id=user_id,
            )
            session.add(favorite)
            await session.commit()
            return True

    async def remove_favorite(self, bookstore_id: str, user_id: str) -> bool:
        """Remove bookstore from favorites"""
        async with get_db_session() as session:
            result = await session.execute(
                select(BookstoreFavorite).where(
                    BookstoreFavorite.bookstore_id == bookstore_id,
                    BookstoreFavorite.user_id == user_id,
                )
            )
            favorite = result.scalar_one_or_none()
            if favorite:
                await session.delete(favorite)
                await session.commit()
            return True

    async def get_favorites(
        self,
        user_id: str,
        page: int,
        page_size: int,
    ) -> dict:
        """Get user's favorite bookstores"""
        async with get_db_session() as session:
            # Get favorite bookstore IDs
            favorites_query = select(BookstoreFavorite.bookstore_id).where(
                BookstoreFavorite.user_id == user_id
            )

            result = await session.execute(
                select(Bookstore).where(
                    Bookstore.id.in_(favorites_query)
                ).offset((page - 1) * page_size).limit(page_size)
            )
            bookstores = result.scalars().all()

            # Count total
            count_result = await session.execute(
                select(func.count()).where(BookstoreFavorite.user_id == user_id)
            )
            total = count_result.scalar() or 0

            items = [
                await self._bookstore_to_dict(session, b, user_id)
                for b in bookstores
            ]

            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "has_more": page * page_size < total,
            }

    async def _bookstore_to_dict(self, session, bookstore: Bookstore, user_id: str) -> dict:
        """Convert bookstore to response dict"""
        # Get checkin count
        checkin_count_result = await session.execute(
            select(func.count()).where(Checkin.bookstore_id == bookstore.id)
        )
        checkin_count = checkin_count_result.scalar() or 0

        # Check if favorited
        favorite_result = await session.execute(
            select(BookstoreFavorite).where(
                BookstoreFavorite.bookstore_id == bookstore.id,
                BookstoreFavorite.user_id == user_id,
            )
        )
        is_favorite = favorite_result.scalar_one_or_none() is not None

        # Get first image from image_urls
        image_urls = bookstore.image_urls or []
        image_url = image_urls[0] if image_urls else None

        return {
            "id": str(bookstore.id),
            "name": bookstore.name,
            "address": bookstore.address,
            "description": bookstore.description,
            "location": {
                "latitude": bookstore.latitude,
                "longitude": bookstore.longitude,
            },
            "phone": bookstore.phone,
            "website": bookstore.website,
            "opening_hours": bookstore.opening_hours,
            "rating": round(float(bookstore.average_rating or 0), 1),
            "review_count": bookstore.review_count or 0,
            "checkin_count": checkin_count,
            "is_favorite": is_favorite,
            "image_url": image_url,
            "image_urls": image_urls,
            "features": bookstore.features or [],
        }

    def _calculate_distance(
        self,
        lat1: float, lon1: float,
        lat2: float, lon2: float,
    ) -> float:
        """Calculate distance between two points using Haversine formula"""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return round(self.EARTH_RADIUS * c, 2)
