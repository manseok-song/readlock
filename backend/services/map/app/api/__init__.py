from fastapi import APIRouter

from .bookstore_routes import router as bookstore_router
from .checkin_routes import router as checkin_router

router = APIRouter()
router.include_router(bookstore_router, prefix="/bookstores", tags=["bookstores"])
router.include_router(checkin_router, prefix="/checkins", tags=["checkins"])
