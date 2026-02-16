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
# 1 password reset per 2 minutes per email
reset_email_limiter = RateLimiter(max_requests=1, window_seconds=120)
# 10 password resets per hour per IP (anti-enumeration)
reset_hourly_limiter = RateLimiter(max_requests=10, window_seconds=3600)
# 3 registrations per hour per IP (anti-bot)
register_limiter = RateLimiter(max_requests=3, window_seconds=3600)
# Minimum 5 seconds between messages per user (anti-bot)
message_interval_limiter = RateLimiter(max_requests=1, window_seconds=5)


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


def check_register_rate(request: Request):
    ip = get_client_ip(request)
    if not register_limiter.check(f"reg:{ip}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registrations. Try again later.",
        )


def check_message_rate(user_id: str):
    if not message_limiter.check(f"msg:{user_id}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many messages. Please wait a moment.",
        )


def check_message_interval(user_id: str):
    if not message_interval_limiter.check(f"msg_int:{user_id}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Please wait a few seconds between messages.",
        )


def check_reset_rate(request: Request, email: str | None = None):
    ip = get_client_ip(request)
    # Short window: 3 per 5 min per IP
    if not reset_limiter.check(f"reset:{ip}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Try again later.",
        )
    # Long window: 10 per hour per IP (anti-enumeration)
    if not reset_hourly_limiter.check(f"reset_h:{ip}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Try again later.",
        )
    # Per-email: 1 per 2 min (prevent spamming one mailbox)
    if email and not reset_email_limiter.check(f"reset_e:{email}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Try again later.",
        )
