from typing import Optional
from datetime import datetime
import hashlib

from sqlalchemy import select

from shared.core.database import get_db_session
from shared.core.redis import cache_service
from ..models.user import UserProfile, ReadingGoal
from ..schemas.user_schemas import (
    ProfileUpdateRequest,
    AvatarUpdateRequest,
    ReadingGoalRequest,
)


class ProfileService:
    """Service for profile operations"""

    async def get_profile(self, user_id: str) -> Optional[dict]:
        """Get user profile"""
        async with get_db_session() as session:
            result = await session.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            profile = result.scalar_one_or_none()
            return profile.to_dict() if profile else None

    async def update_profile(
        self,
        user_id: str,
        data: ProfileUpdateRequest,
    ) -> dict:
        """Update user profile"""
        async with get_db_session() as session:
            result = await session.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            profile = result.scalar_one_or_none()

            if not profile:
                # Create profile if not exists
                profile = UserProfile(user_id=user_id)
                session.add(profile)

            if data.nickname is not None:
                profile.nickname = data.nickname
            if data.bio is not None:
                profile.bio = data.bio

            profile.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(profile)

            # Invalidate cache
            await cache_service.delete(f"profile:{user_id}")

            return profile.to_dict()

    async def upload_avatar(
        self,
        user_id: str,
        file_content: bytes,
        content_type: str,
    ) -> str:
        """Upload avatar image and return URL"""
        # Generate unique filename
        file_hash = hashlib.md5(file_content).hexdigest()
        extension = content_type.split("/")[-1]
        filename = f"avatars/{user_id}/{file_hash}.{extension}"

        # TODO: Upload to S3 or other storage
        # For now, return placeholder URL
        avatar_url = f"https://storage.readlock.app/{filename}"

        # Update profile
        async with get_db_session() as session:
            result = await session.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            profile = result.scalar_one_or_none()

            if profile:
                profile.profile_image = avatar_url
                profile.updated_at = datetime.utcnow()
                await session.commit()

        return avatar_url

    async def update_avatar_customization(
        self,
        user_id: str,
        customization: AvatarUpdateRequest,
    ) -> dict:
        """Update virtual avatar customization"""
        async with get_db_session() as session:
            result = await session.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            profile = result.scalar_one_or_none()

            if not profile:
                return {"avatar_url": None, "customization": None}

            # Avatar customization is handled separately (not in DB currently)
            # Return current profile image
            return {
                "avatar_url": profile.profile_image,
                "customization": None,
            }

    async def get_reading_goal(self, user_id: str) -> dict:
        """Get user's reading goal"""
        from sqlalchemy import and_

        async with get_db_session() as session:
            # Get all active goals for the user
            result = await session.execute(
                select(ReadingGoal).where(
                    and_(
                        ReadingGoal.user_id == user_id,
                        ReadingGoal.is_active == True
                    )
                )
            )
            goals = result.scalars().all()

            # Default values
            response = {
                "daily_minutes": 30,
                "daily_pages": 0,
                "monthly_books": 0,
                "yearly_books": 0,
                "today_minutes": 0,
                "today_pages": 0,
                "month_books": 0,
                "year_books": 0,
            }

            # Map goals to response
            for goal in goals:
                if goal.goal_type == "daily_minutes":
                    response["daily_minutes"] = goal.target
                    response["today_minutes"] = goal.current
                elif goal.goal_type == "daily_pages":
                    response["daily_pages"] = goal.target
                    response["today_pages"] = goal.current
                elif goal.goal_type == "monthly_books":
                    response["monthly_books"] = goal.target
                    response["month_books"] = goal.current
                elif goal.goal_type == "yearly_books":
                    response["yearly_books"] = goal.target
                    response["year_books"] = goal.current

            return response

    async def set_reading_goal(
        self,
        user_id: str,
        data: ReadingGoalRequest,
    ) -> dict:
        """Set user's reading goal"""
        from sqlalchemy import and_

        async with get_db_session() as session:
            now = datetime.utcnow()

            # Update or create goals for each type
            goal_updates = []
            if data.daily_minutes is not None:
                goal_updates.append(("daily_minutes", data.daily_minutes))
            if data.daily_pages is not None:
                goal_updates.append(("daily_pages", data.daily_pages))
            if data.monthly_books is not None:
                goal_updates.append(("monthly_books", data.monthly_books))
            if data.yearly_books is not None:
                goal_updates.append(("yearly_books", data.yearly_books))

            for goal_type, target in goal_updates:
                result = await session.execute(
                    select(ReadingGoal).where(
                        and_(
                            ReadingGoal.user_id == user_id,
                            ReadingGoal.goal_type == goal_type,
                            ReadingGoal.is_active == True
                        )
                    )
                )
                goal = result.scalar_one_or_none()

                if goal:
                    goal.target = target
                    goal.updated_at = now
                else:
                    goal = ReadingGoal(
                        user_id=user_id,
                        goal_type=goal_type,
                        target=target,
                        year=now.year if "yearly" in goal_type else None,
                        month=now.month if "monthly" in goal_type else None,
                    )
                    session.add(goal)

            await session.commit()

            return await self.get_reading_goal(user_id)
