"""Custom exceptions for AgentFlow API."""

class AgentFlowError(Exception):
    """Base class for domain exceptions."""

class R2RServiceError(AgentFlowError):
    """Raised when R2R service integration fails."""

class MemoryServiceError(AgentFlowError):
    """Raised when memory operations fail."""
