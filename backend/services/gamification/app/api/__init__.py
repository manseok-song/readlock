from fastapi import APIRouter
from .badge_routes import router as badge_router
from .level_routes import router as level_router
from .shop_routes import router as shop_router
from .leaderboard_routes import router as leaderboard_router

router = APIRouter()
router.include_router(badge_router, prefix="/badges", tags=["badges"])
router.include_router(level_router, prefix="/levels", tags=["levels"])
router.include_router(shop_router, prefix="/shop", tags=["shop"])
router.include_router(leaderboard_router, prefix="/leaderboard", tags=["leaderboard"])
