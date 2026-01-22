"""Auth service implementation."""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.core.security import (
    create_token_pair,
    get_password_hash,
    verify_password,
    verify_token,
)

from ..models.user import User, UserProfile


class AuthService:
    """Authentication service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(
        self,
        email: str,
        password: str,
        nickname: str,
    ) -> Optional[dict[str, Any]]:
        """Register a new user."""
        # Check if email exists
        existing = await self.db.execute(
            select(User).where(User.email == email)
        )
        if existing.scalar_one_or_none():
            return None

        # Check if nickname exists
        existing_profile = await self.db.execute(
            select(UserProfile).where(UserProfile.nickname == nickname)
        )
        if existing_profile.scalar_one_or_none():
            return None

        # Create user
        user = User(
            email=email,
            password_hash=get_password_hash(password),
            provider="local",
        )
        self.db.add(user)
        await self.db.flush()

        # Create profile
        profile = UserProfile(
            user_id=user.id,
            nickname=nickname,
        )
        self.db.add(profile)
        await self.db.commit()

        # Refresh to get all data
        await self.db.refresh(user)
        await self.db.refresh(profile)

        # Generate tokens
        tokens = create_token_pair(user.id, user.email)

        return {
            "user": self._serialize_user(user, profile),
            "tokens": self._serialize_tokens(tokens),
        }

    async def login(
        self,
        email: str,
        password: str,
    ) -> Optional[dict[str, Any]]:
        """Login with email and password."""
        # Find user
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if user is None:
            return None

        if user.password_hash is None:
            return None

        if not verify_password(password, user.password_hash):
            return None

        if user.status != "active":
            return None

        # Update last login
        user.last_login_at = datetime.utcnow()
        await self.db.commit()

        # Generate tokens
        tokens = create_token_pair(user.id, user.email)

        return {
            "user": self._serialize_user(user, user.profile),
            "tokens": self._serialize_tokens(tokens),
        }

    async def oauth_login(
        self,
        provider: str,
        id_token: str,
    ) -> Optional[dict[str, Any]]:
        """Login with OAuth provider."""
        # Verify token with provider
        oauth_data = await self._verify_oauth_token(provider, id_token)

        if oauth_data is None:
            return None

        email = oauth_data.get("email")
        provider_id = oauth_data.get("sub") or oauth_data.get("id")

        # Find existing user
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(
                (User.email == email) |
                ((User.provider == provider) & (User.provider_id == provider_id))
            )
        )
        user = result.scalar_one_or_none()

        is_new_user = False

        if user is None:
            # Create new user
            is_new_user = True
            user = User(
                email=email,
                provider=provider,
                provider_id=provider_id,
            )
            self.db.add(user)
            await self.db.flush()

            # Create profile
            nickname = await self._generate_unique_nickname(email.split("@")[0])
            profile = UserProfile(
                user_id=user.id,
                nickname=nickname,
                profile_image=oauth_data.get("picture"),
            )
            self.db.add(profile)
            await self.db.commit()
            await self.db.refresh(user)
            await self.db.refresh(profile)
            user.profile = profile
        else:
            # Update provider info if needed
            if user.provider == "local":
                user.provider = provider
                user.provider_id = provider_id

            user.last_login_at = datetime.utcnow()
            await self.db.commit()

        tokens = create_token_pair(user.id, user.email)

        return {
            "user": self._serialize_user(user, user.profile),
            "tokens": self._serialize_tokens(tokens),
            "is_new_user": is_new_user,
        }

    async def refresh_tokens(
        self,
        refresh_token: str,
    ) -> Optional[dict[str, Any]]:
        """Refresh access token."""
        token_data = verify_token(refresh_token, "refresh")

        if token_data is None:
            return None

        # Verify user exists
        result = await self.db.execute(
            select(User).where(User.id == UUID(token_data.user_id))
        )
        user = result.scalar_one_or_none()

        if user is None or user.status != "active":
            return None

        # Generate new tokens
        tokens = create_token_pair(user.id, user.email)

        return self._serialize_tokens(tokens)

    async def logout(self, user_id: str) -> None:
        """Logout user (invalidate FCM token)."""
        result = await self.db.execute(
            select(User).where(User.id == UUID(user_id))
        )
        user = result.scalar_one_or_none()

        if user:
            user.fcm_token = None
            await self.db.commit()

    async def update_fcm_token(
        self,
        user_id: str,
        fcm_token: str,
        platform: str,
    ) -> None:
        """Update FCM token for push notifications."""
        result = await self.db.execute(
            select(User).where(User.id == UUID(user_id))
        )
        user = result.scalar_one_or_none()

        if user:
            user.fcm_token = fcm_token
            await self.db.commit()

    async def get_user_by_id(self, user_id: str) -> Optional[dict[str, Any]]:
        """Get user by ID."""
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id == UUID(user_id))
        )
        user = result.scalar_one_or_none()

        if user is None:
            return None

        return self._serialize_user(user, user.profile)

    async def _verify_oauth_token(
        self,
        provider: str,
        id_token: str,
    ) -> Optional[dict[str, Any]]:
        """Verify OAuth token with provider."""
        # TODO: Implement actual OAuth token verification
        # This should verify with Google, Apple, or Kakao servers

        # For now, decode JWT without verification (UNSAFE - for development only)
        import base64
        import json

        try:
            parts = id_token.split(".")
            if len(parts) != 3:
                return None

            payload = parts[1]
            # Add padding if needed
            payload += "=" * (4 - len(payload) % 4)
            decoded = base64.urlsafe_b64decode(payload)
            return json.loads(decoded)
        except Exception:
            return None

    async def _generate_unique_nickname(self, base: str) -> str:
        """Generate a unique nickname."""
        import random
        import string

        nickname = base[:15]  # Max 20 chars, leave room for suffix

        # Check if exists
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.nickname == nickname)
        )

        if result.scalar_one_or_none() is None:
            return nickname

        # Add random suffix
        for _ in range(10):
            suffix = "".join(random.choices(string.digits, k=4))
            new_nickname = f"{nickname}_{suffix}"

            result = await self.db.execute(
                select(UserProfile).where(UserProfile.nickname == new_nickname)
            )

            if result.scalar_one_or_none() is None:
                return new_nickname

        # Fallback to timestamp
        import time
        return f"{nickname}_{int(time.time())}"

    def _serialize_user(self, user: User, profile: UserProfile) -> dict:
        """Serialize user for response."""
        return {
            "id": str(user.id),
            "email": user.email,
            "provider": user.provider,
            "lastLoginAt": user.last_login_at.isoformat() if user.last_login_at else None,
            "createdAt": user.created_at.isoformat(),
            "profile": {
                "id": str(profile.id),
                "userId": str(profile.user_id),
                "nickname": profile.nickname,
                "bio": profile.bio,
                "profileImage": profile.profile_image,
                "readingGoalMin": profile.reading_goal_min,
                "isPublic": profile.is_public,
                "level": profile.level,
                "exp": profile.exp,
                "coins": profile.coins,
                "premiumUntil": profile.premium_until.isoformat() if profile.premium_until else None,
                "createdAt": profile.created_at.isoformat(),
                "updatedAt": profile.updated_at.isoformat(),
            },
        }

    def _serialize_tokens(self, tokens) -> dict:
        """Serialize tokens for response."""
        return {
            "accessToken": tokens.access_token,
            "refreshToken": tokens.refresh_token,
            "expiresIn": tokens.expires_in,
            "tokenType": tokens.token_type,
        }
