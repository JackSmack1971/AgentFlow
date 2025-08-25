from slowapi import Limiter
from fastapi import Request
import ipaddress


class RateLimiterInitError(Exception):
    """Raised when the rate limiter fails to initialize."""


def get_client_ip(request: Request) -> str:
    """Get client IP with validation of forwarded headers."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for and is_trusted_proxy(request):
        # Take only the first IP and validate format
        client_ip = forwarded_for.split(",")[0].strip()
        if is_valid_ip(client_ip):
            return client_ip
    return request.client.host or "unknown"


def is_trusted_proxy(request: Request) -> bool:
    """Validate trusted proxy (implement proper validation)."""
    # TODO: Implement proper proxy validation based on your infrastructure
    # For now, return False to be secure by default
    # In production, validate against known proxy IPs/ranges
    return False  # Secure default - no forwarded headers trusted


def is_valid_ip(ip: str) -> bool:
    """Validate IP address format."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


try:
    limiter = Limiter(key_func=get_client_ip)
except Exception as exc:  # pragma: no cover - safety
    raise RateLimiterInitError("Limiter initialization failed") from exc
