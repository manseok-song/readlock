from fastapi import APIRouter

from .book_routes import router as book_router

router = APIRouter()
router.include_router(book_router, prefix="/books", tags=["books"])
