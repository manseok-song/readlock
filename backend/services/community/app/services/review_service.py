from typing import Optional
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select, func

from shared.core.database import get_db_session
from ..models.community import Review, ReviewLike, Comment
from ..schemas.community_schemas import ReviewCreateRequest, ReviewUpdateRequest


class ReviewService:
    """Service for review operations"""

    async def create_review(self, user_id: str, data: ReviewCreateRequest) -> dict:
        """Create a new review"""
        async with get_db_session() as session:
            # Check if user already reviewed this book
            existing = await session.execute(
                select(Review).where(
                    Review.user_id == user_id,
                    Review.book_id == data.book_id,
                )
            )
            if existing.scalar_one_or_none():
                raise ValueError("Already reviewed this book")

            review = Review(
                id=str(uuid4()),
                user_id=user_id,
                book_id=data.book_id,
                rating=data.rating,
                title=data.title,
                content=data.content,
                contains_spoiler=data.contains_spoiler,
                is_public=data.is_public,
            )
            session.add(review)
            await session.commit()
            await session.refresh(review)

            return await self.get_review_by_id(review.id, user_id)

    async def get_review_by_id(self, review_id: str, viewer_id: str) -> Optional[dict]:
        """Get review by ID"""
        async with get_db_session() as session:
            result = await session.execute(
                select(Review).where(Review.id == review_id)
            )
            review = result.scalar_one_or_none()
            if not review:
                return None

            if not review.is_public and review.user_id != viewer_id:
                return None

            return await self._review_to_dict(session, review, viewer_id)

    async def get_reviews(
        self,
        book_id: Optional[str] = None,
        user_id: Optional[str] = None,
        viewer_id: str = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """Get reviews with filters"""
        async with get_db_session() as session:
            query = select(Review).where(Review.is_public == True)

            if book_id:
                query = query.where(Review.book_id == book_id)
            if user_id:
                query = query.where(Review.user_id == user_id)

            # Count total
            count_query = select(func.count()).select_from(query.subquery())
            count_result = await session.execute(count_query)
            total = count_result.scalar() or 0

            # Paginate
            query = query.order_by(Review.created_at.desc())
            query = query.offset((page - 1) * page_size).limit(page_size)

            result = await session.execute(query)
            reviews = result.scalars().all()

            items = [
                await self._review_to_dict(session, r, viewer_id)
                for r in reviews
            ]

            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "has_more": page * page_size < total,
            }

    async def update_review(
        self,
        review_id: str,
        user_id: str,
        data: ReviewUpdateRequest,
    ) -> Optional[dict]:
        """Update a review"""
        async with get_db_session() as session:
            result = await session.execute(
                select(Review).where(
                    Review.id == review_id,
                    Review.user_id == user_id,
                )
            )
            review = result.scalar_one_or_none()
            if not review:
                return None

            if data.rating is not None:
                review.rating = data.rating
            if data.title is not None:
                review.title = data.title
            if data.content is not None:
                review.content = data.content
            if data.contains_spoiler is not None:
                review.contains_spoiler = data.contains_spoiler
            if data.is_public is not None:
                review.is_public = data.is_public

            review.updated_at = datetime.utcnow()
            await session.commit()

            return await self.get_review_by_id(review_id, user_id)

    async def delete_review(self, review_id: str, user_id: str) -> bool:
        """Delete a review"""
        async with get_db_session() as session:
            result = await session.execute(
                select(Review).where(
                    Review.id == review_id,
                    Review.user_id == user_id,
                )
            )
            review = result.scalar_one_or_none()
            if not review:
                return False

            await session.delete(review)
            await session.commit()
            return True

    async def like_review(self, review_id: str, user_id: str) -> bool:
        """Like a review"""
        async with get_db_session() as session:
            result = await session.execute(
                select(Review).where(Review.id == review_id)
            )
            if not result.scalar_one_or_none():
                return False

            existing = await session.execute(
                select(ReviewLike).where(
                    ReviewLike.review_id == review_id,
                    ReviewLike.user_id == user_id,
                )
            )
            if existing.scalar_one_or_none():
                return True

            like = ReviewLike(
                id=str(uuid4()),
                review_id=review_id,
                user_id=user_id,
            )
            session.add(like)
            await session.commit()
            return True

    async def unlike_review(self, review_id: str, user_id: str) -> bool:
        """Unlike a review"""
        async with get_db_session() as session:
            result = await session.execute(
                select(ReviewLike).where(
                    ReviewLike.review_id == review_id,
                    ReviewLike.user_id == user_id,
                )
            )
            like = result.scalar_one_or_none()
            if like:
                await session.delete(like)
                await session.commit()
            return True

    async def add_comment(
        self,
        review_id: str,
        user_id: str,
        content: str,
    ) -> Optional[dict]:
        """Add a comment to a review"""
        async with get_db_session() as session:
            result = await session.execute(
                select(Review).where(Review.id == review_id)
            )
            if not result.scalar_one_or_none():
                return None

            comment = Comment(
                id=str(uuid4()),
                review_id=review_id,
                user_id=user_id,
                content=content,
            )
            session.add(comment)
            await session.commit()
            await session.refresh(comment)

            return {
                "id": comment.id,
                "content": comment.content,
                "author": {
                    "id": user_id,
                    "nickname": "User",  # TODO: Fetch
                    "avatar_url": None,
                    "level": 1,
                },
                "created_at": comment.created_at,
            }

    async def _review_to_dict(self, session, review: Review, viewer_id: str) -> dict:
        """Convert review to response dict"""
        # Get likes count
        likes_result = await session.execute(
            select(func.count()).where(ReviewLike.review_id == review.id)
        )
        likes_count = likes_result.scalar() or 0

        # Get comments count
        comments_result = await session.execute(
            select(func.count()).where(Comment.review_id == review.id)
        )
        comments_count = comments_result.scalar() or 0

        # Check if viewer liked
        is_liked = False
        if viewer_id:
            liked_result = await session.execute(
                select(ReviewLike).where(
                    ReviewLike.review_id == review.id,
                    ReviewLike.user_id == viewer_id,
                )
            )
            is_liked = liked_result.scalar_one_or_none() is not None

        return {
            "id": review.id,
            "rating": review.rating,
            "title": review.title,
            "content": review.content,
            "contains_spoiler": review.contains_spoiler,
            "is_public": review.is_public,
            "author": {
                "id": review.user_id,
                "nickname": "User",
                "avatar_url": None,
                "level": 1,
            },
            "book": {
                "id": review.book_id,
                "title": "Book",
                "author": "Author",
                "cover_image_url": None,
            },
            "likes_count": likes_count,
            "comments_count": comments_count,
            "is_liked": is_liked,
            "created_at": review.created_at,
            "updated_at": review.updated_at,
        }
