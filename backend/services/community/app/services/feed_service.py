from typing import Optional, List
from datetime import datetime, timedelta

from sqlalchemy import select, func, or_, and_

from shared.core.database import get_db_session
from shared.core.redis import cache_service
from ..models.community import Quote, Review, QuoteLike, ReviewLike


class FeedService:
    """Service for generating user feeds"""

    CACHE_TTL = 300  # 5 minutes

    async def get_feed(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """Get personalized feed from followed users"""
        # Get followed user IDs
        following_ids = await self._get_following_ids(user_id)

        if not following_ids:
            # Return discover feed if no followers
            return await self.get_discover_feed(user_id, page, page_size)

        async with get_db_session() as session:
            # Get quotes from followed users
            quotes = await session.execute(
                select(Quote)
                .where(
                    Quote.user_id.in_(following_ids),
                    Quote.is_public == True,
                )
                .order_by(Quote.created_at.desc())
                .limit(page_size * 2)  # Get more for mixing
            )
            quotes_list = quotes.scalars().all()

            # Get reviews from followed users
            reviews = await session.execute(
                select(Review)
                .where(
                    Review.user_id.in_(following_ids),
                    Review.is_public == True,
                )
                .order_by(Review.created_at.desc())
                .limit(page_size * 2)
            )
            reviews_list = reviews.scalars().all()

            # Merge and sort by created_at
            items = []
            for quote in quotes_list:
                items.append(await self._quote_to_feed_item(session, quote, user_id))
            for review in reviews_list:
                items.append(await self._review_to_feed_item(session, review, user_id))

            # Sort by created_at
            items.sort(key=lambda x: x["created_at"], reverse=True)

            # Paginate
            start = (page - 1) * page_size
            end = start + page_size
            paginated_items = items[start:end]

            return {
                "items": paginated_items,
                "total": len(items),
                "page": page,
                "page_size": page_size,
                "has_more": end < len(items),
            }

    async def get_discover_feed(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """Get discover feed with popular content"""
        # Try cache first
        cache_key = f"discover_feed:{page}:{page_size}"
        cached = await cache_service.get(cache_key)
        if cached:
            # Update is_liked for viewer
            for item in cached["items"]:
                item["is_liked"] = await self._check_liked(item["id"], item["type"], user_id)
            return cached

        async with get_db_session() as session:
            # Get popular quotes (by likes_count stored in table)
            popular_quotes = await session.execute(
                select(Quote)
                .where(Quote.is_public == True)
                .order_by(Quote.likes_count.desc())
                .limit(page_size)
            )

            # Get popular reviews (by likes_count stored in table)
            popular_reviews = await session.execute(
                select(Review)
                .where(Review.is_public == True)
                .order_by(Review.likes_count.desc())
                .limit(page_size)
            )

            items = []
            for quote in popular_quotes.scalars().all():
                items.append(await self._quote_to_feed_item(session, quote, user_id))
            for review in popular_reviews.scalars().all():
                items.append(await self._review_to_feed_item(session, review, user_id))

            # Sort by likes
            items.sort(key=lambda x: x["likes_count"], reverse=True)

            # Paginate
            start = (page - 1) * page_size
            end = start + page_size
            paginated_items = items[start:end]

            result = {
                "items": paginated_items,
                "total": len(items),
                "page": page,
                "page_size": page_size,
                "has_more": end < len(items),
            }

            # Cache
            await cache_service.set(cache_key, result, ttl=self.CACHE_TTL)

            return result

    async def get_trending(
        self,
        period: str,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """Get trending content for period"""
        days = {"day": 1, "week": 7, "month": 30}.get(period, 7)
        since = datetime.utcnow() - timedelta(days=days)

        async with get_db_session() as session:
            # Get trending quotes (by likes_count)
            trending_quotes = await session.execute(
                select(Quote)
                .where(
                    Quote.is_public == True,
                    Quote.created_at >= since,
                )
                .order_by(Quote.likes_count.desc())
                .limit(page_size)
            )

            # Get trending reviews (by likes_count)
            trending_reviews = await session.execute(
                select(Review)
                .where(
                    Review.is_public == True,
                    Review.created_at >= since,
                )
                .order_by(Review.likes_count.desc())
                .limit(page_size)
            )

            items = []
            for quote in trending_quotes.scalars().all():
                items.append(await self._quote_to_feed_item(session, quote, user_id))
            for review in trending_reviews.scalars().all():
                items.append(await self._review_to_feed_item(session, review, user_id))

            items.sort(key=lambda x: x["likes_count"], reverse=True)

            start = (page - 1) * page_size
            end = start + page_size

            return {
                "items": items[start:end],
                "total": len(items),
                "page": page,
                "page_size": page_size,
                "has_more": end < len(items),
            }

    async def get_book_feed(
        self,
        book_id: str,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """Get feed for a specific book"""
        async with get_db_session() as session:
            quotes = await session.execute(
                select(Quote)
                .where(Quote.book_id == book_id, Quote.is_public == True)
                .order_by(Quote.created_at.desc())
            )
            reviews = await session.execute(
                select(Review)
                .where(Review.book_id == book_id, Review.is_public == True)
                .order_by(Review.created_at.desc())
            )

            items = []
            for quote in quotes.scalars().all():
                items.append(await self._quote_to_feed_item(session, quote, user_id))
            for review in reviews.scalars().all():
                items.append(await self._review_to_feed_item(session, review, user_id))

            items.sort(key=lambda x: x["created_at"], reverse=True)

            start = (page - 1) * page_size
            end = start + page_size

            return {
                "items": items[start:end],
                "total": len(items),
                "page": page,
                "page_size": page_size,
                "has_more": end < len(items),
            }

    async def get_user_feed(
        self,
        target_user_id: str,
        viewer_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """Get feed from a specific user"""
        async with get_db_session() as session:
            quotes = await session.execute(
                select(Quote)
                .where(Quote.user_id == target_user_id, Quote.is_public == True)
                .order_by(Quote.created_at.desc())
            )
            reviews = await session.execute(
                select(Review)
                .where(Review.user_id == target_user_id, Review.is_public == True)
                .order_by(Review.created_at.desc())
            )

            items = []
            for quote in quotes.scalars().all():
                items.append(await self._quote_to_feed_item(session, quote, viewer_id))
            for review in reviews.scalars().all():
                items.append(await self._review_to_feed_item(session, review, viewer_id))

            items.sort(key=lambda x: x["created_at"], reverse=True)

            start = (page - 1) * page_size
            end = start + page_size

            return {
                "items": items[start:end],
                "total": len(items),
                "page": page,
                "page_size": page_size,
                "has_more": end < len(items),
            }

    async def _get_following_ids(self, user_id: str) -> List[str]:
        """Get list of user IDs the user is following"""
        # TODO: Call user service to get following list
        return []

    async def _check_liked(self, item_id: str, item_type: str, user_id: str) -> bool:
        """Check if user liked an item"""
        async with get_db_session() as session:
            if item_type == "quote":
                result = await session.execute(
                    select(QuoteLike).where(
                        QuoteLike.quote_id == item_id,
                        QuoteLike.user_id == user_id,
                    )
                )
            else:
                result = await session.execute(
                    select(ReviewLike).where(
                        ReviewLike.review_id == item_id,
                        ReviewLike.user_id == user_id,
                    )
                )
            return result.scalar_one_or_none() is not None

    async def _quote_to_feed_item(self, session, quote: Quote, viewer_id: str) -> dict:
        """Convert quote to feed item"""
        is_liked = await self._check_liked(quote.id, "quote", viewer_id)

        return {
            "id": str(quote.id),
            "type": "quote",
            "content": quote.content,
            "author": {
                "id": str(quote.user_id),
                "nickname": "User",
                "avatar_url": None,
                "level": 1,
            },
            "book": {
                "id": str(quote.book_id),
                "title": "Book",
                "author": "Author",
                "cover_image_url": None,
            },
            "rating": None,
            "page_number": quote.page_number,
            "memo": quote.memo,
            "likes_count": quote.likes_count or 0,
            "comments_count": 0,
            "is_liked": is_liked,
            "created_at": quote.created_at,
        }

    async def _review_to_feed_item(self, session, review: Review, viewer_id: str) -> dict:
        """Convert review to feed item"""
        is_liked = await self._check_liked(review.id, "review", viewer_id)

        return {
            "id": str(review.id),
            "type": "review",
            "content": review.content[:200] + "..." if len(review.content) > 200 else review.content,
            "author": {
                "id": str(review.user_id),
                "nickname": "User",
                "avatar_url": None,
                "level": 1,
            },
            "book": {
                "id": str(review.book_id),
                "title": "Book",
                "author": "Author",
                "cover_image_url": None,
            },
            "rating": review.rating,
            "page_number": None,
            "has_spoiler": review.has_spoiler,
            "likes_count": review.likes_count or 0,
            "comments_count": 0,
            "is_liked": is_liked,
            "created_at": review.created_at,
        }
