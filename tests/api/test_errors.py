"""Tests for error taxonomy and codes."""

from apps.api.app.errors import DomainError, ErrorCode, ProviderError
from apps.api.app.exceptions import (
    HealthCheckError,
    InvalidCredentialsError,
    R2RServiceError,
)


def test_r2r_service_error_taxonomy() -> None:
    err = R2RServiceError()
    assert isinstance(err, ProviderError)
    assert err.code is ErrorCode.R2R_SERVICE_ERROR


def test_invalid_credentials_error_taxonomy() -> None:
    err = InvalidCredentialsError()
    assert isinstance(err, DomainError)
    assert err.code is ErrorCode.INVALID_CREDENTIALS


def test_health_check_error_code_and_attr() -> None:
    err = HealthCheckError(service="redis")
    assert isinstance(err, DomainError)
    assert err.service == "redis"
    assert err.code is ErrorCode.HEALTH_CHECK_ERROR
