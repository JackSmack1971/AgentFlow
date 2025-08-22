from __future__ import annotations


class R2RError(Exception):
    """Base exception for R2R client errors."""


class AuthError(R2RError):
    """Authentication failure."""


class RateLimitedError(R2RError):
    """Rate limit exceeded."""


class UnavailableError(R2RError):
    """Service unavailable or network error."""


class TimeoutError(R2RError):
    """Request timed out."""


class BadRequestError(R2RError):
    """Invalid request sent to server."""


__all__ = [
    "R2RError",
    "AuthError",
    "RateLimitedError",
    "UnavailableError",
    "TimeoutError",
    "BadRequestError",
]
