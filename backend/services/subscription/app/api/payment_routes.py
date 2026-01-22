from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from shared.middleware.auth import get_current_user
from ..schemas.subscription_schemas import (
    PaymentMethodResponse,
    PaymentMethodCreateRequest,
    PaymentHistoryResponse,
    CoinPurchaseRequest,
)
from ..services.payment_service import PaymentService

router = APIRouter()


def get_payment_service() -> PaymentService:
    return PaymentService()


@router.get("/methods", response_model=List[PaymentMethodResponse])
async def get_payment_methods(
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """Get user's payment methods"""
    return await service.get_payment_methods(user_id=current_user.user_id)


@router.post("/methods", response_model=PaymentMethodResponse)
async def add_payment_method(
    data: PaymentMethodCreateRequest,
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """Add a new payment method"""
    result = await service.add_payment_method(
        user_id=current_user.user_id,
        payment_token=data.payment_token,
        set_default=data.set_default,
    )
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"],
        )
    return result["payment_method"]


@router.delete("/methods/{method_id}")
async def remove_payment_method(
    method_id: str,
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """Remove a payment method"""
    result = await service.remove_payment_method(
        user_id=current_user.user_id,
        method_id=method_id,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment method not found",
        )
    return {"status": "removed"}


@router.post("/methods/{method_id}/default")
async def set_default_payment_method(
    method_id: str,
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """Set a payment method as default"""
    result = await service.set_default_method(
        user_id=current_user.user_id,
        method_id=method_id,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment method not found",
        )
    return {"status": "set_default"}


@router.get("/history", response_model=List[PaymentHistoryResponse])
async def get_payment_history(
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """Get payment history"""
    return await service.get_payment_history(user_id=current_user.user_id)


@router.post("/coins/purchase")
async def purchase_coins(
    data: CoinPurchaseRequest,
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """Purchase coins with real money"""
    result = await service.purchase_coins(
        user_id=current_user.user_id,
        package_id=data.package_id,
        payment_method_id=data.payment_method_id,
    )
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"],
        )
    return result


@router.get("/coins/packages")
async def get_coin_packages(
    service: PaymentService = Depends(get_payment_service),
):
    """Get available coin packages"""
    return await service.get_coin_packages()
