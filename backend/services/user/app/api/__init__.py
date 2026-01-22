from fastapi import APIRouter

from .user_routes import router as user_router
from .profile_routes import router as profile_router
from .follow_routes import router as follow_router

router = APIRouter()
router.include_router(user_router, prefix="/users", tags=["users"])
router.include_router(profile_router, prefix="/profile", tags=["profile"])
router.include_router(follow_router, prefix="/social", tags=["social"])
