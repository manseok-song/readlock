from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional

from shared.middleware.auth import get_current_user
from ..schemas.community_schemas import (
    QuoteCreateRequest,
    QuoteUpdateRequest,
    QuoteResponse,
    QuoteListResponse,
)
from ..services.quote_service import QuoteService

router = APIRouter()


def get_quote_service() -> QuoteService:
    return QuoteService()


@router.post("/", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
async def create_quote(
    data: QuoteCreateRequest,
    current_user: dict = Depends(get_current_user),
    quote_service: QuoteService = Depends(get_quote_service),
):
    """Create a new quote"""
    quote = await quote_service.create_quote(
        user_id=current_user.user_id,
        data=data,
    )
    return quote


@router.get("/", response_model=QuoteListResponse)
async def get_quotes(
    book_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    quote_service: QuoteService = Depends(get_quote_service),
):
    """Get quotes with optional filters"""
    return await quote_service.get_quotes(
        book_id=book_id,
        user_id=user_id,
        viewer_id=current_user.user_id,
        page=page,
        page_size=page_size,
    )


@router.get("/me", response_model=QuoteListResponse)
async def get_my_quotes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    quote_service: QuoteService = Depends(get_quote_service),
):
    """Get current user's quotes"""
    return await quote_service.get_quotes(
        user_id=current_user.user_id,
        viewer_id=current_user.user_id,
        page=page,
        page_size=page_size,
    )


@router.get("/{quote_id}", response_model=QuoteResponse)
async def get_quote(
    quote_id: str,
    current_user: dict = Depends(get_current_user),
    quote_service: QuoteService = Depends(get_quote_service),
):
    """Get quote by ID"""
    quote = await quote_service.get_quote_by_id(
        quote_id=quote_id,
        viewer_id=current_user.user_id,
    )
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found",
        )
    return quote


@router.patch("/{quote_id}", response_model=QuoteResponse)
async def update_quote(
    quote_id: str,
    data: QuoteUpdateRequest,
    current_user: dict = Depends(get_current_user),
    quote_service: QuoteService = Depends(get_quote_service),
):
    """Update a quote"""
    quote = await quote_service.update_quote(
        quote_id=quote_id,
        user_id=current_user.user_id,
        data=data,
    )
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found or not authorized",
        )
    return quote


@router.delete("/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quote(
    quote_id: str,
    current_user: dict = Depends(get_current_user),
    quote_service: QuoteService = Depends(get_quote_service),
):
    """Delete a quote"""
    success = await quote_service.delete_quote(
        quote_id=quote_id,
        user_id=current_user.user_id,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found or not authorized",
        )


@router.post("/{quote_id}/like")
async def like_quote(
    quote_id: str,
    current_user: dict = Depends(get_current_user),
    quote_service: QuoteService = Depends(get_quote_service),
):
    """Like a quote"""
    success = await quote_service.like_quote(
        quote_id=quote_id,
        user_id=current_user.user_id,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found",
        )
    return {"status": "liked"}


@router.delete("/{quote_id}/like")
async def unlike_quote(
    quote_id: str,
    current_user: dict = Depends(get_current_user),
    quote_service: QuoteService = Depends(get_quote_service),
):
    """Unlike a quote"""
    await quote_service.unlike_quote(
        quote_id=quote_id,
        user_id=current_user.user_id,
    )
    return {"status": "unliked"}
