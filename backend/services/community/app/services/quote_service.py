from typing import Optional
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select, func, and_
from sqlalchemy.orm import joinedload

from shared.core.database import get_db_session
from ..models.community import Quote, QuoteLike
from ..schemas.community_schemas import QuoteCreateRequest, QuoteUpdateRequest


class QuoteService:
    """Service for quote operations"""

    async def create_quote(self, user_id: str, data: QuoteCreateRequest) -> dict:
        """Create a new quote"""
        async with get_db_session() as session:
            quote = Quote(
                id=str(uuid4()),
                user_id=user_id,
                book_id=data.book_id,
                content=data.content,
                page_number=data.page_number,
                thought=data.thought,
                background_color=data.background_color,
                is_public=data.is_public,
            )
            session.add(quote)
            await session.commit()
            await session.refresh(quote)

            return await self.get_quote_by_id(quote.id, user_id)

    async def get_quote_by_id(self, quote_id: str, viewer_id: str) -> Optional[dict]:
        """Get quote by ID"""
        async with get_db_session() as session:
            result = await session.execute(
                select(Quote).where(Quote.id == quote_id)
            )
            quote = result.scalar_one_or_none()
            if not quote:
                return None

            # Check access
            if not quote.is_public and quote.user_id != viewer_id:
                return None

            return await self._quote_to_dict(session, quote, viewer_id)

    async def get_quotes(
        self,
        book_id: Optional[str] = None,
        user_id: Optional[str] = None,
        viewer_id: str = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """Get quotes with filters"""
        async with get_db_session() as session:
            query = select(Quote).where(Quote.is_public == True)

            if book_id:
                query = query.where(Quote.book_id == book_id)
            if user_id:
                query = query.where(Quote.user_id == user_id)

            # Count total
            count_query = select(func.count()).select_from(query.subquery())
            count_result = await session.execute(count_query)
            total = count_result.scalar() or 0

            # Paginate
            query = query.order_by(Quote.created_at.desc())
            query = query.offset((page - 1) * page_size).limit(page_size)

            result = await session.execute(query)
            quotes = result.scalars().all()

            items = [
                await self._quote_to_dict(session, q, viewer_id)
                for q in quotes
            ]

            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "has_more": page * page_size < total,
            }

    async def update_quote(
        self,
        quote_id: str,
        user_id: str,
        data: QuoteUpdateRequest,
    ) -> Optional[dict]:
        """Update a quote"""
        async with get_db_session() as session:
            result = await session.execute(
                select(Quote).where(
                    Quote.id == quote_id,
                    Quote.user_id == user_id,
                )
            )
            quote = result.scalar_one_or_none()
            if not quote:
                return None

            if data.content is not None:
                quote.content = data.content
            if data.thought is not None:
                quote.thought = data.thought
            if data.background_color is not None:
                quote.background_color = data.background_color
            if data.is_public is not None:
                quote.is_public = data.is_public

            quote.updated_at = datetime.utcnow()
            await session.commit()

            return await self.get_quote_by_id(quote_id, user_id)

    async def delete_quote(self, quote_id: str, user_id: str) -> bool:
        """Delete a quote"""
        async with get_db_session() as session:
            result = await session.execute(
                select(Quote).where(
                    Quote.id == quote_id,
                    Quote.user_id == user_id,
                )
            )
            quote = result.scalar_one_or_none()
            if not quote:
                return False

            await session.delete(quote)
            await session.commit()
            return True

    async def like_quote(self, quote_id: str, user_id: str) -> bool:
        """Like a quote"""
        async with get_db_session() as session:
            # Check quote exists
            result = await session.execute(
                select(Quote).where(Quote.id == quote_id)
            )
            if not result.scalar_one_or_none():
                return False

            # Check not already liked
            existing = await session.execute(
                select(QuoteLike).where(
                    QuoteLike.quote_id == quote_id,
                    QuoteLike.user_id == user_id,
                )
            )
            if existing.scalar_one_or_none():
                return True  # Already liked

            like = QuoteLike(
                id=str(uuid4()),
                quote_id=quote_id,
                user_id=user_id,
            )
            session.add(like)
            await session.commit()
            return True

    async def unlike_quote(self, quote_id: str, user_id: str) -> bool:
        """Unlike a quote"""
        async with get_db_session() as session:
            result = await session.execute(
                select(QuoteLike).where(
                    QuoteLike.quote_id == quote_id,
                    QuoteLike.user_id == user_id,
                )
            )
            like = result.scalar_one_or_none()
            if like:
                await session.delete(like)
                await session.commit()
            return True

    async def _quote_to_dict(self, session, quote: Quote, viewer_id: str) -> dict:
        """Convert quote to response dict"""
        # Get likes count
        likes_result = await session.execute(
            select(func.count()).where(QuoteLike.quote_id == quote.id)
        )
        likes_count = likes_result.scalar() or 0

        # Check if viewer liked
        is_liked = False
        if viewer_id:
            liked_result = await session.execute(
                select(QuoteLike).where(
                    QuoteLike.quote_id == quote.id,
                    QuoteLike.user_id == viewer_id,
                )
            )
            is_liked = liked_result.scalar_one_or_none() is not None

        # TODO: Get author and book info from respective services
        return {
            "id": quote.id,
            "content": quote.content,
            "page_number": quote.page_number,
            "thought": quote.thought,
            "background_color": quote.background_color,
            "is_public": quote.is_public,
            "author": {
                "id": quote.user_id,
                "nickname": "User",  # TODO: Fetch from user service
                "avatar_url": None,
                "level": 1,
            },
            "book": {
                "id": quote.book_id,
                "title": "Book",  # TODO: Fetch from book service
                "author": "Author",
                "cover_image_url": None,
            },
            "likes_count": likes_count,
            "is_liked": is_liked,
            "created_at": quote.created_at,
        }
