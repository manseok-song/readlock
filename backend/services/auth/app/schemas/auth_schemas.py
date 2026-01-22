"""Auth request/response schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator


class RegisterRequest(BaseModel):
    """Registration request schema."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    nickname: str = Field(..., min_length=2, max_length=20)

    @validator('password')
    def validate_password(cls, v):
        if not any(c.isalpha() for c in v):
            raise ValueError('비밀번호에 영문자가 포함되어야 합니다.')
        if not any(c.isdigit() for c in v):
            raise ValueError('비밀번호에 숫자가 포함되어야 합니다.')
        return v

    @validator('nickname')
    def validate_nickname(cls, v):
        import re
        if not re.match(r'^[가-힣a-zA-Z0-9_]+$', v):
            raise ValueError('닉네임은 한글, 영문, 숫자, 밑줄(_)만 사용 가능합니다.')
        return v


class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str


class OAuthRequest(BaseModel):
    """OAuth login request schema."""
    id_token: str = Field(..., alias="idToken")

    class Config:
        populate_by_name = True


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str = Field(..., alias="refreshToken")

    class Config:
        populate_by_name = True


class UpdateFcmTokenRequest(BaseModel):
    """FCM token update request schema."""
    fcm_token: str = Field(..., alias="fcmToken")
    platform: str = Field(..., pattern="^(android|ios|web)$")

    class Config:
        populate_by_name = True


class UserProfileResponse(BaseModel):
    """User profile response schema."""
    id: str
    user_id: str
    nickname: str
    bio: Optional[str] = None
    profile_image: Optional[str] = None
    reading_goal_min: int = 30
    is_public: bool = True
    level: int = 1
    exp: int = 0
    coins: int = 0
    premium_until: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """User response schema."""
    id: str
    email: str
    profile: UserProfileResponse
    provider: str = "local"
    last_login_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str = Field(..., alias="accessToken")
    refresh_token: str = Field(..., alias="refreshToken")
    expires_in: int = Field(..., alias="expiresIn")
    token_type: str = "bearer"

    class Config:
        populate_by_name = True


class AuthResponse(BaseModel):
    """Auth response schema."""
    user: UserResponse
    tokens: TokenResponse
    is_new_user: bool = Field(default=False, alias="isNewUser")

    class Config:
        populate_by_name = True
