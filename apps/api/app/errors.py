from enum import Enum


class ErrorCode(str, Enum):
    """Enumeration of application error codes."""

    DOMAIN_ERROR = "D000"
    PROVIDER_ERROR = "P000"
    R2R_SERVICE_ERROR = "P001"
    WORKFLOW_EXECUTION_ERROR = "D001"
    MEMORY_SERVICE_ERROR = "D002"
    HEALTH_CHECK_ERROR = "D003"
    RBAC_ERROR = "D004"
    SEED_ERROR = "D005"
    CONFIGURATION_ERROR = "D006"
    AUTHENTICATION_ERROR = "D100"
    INVALID_CREDENTIALS = "D101"
    TOKEN_ERROR = "D102"  # nosec B105
    OTP_ERROR = "D103"
    CACHE_ERROR = "D200"
    METRICS_ERROR = "D300"
    INVALID_RATING = "D301"


class AgentFlowError(Exception):
    """Base sealed error for AgentFlow."""

    def __init__(self, message: str, code: ErrorCode) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class DomainError(AgentFlowError):
    """Base error for domain logic issues."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.DOMAIN_ERROR,
    ) -> None:
        super().__init__(message, code)


class ProviderError(AgentFlowError):
    """Base error for external provider failures."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.PROVIDER_ERROR,
    ) -> None:
        super().__init__(message, code)
