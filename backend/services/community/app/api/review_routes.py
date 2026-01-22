from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional

from shared.middleware.auth import get_current_user
from ..schemas.community_schemas import (
    ReviewCreateRequest,
    ReviewUpdateRequest,
    ReviewResponse,
    ReviewListResponse,
)
from ..services.review_service import ReviewService

router = APIRouter()


def get_review_service() -> ReviewService:
    return ReviewService()


@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    data: ReviewCreateRequest,
    current_user: dict = Depends(get_current_user),
    review_service: ReviewService = Depends(get_review_service),
):
    """Create a book review"""
    review = await review_service.create_review(
        user_id=current_user.user_id,
        data=data,
    )
    return review


@router.get("/", response_model=ReviewListResponse)
async def get_reviews(
    book_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    review_service: ReviewService = Depends(get_review_service),
):
    """Get reviews with optional filters"""
    return await review_service.get_reviews(
        book_id=book_id,
        user_id=user_id,
        viewer_id=current_user.user_id,
        page=page,
        page_size=page_size,
    )


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: str,
    current_user: dict = Depends(get_current_user),
    review_service: ReviewService = Depends(get_review_service),
):
    """Get review by ID"""
    review = await review_service.get_review_by_id(
        review_id=review_id,
        viewer_id=current_user.user_id,
    )
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )
    return review


@router.patch("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: str,
    data: ReviewUpdateRequest,
    current_user: dict = Depends(get_current_user),
    review_service: ReviewService = Depends(get_review_service),
):
    """Update a review"""
    review = await review_service.update_review(
        review_id=review_id,
        user_id=current_user.user_id,
        data=data,
    )
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found or not authorized",
        )
    return review


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: str,
    current_user: dict = Depends(get_current_user),
    review_service: ReviewService = Depends(get_review_service),
):
    """Delete a review"""
    success = await review_service.delete_review(
        review_id=review_id,
        user_id=current_user.user_id,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found or not authorized",
        )


@router.post("/{review_id}/like")
async def like_review(
    review_id: str,
    current_user: dict = Depends(get_current_user),
    review_service: ReviewService = Depends(get_review_service),
):
    """Like a review"""
    success = await review_service.like_review(
        review_id=review_id,
        user_id=current_user.user_id,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )
    return {"status": "liked"}


@router.delete("/{review_id}/like")
async def unlike_review(
    review_id: str,
    current_user: dict = Depends(get_current_user),
    review_service: ReviewService = Depends(get_review_service),
):
    """Unlike a review"""
    await review_service.unlike_review(
        review_id=review_id,
        user_id=current_user.user_id,
    )
    return {"status": "unliked"}


@router.post("/{review_id}/comments")
async def add_comment(
    review_id: str,
    content: str = Query(..., min_length=1, max_length=500),
    current_user: dict = Depends(get_current_user),
    review_service: ReviewService = Depends(get_review_service),
):
    """Add a comment to a review"""
    comment = await review_service.add_comment(
        review_id=review_id,
        user_id=current_user.user_id,
        content=content,
    )
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )
    return comment
