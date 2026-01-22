from typing import List, Optional
from datetime import datetime
from uuid import uuid4, UUID

from sqlalchemy import select

from shared.core.database import get_db_session
from ..models.gamification import ShopItem, UserInventory, UserCoins, CoinTransaction


class ShopService:
    """Service for shop and inventory management"""

    async def get_shop_items(self, category: Optional[str] = None) -> List[dict]:
        """Get available shop items"""
        async with get_db_session() as session:
            query = select(ShopItem).where(ShopItem.is_active == True)
            if category:
                query = query.where(ShopItem.category == category)

            query = query.order_by(ShopItem.category, ShopItem.price_coins)
            result = await session.execute(query)
            items = result.scalars().all()

            now = datetime.utcnow()
            return [
                item.to_dict()
                for item in items
                if not item.available_until or item.available_until > now
            ]

    async def get_user_inventory(self, user_id: str) -> List[dict]:
        """Get user's purchased items"""
        async with get_db_session() as session:
            result = await session.execute(
                select(UserInventory, ShopItem)
                .join(ShopItem, UserInventory.item_id == ShopItem.id)
                .where(UserInventory.user_id == user_id)
                .order_by(UserInventory.purchased_at.desc())
            )
            rows = result.all()

            return [
                {
                    "id": inv.id,
                    "item": item.to_dict(),
                    "purchased_at": inv.purchased_at,
                    "is_equipped": inv.is_equipped,
                }
                for inv, item in rows
            ]

    async def get_coin_balance(self, user_id: str) -> dict:
        """Get user's coin balance"""
        async with get_db_session() as session:
            result = await session.execute(
                select(UserCoins).where(UserCoins.user_id == user_id)
            )
            user_coins = result.scalar_one_or_none()

            if not user_coins:
                return {
                    "balance": 0,
                    "lifetime_earned": 0,
                    "lifetime_spent": 0,
                }

            return {
                "balance": user_coins.balance,
                "lifetime_earned": user_coins.lifetime_earned,
                "lifetime_spent": user_coins.lifetime_spent,
            }

    async def get_coin_history(
        self,
        user_id: str,
        page: int,
        page_size: int,
    ) -> List[dict]:
        """Get coin transaction history"""
        async with get_db_session() as session:
            result = await session.execute(
                select(CoinTransaction)
                .where(CoinTransaction.user_id == user_id)
                .order_by(CoinTransaction.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            transactions = result.scalars().all()

            return [
                {
                    "id": t.id,
                    "amount": t.amount,
                    "balance_after": t.balance_after,
                    "transaction_type": t.transaction_type,
                    "source": t.source,
                    "description": t.description or "",
                    "created_at": t.created_at,
                }
                for t in transactions
            ]

    async def purchase_item(self, user_id: str, item_id: str) -> dict:
        """Purchase an item from the shop"""
        async with get_db_session() as session:
            item_result = await session.execute(
                select(ShopItem).where(
                    ShopItem.id == item_id,
                    ShopItem.is_active == True,
                )
            )
            item = item_result.scalar_one_or_none()

            if not item:
                return {"success": False, "error": "Item not found"}

            if item.available_until and item.available_until < datetime.utcnow():
                return {"success": False, "error": "Item no longer available"}

            existing = await session.execute(
                select(UserInventory).where(
                    UserInventory.user_id == user_id,
                    UserInventory.item_id == item_id,
                )
            )
            if existing.scalar_one_or_none():
                return {"success": False, "error": "Item already owned"}

            coins_result = await session.execute(
                select(UserCoins).where(UserCoins.user_id == user_id)
            )
            user_coins = coins_result.scalar_one_or_none()

            if not user_coins:
                user_coins = UserCoins(
                    id=str(uuid4()),
                    user_id=user_id,
                    balance=0,
                    lifetime_earned=0,
                    lifetime_spent=0,
                )
                session.add(user_coins)

            if user_coins.balance < item.price_coins:
                return {
                    "success": False,
                    "error": "Insufficient coins",
                    "required": item.price_coins,
                    "current": user_coins.balance,
                }

            user_coins.balance -= item.price_coins
            user_coins.lifetime_spent += item.price_coins

            transaction = CoinTransaction(
                id=str(uuid4()),
                user_id=user_id,
                amount=-item.price_coins,
                balance_after=user_coins.balance,
                transaction_type="spend",
                source="shop",
                description=f"Purchased: {item.name}",
            )
            session.add(transaction)

            inventory_item = UserInventory(
                id=str(uuid4()),
                user_id=user_id,
                item_id=item_id,
            )
            session.add(inventory_item)

            await session.commit()

            return {
                "success": True,
                "item": item.to_dict(),
                "new_balance": user_coins.balance,
            }

    async def equip_item(self, user_id: str, item_id: str) -> bool:
        """Equip an item from inventory"""
        async with get_db_session() as session:
            result = await session.execute(
                select(UserInventory, ShopItem)
                .join(ShopItem, UserInventory.item_id == ShopItem.id)
                .where(
                    UserInventory.user_id == user_id,
                    UserInventory.item_id == item_id,
                )
            )
            row = result.one_or_none()

            if not row:
                return False

            inv_item, shop_item = row

            unequip_result = await session.execute(
                select(UserInventory)
                .join(ShopItem, UserInventory.item_id == ShopItem.id)
                .where(
                    UserInventory.user_id == user_id,
                    UserInventory.is_equipped == True,
                    ShopItem.category == shop_item.category,
                    ShopItem.subcategory == shop_item.subcategory,
                )
            )
            for other_inv in unequip_result.scalars().all():
                other_inv.is_equipped = False

            inv_item.is_equipped = True
            await session.commit()
            return True

    async def unequip_item(self, user_id: str, item_id: str) -> None:
        """Unequip an item"""
        async with get_db_session() as session:
            result = await session.execute(
                select(UserInventory).where(
                    UserInventory.user_id == user_id,
                    UserInventory.item_id == item_id,
                )
            )
            inv_item = result.scalar_one_or_none()

            if inv_item:
                inv_item.is_equipped = False
                await session.commit()
