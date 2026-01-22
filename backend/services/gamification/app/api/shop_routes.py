from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional

from shared.middleware.auth import get_current_user
from ..schemas.gamification_schemas import (
    ShopItemResponse,
    UserInventoryResponse,
    CoinBalanceResponse,
    CoinHistoryResponse,
    PurchaseRequest,
)
from ..services.shop_service import ShopService

router = APIRouter()


def get_shop_service() -> ShopService:
    return ShopService()


@router.get("/items", response_model=List[ShopItemResponse])
async def get_shop_items(
    category: Optional[str] = Query(None),
    service: ShopService = Depends(get_shop_service),
):
    """Get available shop items"""
    return await service.get_shop_items(category=category)


@router.get("/inventory", response_model=List[UserInventoryResponse])
async def get_my_inventory(
    current_user: dict = Depends(get_current_user),
    service: ShopService = Depends(get_shop_service),
):
    """Get user's purchased items"""
    return await service.get_user_inventory(user_id=current_user.user_id)


@router.get("/coins", response_model=CoinBalanceResponse)
async def get_coin_balance(
    current_user: dict = Depends(get_current_user),
    service: ShopService = Depends(get_shop_service),
):
    """Get user's coin balance"""
    return await service.get_coin_balance(user_id=current_user.user_id)


@router.get("/coins/history", response_model=List[CoinHistoryResponse])
async def get_coin_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    service: ShopService = Depends(get_shop_service),
):
    """Get coin transaction history"""
    return await service.get_coin_history(
        user_id=current_user.user_id,
        page=page,
        page_size=page_size,
    )


@router.post("/purchase")
async def purchase_item(
    data: PurchaseRequest,
    current_user: dict = Depends(get_current_user),
    service: ShopService = Depends(get_shop_service),
):
    """Purchase an item from the shop"""
    result = await service.purchase_item(
        user_id=current_user.user_id,
        item_id=data.item_id,
    )
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"],
        )
    return result


@router.post("/equip/{item_id}")
async def equip_item(
    item_id: str,
    current_user: dict = Depends(get_current_user),
    service: ShopService = Depends(get_shop_service),
):
    """Equip an item from inventory"""
    result = await service.equip_item(
        user_id=current_user.user_id,
        item_id=item_id,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item not found in inventory",
        )
    return {"status": "equipped", "item_id": item_id}


@router.post("/unequip/{item_id}")
async def unequip_item(
    item_id: str,
    current_user: dict = Depends(get_current_user),
    service: ShopService = Depends(get_shop_service),
):
    """Unequip an item"""
    await service.unequip_item(
        user_id=current_user.user_id,
        item_id=item_id,
    )
    return {"status": "unequipped", "item_id": item_id}
