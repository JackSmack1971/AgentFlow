from slowapi import Limiter
from slowapi.util import get_remote_address


class RateLimiterInitError(Exception):
    """Raised when the rate limiter fails to initialize."""


try:
    limiter = Limiter(key_func=get_remote_address)
except Exception as exc:  # pragma: no cover - safety
    raise RateLimiterInitError("Limiter initialization failed") from exc
