from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List

from shared.middleware.auth import get_current_user
from ..schemas.map_schemas import (
    BookstoreResponse,
    BookstoreListResponse,
    BookstoreDetailResponse,
    BookstoreReviewCreateRequest,
    BookstoreReviewResponse,
)
from ..services.bookstore_service import BookstoreService

router = APIRouter()


def get_bookstore_service() -> BookstoreService:
    return BookstoreService()


@router.get("/nearby", response_model=BookstoreListResponse)
async def get_nearby_bookstores(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius: float = Query(5.0, ge=0.1, le=50),  # km
    types: Optional[List[str]] = Query(None),  # independent, chain, used
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    bookstore_service: BookstoreService = Depends(get_bookstore_service),
):
    """Get nearby bookstores within radius"""
    return await bookstore_service.get_nearby(
        latitude=latitude,
        longitude=longitude,
        radius_km=radius,
        types=types,
        user_id=current_user.user_id,
        page=page,
        page_size=page_size,
    )


@router.get("/search", response_model=BookstoreListResponse)
async def search_bookstores(
    query: str = Query(..., min_length=1, max_length=100),
    latitude: Optional[float] = Query(None, ge=-90, le=90),
    longitude: Optional[float] = Query(None, ge=-180, le=180),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    bookstore_service: BookstoreService = Depends(get_bookstore_service),
):
    """Search bookstores by name or address"""
    return await bookstore_service.search(
        query=query,
        latitude=latitude,
        longitude=longitude,
        user_id=current_user.user_id,
        page=page,
        page_size=page_size,
    )


@router.get("/{bookstore_id}", response_model=BookstoreDetailResponse)
async def get_bookstore(
    bookstore_id: str,
    current_user: dict = Depends(get_current_user),
    bookstore_service: BookstoreService = Depends(get_bookstore_service),
):
    """Get bookstore details"""
    bookstore = await bookstore_service.get_by_id(
        bookstore_id=bookstore_id,
        user_id=current_user.user_id,
    )
    if not bookstore:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookstore not found",
        )
    return bookstore


@router.post("/{bookstore_id}/reviews", response_model=BookstoreReviewResponse)
async def create_review(
    bookstore_id: str,
    data: BookstoreReviewCreateRequest,
    current_user: dict = Depends(get_current_user),
    bookstore_service: BookstoreService = Depends(get_bookstore_service),
):
    """Create a bookstore review"""
    review = await bookstore_service.create_review(
        bookstore_id=bookstore_id,
        user_id=current_user.user_id,
        data=data,
    )
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookstore not found",
        )
    return review


@router.get("/{bookstore_id}/reviews", response_model=List[BookstoreReviewResponse])
async def get_reviews(
    bookstore_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    bookstore_service: BookstoreService = Depends(get_bookstore_service),
):
    """Get bookstore reviews"""
    return await bookstore_service.get_reviews(
        bookstore_id=bookstore_id,
        page=page,
        page_size=page_size,
    )


@router.post("/{bookstore_id}/favorite")
async def add_favorite(
    bookstore_id: str,
    current_user: dict = Depends(get_current_user),
    bookstore_service: BookstoreService = Depends(get_bookstore_service),
):
    """Add bookstore to favorites"""
    success = await bookstore_service.add_favorite(
        bookstore_id=bookstore_id,
        user_id=current_user.user_id,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookstore not found",
        )
    return {"status": "added"}


@router.delete("/{bookstore_id}/favorite")
async def remove_favorite(
    bookstore_id: str,
    current_user: dict = Depends(get_current_user),
    bookstore_service: BookstoreService = Depends(get_bookstore_service),
):
    """Remove bookstore from favorites"""
    await bookstore_service.remove_favorite(
        bookstore_id=bookstore_id,
        user_id=current_user.user_id,
    )
    return {"status": "removed"}


@router.get("/favorites/list", response_model=BookstoreListResponse)
async def get_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    bookstore_service: BookstoreService = Depends(get_bookstore_service),
):
    """Get user's favorite bookstores"""
    return await bookstore_service.get_favorites(
        user_id=current_user.user_id,
        page=page,
        page_size=page_size,
    )
