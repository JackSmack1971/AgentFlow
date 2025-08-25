# AGENTS.md: AI Collaboration Guide - Observability Module

This document provides essential context for AI models interacting with the observability module of the AgentFlow API. This module is responsible for distributed tracing, logging correlation, and monitoring infrastructure that enables production-grade observability across the entire platform.

## 1. Project Overview & Purpose

* **Primary Goal:** The observability module provides comprehensive monitoring, tracing, and logging capabilities for the AgentFlow API, enabling distributed tracing across AI agent workflows, memory operations, RAG queries, and tool executions.
* **Business Domain:** Production observability, distributed systems monitoring, application performance monitoring (APM), and operational intelligence for AI agent platforms.
* **Key Features:**
  - OpenTelemetry-compliant distributed tracing with automatic instrumentation
  - Structured logging with trace correlation using request IDs
  - Middleware-based request auditing and performance tracking
  - Health check endpoints for service monitoring
  - Error tracking and exception correlation across the entire request lifecycle

## 2. Core Technologies & Stack

* **Languages:** Python 3.11+ (primary), with OpenTelemetry SDK integration
* **Frameworks & Runtimes:** 
  - FastAPI 0.115.12+ with async/await patterns
  - OpenTelemetry Python SDK (latest stable) for distributed tracing
  - Loguru for structured logging with JSON serialization
  - Starlette middleware framework for request processing
* **Databases:** N/A (observability data exported to external systems)
* **Key Libraries/Dependencies:**
  - `opentelemetry-api` and `opentelemetry-sdk` (core telemetry)
  - `opentelemetry-exporter-otlp-proto-http` (OTLP HTTP exporter)
  - `loguru` (structured logging with context variables)
  - `starlette` (middleware base classes)
  - `fastapi` (HTTP framework integration)
* **Package Managers:** uv (Python dependency management)
* **Platforms:** Production deployment supports OpenTelemetry Collector, Jaeger, and OTEL-compatible backends

## 3. Architectural Patterns & Structure

* **Overall Architecture:** Middleware-based observability layer that wraps all FastAPI requests with tracing, logging, and auditing capabilities. Follows the "observability as a cross-cutting concern" pattern with minimal performance impact.
* **Directory Structure Philosophy:**
  - `/apps/api/app/observability/` - Core observability module with tracing setup
  - `/apps/api/app/middleware/` - HTTP middleware for correlation, audit, and error handling
  - `/apps/api/app/utils/logging.py` - Logging utilities and context variable management
  - `/apps/api/app/routers/health.py` - Health check endpoints for monitoring
* **Module Organization:** 
  - `tracing.py`: OpenTelemetry setup, provider configuration, and span management
  - Middleware integration: correlation ID, audit logging, and request tracking
  - Context variables: thread-safe request ID propagation across async operations
* **Common Patterns & Idioms:**
  - **Best-effort observability**: All observability code uses try/except blocks to prevent application failures
  - **Context propagation**: Request IDs flow through context variables and OpenTelemetry spans
  - **Structured logging**: JSON-formatted logs with trace correlation fields
  - **Middleware composition**: Layered middleware approach for separation of concerns
  - **Resource attribution**: Proper service.name and service.version attributes for telemetry data

## 4. Coding Conventions & Style Guide

* **Formatting:** 
  - Python: Follow PEP 8 and use Black for formatting with 100-character line length
  - OpenTelemetry: Use semantic conventions for span names and attributes
  - Logging: Structured JSON format with consistent field naming
* **Naming Conventions:**
  - Functions: `snake_case` (e.g., `setup_tracing`, `add_request_id_to_current_span`)
  - Classes: `PascalCase` for middleware (e.g., `CorrelationIdMiddleware`, `AuditMiddleware`)
  - Constants: `SCREAMING_SNAKE_CASE` for configuration values
  - Span names: Follow OpenTelemetry semantic conventions (e.g., `http.server.request`)
* **API Design Principles:**
  - **Non-blocking observability**: Tracing and logging must never block application logic
  - **Graceful degradation**: Observability failures should be logged but not propagate
  - **Minimal overhead**: Instrument only meaningful operations to avoid performance impact
  - **Context preservation**: Maintain trace context across async boundaries and middleware layers
* **Documentation Style:**
  - Use comprehensive docstrings for all public functions
  - Include type hints for all parameters and return values
  - Document OpenTelemetry semantic conventions usage
* **Error Handling:**
  - Use custom exception classes for middleware errors (`MiddlewareError`, `CorrelationIdError`)
  - All observability code wrapped in try/except with debug logging
  - Proper exception chaining for debugging while maintaining application stability
* **Forbidden Patterns:**
  - **NEVER** let observability code crash the main application logic
  - **NEVER** use synchronous I/O operations in tracing or logging code
  - **NEVER** log sensitive data (PII, credentials, tokens) without proper sanitization
  - **NEVER** create spans or metrics without checking `span.is_recording()` first
  - **NEVER** block on span operations or export failures

## 5. Key Files & Entrypoints

* **Main Entrypoints:**
  - `apps/api/app/observability/tracing.py` - OpenTelemetry configuration and span management
  - `apps/api/app/main.py` - Application startup with observability initialization
  - `apps/api/app/middleware/correlation.py` - Request ID correlation middleware
  - `apps/api/app/middleware/audit.py` - Request auditing and performance tracking
* **Configuration:**
  - Environment variables: `OTEL_SERVICE_NAME`, `OTEL_EXPORTER_OTLP_ENDPOINT`
  - Settings in `apps/api/app/config.py` with `app_name` and `log_level` configuration
  - OpenTelemetry auto-configuration through standard environment variables
* **Health Endpoints:** `apps/api/app/routers/health.py` with `/health` and `/ready` endpoints

## 6. Development & Testing Workflow

* **Local Development Environment:**
  - Install dependencies: `uv sync` from project root
  - Run with tracing: `uvicorn apps.api.app.main:app --reload`
  - View traces locally: Set `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318`
  - Test observability: Use `/health` endpoint and check logs for trace correlation
* **Task Configuration:**
  - No custom tasks - observability is automatically initialized at startup
  - Configuration through environment variables and FastAPI dependency injection
  - Use `setup_tracing(service_name)` function for manual initialization in tests
* **Testing:**
  - Unit tests in `tests/api/test_middleware.py` verify correlation ID and span attribution
  - Test observability with `TestClient` and mock OpenTelemetry exporters
  - Verify trace context propagation across middleware layers
  - Test graceful degradation when OpenTelemetry dependencies are missing
* **CI/CD Process:**
  - Linting includes observability code style checks
  - Tests run with and without OpenTelemetry dependencies installed
  - Performance benchmarks ensure observability overhead stays under 5ms per request

## 7. Specific Instructions for AI Collaboration

* **Contribution Guidelines:**
  - All observability changes must maintain backward compatibility
  - New instrumentation requires corresponding test coverage
  - Follow OpenTelemetry semantic conventions for new span attributes
  - Ensure all observability code includes proper error handling
* **Security:**
  - Never log or trace sensitive information (passwords, tokens, PII)
  - Use attribute filtering for production deployments
  - Sanitize request bodies and headers before adding to spans
  - Validate all environment variable inputs for observability configuration
* **Dependencies:**
  - Use optional imports for OpenTelemetry to support environments without tracing
  - Pin OpenTelemetry versions to avoid breaking changes in instrumentation
  - Test observability code with `opentelemetry-distro` for auto-instrumentation
* **Commit Messages & Pull Requests:**
  - Use conventional commits: `feat(observability):`, `fix(tracing):`, `perf(logging):`
  - Include performance impact analysis for new instrumentation
  - Test observability changes in isolation to verify no application impact
* **Avoidances/Forbidden Actions:**
  - **DO NOT** add heavy instrumentation to hot paths (request processing loops)
  - **DO NOT** modify core OpenTelemetry configuration without team review
  - **DO NOT** remove existing trace correlation without migration plan
  - **DO NOT** add synchronous operations to async observability code
  - **DO NOT** hardcode observability backend endpoints or credentials
* **Debugging Guidance:**
  - Use `OTEL_LOG_LEVEL=debug` to diagnose export issues
  - Check correlation between logs and traces using request_id fields
  - Verify span hierarchy using trace visualization tools
  - Test context propagation across middleware boundaries
* **OpenTelemetry Best Practices:**
  - Initialize providers early in application startup (before business logic)
  - Use batch span processors for production (never simple processors)
  - Configure appropriate resource attributes (service.name, service.version)
  - Implement proper sampling strategies for high-throughput environments
  - Always use OpenTelemetry Collector in production (never direct exports)
* **Performance Considerations:**
  - Check `span.is_recording()` before adding expensive attributes
  - Limit span attribute cardinality to prevent memory issues
  - Use lazy evaluation for complex span attribute computation
  - Monitor observability overhead and adjust instrumentation accordingly
* **Production Deployment:**
  - Configure OTLP endpoint to point to OpenTelemetry Collector
  - Enable compression for trace exports (`gzip`)
  - Set appropriate batch sizes and timeout values
  - Implement health checks for observability export success
  - Monitor observability pipeline health and export failure rates

## OpenTelemetry Integration Patterns

The observability module follows these specific patterns for OpenTelemetry integration:

### Tracing Setup
```python
# Initialize tracing early in application lifecycle
resource = Resource.create({"service.name": service_name})
provider = TracerProvider(resource=resource)
span_exporter = exporter or OTLPSpanExporter()
processor = BatchSpanProcessor(span_exporter)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
```

### Request Correlation
```python
# Propagate request IDs through context variables and spans
request_id = request_id_ctx_var.get()
span = trace.get_current_span()
if span and span.is_recording():
    span.set_attribute("request_id", request_id)
```

### Error Handling
```python
# Always wrap observability code in try/except
try:
    # OpenTelemetry operations
    span.set_attribute("operation", "example")
except Exception as exc:
    logger.debug("span_attribute_skipped", error=str(exc))
```

This observability module enables comprehensive monitoring of the AgentFlow platform while maintaining high performance and reliability standards essential for production AI agent deployments.
