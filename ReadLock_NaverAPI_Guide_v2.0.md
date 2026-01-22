# ReadLock 2.0 - 네이버 책 API 연동 가이드

**Version:** 2.0  
**Backend:** FastAPI (Python)  
**Frontend:** Flutter (Dart)

---

## 1. 네이버 책 API 소개

### 1.1 API 정보

- **API 이름:** 네이버 검색 API - 책
- **Base URL:** `https://openapi.naver.com/v1/search/book.json`
- **인증:** Client ID + Client Secret (Header)
- **일일 한도:** 25,000건 (무료)

### 1.2 발급 방법

1. [네이버 개발자 센터](https://developers.naver.com) 접속
2. 애플리케이션 등록
3. 검색 API 선택
4. Client ID / Client Secret 발급

---

## 2. Backend (FastAPI)

### 2.1 프로젝트 구조

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py
│   │       └── endpoints/
│   │           ├── auth.py
│   │           ├── books.py
│   │           └── reading.py
│   ├── services/
│   │   ├── naver_book_service.py
│   │   └── book_service.py
│   ├── models/
│   │   └── book.py
│   ├── schemas/
│   │   ├── book.py
│   │   └── common.py
│   └── db/
│       ├── database.py
│       └── models.py
├── requirements.txt
└── .env
```

### 2.2 requirements.txt

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
httpx==0.26.0
pydantic==2.5.3
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
sqlalchemy==2.0.25
asyncpg==0.29.0
redis==5.0.1
python-multipart==0.0.6
```

### 2.3 config.py

```python
# app/core/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "ReadLock API"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379"
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Naver API
    NAVER_CLIENT_ID: str
    NAVER_CLIENT_SECRET: str
    NAVER_BOOK_API_URL: str = "https://openapi.naver.com/v1/search/book.json"
    
    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
```

### 2.4 네이버 책 API 서비스

```python
# app/services/naver_book_service.py
import re
import httpx
from typing import Optional, List
from pydantic import BaseModel

from app.core.config import settings


class NaverBookItem(BaseModel):
    """네이버 API 응답 아이템"""
    title: str
    link: str
    image: str = ""
    author: str
    discount: str = ""
    publisher: str
    pubdate: str = ""
    isbn: str
    description: str = ""


class NaverBookSearchResult(BaseModel):
    """네이버 API 검색 결과"""
    lastBuildDate: str
    total: int
    start: int
    display: int
    items: List[NaverBookItem]


class BookDTO(BaseModel):
    """정규화된 도서 정보"""
    isbn: str
    title: str
    author: str
    publisher: str
    published_date: Optional[str] = None
    description: Optional[str] = None
    cover_image: Optional[str] = None
    page_count: Optional[int] = None
    link: Optional[str] = None
    price: Optional[int] = None
    discount_price: Optional[int] = None


class NaverBookService:
    """네이버 책 검색 API 서비스"""

    def __init__(self):
        self.client_id = settings.NAVER_CLIENT_ID
        self.client_secret = settings.NAVER_CLIENT_SECRET
        self.base_url = settings.NAVER_BOOK_API_URL

    @property
    def _headers(self) -> dict:
        return {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }

    async def search(
        self,
        query: str,
        display: int = 10,
        start: int = 1,
        sort: str = "sim",
    ) -> NaverBookSearchResult:
        """
        도서 검색
        
        Args:
            query: 검색어 (제목, 저자, ISBN 등)
            display: 검색 결과 개수 (기본 10, 최대 100)
            start: 검색 시작 위치 (기본 1)
            sort: 정렬 방식 (sim: 정확도순, date: 출간일순)
        
        Returns:
            NaverBookSearchResult
        
        Raises:
            httpx.HTTPStatusError: API 호출 실패 시
        """
        params = {
            "query": query,
            "display": min(display, 100),
            "start": start,
            "sort": sort,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.base_url,
                headers=self._headers,
                params=params,
                timeout=10.0,
            )
            response.raise_for_status()
            
            data = response.json()
            return NaverBookSearchResult(**data)

    async def search_by_isbn(self, isbn: str) -> Optional[BookDTO]:
        """
        ISBN으로 도서 검색
        
        Args:
            isbn: ISBN (10자리 또는 13자리)
        
        Returns:
            BookDTO or None
        """
        # ISBN 정규화 (하이픈 제거)
        clean_isbn = isbn.replace("-", "").replace(" ", "")
        
        # ISBN 검색 (d_isbn 파라미터 사용)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.base_url,
                headers=self._headers,
                params={"d_isbn": clean_isbn},
                timeout=10.0,
            )
            response.raise_for_status()
            
            data = response.json()
            result = NaverBookSearchResult(**data)
            
            if not result.items:
                return None
            
            return self._normalize_book(result.items[0])

    def _normalize_book(self, item: NaverBookItem) -> BookDTO:
        """
        네이버 API 응답을 표준 형식으로 변환
        """
        # ISBN 추출 (ISBN10 ISBN13 형식에서 ISBN13 추출)
        isbn_parts = item.isbn.split()
        isbn = isbn_parts[-1] if isbn_parts else item.isbn
        
        # HTML 태그 제거
        def clean_html(text: str) -> str:
            return re.sub(r'<[^>]+>', '', text) if text else ""
        
        # 가격 파싱
        price = None
        discount_price = None
        if item.discount:
            try:
                discount_price = int(item.discount)
            except ValueError:
                pass
        
        # 출판일 형식 변환 (YYYYMMDD -> YYYY-MM-DD)
        published_date = None
        if item.pubdate and len(item.pubdate) == 8:
            published_date = f"{item.pubdate[:4]}-{item.pubdate[4:6]}-{item.pubdate[6:]}"
        
        return BookDTO(
            isbn=isbn,
            title=clean_html(item.title),
            author=clean_html(item.author),
            publisher=item.publisher,
            published_date=published_date,
            description=clean_html(item.description),
            cover_image=item.image if item.image else None,
            link=item.link,
            price=price,
            discount_price=discount_price,
        )

    async def search_normalized(
        self,
        query: str,
        display: int = 10,
        start: int = 1,
        sort: str = "sim",
    ) -> tuple[List[BookDTO], int]:
        """
        검색 결과를 정규화된 형식으로 반환
        
        Returns:
            (도서 목록, 총 결과 수)
        """
        result = await self.search(query, display, start, sort)
        
        books = [self._normalize_book(item) for item in result.items]
        
        return books, result.total


# Singleton instance
naver_book_service = NaverBookService()
```

### 2.5 Books API 엔드포인트

```python
# app/api/v1/endpoints/books.py
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List

from app.services.naver_book_service import naver_book_service, BookDTO
from app.services.book_service import book_service
from app.schemas.book import (
    BookSearchResponse,
    BookDetailResponse,
    UserBookCreate,
    UserBookUpdate,
    UserBookResponse,
)
from app.schemas.common import ApiResponse
from app.api.deps import get_current_user
from app.db.models import User

router = APIRouter()


@router.get("/search", response_model=ApiResponse[BookSearchResponse])
async def search_books(
    query: str = Query(..., min_length=1, description="검색어"),
    display: int = Query(10, ge=1, le=100, description="결과 개수"),
    start: int = Query(1, ge=1, description="시작 위치"),
    sort: str = Query("sim", regex="^(sim|date)$", description="정렬"),
):
    """
    도서 검색 (네이버 책 API)
    
    - **query**: 검색어 (제목, 저자, ISBN 등)
    - **display**: 검색 결과 개수 (1-100)
    - **start**: 검색 시작 위치
    - **sort**: 정렬 방식 (sim: 정확도순, date: 출간일순)
    """
    try:
        books, total = await naver_book_service.search_normalized(
            query=query,
            display=display,
            start=start,
            sort=sort,
        )
        
        return ApiResponse(
            success=True,
            data=BookSearchResponse(
                total=total,
                start=start,
                display=len(books),
                items=books,
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{isbn}", response_model=ApiResponse[BookDetailResponse])
async def get_book_by_isbn(isbn: str):
    """
    ISBN으로 도서 상세 조회
    
    - **isbn**: ISBN (10자리 또는 13자리)
    """
    # ISBN 유효성 검사
    clean_isbn = isbn.replace("-", "").replace(" ", "")
    if len(clean_isbn) not in [10, 13]:
        raise HTTPException(status_code=400, detail="유효하지 않은 ISBN입니다")
    
    try:
        book = await naver_book_service.search_by_isbn(clean_isbn)
        
        if not book:
            raise HTTPException(status_code=404, detail="도서를 찾을 수 없습니다")
        
        return ApiResponse(
            success=True,
            data=BookDetailResponse(book=book),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan", response_model=ApiResponse[BookDetailResponse])
async def scan_barcode(body: dict):
    """
    바코드 스캔으로 도서 조회
    
    - **isbn**: 스캔된 ISBN 바코드
    """
    isbn = body.get("isbn", "")
    clean_isbn = isbn.replace("-", "").replace(" ", "")
    
    if len(clean_isbn) not in [10, 13]:
        raise HTTPException(status_code=400, detail="유효하지 않은 ISBN입니다")
    
    try:
        book = await naver_book_service.search_by_isbn(clean_isbn)
        
        if not book:
            raise HTTPException(status_code=404, detail="도서를 찾을 수 없습니다")
        
        return ApiResponse(
            success=True,
            data=BookDetailResponse(book=book),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 내 책장 API ==========

@router.get("/me/books", response_model=ApiResponse[List[UserBookResponse]])
async def get_my_books(
    status: Optional[str] = Query(None, regex="^(wishlist|reading|completed)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """
    내 책장 목록 조회
    """
    user_books, total = await book_service.get_user_books(
        user_id=current_user.id,
        status=status,
        page=page,
        limit=limit,
    )
    
    return ApiResponse(
        success=True,
        data=user_books,
        meta={"page": page, "limit": limit, "total": total},
    )


@router.post("/me/books", response_model=ApiResponse[UserBookResponse], status_code=201)
async def add_to_bookshelf(
    body: UserBookCreate,
    current_user: User = Depends(get_current_user),
):
    """
    책장에 도서 추가
    """
    # ISBN으로 도서 정보 조회 (없으면 네이버 API에서 가져와 DB에 저장)
    book = await book_service.get_or_create_book(body.isbn)
    
    if not book:
        raise HTTPException(status_code=404, detail="도서를 찾을 수 없습니다")
    
    # 이미 책장에 있는지 확인
    existing = await book_service.get_user_book(
        user_id=current_user.id,
        book_id=book.id,
    )
    
    if existing:
        raise HTTPException(status_code=409, detail="이미 책장에 추가된 도서입니다")
    
    # 책장에 추가
    user_book = await book_service.add_to_bookshelf(
        user_id=current_user.id,
        book_id=book.id,
        status=body.status,
        total_pages=body.total_pages,
    )
    
    return ApiResponse(success=True, data=user_book)


@router.patch("/me/books/{id}", response_model=ApiResponse[UserBookResponse])
async def update_user_book(
    id: str,
    body: UserBookUpdate,
    current_user: User = Depends(get_current_user),
):
    """
    독서 상태/진행률 업데이트
    """
    user_book = await book_service.update_user_book(
        user_book_id=id,
        user_id=current_user.id,
        **body.model_dump(exclude_unset=True),
    )
    
    if not user_book:
        raise HTTPException(status_code=404, detail="책장에 없는 도서입니다")
    
    return ApiResponse(success=True, data=user_book)


@router.delete("/me/books/{id}", status_code=204)
async def remove_from_bookshelf(
    id: str,
    current_user: User = Depends(get_current_user),
):
    """
    책장에서 도서 삭제
    """
    success = await book_service.remove_from_bookshelf(
        user_book_id=id,
        user_id=current_user.id,
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="책장에 없는 도서입니다")
```

### 2.6 Schemas

```python
# app/schemas/book.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class BookBase(BaseModel):
    isbn: str
    title: str
    author: str
    publisher: Optional[str] = None
    published_date: Optional[str] = None
    description: Optional[str] = None
    cover_image: Optional[str] = None
    page_count: Optional[int] = None
    link: Optional[str] = None


class BookSearchResponse(BaseModel):
    total: int
    start: int
    display: int
    items: List[BookBase]


class BookDetailResponse(BaseModel):
    book: BookBase


class UserBookCreate(BaseModel):
    isbn: str
    status: str = "wishlist"
    total_pages: Optional[int] = None


class UserBookUpdate(BaseModel):
    status: Optional[str] = None
    current_page: Optional[int] = None
    total_pages: Optional[int] = None


class UserBookResponse(BaseModel):
    id: str
    book: BookBase
    status: str
    current_page: int
    total_pages: Optional[int]
    progress: float
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# app/schemas/common.py
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[dict] = None
    meta: Optional[dict] = None
```

### 2.7 main.py

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router

app = FastAPI(
    title=settings.APP_NAME,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 3. Flutter Client

### 3.1 API Client

```dart
// lib/data/datasources/remote/book_api.dart
import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

part 'book_api.g.dart';

@RestApi()
abstract class BookApi {
  factory BookApi(Dio dio, {String baseUrl}) = _BookApi;

  @GET('/books/search')
  Future<ApiResponse<BookSearchData>> searchBooks({
    @Query('query') required String query,
    @Query('display') int display = 10,
    @Query('start') int start = 1,
    @Query('sort') String sort = 'sim',
  });

  @GET('/books/{isbn}')
  Future<ApiResponse<BookDetailData>> getBookByIsbn(
    @Path('isbn') String isbn,
  );

  @POST('/books/scan')
  Future<ApiResponse<BookDetailData>> scanBarcode(
    @Body() Map<String, String> body,
  );

  @GET('/me/books')
  Future<ApiResponse<List<UserBookData>>> getMyBooks({
    @Query('status') String? status,
    @Query('page') int page = 1,
    @Query('limit') int limit = 20,
  });

  @POST('/me/books')
  Future<ApiResponse<UserBookData>> addToBookshelf(
    @Body() AddBookRequest body,
  );

  @PATCH('/me/books/{id}')
  Future<ApiResponse<UserBookData>> updateUserBook(
    @Path('id') String id,
    @Body() UpdateBookRequest body,
  );

  @DELETE('/me/books/{id}')
  Future<void> removeFromBookshelf(
    @Path('id') String id,
  );
}
```

### 3.2 Book Repository

```dart
// lib/data/repositories/book_repository_impl.dart
import 'package:dartz/dartz.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/errors/failures.dart';
import '../../domain/entities/book.dart';
import '../../domain/repositories/book_repository.dart';
import '../datasources/remote/book_api.dart';

class BookRepositoryImpl implements BookRepository {
  final BookApi _api;

  BookRepositoryImpl(this._api);

  @override
  Future<Either<Failure, BookSearchResult>> searchBooks({
    required String query,
    int display = 10,
    int start = 1,
    String sort = 'sim',
  }) async {
    try {
      final response = await _api.searchBooks(
        query: query,
        display: display,
        start: start,
        sort: sort,
      );

      if (response.success && response.data != null) {
        return Right(BookSearchResult(
          total: response.data!.total,
          start: response.data!.start,
          display: response.data!.display,
          items: response.data!.items.map((e) => Book.fromData(e)).toList(),
        ));
      }

      return Left(ServerFailure(response.error?.message ?? '검색 실패'));
    } on DioException catch (e) {
      return Left(NetworkFailure(_getErrorMessage(e)));
    } catch (e) {
      return Left(UnknownFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, Book>> scanBarcode(String isbn) async {
    try {
      final response = await _api.scanBarcode({'isbn': isbn});

      if (response.success && response.data != null) {
        return Right(Book.fromData(response.data!.book));
      }

      return Left(ServerFailure(response.error?.message ?? '스캔 실패'));
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) {
        return Left(NotFoundFailure('도서를 찾을 수 없습니다'));
      }
      return Left(NetworkFailure(_getErrorMessage(e)));
    } catch (e) {
      return Left(UnknownFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, List<UserBook>>> getMyBooks({
    String? status,
    int page = 1,
    int limit = 20,
  }) async {
    try {
      final response = await _api.getMyBooks(
        status: status,
        page: page,
        limit: limit,
      );

      if (response.success && response.data != null) {
        return Right(response.data!.map((e) => UserBook.fromData(e)).toList());
      }

      return Left(ServerFailure(response.error?.message ?? '조회 실패'));
    } on DioException catch (e) {
      return Left(NetworkFailure(_getErrorMessage(e)));
    } catch (e) {
      return Left(UnknownFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, UserBook>> addToBookshelf({
    required String isbn,
    required String status,
    int? totalPages,
  }) async {
    try {
      final response = await _api.addToBookshelf(AddBookRequest(
        isbn: isbn,
        status: status,
        totalPages: totalPages,
      ));

      if (response.success && response.data != null) {
        return Right(UserBook.fromData(response.data!));
      }

      return Left(ServerFailure(response.error?.message ?? '추가 실패'));
    } on DioException catch (e) {
      if (e.response?.statusCode == 409) {
        return Left(ConflictFailure('이미 책장에 추가된 도서입니다'));
      }
      return Left(NetworkFailure(_getErrorMessage(e)));
    } catch (e) {
      return Left(UnknownFailure(e.toString()));
    }
  }

  String _getErrorMessage(DioException e) {
    if (e.type == DioExceptionType.connectionTimeout) {
      return '연결 시간이 초과되었습니다';
    }
    if (e.type == DioExceptionType.receiveTimeout) {
      return '응답 시간이 초과되었습니다';
    }
    if (e.response?.data?['error']?['message'] != null) {
      return e.response!.data['error']['message'];
    }
    return '네트워크 오류가 발생했습니다';
  }
}

// Provider
final bookRepositoryProvider = Provider<BookRepository>((ref) {
  final api = ref.watch(bookApiProvider);
  return BookRepositoryImpl(api);
});
```

### 3.3 Book Search Provider

```dart
// lib/presentation/providers/book_search_provider.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../domain/entities/book.dart';
import '../../domain/repositories/book_repository.dart';

part 'book_search_provider.g.dart';

@freezed
class BookSearchState with _$BookSearchState {
  const factory BookSearchState({
    @Default('') String query,
    @Default([]) List<Book> results,
    @Default(0) int total,
    @Default(false) bool isLoading,
    @Default(false) bool hasMore,
    String? error,
  }) = _BookSearchState;
}

@riverpod
class BookSearchNotifier extends _$BookSearchNotifier {
  static const _pageSize = 20;
  int _currentStart = 1;

  @override
  BookSearchState build() {
    return const BookSearchState();
  }

  Future<void> search(String query) async {
    if (query.isEmpty) {
      state = const BookSearchState();
      return;
    }

    state = state.copyWith(
      query: query,
      isLoading: true,
      error: null,
    );

    _currentStart = 1;

    final repository = ref.read(bookRepositoryProvider);
    final result = await repository.searchBooks(
      query: query,
      display: _pageSize,
      start: _currentStart,
    );

    result.fold(
      (failure) {
        state = state.copyWith(
          isLoading: false,
          error: failure.message,
        );
      },
      (searchResult) {
        state = state.copyWith(
          results: searchResult.items,
          total: searchResult.total,
          isLoading: false,
          hasMore: searchResult.items.length < searchResult.total,
        );
        _currentStart += searchResult.items.length;
      },
    );
  }

  Future<void> loadMore() async {
    if (state.isLoading || !state.hasMore) return;

    state = state.copyWith(isLoading: true);

    final repository = ref.read(bookRepositoryProvider);
    final result = await repository.searchBooks(
      query: state.query,
      display: _pageSize,
      start: _currentStart,
    );

    result.fold(
      (failure) {
        state = state.copyWith(
          isLoading: false,
          error: failure.message,
        );
      },
      (searchResult) {
        final newResults = [...state.results, ...searchResult.items];
        state = state.copyWith(
          results: newResults,
          isLoading: false,
          hasMore: newResults.length < searchResult.total,
        );
        _currentStart += searchResult.items.length;
      },
    );
  }

  void clear() {
    _currentStart = 1;
    state = const BookSearchState();
  }
}

// 내 책장 Provider
@riverpod
Future<List<UserBook>> myBooks(
  MyBooksRef ref, {
  String? status,
}) async {
  final repository = ref.watch(bookRepositoryProvider);
  final result = await repository.getMyBooks(status: status);

  return result.fold(
    (failure) => throw Exception(failure.message),
    (books) => books,
  );
}
```

### 3.4 Book Search Widget

```dart
// lib/presentation/widgets/book/book_search_delegate.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cached_network_image/cached_network_image.dart';

import '../../providers/book_search_provider.dart';
import '../../screens/library/book_detail_screen.dart';

class BookSearchDelegate extends SearchDelegate<Book?> {
  final WidgetRef ref;

  BookSearchDelegate(this.ref);

  @override
  String get searchFieldLabel => '제목, 저자, ISBN 검색';

  @override
  ThemeData appBarTheme(BuildContext context) {
    return Theme.of(context).copyWith(
      appBarTheme: AppBarTheme(
        backgroundColor: Theme.of(context).colorScheme.surface,
        elevation: 0,
      ),
      inputDecorationTheme: const InputDecorationTheme(
        border: InputBorder.none,
      ),
    );
  }

  @override
  List<Widget>? buildActions(BuildContext context) {
    return [
      if (query.isNotEmpty)
        IconButton(
          icon: const Icon(Icons.clear),
          onPressed: () {
            query = '';
            ref.read(bookSearchNotifierProvider.notifier).clear();
          },
        ),
    ];
  }

  @override
  Widget? buildLeading(BuildContext context) {
    return IconButton(
      icon: const Icon(Icons.arrow_back),
      onPressed: () => close(context, null),
    );
  }

  @override
  Widget buildResults(BuildContext context) {
    return _BookSearchResults(
      ref: ref,
      onBookSelected: (book) => close(context, book),
    );
  }

  @override
  Widget buildSuggestions(BuildContext context) {
    if (query.length < 2) {
      return const Center(
        child: Text('검색어를 2자 이상 입력해주세요'),
      );
    }

    // 디바운스 검색
    Future.delayed(const Duration(milliseconds: 300), () {
      if (query.isNotEmpty) {
        ref.read(bookSearchNotifierProvider.notifier).search(query);
      }
    });

    return _BookSearchResults(
      ref: ref,
      onBookSelected: (book) {
        close(context, book);
      },
    );
  }
}

class _BookSearchResults extends ConsumerWidget {
  final WidgetRef ref;
  final ValueChanged<Book> onBookSelected;

  const _BookSearchResults({
    required this.ref,
    required this.onBookSelected,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(bookSearchNotifierProvider);

    if (state.isLoading && state.results.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }

    if (state.error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48),
            const SizedBox(height: 16),
            Text(state.error!),
          ],
        ),
      );
    }

    if (state.results.isEmpty) {
      return const Center(
        child: Text('검색 결과가 없습니다'),
      );
    }

    return NotificationListener<ScrollNotification>(
      onNotification: (notification) {
        if (notification is ScrollEndNotification &&
            notification.metrics.extentAfter < 200) {
          ref.read(bookSearchNotifierProvider.notifier).loadMore();
        }
        return false;
      },
      child: ListView.builder(
        itemCount: state.results.length + (state.hasMore ? 1 : 0),
        itemBuilder: (context, index) {
          if (index >= state.results.length) {
            return const Center(
              child: Padding(
                padding: EdgeInsets.all(16),
                child: CircularProgressIndicator(),
              ),
            );
          }

          final book = state.results[index];
          return _BookListTile(
            book: book,
            onTap: () => onBookSelected(book),
          );
        },
      ),
    );
  }
}

class _BookListTile extends StatelessWidget {
  final Book book;
  final VoidCallback onTap;

  const _BookListTile({
    required this.book,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      onTap: onTap,
      leading: SizedBox(
        width: 50,
        height: 70,
        child: book.coverImage != null
            ? CachedNetworkImage(
                imageUrl: book.coverImage!,
                fit: BoxFit.cover,
                placeholder: (_, __) => Container(
                  color: Colors.grey[300],
                  child: const Icon(Icons.book),
                ),
                errorWidget: (_, __, ___) => Container(
                  color: Colors.grey[300],
                  child: const Icon(Icons.book),
                ),
              )
            : Container(
                color: Colors.grey[300],
                child: const Icon(Icons.book),
              ),
      ),
      title: Text(
        book.title,
        maxLines: 2,
        overflow: TextOverflow.ellipsis,
      ),
      subtitle: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            book.author,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          Text(
            book.publisher ?? '',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
      isThreeLine: true,
    );
  }
}
```

---

## 4. 사용 예시

### 4.1 Backend 실행

```bash
# .env 파일 생성
cat > .env << EOF
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/readlock
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
NAVER_CLIENT_ID=your-client-id
NAVER_CLIENT_SECRET=your-client-secret
EOF

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
uvicorn app.main:app --reload --port 8000

# API 문서
# http://localhost:8000/docs
```

### 4.2 Flutter 사용

```dart
// 도서 검색
final searchNotifier = ref.read(bookSearchNotifierProvider.notifier);
await searchNotifier.search('데미안');

// 바코드 스캔 결과 처리
final result = await ref.read(bookRepositoryProvider).scanBarcode(isbn);
result.fold(
  (failure) => showError(failure.message),
  (book) => navigateToBookDetail(book),
);

// 책장에 추가
final result = await ref.read(bookRepositoryProvider).addToBookshelf(
  isbn: book.isbn,
  status: 'wishlist',
);
```

---

## 5. API 테스트

```bash
# 도서 검색
curl "http://localhost:8000/api/v1/books/search?query=데미안"

# ISBN 검색
curl "http://localhost:8000/api/v1/books/9788932917245"

# 바코드 스캔
curl -X POST "http://localhost:8000/api/v1/books/scan" \
  -H "Content-Type: application/json" \
  -d '{"isbn": "9788932917245"}'

# 내 책장 조회 (인증 필요)
curl "http://localhost:8000/api/v1/me/books" \
  -H "Authorization: Bearer {token}"

# 책장에 추가 (인증 필요)
curl -X POST "http://localhost:8000/api/v1/me/books" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"isbn": "9788932917245", "status": "wishlist"}'
```
