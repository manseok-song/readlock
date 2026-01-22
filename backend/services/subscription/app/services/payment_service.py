from typing import Optional, List
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select

from shared.core.database import get_db_session
from ..models.subscription import PaymentMethod, Payment, CoinPackage


class PaymentService:
    """Service for payment management"""

    COIN_PACKAGES = [
        {"id": "coins_100", "name": "100 Coins", "coins": 100, "bonus_coins": 0, "price": 1000, "is_best_value": False},
        {"id": "coins_500", "name": "500 Coins", "coins": 500, "bonus_coins": 50, "price": 4500, "is_best_value": False},
        {"id": "coins_1000", "name": "1000 Coins", "coins": 1000, "bonus_coins": 150, "price": 8000, "is_best_value": True},
        {"id": "coins_3000", "name": "3000 Coins", "coins": 3000, "bonus_coins": 600, "price": 22000, "is_best_value": False},
    ]

    async def get_payment_methods(self, user_id: str) -> List[dict]:
        """Get user's payment methods"""
        async with get_db_session() as session:
            result = await session.execute(
                select(PaymentMethod)
                .where(PaymentMethod.user_id == user_id)
                .order_by(PaymentMethod.is_default.desc(), PaymentMethod.created_at.desc())
            )
            methods = result.scalars().all()
            return [m.to_dict() for m in methods]

    async def add_payment_method(
        self,
        user_id: str,
        payment_token: str,
        set_default: bool = True,
    ) -> dict:
        """Add a new payment method"""
        async with get_db_session() as session:
            # TODO: Create payment method in Stripe
            # For now, create a mock entry

            if set_default:
                existing = await session.execute(
                    select(PaymentMethod).where(
                        PaymentMethod.user_id == user_id,
                        PaymentMethod.is_default == True,
                    )
                )
                for method in existing.scalars().all():
                    method.is_default = False

            payment_method = PaymentMethod(
                id=str(uuid4()),
                user_id=user_id,
                type="card",
                last4="4242",
                brand="Visa",
                exp_month=12,
                exp_year=2025,
                is_default=set_default,
            )
            session.add(payment_method)
            await session.commit()

            return {
                "success": True,
                "payment_method": payment_method.to_dict(),
            }

    async def remove_payment_method(
        self,
        user_id: str,
        method_id: str,
    ) -> bool:
        """Remove a payment method"""
        async with get_db_session() as session:
            result = await session.execute(
                select(PaymentMethod).where(
                    PaymentMethod.id == method_id,
                    PaymentMethod.user_id == user_id,
                )
            )
            method = result.scalar_one_or_none()

            if not method:
                return False

            # TODO: Remove from Stripe

            await session.delete(method)
            await session.commit()
            return True

    async def set_default_method(
        self,
        user_id: str,
        method_id: str,
    ) -> bool:
        """Set a payment method as default"""
        async with get_db_session() as session:
            result = await session.execute(
                select(PaymentMethod).where(
                    PaymentMethod.id == method_id,
                    PaymentMethod.user_id == user_id,
                )
            )
            method = result.scalar_one_or_none()

            if not method:
                return False

            other_methods = await session.execute(
                select(PaymentMethod).where(
                    PaymentMethod.user_id == user_id,
                    PaymentMethod.is_default == True,
                )
            )
            for other in other_methods.scalars().all():
                other.is_default = False

            method.is_default = True

            # TODO: Update default in Stripe

            await session.commit()
            return True

    async def get_payment_history(self, user_id: str) -> List[dict]:
        """Get payment history"""
        async with get_db_session() as session:
            result = await session.execute(
                select(Payment)
                .where(Payment.user_id == user_id)
                .order_by(Payment.created_at.desc())
                .limit(50)
            )
            payments = result.scalars().all()
            return [p.to_dict() for p in payments]

    async def get_coin_packages(self) -> List[dict]:
        """Get available coin packages"""
        async with get_db_session() as session:
            result = await session.execute(
                select(CoinPackage).where(CoinPackage.is_active == True)
            )
            packages = result.scalars().all()

            if not packages:
                return self.COIN_PACKAGES

            return [p.to_dict() for p in packages]

    async def purchase_coins(
        self,
        user_id: str,
        package_id: str,
        payment_method_id: Optional[str] = None,
    ) -> dict:
        """Purchase coins with real money"""
        async with get_db_session() as session:
            package = next((p for p in self.COIN_PACKAGES if p["id"] == package_id), None)
            if not package:
                return {"success": False, "error": "Package not found"}

            # TODO: Process payment via Stripe
            # TODO: Add coins to user's account via gamification service

            payment = Payment(
                id=str(uuid4()),
                user_id=user_id,
                amount=package["price"],
                status="succeeded",
                description=f"Coin purchase: {package['name']}",
                payment_method_id=payment_method_id,
                payment_metadata={"package_id": package_id, "coins": package["coins"], "bonus": package["bonus_coins"]},
            )
            session.add(payment)
            await session.commit()

            return {
                "success": True,
                "coins_added": package["coins"] + package["bonus_coins"],
                "payment_id": payment.id,
            }
