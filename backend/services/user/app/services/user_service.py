from typing import Optional
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from shared.core.database import get_db_session
from ..models.user import User, UserProfile, Follow
from ..schemas.user_schemas import UserUpdateRequest


class UserService:
    """Service for user operations"""

    async def get_user_with_profile(self, user_id: str) -> Optional[dict]:
        """Get user with full profile"""
        async with get_db_session() as session:
            result = await session.execute(
                select(User)
                .options(joinedload(User.profile))
                .where(User.id == user_id)
            )
            user = result.unique().scalar_one_or_none()
            if not user:
                return None

            # Get counts
            followers_count = await self._get_followers_count(session, user_id)
            following_count = await self._get_following_count(session, user_id)
            books_count, completed_count = await self._get_books_count(session, user_id)

            return {
                "id": user.id,
                "email": user.email,
                "profile": user.profile.to_dict() if user.profile else None,
                "followers_count": followers_count,
                "following_count": following_count,
                "books_count": books_count,
                "completed_books_count": completed_count,
                "created_at": user.created_at,
            }

    async def get_public_profile(
        self,
        user_id: str,
        viewer_id: str,
    ) -> Optional[dict]:
        """Get user's public profile"""
        async with get_db_session() as session:
            result = await session.execute(
                select(User)
                .options(joinedload(User.profile))
                .where(User.id == user_id)
            )
            user = result.unique().scalar_one_or_none()
            if not user:
                return None

            # Get counts
            followers_count = await self._get_followers_count(session, user_id)
            following_count = await self._get_following_count(session, user_id)
            books_count, completed_count = await self._get_books_count(session, user_id)

            # Check if viewer follows this user
            is_following = await self._check_following(session, viewer_id, user_id)

            return {
                "id": user.id,
                "email": user.email,  # Could be hidden for privacy
                "profile": user.profile.to_dict() if user.profile else None,
                "followers_count": followers_count,
                "following_count": following_count,
                "books_count": books_count,
                "completed_books_count": completed_count,
                "is_following": is_following,
                "created_at": user.created_at,
            }

    async def update_user(
        self,
        user_id: str,
        data: UserUpdateRequest,
    ) -> Optional[dict]:
        """Update user profile"""
        async with get_db_session() as session:
            result = await session.execute(
                select(User)
                .options(joinedload(User.profile))
                .where(User.id == user_id)
            )
            user = result.unique().scalar_one_or_none()
            if not user:
                return None

            if user.profile:
                if data.nickname is not None:
                    user.profile.nickname = data.nickname
                if data.bio is not None:
                    user.profile.bio = data.bio
                user.profile.updated_at = datetime.utcnow()

            await session.commit()
            return await self.get_user_with_profile(user_id)

    async def search_users(
        self,
        query: str,
        page: int,
        page_size: int,
        current_user_id: str,
    ) -> dict:
        """Search users by nickname"""
        async with get_db_session() as session:
            # Search query
            search_query = select(UserProfile).where(
                UserProfile.nickname.ilike(f"%{query}%")
            )

            # Count total
            count_result = await session.execute(
                select(func.count()).select_from(search_query.subquery())
            )
            total = count_result.scalar() or 0

            # Paginate
            search_query = search_query.offset((page - 1) * page_size).limit(page_size)
            result = await session.execute(search_query)
            profiles = result.scalars().all()

            # Check following status for each
            items = []
            for profile in profiles:
                is_following = await self._check_following(
                    session, current_user_id, profile.user_id
                )
                items.append({
                    "id": profile.user_id,
                    "nickname": profile.nickname,
                    "avatar_url": profile.avatar_url,
                    "level": profile.level,
                    "is_following": is_following,
                })

            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "has_more": page * page_size < total,
            }

    async def _get_followers_count(self, session, user_id: str) -> int:
        result = await session.execute(
            select(func.count()).where(Follow.following_id == user_id)
        )
        return result.scalar() or 0

    async def _get_following_count(self, session, user_id: str) -> int:
        result = await session.execute(
            select(func.count()).where(Follow.follower_id == user_id)
        )
        return result.scalar() or 0

    async def _get_books_count(self, session, user_id: str) -> tuple[int, int]:
        # This would need UserBook model imported
        # For now returning placeholder
        return 0, 0

    async def _check_following(
        self,
        session,
        follower_id: str,
        following_id: str,
    ) -> bool:
        result = await session.execute(
            select(Follow).where(
                Follow.follower_id == follower_id,
                Follow.following_id == following_id,
            )
        )
        return result.scalar_one_or_none() is not None
