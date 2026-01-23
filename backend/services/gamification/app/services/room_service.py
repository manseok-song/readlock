from typing import Optional, List
from uuid import uuid4

from sqlalchemy import select

from shared.core.database import get_db_session
from ..models.gamification import UserRoomLayout, ShopItem


class RoomService:
    """Service for room customization management"""

    async def get_room_layout(self, user_id: str) -> dict:
        """Get user's room layout with item details"""
        async with get_db_session() as session:
            result = await session.execute(
                select(UserRoomLayout).where(UserRoomLayout.user_id == user_id)
            )
            layout = result.scalar_one_or_none()

            if not layout:
                return {
                    "id": None,
                    "user_id": user_id,
                    "background_item_id": None,
                    "background_item": None,
                    "layout_data": {},
                    "furniture_items": [],
                    "bookshelf_books": [],
                }

            response = layout.to_dict()

            item_ids = []
            if layout.background_item_id:
                item_ids.append(layout.background_item_id)

            layout_data = layout.layout_data or {}
            for item_id in layout_data.keys():
                try:
                    item_ids.append(item_id)
                except ValueError:
                    pass

            furniture_items = []
            background_item = None

            if item_ids:
                items_result = await session.execute(
                    select(ShopItem).where(ShopItem.id.in_(item_ids))
                )
                items_map = {str(item.id): item.to_dict() for item in items_result.scalars().all()}

                if layout.background_item_id:
                    background_item = items_map.get(str(layout.background_item_id))

                for item_id in layout_data.keys():
                    if item_id in items_map:
                        item_data = items_map[item_id].copy()
                        item_data["position"] = layout_data[item_id]
                        furniture_items.append(item_data)

            response["background_item"] = background_item
            response["furniture_items"] = furniture_items
            return response

    async def update_room_layout(
        self,
        user_id: str,
        background_item_id: Optional[str] = None,
        layout_data: Optional[dict] = None,
    ) -> dict:
        """Update user's room layout"""
        async with get_db_session() as session:
            result = await session.execute(
                select(UserRoomLayout).where(UserRoomLayout.user_id == user_id)
            )
            layout = result.scalar_one_or_none()

            if not layout:
                layout = UserRoomLayout(
                    id=uuid4(),
                    user_id=user_id,
                )
                session.add(layout)

            if background_item_id is not None:
                layout.background_item_id = background_item_id if background_item_id else None

            if layout_data is not None:
                layout.layout_data = layout_data

            await session.commit()
            await session.refresh(layout)

            return await self.get_room_layout(user_id)

    async def update_bookshelf(self, user_id: str, book_ids: List[str]) -> dict:
        """Update books displayed on the bookshelf"""
        async with get_db_session() as session:
            result = await session.execute(
                select(UserRoomLayout).where(UserRoomLayout.user_id == user_id)
            )
            layout = result.scalar_one_or_none()

            if not layout:
                layout = UserRoomLayout(
                    id=uuid4(),
                    user_id=user_id,
                    bookshelf_books=book_ids,
                )
                session.add(layout)
            else:
                layout.bookshelf_books = book_ids

            await session.commit()
            await session.refresh(layout)

            return await self.get_room_layout(user_id)
