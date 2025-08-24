"""Security tests for circuit breaker functionality.

Tests cover:
- Circuit breaker state management
- Failure detection and recovery
- Graceful degradation
- Service isolation
- Automatic recovery mechanisms
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from apps.api.app.services.circuit_breaker import (
    ServiceCircuitBreaker,
    ServiceUnavailableError,
    circuit_breaker_manager,
    get_service_timeout
)


class TestCircuitBreakerInitialization:
    """Test circuit breaker initialization and setup."""

    def test_circuit_breaker_manager_creation(self):
        """Test that circuit breaker manager is created properly."""
        manager = ServiceCircuitBreaker()

        expected_services = ["mem0", "qdrant", "r2r", "neo4j"]
        assert len(manager._breakers) == len(expected_services)

        for service in expected_services:
            assert service in manager._breakers
            assert manager._breakers[service] is not None

    def test_individual_breaker_configuration(self):
        """Test that individual circuit breakers are configured correctly."""
        manager = ServiceCircuitBreaker()

        # Test mem0 breaker configuration
        mem0_breaker = manager._breakers["mem0"]
        assert mem0_breaker.name == "mem0_breaker"
        assert mem0_breaker.failure_threshold == 3  # Default from settings
        assert mem0_breaker.expected_exception == Exception

    def test_breaker_state_initialization(self):
        """Test that all breakers start in closed state."""
        manager = ServiceCircuitBreaker()

        for service, breaker in manager._breakers.items():
            assert breaker.current_state == "closed"

    def test_get_breaker_method(self):
        """Test getting circuit breaker for specific service."""
        manager = ServiceCircuitBreaker()

        # Valid service
        breaker = manager.get_breaker("mem0")
        assert breaker is not None
        assert breaker.name == "mem0_breaker"

        # Invalid service
        with pytest.raises(ValueError, match="Unknown service"):
            manager.get_breaker("unknown_service")


class TestCircuitBreakerFunctionality:
    """Test core circuit breaker functionality."""

    def test_successful_operation_keeps_breaker_closed(self):
        """Test that successful operations keep breaker in closed state."""
        manager = ServiceCircuitBreaker()

        def successful_operation():
            return "success"

        # Execute successful operation
        result = manager.call_with_breaker("mem0", successful_operation)
        assert result == "success"

        # Breaker should remain closed
        assert manager.get_breaker_state("mem0") == "closed"

    def test_failure_operation_opens_breaker(self):
        """Test that failed operations eventually open the breaker."""
        manager = ServiceCircuitBreaker()

        def failing_operation():
            raise Exception("Service unavailable")

        # Execute multiple failing operations
        for _ in range(manager.get_breaker("mem0").failure_threshold):
            with pytest.raises(ServiceUnavailableError):
                manager.call_with_breaker("mem0", failing_operation)

        # Breaker should be open
        assert manager.get_breaker_state("mem0") == "open"

    def test_open_breaker_rejects_calls(self):
        """Test that open breaker rejects all calls."""
        manager = ServiceCircuitBreaker()

        def failing_operation():
            raise Exception("Service failure")

        # Force breaker open by exceeding failure threshold
        breaker = manager.get_breaker("mem0")
        for _ in range(breaker.failure_threshold):
            try:
                manager.call_with_breaker("mem0", failing_operation)
            except ServiceUnavailableError:
                pass

        # Now all calls should be rejected
        for _ in range(5):
            with pytest.raises(ServiceUnavailableError, match="temporarily unavailable"):
                manager.call_with_breaker("mem0", lambda: "should not execute")

    def test_breaker_automatic_recovery(self):
        """Test automatic recovery after recovery timeout."""
        import time

        manager = ServiceCircuitBreaker()

        def failing_operation():
            raise Exception("Service failure")

        # Force breaker open
        breaker = manager.get_breaker("mem0")
        for _ in range(breaker.failure_threshold):
            try:
                manager.call_with_breaker("mem0", failing_operation)
            except ServiceUnavailableError:
                pass

        assert manager.get_breaker_state("mem0") == "open"

        # Wait for recovery timeout
        time.sleep(breaker.recovery_timeout + 0.1)

        # Next call should transition to half-open and succeed
        def successful_operation():
            return "recovered"

        result = manager.call_with_breaker("mem0", successful_operation)
        assert result == "recovered"

        # Breaker should be closed again
        assert manager.get_breaker_state("mem0") == "closed"


class TestCircuitBreakerStateManagement:
    """Test circuit breaker state transitions."""

    def test_closed_to_open_transition(self):
        """Test transition from closed to open state."""
        manager = ServiceCircuitBreaker()

        def failing_operation():
            raise Exception("Failure")

        breaker = manager.get_breaker("mem0")

        # Start closed
        assert breaker.current_state == "closed"

        # Trigger failures
        for i in range(breaker.failure_threshold):
            try:
                manager.call_with_breaker("mem0", failing_operation)
            except ServiceUnavailableError:
                pass

        # Should be open
        assert breaker.current_state == "open"

    def test_open_to_half_open_transition(self):
        """Test transition from open to half-open state."""
        import time

        manager = ServiceCircuitBreaker()

        def failing_operation():
            raise Exception("Failure")

        # Force to open state
        breaker = manager.get_breaker("mem0")
        for _ in range(breaker.failure_threshold):
            try:
                manager.call_with_breaker("mem0", failing_operation)
            except ServiceUnavailableError:
                pass

        assert breaker.current_state == "open"

        # Wait for recovery timeout
        time.sleep(breaker.recovery_timeout + 0.1)

        # Next call should transition to half-open
        def successful_operation():
            return "success"

        result = manager.call_with_breaker("mem0", successful_operation)
        assert result == "success"

    def test_half_open_to_closed_on_success(self):
        """Test transition from half-open to closed on successful operation."""
        import time

        manager = ServiceCircuitBreaker()

        def failing_operation():
            raise Exception("Failure")

        # Force to open state
        breaker = manager.get_breaker("mem0")
        for _ in range(breaker.failure_threshold):
            try:
                manager.call_with_breaker("mem0", failing_operation)
            except ServiceUnavailableError:
                pass

        # Wait for recovery timeout
        time.sleep(breaker.recovery_timeout + 0.1)

        # Successful operation should close the breaker
        def successful_operation():
            return "success"

        result = manager.call_with_breaker("mem0", successful_operation)
        assert result == "success"
        assert breaker.current_state == "closed"

    def test_half_open_to_open_on_failure(self):
        """Test transition from half-open to open on failed operation."""
        import time

        manager = ServiceCircuitBreaker()

        def failing_operation():
            raise Exception("Failure")

        # Force to open state
        breaker = manager.get_breaker("mem0")
        for _ in range(breaker.failure_threshold):
            try:
                manager.call_with_breaker("mem0", failing_operation)
            except ServiceUnavailableError:
                pass

        # Wait for recovery timeout
        time.sleep(breaker.recovery_timeout + 0.1)

        # Failed operation should open the breaker again
        with pytest.raises(ServiceUnavailableError):
            manager.call_with_breaker("mem0", failing_operation)

        assert breaker.current_state == "open"


class TestServiceIsolation:
    """Test that circuit breakers isolate services from each other."""

    def test_service_isolation(self):
        """Test that one service's failure doesn't affect others."""
        manager = ServiceCircuitBreaker()

        def failing_operation():
            raise Exception("mem0 failure")

        def successful_operation():
            return "success"

        # Fail mem0 service
        for _ in range(manager.get_breaker("mem0").failure_threshold):
            try:
                manager.call_with_breaker("mem0", failing_operation)
            except ServiceUnavailableError:
                pass

        # mem0 should be open
        assert manager.get_breaker_state("mem0") == "open"

        # Other services should remain closed
        assert manager.get_breaker_state("qdrant") == "closed"
        assert manager.get_breaker_state("r2r") == "closed"
        assert manager.get_breaker_state("neo4j") == "closed"

        # Other services should still work
        result = manager.call_with_breaker("qdrant", successful_operation)
        assert result == "success"

    def test_get_all_states(self):
        """Test getting states of all circuit breakers."""
        manager = ServiceCircuitBreaker()

        states = manager.get_all_states()

        expected_services = ["mem0", "qdrant", "r2r", "neo4j"]
        assert set(states.keys()) == set(expected_services)

        for service in expected_services:
            assert states[service] == "closed"


class TestServiceTimeouts:
    """Test service timeout configuration."""

    def test_get_service_timeout_known_services(self):
        """Test timeout retrieval for known services."""
        # Test each known service
        services = ["mem0", "qdrant", "r2r", "neo4j"]

        for service in services:
            timeout = get_service_timeout(service)
            assert isinstance(timeout, float)
            assert timeout > 0

    def test_get_service_timeout_unknown_service(self):
        """Test timeout for unknown service falls back to default."""
        timeout = get_service_timeout("unknown_service")

        # Should return default timeout
        from apps.api.app.core.settings import get_settings
        settings = get_settings()
        assert timeout == settings.http_timeout


class TestCircuitBreakerErrorHandling:
    """Test error handling in circuit breaker operations."""

    def test_call_with_breaker_success(self):
        """Test successful call with circuit breaker."""
        manager = ServiceCircuitBreaker()

        def operation():
            return "success"

        result = manager.call_with_breaker("mem0", operation)
        assert result == "success"

    def test_call_with_breaker_failure_propagation(self):
        """Test that circuit breaker propagates original exceptions."""
        manager = ServiceCircuitBreaker()

        class CustomError(Exception):
            pass

        def failing_operation():
            raise CustomError("Custom failure")

        # First few calls should propagate original exception
        breaker = manager.get_breaker("mem0")
        for _ in range(breaker.failure_threshold - 1):
            with pytest.raises(CustomError):
                manager.call_with_breaker("mem0", failing_operation)

        # Last call should open breaker and raise ServiceUnavailableError
        with pytest.raises(ServiceUnavailableError):
            manager.call_with_breaker("mem0", failing_operation)

    def test_call_with_breaker_with_args_kwargs(self):
        """Test circuit breaker with function arguments."""
        manager = ServiceCircuitBreaker()

        def operation_with_args(a, b, c=None):
            return f"{a}-{b}-{c}"

        result = manager.call_with_breaker(
            "mem0",
            operation_with_args,
            "arg1",
            "arg2",
            c="arg3"
        )

        assert result == "arg1-arg2-arg3"


class TestCircuitBreakerConcurrency:
    """Test circuit breaker behavior under concurrent load."""

    @pytest.mark.asyncio
    async def test_concurrent_circuit_breaker_calls(self):
        """Test circuit breaker under concurrent operations."""
        manager = ServiceCircuitBreaker()

        async def async_operation():
            def sync_operation():
                return "success"
            return manager.call_with_breaker("mem0", sync_operation)

        # Run multiple concurrent operations
        tasks = [async_operation() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(result == "success" for result in results)

        # Breaker should remain closed
        assert manager.get_breaker_state("mem0") == "closed"

    @pytest.mark.asyncio
    async def test_concurrent_failure_handling(self):
        """Test circuit breaker with concurrent failures."""
        manager = ServiceCircuitBreaker()

        failure_count = 0

        async def failing_async_operation():
            nonlocal failure_count
            failure_count += 1

            def sync_failing_operation():
                raise Exception(f"Failure {failure_count}")

            return manager.call_with_breaker("mem0", sync_failing_operation)

        # Run concurrent failing operations
        tasks = [failing_async_operation() for _ in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Some should raise ServiceUnavailableError when breaker opens
        service_unavailable_errors = [
            r for r in results
            if isinstance(r, ServiceUnavailableError)
        ]

        assert len(service_unavailable_errors) > 0


class TestGlobalCircuitBreakerManager:
    """Test the global circuit breaker manager instance."""

    def test_global_manager_singleton(self):
        """Test that global manager is a singleton."""
        from apps.api.app.services.circuit_breaker import circuit_breaker_manager

        manager1 = circuit_breaker_manager
        manager2 = circuit_breaker_manager

        assert manager1 is manager2

    def test_global_manager_functionality(self):
        """Test that global manager works correctly."""
        from apps.api.app.services.circuit_breaker import circuit_breaker_manager

        def operation():
            return "test"

        result = circuit_breaker_manager.call_with_breaker("mem0", operation)
        assert result == "test"


class TestCircuitBreakerIntegration:
    """Integration tests for circuit breaker with external services."""

    def test_breaker_with_external_service_simulation(self):
        """Test circuit breaker with simulated external service."""
        manager = ServiceCircuitBreaker()

        call_count = 0

        def external_service_simulation():
            nonlocal call_count
            call_count += 1

            # Simulate occasional failures
            if call_count % 7 == 0:  # Fail every 7th call
                raise Exception("Simulated service failure")

            return f"Response {call_count}"

        # Make multiple calls
        successful_calls = 0
        failed_calls = 0

        for _ in range(20):
            try:
                result = manager.call_with_breaker("mem0", external_service_simulation)
                successful_calls += 1
            except ServiceUnavailableError:
                failed_calls += 1
                break  # Stop when breaker opens

        # Should have some successful calls before breaker opens
        assert successful_calls > 0
        assert failed_calls > 0

        # If breaker opened, subsequent calls should fail fast
        if failed_calls > 0:
            for _ in range(5):
                with pytest.raises(ServiceUnavailableError):
                    manager.call_with_breaker("mem0", external_service_simulation)

    def test_breaker_recovery_after_service_restoration(self):
        """Test breaker recovery after external service is restored."""
        import time

        manager = ServiceCircuitBreaker()

        def failing_service():
            raise Exception("Service down")

        # Force breaker open
        breaker = manager.get_breaker("mem0")
        for _ in range(breaker.failure_threshold):
            try:
                manager.call_with_breaker("mem0", failing_service)
            except ServiceUnavailableError:
                pass

        assert manager.get_breaker_state("mem0") == "open"

        # Wait for recovery timeout
        time.sleep(breaker.recovery_timeout + 0.1)

        # Now service is restored
        def restored_service():
            return "Service restored"

        # First call should succeed and close breaker
        result = manager.call_with_breaker("mem0", restored_service)
        assert result == "Service restored"
        assert manager.get_breaker_state("mem0") == "closed"

        # Subsequent calls should succeed
        for _ in range(5):
            result = manager.call_with_breaker("mem0", restored_service)
            assert result == "Service restored"


class TestCircuitBreakerMonitoring:
    """Test circuit breaker monitoring and metrics."""

    def test_breaker_state_monitoring(self):
        """Test monitoring of circuit breaker states."""
        manager = ServiceCircuitBreaker()

        # Initially all closed
        states = manager.get_all_states()
        assert all(state == "closed" for state in states.values())

        # Force one breaker open
        def failing_operation():
            raise Exception("Failure")

        breaker = manager.get_breaker("mem0")
        for _ in range(breaker.failure_threshold):
            try:
                manager.call_with_breaker("mem0", failing_operation)
            except ServiceUnavailableError:
                pass

        # Check states again
        states = manager.get_all_states()
        assert states["mem0"] == "open"
        assert all(state == "closed" for service, state in states.items() if service != "mem0")

    def test_breaker_failure_count_tracking(self):
        """Test tracking of failure counts."""
        manager = ServiceCircuitBreaker()

        def failing_operation():
            raise Exception("Failure")

        breaker = manager.get_breaker("mem0")

        # Track failure count
        initial_failures = breaker.failure_count if hasattr(breaker, 'failure_count') else 0

        for _ in range(breaker.failure_threshold):
            try:
                manager.call_with_breaker("mem0", failing_operation)
            except ServiceUnavailableError:
                pass

        # Failure count should have increased
        if hasattr(breaker, 'failure_count'):
            assert breaker.failure_count > initial_failures