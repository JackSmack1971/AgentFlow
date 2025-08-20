"""Custom exceptions for AgentFlow API."""


class AgentFlowError(Exception):
    """Base class for domain exceptions."""


class R2RServiceError(AgentFlowError):
    """Raised when R2R service integration fails."""


class MemoryServiceError(AgentFlowError):
    """Raised when memory operations fail."""


class HealthCheckError(AgentFlowError):
    """Raised when service health checks fail."""

    def __init__(self, service: str, message: str):
        super().__init__(message)
        self.service = service
