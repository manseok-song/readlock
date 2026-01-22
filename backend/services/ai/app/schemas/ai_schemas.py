from typing import Optional, List
from pydantic import BaseModel


class BookRecommendation(BaseModel):
    id: str
    title: str
    authors: List[str]
    cover_image_url: Optional[str] = None
    description: Optional[str] = None
    genres: List[str] = []
    match_score: float = 0.0
    match_reasons: List[str] = []


class RecommendationListResponse(BaseModel):
    items: List[BookRecommendation]
    total: int


class SimilarBooksResponse(BaseModel):
    source_book_id: str
    source_book_title: str
    similar_books: List[BookRecommendation]


class ReadingPattern(BaseModel):
    pattern_type: str
    description: str
    data: dict


class ReadingInsightsResponse(BaseModel):
    favorite_genres: List[dict]
    reading_pace: dict
    best_reading_time: Optional[str] = None
    completion_rate: float
    patterns: List[ReadingPattern]
    suggestions: List[str]
