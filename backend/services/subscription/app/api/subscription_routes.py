from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from shared.middleware.auth import get_current_user
from ..schemas.subscription_schemas import (
    PlanResponse,
    SubscriptionResponse,
    SubscriptionCreateRequest,
)
from ..services.subscription_service import SubscriptionService

router = APIRouter()


def get_subscription_service() -> SubscriptionService:
    return SubscriptionService()


@router.get("/plans", response_model=List[PlanResponse])
async def get_plans(
    service: SubscriptionService = Depends(get_subscription_service),
):
    """Get available subscription plans"""
    return await service.get_plans()


@router.get("/me", response_model=SubscriptionResponse)
async def get_my_subscription(
    current_user: dict = Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service),
):
    """Get current user's subscription"""
    subscription = await service.get_user_subscription(user_id=current_user.user_id)
    if not subscription:
        return {
            "id": None,
            "plan": None,
            "status": "none",
            "current_period_start": None,
            "current_period_end": None,
            "cancel_at_period_end": False,
        }
    return subscription


@router.post("/subscribe", response_model=SubscriptionResponse)
async def create_subscription(
    data: SubscriptionCreateRequest,
    current_user: dict = Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service),
):
    """Create a new subscription"""
    result = await service.create_subscription(
        user_id=current_user.user_id,
        plan_id=data.plan_id,
        payment_method_id=data.payment_method_id,
    )
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"],
        )
    return result["subscription"]


@router.post("/cancel")
async def cancel_subscription(
    current_user: dict = Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service),
):
    """Cancel current subscription"""
    result = await service.cancel_subscription(user_id=current_user.user_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found",
        )
    return {"status": "cancelled", "cancel_at_period_end": True}


@router.post("/resume")
async def resume_subscription(
    current_user: dict = Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service),
):
    """Resume a cancelled subscription"""
    result = await service.resume_subscription(user_id=current_user.user_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot resume subscription",
        )
    return {"status": "resumed"}


@router.post("/change-plan")
async def change_plan(
    plan_id: str,
    current_user: dict = Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service),
):
    """Change subscription plan"""
    result = await service.change_plan(
        user_id=current_user.user_id,
        new_plan_id=plan_id,
    )
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"],
        )
    return result


@router.get("/features")
async def get_premium_features(
    current_user: dict = Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service),
):
    """Get user's available premium features"""
    return await service.get_user_features(user_id=current_user.user_id)
