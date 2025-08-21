"""Custom exceptions for AgentFlow API."""


class AgentFlowError(Exception):
    """Base class for domain exceptions."""


class R2RServiceError(AgentFlowError):
    """Raised when R2R service integration fails."""


class WorkflowExecutionError(AgentFlowError):
    """Raised when workflow execution fails."""


class MemoryServiceError(AgentFlowError):
    """Raised when memory operations fail."""


class HealthCheckError(AgentFlowError):
    """Raised when service health checks fail."""

    def __init__(self, service: str, message: str):
        super().__init__(message)
        self.service = service


class RBACError(AgentFlowError):
    """Raised when permission checks fail or cannot be completed."""


class SeedError(AgentFlowError):
    """Raised when database seeding operations fail."""


class AuthenticationError(AgentFlowError):
    """Raised when authentication fails."""


class InvalidCredentialsError(AuthenticationError):
    """Raised when user credentials are invalid."""


class TokenError(AuthenticationError):
    """Raised when token generation or validation fails."""


class OTPError(AuthenticationError):
    """Raised when one-time password validation fails."""


class CacheError(AgentFlowError):
    """Raised when cache operations fail."""


class MetricsError(AgentFlowError):
    """Raised when metrics calculations fail."""


class InvalidRatingError(MetricsError):
    """Raised when provided ratings are invalid."""
