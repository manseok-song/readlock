"""Rate limiting middleware."""
import time
from typing import Callable, Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.redis import get_redis


class RateLimitExceeded(HTTPException):
    """Rate limit exceeded error."""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "success": False,
                "error": {
                    "code": "RATE_001",
                    "message": "요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요.",
                    "retry_after": retry_after,
                }
            },
            headers={"Retry-After": str(retry_after)},
        )


class RateLimiter:
    """Rate limiter using Redis."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int = 10,
    ):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.window_size = 60  # 1 minute in seconds

    async def is_allowed(self, key: str) -> tuple[bool, int]:
        """
        Check if request is allowed.
        Returns (is_allowed, retry_after_seconds).
        """
        redis = await get_redis()
        current_time = int(time.time())
        window_start = current_time - self.window_size

        # Key for this rate limit window
        rate_key = f"rate_limit:{key}"

        # Remove old entries
        await redis.zremrangebyscore(rate_key, 0, window_start)

        # Count current requests
        current_requests = await redis.zcard(rate_key)

        if current_requests >= self.requests_per_minute:
            # Get oldest request timestamp
            oldest = await redis.zrange(rate_key, 0, 0, withscores=True)
            if oldest:
                retry_after = int(oldest[0][1]) + self.window_size - current_time
                return False, max(retry_after, 1)
            return False, self.window_size

        # Add current request
        await redis.zadd(rate_key, {str(current_time): current_time})
        await redis.expire(rate_key, self.window_size + 1)

        return True, 0

    def get_client_key(self, request: Request) -> str:
        """Get rate limit key for a client."""
        # Try to get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"

        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        return f"ip:{client_ip}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for FastAPI."""

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_size: int = 10,
        exclude_paths: Optional[list[str]] = None,
    ):
        super().__init__(app)
        self.limiter = RateLimiter(requests_per_minute, burst_size)
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json"]

    async def dispatch(self, request: Request, call_next: Callable):
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        client_key = self.limiter.get_client_key(request)
        is_allowed, retry_after = await self.limiter.is_allowed(client_key)

        if not is_allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "error": {
                        "code": "RATE_001",
                        "message": "요청 한도를 초과했습니다.",
                        "retry_after": retry_after,
                    }
                },
                headers={"Retry-After": str(retry_after)},
            )

        response = await call_next(request)
        return response


def rate_limit(requests_per_minute: int = 60):
    """Decorator for rate limiting specific endpoints."""

    def decorator(func: Callable):
        limiter = RateLimiter(requests_per_minute=requests_per_minute)

        async def wrapper(request: Request, *args, **kwargs):
            client_key = limiter.get_client_key(request)
            is_allowed, retry_after = await limiter.is_allowed(client_key)

            if not is_allowed:
                raise RateLimitExceeded(retry_after)

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator
