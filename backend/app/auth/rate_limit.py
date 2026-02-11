"""Simple in-memory rate limiter. No external dependencies."""
import time
from collections import defaultdict
from fastapi import Request, HTTPException, status


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]
        if len(self._requests[key]) >= self.max_requests:
            return False
        self._requests[key].append(now)
        return True


# 10 auth attempts per minute per IP
auth_limiter = RateLimiter(max_requests=10, window_seconds=60)
# 20 messages per minute per user
message_limiter = RateLimiter(max_requests=20, window_seconds=60)
# 3 password reset requests per 5 minutes per IP
reset_limiter = RateLimiter(max_requests=3, window_seconds=300)


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_auth_rate(request: Request):
    ip = get_client_ip(request)
    if not auth_limiter.check(f"auth:{ip}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Try again later.",
        )


def check_message_rate(user_id: str):
    if not message_limiter.check(f"msg:{user_id}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many messages. Please wait a moment.",
        )


def check_reset_rate(request: Request):
    ip = get_client_ip(request)
    if not reset_limiter.check(f"reset:{ip}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Try again later.",
        )
