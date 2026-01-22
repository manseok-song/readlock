from fastapi import APIRouter

from .session_routes import router as session_router
from .stats_routes import router as stats_router

router = APIRouter()
router.include_router(session_router, prefix="/reading", tags=["reading"])
router.include_router(stats_router, prefix="/reading", tags=["stats"])
