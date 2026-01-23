from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import select

from shared.middleware.auth import get_current_user
from shared.core.database import get_db_session
from ..schemas.gamification_schemas import (
    ShopItemResponse,
    UserInventoryResponse,
    CoinBalanceResponse,
    CoinHistoryResponse,
    PurchaseRequest,
)
from ..services.shop_service import ShopService
from ..models.gamification import ShopItem

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


@router.post("/seed-pixel-items")
async def seed_pixel_items():
    """Seed pixel art avatar and room items"""
    pixel_items = [
        # Avatar Face items
        {
            "name": "기본 얼굴",
            "description": "기본 픽셀아트 얼굴",
            "category": "avatar",
            "subcategory": "face",
            "price_coins": 0,
            "required_level": 1,
            "preview_url": "/assets/avatar/face_default.png",
            "asset_data": {
                "type": "avatar_face",
                "pixelSize": 4,
                "width": 16,
                "height": 16,
                "layers": [
                    {
                        "name": "base",
                        "zIndex": 0,
                        "pixels": [
                            {"x": 4, "y": 4, "color": "skin"},
                            {"x": 5, "y": 4, "color": "skin"},
                            {"x": 6, "y": 4, "color": "skin"},
                            {"x": 7, "y": 4, "color": "skin"},
                            {"x": 8, "y": 4, "color": "skin"},
                            {"x": 9, "y": 4, "color": "skin"},
                            {"x": 10, "y": 4, "color": "skin"},
                            {"x": 11, "y": 4, "color": "skin"},
                            {"x": 3, "y": 5, "color": "skin"},
                            {"x": 4, "y": 5, "color": "skin"},
                            {"x": 5, "y": 5, "color": "skin"},
                            {"x": 6, "y": 5, "color": "skin"},
                            {"x": 7, "y": 5, "color": "skin"},
                            {"x": 8, "y": 5, "color": "skin"},
                            {"x": 9, "y": 5, "color": "skin"},
                            {"x": 10, "y": 5, "color": "skin"},
                            {"x": 11, "y": 5, "color": "skin"},
                            {"x": 12, "y": 5, "color": "skin"},
                            {"x": 3, "y": 6, "color": "skin"},
                            {"x": 4, "y": 6, "color": "skin"},
                            {"x": 5, "y": 6, "color": "#000000"},
                            {"x": 6, "y": 6, "color": "skin"},
                            {"x": 7, "y": 6, "color": "skin"},
                            {"x": 8, "y": 6, "color": "skin"},
                            {"x": 9, "y": 6, "color": "skin"},
                            {"x": 10, "y": 6, "color": "#000000"},
                            {"x": 11, "y": 6, "color": "skin"},
                            {"x": 12, "y": 6, "color": "skin"},
                            {"x": 3, "y": 7, "color": "skin"},
                            {"x": 4, "y": 7, "color": "skin"},
                            {"x": 5, "y": 7, "color": "skin"},
                            {"x": 6, "y": 7, "color": "skin"},
                            {"x": 7, "y": 7, "color": "skin"},
                            {"x": 8, "y": 7, "color": "skin"},
                            {"x": 9, "y": 7, "color": "skin"},
                            {"x": 10, "y": 7, "color": "skin"},
                            {"x": 11, "y": 7, "color": "skin"},
                            {"x": 12, "y": 7, "color": "skin"},
                            {"x": 4, "y": 8, "color": "skin"},
                            {"x": 5, "y": 8, "color": "skin"},
                            {"x": 6, "y": 8, "color": "skin"},
                            {"x": 7, "y": 8, "color": "#FF9999"},
                            {"x": 8, "y": 8, "color": "#FF9999"},
                            {"x": 9, "y": 8, "color": "skin"},
                            {"x": 10, "y": 8, "color": "skin"},
                            {"x": 11, "y": 8, "color": "skin"},
                            {"x": 5, "y": 9, "color": "skin"},
                            {"x": 6, "y": 9, "color": "#E88888"},
                            {"x": 7, "y": 9, "color": "skin"},
                            {"x": 8, "y": 9, "color": "skin"},
                            {"x": 9, "y": 9, "color": "#E88888"},
                            {"x": 10, "y": 9, "color": "skin"},
                            {"x": 6, "y": 10, "color": "skin"},
                            {"x": 7, "y": 10, "color": "skin"},
                            {"x": 8, "y": 10, "color": "skin"},
                            {"x": 9, "y": 10, "color": "skin"},
                        ],
                    }
                ],
            },
        },
        {
            "name": "동그란 얼굴",
            "description": "귀여운 동그란 픽셀아트 얼굴",
            "category": "avatar",
            "subcategory": "face",
            "price_coins": 0,
            "required_level": 1,
            "preview_url": "/assets/avatar/face_round.png",
            "asset_data": {"type": "avatar_face", "variant": "round", "pixelSize": 4, "width": 16, "height": 16},
        },
        {
            "name": "각진 얼굴",
            "description": "시크한 각진 픽셀아트 얼굴",
            "category": "avatar",
            "subcategory": "face",
            "price_coins": 0,
            "required_level": 1,
            "preview_url": "/assets/avatar/face_angular.png",
            "asset_data": {"type": "avatar_face", "variant": "angular", "pixelSize": 4, "width": 16, "height": 16},
        },
        {
            "name": "부드러운 얼굴",
            "description": "온화한 느낌의 픽셀아트 얼굴",
            "category": "avatar",
            "subcategory": "face",
            "price_coins": 0,
            "required_level": 1,
            "preview_url": "/assets/avatar/face_soft.png",
            "asset_data": {"type": "avatar_face", "variant": "soft", "pixelSize": 4, "width": 16, "height": 16},
        },
        # Avatar Hair items
        {
            "name": "단발머리",
            "description": "깔끔한 단발머리 스타일",
            "category": "avatar",
            "subcategory": "hair",
            "price_coins": 0,
            "required_level": 1,
            "preview_url": "/assets/avatar/hair_bob.png",
            "asset_data": {
                "type": "avatar_hair",
                "pixelSize": 4,
                "width": 16,
                "height": 16,
                "layers": [
                    {
                        "name": "hair",
                        "zIndex": 1,
                        "pixels": [
                            {"x": 5, "y": 2, "color": "#3D2314"},
                            {"x": 6, "y": 2, "color": "#3D2314"},
                            {"x": 7, "y": 2, "color": "#3D2314"},
                            {"x": 8, "y": 2, "color": "#3D2314"},
                            {"x": 9, "y": 2, "color": "#3D2314"},
                            {"x": 10, "y": 2, "color": "#3D2314"},
                            {"x": 4, "y": 3, "color": "#3D2314"},
                            {"x": 5, "y": 3, "color": "#5C3A21"},
                            {"x": 6, "y": 3, "color": "#5C3A21"},
                            {"x": 7, "y": 3, "color": "#5C3A21"},
                            {"x": 8, "y": 3, "color": "#5C3A21"},
                            {"x": 9, "y": 3, "color": "#5C3A21"},
                            {"x": 10, "y": 3, "color": "#5C3A21"},
                            {"x": 11, "y": 3, "color": "#3D2314"},
                            {"x": 3, "y": 4, "color": "#3D2314"},
                            {"x": 4, "y": 4, "color": "#5C3A21"},
                            {"x": 11, "y": 4, "color": "#5C3A21"},
                            {"x": 12, "y": 4, "color": "#3D2314"},
                            {"x": 2, "y": 5, "color": "#3D2314"},
                            {"x": 3, "y": 5, "color": "#5C3A21"},
                            {"x": 12, "y": 5, "color": "#5C3A21"},
                            {"x": 13, "y": 5, "color": "#3D2314"},
                            {"x": 2, "y": 6, "color": "#3D2314"},
                            {"x": 3, "y": 6, "color": "#5C3A21"},
                            {"x": 12, "y": 6, "color": "#5C3A21"},
                            {"x": 13, "y": 6, "color": "#3D2314"},
                            {"x": 2, "y": 7, "color": "#3D2314"},
                            {"x": 13, "y": 7, "color": "#3D2314"},
                        ],
                    }
                ],
            },
        },
        {
            "name": "긴 생머리",
            "description": "자연스러운 긴 생머리",
            "category": "avatar",
            "subcategory": "hair",
            "price_coins": 0,
            "required_level": 1,
            "preview_url": "/assets/avatar/hair_long.png",
            "asset_data": {"type": "avatar_hair", "variant": "long_straight", "pixelSize": 4, "width": 16, "height": 20},
        },
        {
            "name": "긴 웨이브",
            "description": "우아한 웨이브 스타일",
            "category": "avatar",
            "subcategory": "hair",
            "price_coins": 100,
            "required_level": 3,
            "preview_url": "/assets/avatar/hair_wave.png",
            "asset_data": {"type": "avatar_hair", "variant": "long_wave", "pixelSize": 4, "width": 16, "height": 20},
        },
        {
            "name": "포니테일",
            "description": "활동적인 포니테일 스타일",
            "category": "avatar",
            "subcategory": "hair",
            "price_coins": 100,
            "required_level": 3,
            "preview_url": "/assets/avatar/hair_ponytail.png",
            "asset_data": {"type": "avatar_hair", "variant": "ponytail", "pixelSize": 4, "width": 16, "height": 18},
        },
        {
            "name": "숏컷",
            "description": "시원한 숏컷 스타일",
            "category": "avatar",
            "subcategory": "hair",
            "price_coins": 150,
            "required_level": 5,
            "preview_url": "/assets/avatar/hair_short.png",
            "asset_data": {"type": "avatar_hair", "variant": "short", "pixelSize": 4, "width": 16, "height": 14},
        },
        {
            "name": "댄디컷",
            "description": "세련된 댄디컷 스타일",
            "category": "avatar",
            "subcategory": "hair",
            "price_coins": 150,
            "required_level": 5,
            "preview_url": "/assets/avatar/hair_dandy.png",
            "asset_data": {"type": "avatar_hair", "variant": "dandy", "pixelSize": 4, "width": 16, "height": 14},
        },
        # Avatar Outfit items
        {
            "name": "캐주얼 티셔츠",
            "description": "편안한 캐주얼 티셔츠",
            "category": "avatar",
            "subcategory": "outfit",
            "price_coins": 0,
            "required_level": 1,
            "preview_url": "/assets/avatar/outfit_tshirt.png",
            "asset_data": {
                "type": "avatar_outfit",
                "pixelSize": 4,
                "width": 16,
                "height": 12,
                "layers": [
                    {
                        "name": "outfit",
                        "zIndex": 2,
                        "pixels": [
                            {"x": 5, "y": 11, "color": "#4A90D9"},
                            {"x": 6, "y": 11, "color": "#4A90D9"},
                            {"x": 7, "y": 11, "color": "#4A90D9"},
                            {"x": 8, "y": 11, "color": "#4A90D9"},
                            {"x": 9, "y": 11, "color": "#4A90D9"},
                            {"x": 10, "y": 11, "color": "#4A90D9"},
                            {"x": 4, "y": 12, "color": "#4A90D9"},
                            {"x": 5, "y": 12, "color": "#5BA0E9"},
                            {"x": 6, "y": 12, "color": "#5BA0E9"},
                            {"x": 7, "y": 12, "color": "#5BA0E9"},
                            {"x": 8, "y": 12, "color": "#5BA0E9"},
                            {"x": 9, "y": 12, "color": "#5BA0E9"},
                            {"x": 10, "y": 12, "color": "#5BA0E9"},
                            {"x": 11, "y": 12, "color": "#4A90D9"},
                            {"x": 3, "y": 13, "color": "#4A90D9"},
                            {"x": 4, "y": 13, "color": "#5BA0E9"},
                            {"x": 5, "y": 13, "color": "#5BA0E9"},
                            {"x": 6, "y": 13, "color": "#5BA0E9"},
                            {"x": 7, "y": 13, "color": "#5BA0E9"},
                            {"x": 8, "y": 13, "color": "#5BA0E9"},
                            {"x": 9, "y": 13, "color": "#5BA0E9"},
                            {"x": 10, "y": 13, "color": "#5BA0E9"},
                            {"x": 11, "y": 13, "color": "#5BA0E9"},
                            {"x": 12, "y": 13, "color": "#4A90D9"},
                        ],
                    }
                ],
            },
        },
        {
            "name": "기본 후드티",
            "description": "따뜻한 기본 후드티",
            "category": "avatar",
            "subcategory": "outfit",
            "price_coins": 0,
            "required_level": 1,
            "preview_url": "/assets/avatar/outfit_hoodie.png",
            "asset_data": {"type": "avatar_outfit", "variant": "hoodie", "pixelSize": 4, "width": 16, "height": 14},
        },
        {
            "name": "독서가 스웨터",
            "description": "아늑한 독서가 스웨터",
            "category": "avatar",
            "subcategory": "outfit",
            "price_coins": 150,
            "required_level": 5,
            "preview_url": "/assets/avatar/outfit_sweater.png",
            "asset_data": {"type": "avatar_outfit", "variant": "sweater", "pixelSize": 4, "width": 16, "height": 14},
        },
        {
            "name": "정장 셔츠",
            "description": "깔끔한 정장 셔츠",
            "category": "avatar",
            "subcategory": "outfit",
            "price_coins": 200,
            "required_level": 7,
            "preview_url": "/assets/avatar/outfit_shirt.png",
            "asset_data": {"type": "avatar_outfit", "variant": "dress_shirt", "pixelSize": 4, "width": 16, "height": 14},
        },
        {
            "name": "아늑한 가디건",
            "description": "포근한 가디건",
            "category": "avatar",
            "subcategory": "outfit",
            "price_coins": 180,
            "required_level": 6,
            "preview_url": "/assets/avatar/outfit_cardigan.png",
            "asset_data": {"type": "avatar_outfit", "variant": "cardigan", "pixelSize": 4, "width": 16, "height": 14},
        },
        # Avatar Accessory items
        {
            "name": "없음",
            "description": "악세서리 없음",
            "category": "avatar",
            "subcategory": "accessory",
            "price_coins": 0,
            "required_level": 1,
            "preview_url": "/assets/avatar/accessory_none.png",
            "asset_data": {"type": "avatar_accessory", "variant": "none"},
        },
        {
            "name": "둥근 안경",
            "description": "지적인 둥근 안경",
            "category": "avatar",
            "subcategory": "accessory",
            "price_coins": 80,
            "required_level": 2,
            "preview_url": "/assets/avatar/accessory_glasses_round.png",
            "asset_data": {
                "type": "avatar_accessory",
                "pixelSize": 4,
                "width": 16,
                "height": 8,
                "layers": [
                    {
                        "name": "accessory",
                        "zIndex": 3,
                        "pixels": [
                            {"x": 4, "y": 6, "color": "#2C2C2C"},
                            {"x": 5, "y": 6, "color": "#2C2C2C"},
                            {"x": 6, "y": 6, "color": "#2C2C2C"},
                            {"x": 7, "y": 6, "color": "#2C2C2C"},
                            {"x": 8, "y": 6, "color": "#2C2C2C"},
                            {"x": 9, "y": 6, "color": "#2C2C2C"},
                            {"x": 10, "y": 6, "color": "#2C2C2C"},
                            {"x": 11, "y": 6, "color": "#2C2C2C"},
                            {"x": 4, "y": 7, "color": "#2C2C2C"},
                            {"x": 6, "y": 7, "color": "#2C2C2C"},
                            {"x": 9, "y": 7, "color": "#2C2C2C"},
                            {"x": 11, "y": 7, "color": "#2C2C2C"},
                        ],
                    }
                ],
            },
        },
        {
            "name": "네모 안경",
            "description": "세련된 네모 안경",
            "category": "avatar",
            "subcategory": "accessory",
            "price_coins": 80,
            "required_level": 2,
            "preview_url": "/assets/avatar/accessory_glasses_square.png",
            "asset_data": {"type": "avatar_accessory", "variant": "glasses_square", "pixelSize": 4, "width": 16, "height": 8},
        },
        {
            "name": "헤드폰",
            "description": "멋진 헤드폰",
            "category": "avatar",
            "subcategory": "accessory",
            "price_coins": 120,
            "required_level": 4,
            "preview_url": "/assets/avatar/accessory_headphones.png",
            "asset_data": {"type": "avatar_accessory", "variant": "headphones", "pixelSize": 4, "width": 16, "height": 12},
        },
        # Room Background items
        {
            "name": "아늑한 서재",
            "description": "기본 아늑한 서재 배경",
            "category": "room",
            "subcategory": "background",
            "price_coins": 0,
            "required_level": 1,
            "preview_url": "/assets/room/bg_study.png",
            "asset_data": {
                "type": "room_background",
                "pixelSize": 4,
                "width": 80,
                "height": 60,
                "colors": {
                    "wall": "#E8D4B8",
                    "floor": "#8B6B4F",
                    "accent": "#654321",
                },
            },
        },
        {
            "name": "모던 스튜디오",
            "description": "깔끔한 모던 스튜디오",
            "category": "room",
            "subcategory": "background",
            "price_coins": 300,
            "required_level": 5,
            "preview_url": "/assets/room/bg_modern.png",
            "asset_data": {
                "type": "room_background",
                "variant": "modern",
                "pixelSize": 4,
                "width": 80,
                "height": 60,
                "colors": {"wall": "#F5F5F5", "floor": "#D3D3D3", "accent": "#4A4A4A"},
            },
        },
        {
            "name": "창가 카페",
            "description": "햇살 가득한 창가 카페",
            "category": "room",
            "subcategory": "background",
            "price_coins": 400,
            "required_level": 8,
            "preview_url": "/assets/room/bg_cafe.png",
            "asset_data": {
                "type": "room_background",
                "variant": "cafe",
                "pixelSize": 4,
                "width": 80,
                "height": 60,
                "colors": {"wall": "#FFF8E7", "floor": "#A0522D", "accent": "#8FBC8F"},
            },
        },
        {
            "name": "밤하늘 다락방",
            "description": "별이 빛나는 다락방",
            "category": "room",
            "subcategory": "background",
            "price_coins": 500,
            "required_level": 10,
            "preview_url": "/assets/room/bg_attic.png",
            "asset_data": {
                "type": "room_background",
                "variant": "attic",
                "pixelSize": 4,
                "width": 80,
                "height": 60,
                "colors": {"wall": "#1A1A2E", "floor": "#5D4E37", "accent": "#FFD700"},
            },
        },
        # Room Furniture items
        {
            "name": "나무 책장",
            "description": "책을 진열할 수 있는 나무 책장",
            "category": "room",
            "subcategory": "furniture",
            "price_coins": 0,
            "required_level": 1,
            "preview_url": "/assets/room/furniture_bookshelf.png",
            "asset_data": {
                "type": "room_furniture",
                "furnitureType": "bookshelf",
                "pixelSize": 4,
                "width": 24,
                "height": 40,
                "bookSlots": 10,
                "layers": [
                    {
                        "name": "frame",
                        "zIndex": 0,
                        "pixels": [
                            {"x": 0, "y": 0, "color": "#654321"},
                            {"x": 1, "y": 0, "color": "#8B6B4F"},
                            {"x": 2, "y": 0, "color": "#8B6B4F"},
                        ],
                    }
                ],
            },
        },
        {
            "name": "독서 책상",
            "description": "편안하게 책을 읽을 수 있는 책상",
            "category": "room",
            "subcategory": "furniture",
            "price_coins": 200,
            "required_level": 3,
            "preview_url": "/assets/room/furniture_desk.png",
            "asset_data": {
                "type": "room_furniture",
                "furnitureType": "desk",
                "pixelSize": 4,
                "width": 32,
                "height": 24,
            },
        },
        {
            "name": "안락 의자",
            "description": "포근한 안락 의자",
            "category": "room",
            "subcategory": "furniture",
            "price_coins": 150,
            "required_level": 2,
            "preview_url": "/assets/room/furniture_chair.png",
            "asset_data": {
                "type": "room_furniture",
                "furnitureType": "chair",
                "pixelSize": 4,
                "width": 16,
                "height": 20,
            },
        },
        {
            "name": "스탠드 조명",
            "description": "아늑한 분위기의 스탠드 조명",
            "category": "room",
            "subcategory": "furniture",
            "price_coins": 100,
            "required_level": 2,
            "preview_url": "/assets/room/furniture_lamp.png",
            "asset_data": {
                "type": "room_furniture",
                "furnitureType": "lamp",
                "pixelSize": 4,
                "width": 8,
                "height": 28,
            },
        },
        # Room Decoration items
        {
            "name": "화분",
            "description": "싱그러운 화분",
            "category": "room",
            "subcategory": "decoration",
            "price_coins": 50,
            "required_level": 1,
            "preview_url": "/assets/room/deco_plant.png",
            "asset_data": {
                "type": "room_decoration",
                "decorationType": "plant",
                "pixelSize": 4,
                "width": 8,
                "height": 16,
            },
        },
        {
            "name": "액자",
            "description": "아름다운 액자",
            "category": "room",
            "subcategory": "decoration",
            "price_coins": 80,
            "required_level": 2,
            "preview_url": "/assets/room/deco_frame.png",
            "asset_data": {
                "type": "room_decoration",
                "decorationType": "frame",
                "pixelSize": 4,
                "width": 12,
                "height": 16,
            },
        },
        {
            "name": "러그",
            "description": "포근한 러그",
            "category": "room",
            "subcategory": "decoration",
            "price_coins": 120,
            "required_level": 3,
            "preview_url": "/assets/room/deco_rug.png",
            "asset_data": {
                "type": "room_decoration",
                "decorationType": "rug",
                "pixelSize": 4,
                "width": 24,
                "height": 16,
            },
        },
    ]

    async with get_db_session() as session:
        existing = await session.execute(
            select(ShopItem).where(ShopItem.category.in_(["avatar", "room"]))
        )
        existing_names = {item.name for item in existing.scalars().all()}

        added = []
        for item_data in pixel_items:
            if item_data["name"] not in existing_names:
                item = ShopItem(
                    id=uuid4(),
                    name=item_data["name"],
                    description=item_data["description"],
                    category=item_data["category"],
                    subcategory=item_data["subcategory"],
                    price_coins=item_data["price_coins"],
                    required_level=item_data["required_level"],
                    preview_url=item_data["preview_url"],
                    asset_data=item_data["asset_data"],
                    is_active=True,
                )
                session.add(item)
                added.append(item_data["name"])

        await session.commit()

    return {
        "status": "success",
        "added_items": added,
        "total_added": len(added),
        "message": f"Added {len(added)} pixel art items to shop",
    }
