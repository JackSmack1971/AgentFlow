"""Circuit breaker implementation for external service calls.

This module provides circuit breaker functionality for external services to prevent
cascading failures and improve system resilience.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, TypeVar

from pybreaker import CircuitBreaker, CircuitBreakerError

from ..core.settings import get_settings

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

# Global settings
settings = get_settings()


class ServiceCircuitBreaker:
    """Manages circuit breakers for different external services."""

    def __init__(self) -> None:
        self._breakers: dict[str, CircuitBreaker] = {}
        self._setup_breakers()

    def _setup_breakers(self) -> None:
        """Initialize circuit breakers for each service with service-specific configuration."""

        # Mem0 service circuit breaker
        self._breakers["mem0"] = CircuitBreaker(
            failure_threshold=settings.cb_failure_threshold,
            recovery_timeout=settings.cb_recovery_timeout_seconds,
            expected_exception=Exception,
            name="mem0_breaker",
        )

        # Qdrant service circuit breaker
        self._breakers["qdrant"] = CircuitBreaker(
            failure_threshold=settings.cb_failure_threshold,
            recovery_timeout=settings.cb_recovery_timeout_seconds,
            expected_exception=Exception,
            name="qdrant_breaker",
        )

        # R2R service circuit breaker
        self._breakers["r2r"] = CircuitBreaker(
            failure_threshold=settings.cb_failure_threshold,
            recovery_timeout=settings.cb_recovery_timeout_seconds,
            expected_exception=Exception,
            name="r2r_breaker",
        )

        # Neo4j service circuit breaker
        self._breakers["neo4j"] = CircuitBreaker(
            failure_threshold=settings.cb_failure_threshold,
            recovery_timeout=settings.cb_recovery_timeout_seconds,
            expected_exception=Exception,
            name="neo4j_breaker",
        )

        # Set up event listeners for logging
        for name, breaker in self._breakers.items():
            breaker.add_listener(self._create_listener(name))

    def _create_listener(self, service_name: str) -> Any:
        """Create a listener for circuit breaker state changes."""

        def listener(event: Any) -> None:
            if event.event_type == "state_changed":
                logger.warning(
                    "Circuit breaker for %s changed state: %s -> %s",
                    service_name,
                    event.old_state,
                    event.new_state,
                )
            elif event.event_type == "failure":
                logger.warning(
                    "Circuit breaker for %s recorded failure: %s",
                    service_name,
                    str(event.exception),
                )

        return listener

    def get_breaker(self, service_name: str) -> CircuitBreaker:
        """Get the circuit breaker for a specific service."""
        if service_name not in self._breakers:
            raise ValueError(f"Unknown service: {service_name}")
        return self._breakers[service_name]

    def call_with_breaker(
        self,
        service_name: str,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute a function with the circuit breaker for the specified service."""
        breaker = self.get_breaker(service_name)

        try:
            return breaker.call(func, *args, **kwargs)
        except CircuitBreakerError as exc:
            logger.error(
                "Circuit breaker for %s is open. Returning service unavailable.",
                service_name,
            )
            raise ServiceUnavailableError(
                f"Service {service_name} is temporarily unavailable due to circuit breaker"
            ) from exc

    def get_breaker_state(self, service_name: str) -> str:
        """Get the current state of a service's circuit breaker."""
        breaker = self.get_breaker(service_name)
        return breaker.current_state

    def get_all_states(self) -> dict[str, str]:
        """Get the current state of all circuit breakers."""
        return {name: breaker.current_state for name, breaker in self._breakers.items()}


class ServiceUnavailableError(Exception):
    """Raised when a service is unavailable due to circuit breaker being open."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


# Global circuit breaker manager instance
circuit_breaker_manager = ServiceCircuitBreaker()


def get_service_timeout(service_name: str) -> float:
    """Get the configured timeout for a specific service."""
    timeout_map = {
        "mem0": settings.service_timeout_mem0,
        "qdrant": settings.service_timeout_qdrant,
        "r2r": settings.service_timeout_r2r,
        "neo4j": settings.service_timeout_neo4j,
    }

    if service_name not in timeout_map:
        logger.warning("Unknown service %s, using default timeout", service_name)
        return settings.http_timeout

    return timeout_map[service_name]


__all__ = [
    "ServiceCircuitBreaker",
    "ServiceUnavailableError",
    "circuit_breaker_manager",
    "get_service_timeout",
]