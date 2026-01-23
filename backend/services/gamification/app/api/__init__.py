from fastapi import APIRouter
from .badge_routes import router as badge_router
from .level_routes import router as level_router
from .shop_routes import router as shop_router
from .leaderboard_routes import router as leaderboard_router
from .avatar_routes import router as avatar_router
from .room_routes import router as room_router

router = APIRouter()
router.include_router(badge_router, prefix="/badges", tags=["badges"])
router.include_router(level_router, prefix="/levels", tags=["levels"])
router.include_router(shop_router, prefix="/shop", tags=["shop"])
router.include_router(leaderboard_router, prefix="/leaderboard", tags=["leaderboard"])
router.include_router(avatar_router, prefix="/avatar", tags=["avatar"])
router.include_router(room_router, prefix="/room", tags=["room"])
