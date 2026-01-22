from fastapi import APIRouter

from .quote_routes import router as quote_router
from .review_routes import router as review_router
from .feed_routes import router as feed_router

router = APIRouter()
router.include_router(quote_router, prefix="/quotes", tags=["quotes"])
router.include_router(review_router, prefix="/reviews", tags=["reviews"])
router.include_router(feed_router, prefix="/feed", tags=["feed"])
