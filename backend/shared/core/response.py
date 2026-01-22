"""Standard API response schemas."""
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Error detail schema."""
    code: str
    message: str
    details: Optional[Any] = None


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    page: int
    limit: int
    total: int
    total_pages: int

    @classmethod
    def create(cls, page: int, limit: int, total: int) -> "PaginationMeta":
        return cls(
            page=page,
            limit=limit,
            total=total,
            total_pages=(total + limit - 1) // limit if limit > 0 else 0,
        )


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    success: bool = True
    data: Optional[T] = None
    meta: Optional[PaginationMeta] = None
    error: Optional[ErrorDetail] = None

    @classmethod
    def ok(cls, data: T, meta: Optional[PaginationMeta] = None) -> "ApiResponse[T]":
        """Create a success response."""
        return cls(success=True, data=data, meta=meta)

    @classmethod
    def paginated(
        cls,
        data: T,
        page: int,
        limit: int,
        total: int,
    ) -> "ApiResponse[T]":
        """Create a paginated response."""
        return cls(
            success=True,
            data=data,
            meta=PaginationMeta.create(page, limit, total),
        )

    @classmethod
    def error(
        cls,
        code: str,
        message: str,
        details: Optional[Any] = None,
    ) -> "ApiResponse[None]":
        """Create an error response."""
        return cls(
            success=False,
            error=ErrorDetail(code=code, message=message, details=details),
        )


def success_response(
    data: Any = None,
    meta: Optional[dict] = None,
) -> dict:
    """Create a success response dictionary."""
    response = {"success": True}
    if data is not None:
        response["data"] = data
    if meta is not None:
        response["meta"] = meta
    return response


def error_response(
    code: str,
    message: str,
    details: Optional[Any] = None,
) -> dict:
    """Create an error response dictionary."""
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details,
        }
    }


def paginated_response(
    items: list,
    page: int,
    limit: int,
    total: int,
) -> dict:
    """Create a paginated response dictionary."""
    return {
        "success": True,
        "data": {"items": items},
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 0,
        }
    }
