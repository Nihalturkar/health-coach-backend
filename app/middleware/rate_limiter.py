from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.redis import redis_client


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Per-user rate limiting via Redis. 100 requests per minute per user."""

    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.rpm = requests_per_minute

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting if Redis is unavailable
        if not redis_client:
            return await call_next(request)

        # Extract user identifier (IP for unauthenticated, user_id for authenticated)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # Use token hash as key (lightweight, no DB lookup)
            import hashlib
            key = f"rate:{hashlib.md5(auth_header.encode()).hexdigest()}"
        else:
            client_ip = request.client.host if request.client else "unknown"
            key = f"rate:{client_ip}"

        try:
            current = await redis_client.incr(key)
            if current == 1:
                await redis_client.expire(key, 60)

            if current > self.rpm:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please wait a minute.",
                )
        except HTTPException:
            raise
        except Exception:
            # If Redis fails, don't block the request
            pass

        return await call_next(request)
