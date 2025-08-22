"""Custom exceptions for AgentFlow API."""

from __future__ import annotations

from .errors import AgentFlowError, DomainError, ErrorCode, ProviderError

__all__ = [
    "AgentFlowError",
    "R2RServiceError",
    "WorkflowExecutionError",
    "MemoryServiceError",
    "HealthCheckError",
    "RBACError",
    "SeedError",
    "AuthenticationError",
    "InvalidCredentialsError",
    "TokenError",
    "OTPError",
    "CacheError",
    "MetricsError",
    "InvalidRatingError",
]
# noqa: F401


class R2RServiceError(ProviderError):
    """Raised when R2R service integration fails."""

    def __init__(
        self,
        message: str = "R2R service integration failed",
    ) -> None:
        super().__init__(message, ErrorCode.R2R_SERVICE_ERROR)


class WorkflowExecutionError(DomainError):
    """Raised when workflow execution fails."""

    def __init__(self, message: str = "Workflow execution failed") -> None:
        super().__init__(message, ErrorCode.WORKFLOW_EXECUTION_ERROR)


class MemoryServiceError(DomainError):
    """Raised when memory operations fail."""

    def __init__(self, message: str = "Memory operation failed") -> None:
        super().__init__(message, ErrorCode.MEMORY_SERVICE_ERROR)


class HealthCheckError(DomainError):
    """Raised when service health checks fail."""

    def __init__(
        self, service: str, message: str = "Service health check failed"
    ) -> None:
        super().__init__(message, ErrorCode.HEALTH_CHECK_ERROR)
        self.service = service


class RBACError(DomainError):
    """Raised when permission checks fail or cannot be completed."""

    def __init__(self, message: str = "Permission check failed") -> None:
        super().__init__(message, ErrorCode.RBAC_ERROR)


class SeedError(DomainError):
    """Raised when database seeding operations fail."""

    def __init__(self, message: str = "Database seeding failed") -> None:
        super().__init__(message, ErrorCode.SEED_ERROR)


class AuthenticationError(DomainError):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        code: ErrorCode = ErrorCode.AUTHENTICATION_ERROR,
    ) -> None:
        super().__init__(message, code)


class InvalidCredentialsError(AuthenticationError):
    """Raised when user credentials are invalid."""

    def __init__(self, message: str = "Invalid credentials") -> None:
        super().__init__(message, ErrorCode.INVALID_CREDENTIALS)


class TokenError(AuthenticationError):
    """Raised when token generation or validation fails."""

    def __init__(self, message: str = "Token error") -> None:
        super().__init__(message, ErrorCode.TOKEN_ERROR)


class OTPError(AuthenticationError):
    """Raised when one-time password validation fails."""

    def __init__(self, message: str = "OTP validation failed") -> None:
        super().__init__(message, ErrorCode.OTP_ERROR)


class CacheError(DomainError):
    """Raised when cache operations fail."""

    def __init__(self, message: str = "Cache operation failed") -> None:
        super().__init__(message, ErrorCode.CACHE_ERROR)


class MetricsError(DomainError):
    """Raised when metrics calculations fail."""

    def __init__(self, message: str = "Metrics calculation failed") -> None:
        super().__init__(message, ErrorCode.METRICS_ERROR)


class InvalidRatingError(MetricsError):
    """Raised when provided ratings are invalid."""

    def __init__(self, message: str = "Invalid rating") -> None:
        super().__init__(message)
        self.code = ErrorCode.INVALID_RATING
