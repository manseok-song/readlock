from fastapi import APIRouter, Depends, Query
from typing import Optional, List

from shared.middleware.auth import get_current_user
from ..schemas.ai_schemas import (
    RecommendationListResponse,
    SimilarBooksResponse,
    ReadingInsightsResponse,
)
from ..services.recommendation_service import RecommendationService

router = APIRouter()


def get_recommendation_service() -> RecommendationService:
    return RecommendationService()


@router.get("/personalized", response_model=RecommendationListResponse)
async def get_personalized_recommendations(
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    service: RecommendationService = Depends(get_recommendation_service),
):
    """Get personalized book recommendations based on reading history"""
    return await service.get_personalized(user_id=current_user.user_id, limit=limit)


@router.get("/similar/{book_id}", response_model=SimilarBooksResponse)
async def get_similar_books(
    book_id: str,
    limit: int = Query(10, ge=1, le=20),
    current_user: dict = Depends(get_current_user),
    service: RecommendationService = Depends(get_recommendation_service),
):
    """Get similar books based on a specific book"""
    return await service.get_similar_books(book_id=book_id, limit=limit)


@router.get("/trending", response_model=RecommendationListResponse)
async def get_trending_books(
    period: str = Query("week", pattern="^(day|week|month)$"),
    genre: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    service: RecommendationService = Depends(get_recommendation_service),
):
    """Get trending books"""
    return await service.get_trending(period=period, genre=genre, limit=limit)


@router.get("/by-mood", response_model=RecommendationListResponse)
async def get_books_by_mood(
    mood: str = Query(..., min_length=1, max_length=50),
    limit: int = Query(10, ge=1, le=20),
    current_user: dict = Depends(get_current_user),
    service: RecommendationService = Depends(get_recommendation_service),
):
    """Get book recommendations based on mood"""
    return await service.get_by_mood(mood=mood, user_id=current_user.user_id, limit=limit)


@router.get("/insights", response_model=ReadingInsightsResponse)
async def get_reading_insights(
    current_user: dict = Depends(get_current_user),
    service: RecommendationService = Depends(get_recommendation_service),
):
    """Get AI-generated reading insights and patterns"""
    return await service.get_reading_insights(user_id=current_user.user_id)


@router.post("/feedback")
async def submit_recommendation_feedback(
    book_id: str,
    is_relevant: bool,
    current_user: dict = Depends(get_current_user),
    service: RecommendationService = Depends(get_recommendation_service),
):
    """Submit feedback on a recommendation to improve future suggestions"""
    await service.record_feedback(
        user_id=current_user.user_id,
        book_id=book_id,
        is_relevant=is_relevant,
    )
    return {"status": "recorded"}
