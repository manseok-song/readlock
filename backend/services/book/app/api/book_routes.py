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


@router.post("/seed-sample-books", response_model=dict)
async def seed_sample_books(
    book_service: BookService = Depends(get_book_service),
):
    """
    Create sample books for testing (development only)
    해밀누리 출판사 책들
    """
    sample_books = [
        {
            "isbn": "9791198682116",
            "title": "도구라 마구라 1",
            "author": "유메노 규사쿠",
            "publisher": "해밀누리",
            "description": "일본 3대 기서 중 하나로 꼽히는 미스터리 소설의 걸작. 정신병원을 배경으로 펼쳐지는 미궁 속의 이야기.",
            "cover_image": "https://contents.kyobobook.co.kr/sih/fit-in/458x0/pdt/9791198682116.jpg",
            "category": "일본소설",
            "page_count": 400,
        },
        {
            "isbn": "9791198682123",
            "title": "도구라 마구라 2",
            "author": "유메노 규사쿠",
            "publisher": "해밀누리",
            "description": "일본 3대 기서 도구라 마구라의 두 번째 권. 충격적인 결말을 향해 달려가는 광기의 서사.",
            "cover_image": "https://contents.kyobobook.co.kr/sih/fit-in/458x0/pdt/9791198682123.jpg",
            "category": "일본소설",
            "page_count": 420,
        },
        {
            "isbn": "9791198682109",
            "title": "백야",
            "author": "표도르 도스토옙스키",
            "publisher": "해밀누리",
            "description": "도스토옙스키의 초기 작품. 백야의 밤을 배경으로 한 순수하고 슬픈 사랑 이야기.",
            "cover_image": "https://contents.kyobobook.co.kr/sih/fit-in/458x0/pdt/9791198682109.jpg",
            "category": "러시아소설",
            "page_count": 200,
        },
        {
            "isbn": "9791198682130",
            "title": "겨울밤에 읽는 일본 문학 단편선",
            "author": "다자이 오사무, 미야자와 겐지, 아쿠타가와 류노스케",
            "publisher": "해밀누리",
            "description": "일본 근대 문학의 거장들이 남긴 주옥같은 단편들을 모은 앤솔러지.",
            "cover_image": "https://contents.kyobobook.co.kr/sih/fit-in/458x0/pdt/9791198682130.jpg",
            "category": "일본소설",
            "page_count": 280,
        },
        {
            "isbn": "9791198682147",
            "title": "소녀지옥",
            "author": "유메노 규사쿠",
            "publisher": "해밀누리",
            "description": "유메노 규사쿠의 기묘하고 섬뜩한 단편집. 소녀들의 어두운 내면을 그린 작품.",
            "cover_image": "https://contents.kyobobook.co.kr/sih/fit-in/458x0/pdt/9791198682147.jpg",
            "category": "일본소설",
            "page_count": 240,
        },
        {
            "isbn": "9791198682154",
            "title": "걷기의 철학",
            "author": "헨리 데이비드 소로",
            "publisher": "해밀누리",
            "description": "월든의 저자 소로가 걷기를 통해 발견한 삶의 지혜와 자연에 대한 명상.",
            "cover_image": "https://contents.kyobobook.co.kr/sih/fit-in/458x0/pdt/9791198682154.jpg",
            "category": "에세이",
            "page_count": 160,
        },
    ]

    created_books = []
    for book_data in sample_books:
        try:
            book = await book_service.create_book(book_data)
            created_books.append(book)
        except Exception as e:
            # Book might already exist
            pass

    return {
        "message": f"Created {len(created_books)} sample books",
        "books": created_books,
    }
