"""Auth API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.core.database import get_db
from shared.core.response import success_response, error_response
from shared.middleware.auth import get_current_user, TokenData

from ..schemas.auth_schemas import (
    RegisterRequest,
    LoginRequest,
    OAuthRequest,
    RefreshTokenRequest,
    UpdateFcmTokenRequest,
    AuthResponse,
    TokenResponse,
)
from ..services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user."""
    service = AuthService(db)

    result = await service.register(
        email=request.email,
        password=request.password,
        nickname=request.nickname,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_response("USER_002", "이미 사용 중인 이메일입니다."),
        )

    return success_response({
        "user": result["user"],
        "tokens": result["tokens"],
    })


@router.post("/login", response_model=dict)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Login with email and password."""
    service = AuthService(db)

    result = await service.login(
        email=request.email,
        password=request.password,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response(
                "AUTH_001",
                "이메일 또는 비밀번호가 올바르지 않습니다."
            ),
        )

    return success_response({
        "user": result["user"],
        "tokens": result["tokens"],
    })


@router.post("/oauth/{provider}", response_model=dict)
async def oauth_login(
    provider: str,
    request: OAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    """Login with OAuth provider (google/apple/kakao)."""
    if provider not in ["google", "apple", "kakao"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response("AUTH_005", "지원하지 않는 OAuth 제공자입니다."),
        )

    service = AuthService(db)

    result = await service.oauth_login(
        provider=provider,
        id_token=request.id_token,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response("AUTH_005", "OAuth 인증에 실패했습니다."),
        )

    return success_response({
        "user": result["user"],
        "tokens": result["tokens"],
        "isNewUser": result["is_new_user"],
    })


@router.post("/refresh", response_model=dict)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token."""
    service = AuthService(db)

    result = await service.refresh_tokens(request.refresh_token)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response("AUTH_002", "유효하지 않거나 만료된 토큰입니다."),
        )

    return success_response({
        "tokens": result,
    })


@router.delete("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    token_data: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Logout user."""
    service = AuthService(db)
    await service.logout(token_data.user_id)
    return None


@router.patch("/fcm-token", response_model=dict)
async def update_fcm_token(
    request: UpdateFcmTokenRequest,
    token_data: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update FCM token for push notifications."""
    service = AuthService(db)

    await service.update_fcm_token(
        user_id=token_data.user_id,
        fcm_token=request.fcm_token,
        platform=request.platform,
    )

    return success_response({"message": "FCM 토큰이 업데이트되었습니다."})


@router.get("/me", response_model=dict)
async def get_current_user_info(
    token_data: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user information."""
    service = AuthService(db)

    user = await service.get_user_by_id(token_data.user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("USER_001", "사용자를 찾을 수 없습니다."),
        )

    return success_response(user)
