from typing import Optional
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select, func, and_

from shared.core.database import get_db_session
from ..models.user import User, UserProfile, Follow


class FollowService:
    """Service for follow/unfollow operations"""

    async def follow_user(
        self,
        follower_id: str,
        following_id: str,
    ) -> Optional[dict]:
        """Follow a user"""
        async with get_db_session() as session:
            # Check if target user exists
            result = await session.execute(
                select(User).where(User.id == following_id)
            )
            if not result.scalar_one_or_none():
                return None

            # Check if already following
            existing = await session.execute(
                select(Follow).where(
                    Follow.follower_id == follower_id,
                    Follow.following_id == following_id,
                )
            )
            if existing.scalar_one_or_none():
                # Already following, return existing
                return {
                    "follower_id": follower_id,
                    "following_id": following_id,
                    "created_at": datetime.utcnow(),
                }

            # Create follow relationship
            follow = Follow(
                id=str(uuid4()),
                follower_id=follower_id,
                following_id=following_id,
            )
            session.add(follow)
            await session.commit()

            # TODO: Send notification to followed user

            return {
                "follower_id": follower_id,
                "following_id": following_id,
                "created_at": follow.created_at,
            }

    async def unfollow_user(
        self,
        follower_id: str,
        following_id: str,
    ) -> bool:
        """Unfollow a user"""
        async with get_db_session() as session:
            result = await session.execute(
                select(Follow).where(
                    Follow.follower_id == follower_id,
                    Follow.following_id == following_id,
                )
            )
            follow = result.scalar_one_or_none()
            if not follow:
                return False

            await session.delete(follow)
            await session.commit()
            return True

    async def is_following(
        self,
        follower_id: str,
        following_id: str,
    ) -> bool:
        """Check if user is following another user"""
        async with get_db_session() as session:
            result = await session.execute(
                select(Follow).where(
                    Follow.follower_id == follower_id,
                    Follow.following_id == following_id,
                )
            )
            return result.scalar_one_or_none() is not None

    async def get_followers(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        viewer_id: Optional[str] = None,
    ) -> dict:
        """Get user's followers"""
        async with get_db_session() as session:
            # Count total
            count_result = await session.execute(
                select(func.count()).where(Follow.following_id == user_id)
            )
            total = count_result.scalar() or 0

            # Get follower IDs with pagination
            follows_query = (
                select(Follow)
                .where(Follow.following_id == user_id)
                .order_by(Follow.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            result = await session.execute(follows_query)
            follows = result.scalars().all()

            # Get profiles for followers
            items = []
            for follow in follows:
                profile_result = await session.execute(
                    select(UserProfile).where(UserProfile.user_id == follow.follower_id)
                )
                profile = profile_result.scalar_one_or_none()

                if profile:
                    # Check if viewer follows this follower
                    is_following = False
                    is_follower = False
                    if viewer_id:
                        is_following = await self.is_following(viewer_id, follow.follower_id)
                        is_follower = await self.is_following(follow.follower_id, viewer_id)

                    items.append({
                        "id": follow.follower_id,
                        "nickname": profile.nickname,
                        "avatar_url": profile.avatar_url,
                        "level": profile.level,
                        "bio": profile.bio,
                        "is_following": is_following,
                        "is_follower": is_follower,
                    })

            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "has_more": page * page_size < total,
            }

    async def get_following(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        viewer_id: Optional[str] = None,
    ) -> dict:
        """Get users that user is following"""
        async with get_db_session() as session:
            # Count total
            count_result = await session.execute(
                select(func.count()).where(Follow.follower_id == user_id)
            )
            total = count_result.scalar() or 0

            # Get following IDs with pagination
            follows_query = (
                select(Follow)
                .where(Follow.follower_id == user_id)
                .order_by(Follow.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            result = await session.execute(follows_query)
            follows = result.scalars().all()

            # Get profiles
            items = []
            for follow in follows:
                profile_result = await session.execute(
                    select(UserProfile).where(UserProfile.user_id == follow.following_id)
                )
                profile = profile_result.scalar_one_or_none()

                if profile:
                    # Check relationships
                    is_following = True  # User is following them by definition
                    is_follower = await self.is_following(follow.following_id, user_id)

                    items.append({
                        "id": follow.following_id,
                        "nickname": profile.nickname,
                        "avatar_url": profile.avatar_url,
                        "level": profile.level,
                        "bio": profile.bio,
                        "is_following": is_following,
                        "is_follower": is_follower,
                    })

            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "has_more": page * page_size < total,
            }
