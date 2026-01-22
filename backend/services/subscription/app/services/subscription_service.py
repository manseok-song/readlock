from typing import Optional, List
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import select

from shared.core.database import get_db_session
from ..models.subscription import Plan, Subscription, PaymentMethod


class SubscriptionService:
    """Service for subscription management"""

    PLANS = [
        {
            "id": "free",
            "name": "Free",
            "description": "Basic reading features",
            "price_monthly": 0,
            "price_yearly": 0,
            "features": [
                {"id": "basic_reading", "name": "Basic Reading Mode", "description": "Phone lock reading", "included": True},
                {"id": "library", "name": "Personal Library", "description": "Up to 50 books", "included": True},
                {"id": "stats", "name": "Reading Statistics", "description": "Basic stats", "included": True},
                {"id": "ai_recommendations", "name": "AI Recommendations", "description": "Personalized suggestions", "included": False},
                {"id": "advanced_stats", "name": "Advanced Statistics", "description": "Detailed analytics", "included": False},
                {"id": "custom_avatar", "name": "Custom Avatar", "description": "Full customization", "included": False},
            ],
            "is_popular": False,
            "trial_days": 0,
        },
        {
            "id": "premium",
            "name": "Premium",
            "description": "Enhanced reading experience",
            "price_monthly": 4900,
            "price_yearly": 49000,
            "features": [
                {"id": "basic_reading", "name": "Basic Reading Mode", "description": "Phone lock reading", "included": True},
                {"id": "library", "name": "Personal Library", "description": "Unlimited books", "included": True},
                {"id": "stats", "name": "Reading Statistics", "description": "Basic stats", "included": True},
                {"id": "ai_recommendations", "name": "AI Recommendations", "description": "Personalized suggestions", "included": True},
                {"id": "advanced_stats", "name": "Advanced Statistics", "description": "Detailed analytics", "included": True},
                {"id": "custom_avatar", "name": "Custom Avatar", "description": "Full customization", "included": False},
            ],
            "is_popular": True,
            "trial_days": 7,
        },
        {
            "id": "premium_plus",
            "name": "Premium+",
            "description": "Ultimate reading experience",
            "price_monthly": 7900,
            "price_yearly": 79000,
            "features": [
                {"id": "basic_reading", "name": "Basic Reading Mode", "description": "Phone lock reading", "included": True},
                {"id": "library", "name": "Personal Library", "description": "Unlimited books", "included": True},
                {"id": "stats", "name": "Reading Statistics", "description": "Basic stats", "included": True},
                {"id": "ai_recommendations", "name": "AI Recommendations", "description": "Personalized suggestions", "included": True},
                {"id": "advanced_stats", "name": "Advanced Statistics", "description": "Detailed analytics", "included": True},
                {"id": "custom_avatar", "name": "Custom Avatar", "description": "Full customization", "included": True},
                {"id": "bonus_coins", "name": "Monthly Coins", "description": "100 bonus coins/month", "included": True},
                {"id": "exclusive_items", "name": "Exclusive Items", "description": "Premium shop items", "included": True},
            ],
            "is_popular": False,
            "trial_days": 7,
        },
    ]

    async def get_plans(self) -> List[dict]:
        """Get available subscription plans"""
        async with get_db_session() as session:
            result = await session.execute(
                select(Plan).where(Plan.is_active == True)
            )
            plans = result.scalars().all()

            if not plans:
                return self.PLANS

            return [p.to_dict() for p in plans]

    async def get_user_subscription(self, user_id: str) -> Optional[dict]:
        """Get user's current subscription"""
        async with get_db_session() as session:
            result = await session.execute(
                select(Subscription, Plan)
                .join(Plan, Subscription.plan_id == Plan.id)
                .where(Subscription.user_id == user_id)
            )
            row = result.one_or_none()

            if not row:
                return None

            subscription, plan = row
            return {
                "id": subscription.id,
                "plan": plan.to_dict(),
                "status": subscription.status,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "trial_end": subscription.trial_end,
            }

    async def create_subscription(
        self,
        user_id: str,
        plan_id: str,
        payment_method_id: Optional[str] = None,
        billing_cycle: str = "monthly",
    ) -> dict:
        """Create a new subscription"""
        async with get_db_session() as session:
            existing = await session.execute(
                select(Subscription).where(
                    Subscription.user_id == user_id,
                    Subscription.status.in_(["active", "trialing"]),
                )
            )
            if existing.scalar_one_or_none():
                return {"success": False, "error": "Already has active subscription"}

            plan_result = await session.execute(
                select(Plan).where(Plan.id == plan_id, Plan.is_active == True)
            )
            plan = plan_result.scalar_one_or_none()

            if not plan:
                plan_def = next((p for p in self.PLANS if p["id"] == plan_id), None)
                if not plan_def:
                    return {"success": False, "error": "Plan not found"}

                plan = Plan(
                    id=plan_def["id"],
                    name=plan_def["name"],
                    description=plan_def["description"],
                    price_monthly=plan_def["price_monthly"],
                    price_yearly=plan_def["price_yearly"],
                    features=plan_def["features"],
                    is_popular=plan_def["is_popular"],
                    trial_days=plan_def["trial_days"],
                )
                session.add(plan)

            now = datetime.utcnow()
            trial_end = None
            status = "active"

            if plan.trial_days > 0:
                trial_end = now + timedelta(days=plan.trial_days)
                status = "trialing"

            if billing_cycle == "yearly":
                period_end = now + timedelta(days=365)
            else:
                period_end = now + timedelta(days=30)

            subscription = Subscription(
                id=str(uuid4()),
                user_id=user_id,
                plan_id=plan.id,
                status=status,
                billing_cycle=billing_cycle,
                current_period_start=now,
                current_period_end=period_end,
                trial_end=trial_end,
            )
            session.add(subscription)

            # TODO: Create Stripe subscription

            await session.commit()

            return {
                "success": True,
                "subscription": {
                    "id": subscription.id,
                    "plan": plan.to_dict(),
                    "status": subscription.status,
                    "current_period_start": subscription.current_period_start,
                    "current_period_end": subscription.current_period_end,
                    "cancel_at_period_end": subscription.cancel_at_period_end,
                    "trial_end": subscription.trial_end,
                },
            }

    async def cancel_subscription(self, user_id: str) -> bool:
        """Cancel subscription at period end"""
        async with get_db_session() as session:
            result = await session.execute(
                select(Subscription).where(
                    Subscription.user_id == user_id,
                    Subscription.status.in_(["active", "trialing"]),
                )
            )
            subscription = result.scalar_one_or_none()

            if not subscription:
                return False

            subscription.cancel_at_period_end = True
            subscription.cancelled_at = datetime.utcnow()

            # TODO: Cancel in Stripe

            await session.commit()
            return True

    async def resume_subscription(self, user_id: str) -> bool:
        """Resume a cancelled subscription"""
        async with get_db_session() as session:
            result = await session.execute(
                select(Subscription).where(
                    Subscription.user_id == user_id,
                    Subscription.cancel_at_period_end == True,
                )
            )
            subscription = result.scalar_one_or_none()

            if not subscription:
                return False

            if subscription.current_period_end < datetime.utcnow():
                return False

            subscription.cancel_at_period_end = False
            subscription.cancelled_at = None

            # TODO: Resume in Stripe

            await session.commit()
            return True

    async def change_plan(self, user_id: str, new_plan_id: str) -> dict:
        """Change subscription plan"""
        async with get_db_session() as session:
            result = await session.execute(
                select(Subscription).where(
                    Subscription.user_id == user_id,
                    Subscription.status.in_(["active", "trialing"]),
                )
            )
            subscription = result.scalar_one_or_none()

            if not subscription:
                return {"success": False, "error": "No active subscription"}

            if subscription.plan_id == new_plan_id:
                return {"success": False, "error": "Already on this plan"}

            plan_result = await session.execute(
                select(Plan).where(Plan.id == new_plan_id, Plan.is_active == True)
            )
            new_plan = plan_result.scalar_one_or_none()

            if not new_plan:
                return {"success": False, "error": "Plan not found"}

            old_plan_id = subscription.plan_id
            subscription.plan_id = new_plan_id

            # TODO: Update in Stripe with proration

            await session.commit()

            return {
                "success": True,
                "old_plan_id": old_plan_id,
                "new_plan_id": new_plan_id,
                "effective_date": datetime.utcnow(),
            }

    async def get_user_features(self, user_id: str) -> dict:
        """Get features available to user based on subscription"""
        subscription = await self.get_user_subscription(user_id)

        if not subscription or subscription["status"] not in ["active", "trialing"]:
            free_plan = next((p for p in self.PLANS if p["id"] == "free"), None)
            return {
                "plan": "free",
                "features": {f["id"]: f["included"] for f in free_plan["features"]},
            }

        return {
            "plan": subscription["plan"]["id"],
            "features": {
                f["id"]: f["included"]
                for f in subscription["plan"]["features"]
            },
        }
