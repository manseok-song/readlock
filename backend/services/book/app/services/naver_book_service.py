import httpx
from typing import Optional, List
from pydantic import BaseModel

from shared.core.config import settings
from shared.core.redis import cache_service


class NaverBookItem(BaseModel):
    """Book item from Naver API"""
    title: str
    link: str
    image: Optional[str] = None
    author: str
    discount: Optional[str] = None
    publisher: str
    pubdate: Optional[str] = None
    isbn: str
    description: Optional[str] = None


class NaverBookResponse(BaseModel):
    """Response from Naver Book API"""
    lastBuildDate: str
    total: int
    start: int
    display: int
    items: List[NaverBookItem]


class NaverBookService:
    """Service for interacting with Naver Book API"""

    SEARCH_URL = "https://openapi.naver.com/v1/search/book.json"
    DETAIL_URL = "https://openapi.naver.com/v1/search/book_adv.json"

    def __init__(self):
        self.client_id = settings.NAVER_CLIENT_ID
        self.client_secret = settings.NAVER_CLIENT_SECRET
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def headers(self) -> dict:
        return {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client

    async def search_books(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """
        Search books using Naver Book API

        Args:
            query: Search query
            page: Page number (1-indexed)
            page_size: Number of items per page (max 100)

        Returns:
            Dictionary with search results
        """
        # Check cache first
        cache_key = f"book_search:{query}:{page}:{page_size}"
        cached = await cache_service.get(cache_key)
        if cached:
            return cached

        client = await self._get_client()

        # Naver API uses 'start' (1-indexed) instead of page
        start = (page - 1) * page_size + 1

        try:
            response = await client.get(
                self.SEARCH_URL,
                headers=self.headers,
                params={
                    "query": query,
                    "display": min(page_size, 100),
                    "start": min(start, 1000),  # Naver API limit
                },
            )
            response.raise_for_status()
            data = response.json()

            # Transform to our format
            result = {
                "items": [self._transform_book(item) for item in data.get("items", [])],
                "total": data.get("total", 0),
                "page": page,
                "page_size": page_size,
                "has_more": start + page_size <= min(data.get("total", 0), 1000),
            }

            # Cache for 1 hour
            await cache_service.set(cache_key, result, ttl=3600)

            return result

        except httpx.HTTPError as e:
            print(f"Naver API error: {e}")
            return {
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "has_more": False,
                "error": str(e),
            }

    async def get_book_by_isbn(self, isbn: str) -> Optional[dict]:
        """
        Get book details by ISBN

        Args:
            isbn: ISBN-10 or ISBN-13

        Returns:
            Book dictionary or None if not found
        """
        # Check cache first
        cache_key = f"book_isbn:{isbn}"
        cached = await cache_service.get(cache_key)
        if cached:
            return cached

        client = await self._get_client()

        # Clean ISBN (remove hyphens)
        clean_isbn = isbn.replace("-", "")

        try:
            response = await client.get(
                self.DETAIL_URL,
                headers=self.headers,
                params={
                    "d_isbn": clean_isbn,
                },
            )
            response.raise_for_status()
            data = response.json()

            items = data.get("items", [])
            if not items:
                return None

            book = self._transform_book(items[0])

            # Cache for 24 hours
            await cache_service.set(cache_key, book, ttl=86400)

            return book

        except httpx.HTTPError as e:
            print(f"Naver API error: {e}")
            return None

    def _transform_book(self, naver_item: dict) -> dict:
        """
        Transform Naver API book item to our format

        Args:
            naver_item: Book item from Naver API

        Returns:
            Transformed book dictionary
        """
        from datetime import date

        # Parse ISBN (can be "ISBN10 ISBN13" format)
        isbn_raw = naver_item.get("isbn", "")
        isbns = isbn_raw.split()
        isbn = isbns[-1] if isbns else ""  # Prefer ISBN-13

        # Parse authors (can be "Author1^Author2" format) and join as string
        authors_raw = naver_item.get("author", "")
        authors = [a.strip() for a in authors_raw.split("^") if a.strip()]
        author = ", ".join(authors) if authors else None

        # Parse publication date
        pubdate = naver_item.get("pubdate", "")
        published_date = None
        if len(pubdate) >= 8:
            try:
                published_date = date(int(pubdate[:4]), int(pubdate[4:6]), int(pubdate[6:8]))
            except ValueError:
                pass
        elif len(pubdate) >= 6:
            try:
                published_date = date(int(pubdate[:4]), int(pubdate[4:6]), 1)
            except ValueError:
                pass
        elif len(pubdate) >= 4:
            try:
                published_date = date(int(pubdate[:4]), 1, 1)
            except ValueError:
                pass

        return {
            "id": None,  # Will be assigned when saved to database
            "isbn": isbn,
            "title": naver_item.get("title", "").replace("<b>", "").replace("</b>", ""),
            "author": author,
            "publisher": naver_item.get("publisher", ""),
            "published_date": published_date,
            "description": naver_item.get("description", "").replace("<b>", "").replace("</b>", ""),
            "cover_image": naver_item.get("image"),
            "category": None,
            "naver_link": naver_item.get("link"),
        }

    async def close(self):
        """Close the HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
