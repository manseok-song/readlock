from fastapi import APIRouter
from .recommendation_routes import router as recommendation_router

router = APIRouter()
router.include_router(recommendation_router, prefix="/recommendations", tags=["recommendations"])
