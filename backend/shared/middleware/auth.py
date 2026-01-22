"""Authentication middleware and dependencies."""
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import verify_token, TokenData

# HTTP Bearer scheme
security = HTTPBearer(auto_error=False)


class AuthError(HTTPException):
    """Authentication error."""

    def __init__(self, detail: str, code: str = "AUTH_001"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": code,
                    "message": detail,
                }
            },
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenError(HTTPException):
    """Forbidden error."""

    def __init__(self, detail: str = "접근 권한이 없습니다."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "AUTH_004",
                    "message": detail,
                }
            },
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[TokenData]:
    """Get current user from token (optional)."""
    if credentials is None:
        return None

    token_data = verify_token(credentials.credentials, "access")
    if token_data is None:
        return None

    return token_data


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> TokenData:
    """Get current user from token (required)."""
    if credentials is None:
        raise AuthError("인증 토큰이 필요합니다.", "AUTH_001")

    token_data = verify_token(credentials.credentials, "access")

    if token_data is None:
        raise AuthError("유효하지 않거나 만료된 토큰입니다.", "AUTH_002")

    return token_data


async def get_current_user_id(
    token_data: TokenData = Depends(get_current_user),
) -> UUID:
    """Get current user ID."""
    return UUID(token_data.user_id)


async def get_current_user_id_optional(
    token_data: Optional[TokenData] = Depends(get_current_user_optional),
) -> Optional[UUID]:
    """Get current user ID (optional)."""
    if token_data is None:
        return None
    return UUID(token_data.user_id)


def require_premium(
    token_data: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Dependency that requires premium subscription."""
    # This would need to check the database for premium status
    # For now, just pass through
    return token_data


class PermissionChecker:
    """Permission checker for role-based access."""

    def __init__(self, required_permissions: list[str]):
        self.required_permissions = required_permissions

    async def __call__(
        self,
        token_data: TokenData = Depends(get_current_user),
    ) -> TokenData:
        # TODO: Implement permission checking
        # For now, just pass through
        return token_data
