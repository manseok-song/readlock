from typing import Optional, List
from uuid import uuid4
from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from shared.core.database import get_db_session
from ..models.book import Book, UserBook
from ..schemas.book_schemas import UserBookUpdate


class BookService:
    """Service for book operations"""

    async def get_by_id(self, book_id: str) -> Optional[dict]:
        """Get book by ID"""
        async with get_db_session() as session:
            result = await session.execute(
                select(Book).where(Book.id == book_id)
            )
            book = result.scalar_one_or_none()
            return book.to_dict() if book else None

    async def get_by_isbn(self, isbn: str) -> Optional[dict]:
        """Get book by ISBN"""
        clean_isbn = isbn.replace("-", "")
        async with get_db_session() as session:
            result = await session.execute(
                select(Book).where(Book.isbn == clean_isbn)
            )
            book = result.scalar_one_or_none()
            return book.to_dict() if book else None

    async def create_book(self, book_data: dict) -> dict:
        """Create a new book record"""
        async with get_db_session() as session:
            book = Book(
                id=str(uuid4()),
                isbn=book_data.get("isbn"),
                title=book_data["title"],
                author=book_data.get("author") or ", ".join(book_data.get("authors", [])),
                publisher=book_data.get("publisher"),
                published_date=book_data.get("published_date"),
                description=book_data.get("description"),
                cover_image=book_data.get("cover_image") or book_data.get("cover_image_url"),
                category=book_data.get("category"),
                page_count=book_data.get("page_count"),
                naver_link=book_data.get("naver_link") or book_data.get("link"),
            )
            session.add(book)
            await session.commit()
            await session.refresh(book)
            return book.to_dict()

    async def get_user_books(
        self,
        user_id: str,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """Get user's book library"""
        async with get_db_session() as session:
            query = select(UserBook).where(UserBook.user_id == user_id)

            if status:
                query = query.where(UserBook.status == status)

            # Count total
            count_result = await session.execute(
                select(UserBook.id).where(UserBook.user_id == user_id)
            )
            total = len(count_result.all())

            # Paginate
            query = query.order_by(UserBook.updated_at.desc())
            query = query.offset((page - 1) * page_size).limit(page_size)

            result = await session.execute(query)
            user_books = result.scalars().all()

            return {
                "items": [ub.to_dict() for ub in user_books],
                "total": total,
                "page": page,
                "page_size": page_size,
                "has_more": page * page_size < total,
            }

    async def add_to_library(
        self,
        user_id: str,
        book_id: str,
        status: str = "wishlist",
    ) -> dict:
        """Add a book to user's library"""
        async with get_db_session() as session:
            # Check if already exists
            existing = await session.execute(
                select(UserBook).where(
                    and_(
                        UserBook.user_id == user_id,
                        UserBook.book_id == book_id,
                    )
                )
            )
            if existing.scalar_one_or_none():
                raise ValueError("Book already in library")

            user_book = UserBook(
                id=str(uuid4()),
                user_id=user_id,
                book_id=book_id,
                status=status,
                current_page=0,
                started_at=datetime.utcnow() if status == "reading" else None,
            )
            session.add(user_book)
            await session.commit()
            await session.refresh(user_book)
            return user_book.to_dict()

    async def update_user_book(
        self,
        user_id: str,
        user_book_id: str,
        data: UserBookUpdate,
    ) -> Optional[dict]:
        """Update a user's book"""
        async with get_db_session() as session:
            result = await session.execute(
                select(UserBook).where(
                    and_(
                        UserBook.id == user_book_id,
                        UserBook.user_id == user_id,
                    )
                )
            )
            user_book = result.scalar_one_or_none()
            if not user_book:
                return None

            # Update fields
            if data.status is not None:
                old_status = user_book.status
                user_book.status = data.status

                # Track status changes
                if data.status == "reading" and old_status != "reading":
                    user_book.started_at = datetime.utcnow()
                elif data.status == "completed" and old_status != "completed":
                    user_book.finished_at = datetime.utcnow()

            if data.current_page is not None:
                user_book.current_page = data.current_page

            if data.total_pages is not None:
                user_book.total_pages = data.total_pages

            user_book.updated_at = datetime.utcnow()

            await session.commit()
            await session.refresh(user_book)
            return user_book.to_dict()

    async def remove_from_library(
        self,
        user_id: str,
        user_book_id: str,
    ) -> bool:
        """Remove a book from user's library"""
        async with get_db_session() as session:
            result = await session.execute(
                select(UserBook).where(
                    and_(
                        UserBook.id == user_book_id,
                        UserBook.user_id == user_id,
                    )
                )
            )
            user_book = result.scalar_one_or_none()
            if not user_book:
                return False

            await session.delete(user_book)
            await session.commit()
            return True
