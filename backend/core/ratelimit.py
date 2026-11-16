"""
Rate limiting utilities using Redis (with in-memory fallback).
Matches rateLimiter.js from the Express implementation.
"""

from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from core.utils import get_redis_client

def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "ip_unknown")

def redis_rate_limit(prefix, limit, window_seconds, key_func, message=None):
    """
    Decorator for rate limiting a DRF view.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(view_instance, request, *args, **kwargs):
            try:
                identifier = key_func(request)
                if not identifier:
                    return view_func(view_instance, request, *args, **kwargs)

                cache = get_redis_client()
                key = f"ratelimit:{prefix}:{identifier}"
                current = cache.incr(key)

                if current == 1:
                    cache.expire(key, window_seconds)

                if current > limit:
                    ttl = cache.ttl(key)
                    retry_after = ttl if ttl > 0 else window_seconds
                    err_msg = (
                        message
                        or f"Too many requests. Please try again in {retry_after} seconds."
                    )
                    return Response(
                        {
                            "success": False,
                            "message": err_msg,
                            "retryAfter": retry_after,
                        },
                        status=status.HTTP_429_TOO_MANY_REQUESTS,
                    )
            except Exception as e:
                # Fail open if rate limiter has any error
                print(f"[RateLimiter] Error: {e}. Failing open.")

            return view_func(view_instance, request, *args, **kwargs)
        return wrapped
    return decorator

# Preconfigured limiters
def register_rate_limit(view_func):
    return redis_rate_limit(
        prefix="register",
        limit=5,
        window_seconds=60,
        key_func=get_client_ip,
        message="Too many registration attempts from this IP. Please wait a minute before trying again.",
    )(view_func)

def send_otp_rate_limit(view_func):
    return redis_rate_limit(
        prefix="send-otp",
        limit=3,
        window_seconds=600,
        key_func=lambda req: (req.data.get("email") or "").lower().strip() or get_client_ip(req),
        message="Too many OTP requests for this email address. Please try again after 10 minutes.",
    )(view_func)

def verify_otp_rate_limit(view_func):
    return redis_rate_limit(
        prefix="verify-otp",
        limit=5,
        window_seconds=600,
        key_func=lambda req: (req.data.get("email") or "").lower().strip() or get_client_ip(req),
        message="Too many incorrect OTP attempts. Please wait 10 minutes before retrying.",
    )(view_func)

def login_rate_limit(view_func):
    def key_fn(req):
        email = (req.data.get("email") or "").lower().strip()
        return f"email:{email}" if email else f"ip:{get_client_ip(req)}"
    return redis_rate_limit(
        prefix="login",
        limit=5,
        window_seconds=600,
        key_func=key_fn,
        message="Too many login attempts. Account temporarily locked for 10 minutes for security.",
    )(view_func)

def fact_check_rate_limit(view_func):
    def key_fn(req):
        if req.user and getattr(req.user, "id", None):
            return str(req.user.id)
        return get_client_ip(req)
    return redis_rate_limit(
        prefix="factcheck",
        limit=30,
        window_seconds=600,
        key_func=key_fn,
        message="Rate limit reached for fact checking queries. Please wait before submitting more claims.",
    )(view_func)

def admin_login_rate_limit(view_func):
    def key_fn(req):
        email = (req.data.get("email") or "").lower().strip()
        return f"admin_email:{email}" if email else f"admin_ip:{get_client_ip(req)}"
    return redis_rate_limit(
        prefix="admin-login",
        limit=5,
        window_seconds=600,
        key_func=key_fn,
        message="Too many administrative login attempts. Admin portal temporarily rate-limited for 10 minutes.",
    )(view_func)
