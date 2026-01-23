from typing import Optional
from uuid import uuid4

from sqlalchemy import select

from shared.core.database import get_db_session
from ..models.gamification import UserAvatarConfig, ShopItem


class AvatarService:
    """Service for avatar customization management"""

    async def get_avatar_config(self, user_id: str) -> dict:
        """Get user's avatar configuration with item details"""
        async with get_db_session() as session:
            result = await session.execute(
                select(UserAvatarConfig).where(UserAvatarConfig.user_id == user_id)
            )
            config = result.scalar_one_or_none()

            if not config:
                return {
                    "id": None,
                    "user_id": user_id,
                    "face_item_id": None,
                    "hair_item_id": None,
                    "outfit_item_id": None,
                    "accessory_item_id": None,
                    "skin_color": "#FFD5B8",
                    "face_item": None,
                    "hair_item": None,
                    "outfit_item": None,
                    "accessory_item": None,
                }

            response = config.to_dict()

            item_ids = [
                config.face_item_id,
                config.hair_item_id,
                config.outfit_item_id,
                config.accessory_item_id,
            ]
            item_ids = [i for i in item_ids if i]

            if item_ids:
                items_result = await session.execute(
                    select(ShopItem).where(ShopItem.id.in_(item_ids))
                )
                items = {str(item.id): item.to_dict() for item in items_result.scalars().all()}

                response["face_item"] = items.get(str(config.face_item_id)) if config.face_item_id else None
                response["hair_item"] = items.get(str(config.hair_item_id)) if config.hair_item_id else None
                response["outfit_item"] = items.get(str(config.outfit_item_id)) if config.outfit_item_id else None
                response["accessory_item"] = items.get(str(config.accessory_item_id)) if config.accessory_item_id else None
            else:
                response["face_item"] = None
                response["hair_item"] = None
                response["outfit_item"] = None
                response["accessory_item"] = None

            return response

    async def update_avatar_config(
        self,
        user_id: str,
        face_item_id: Optional[str] = None,
        hair_item_id: Optional[str] = None,
        outfit_item_id: Optional[str] = None,
        accessory_item_id: Optional[str] = None,
        skin_color: Optional[str] = None,
    ) -> dict:
        """Update user's avatar configuration"""
        async with get_db_session() as session:
            result = await session.execute(
                select(UserAvatarConfig).where(UserAvatarConfig.user_id == user_id)
            )
            config = result.scalar_one_or_none()

            if not config:
                config = UserAvatarConfig(
                    id=uuid4(),
                    user_id=user_id,
                )
                session.add(config)

            if face_item_id is not None:
                config.face_item_id = face_item_id if face_item_id else None
            if hair_item_id is not None:
                config.hair_item_id = hair_item_id if hair_item_id else None
            if outfit_item_id is not None:
                config.outfit_item_id = outfit_item_id if outfit_item_id else None
            if accessory_item_id is not None:
                config.accessory_item_id = accessory_item_id if accessory_item_id else None
            if skin_color is not None:
                config.skin_color = skin_color

            await session.commit()
            await session.refresh(config)

            return await self.get_avatar_config(user_id)
