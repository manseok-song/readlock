from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Optional

from shared.middleware.auth import get_current_user
from ..schemas.book_schemas import (
    BookSearchResponse,
    BookResponse,
    UserBookCreate,
    UserBookUpdate,
    UserBookResponse,
    UserBooksListResponse,
)
from ..services.book_service import BookService
from ..services.naver_book_service import NaverBookService

router = APIRouter()


def get_book_service() -> BookService:
    return BookService()


def get_naver_service() -> NaverBookService:
    return NaverBookService()


@router.get("/search", response_model=BookSearchResponse)
async def search_books(
    query: str = Query(..., min_length=1, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    naver_service: NaverBookService = Depends(get_naver_service),
):
    """
    Search books using Naver Book API
    """
    result = await naver_service.search_books(
        query=query,
        page=page,
        page_size=page_size,
    )
    return result


@router.get("/isbn/{isbn}", response_model=BookResponse)
async def get_book_by_isbn(
    isbn: str,
    book_service: BookService = Depends(get_book_service),
    naver_service: NaverBookService = Depends(get_naver_service),
):
    """
    Get book details by ISBN
    First checks local database, then fetches from Naver API if not found
    """
    # Try local database first
    book = await book_service.get_by_isbn(isbn)
    if book:
        return book

    # Fetch from Naver API
    book = await naver_service.get_book_by_isbn(isbn)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )

    # Save to local database
    saved_book = await book_service.create_book(book)
    return saved_book


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: str,
    book_service: BookService = Depends(get_book_service),
):
    """
    Get book details by ID
    """
    book = await book_service.get_by_id(book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )
    return book


# User book management
@router.get("/me/books", response_model=UserBooksListResponse)
async def get_user_books(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    book_service: BookService = Depends(get_book_service),
):
    """
    Get current user's book library
    """
    user_books = await book_service.get_user_books(
        user_id=current_user.user_id,
        status=status,
        page=page,
        page_size=page_size,
    )
    return user_books


@router.post("/me/books", response_model=UserBookResponse, status_code=status.HTTP_201_CREATED)
async def add_book_to_library(
    data: UserBookCreate,
    current_user: dict = Depends(get_current_user),
    book_service: BookService = Depends(get_book_service),
):
    """
    Add a book to user's library
    """
    user_book = await book_service.add_to_library(
        user_id=current_user.user_id,
        book_id=data.book_id,
        status=data.status,
    )
    return user_book


@router.patch("/me/books/{user_book_id}", response_model=UserBookResponse)
async def update_user_book(
    user_book_id: str,
    data: UserBookUpdate,
    current_user: dict = Depends(get_current_user),
    book_service: BookService = Depends(get_book_service),
):
    """
    Update a user's book (status, current page, rating)
    """
    user_book = await book_service.update_user_book(
        user_id=current_user.user_id,
        user_book_id=user_book_id,
        data=data,
    )
    if not user_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User book not found",
        )
    return user_book


@router.delete("/me/books/{user_book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_book_from_library(
    user_book_id: str,
    current_user: dict = Depends(get_current_user),
    book_service: BookService = Depends(get_book_service),
):
    """
    Remove a book from user's library
    """
    success = await book_service.remove_from_library(
        user_id=current_user.user_id,
        user_book_id=user_book_id,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User book not found",
        )
