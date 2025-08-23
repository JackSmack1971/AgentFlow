# AGENTS.md: AI Collaboration Guide

This document provides essential context for AI models interacting with this middleware-focused project. Adhering to these guidelines will ensure consistency, maintain code quality, and follow observability best practices.

## 1. Project Overview & Purpose
*   **Primary Goal:** High-performance middleware stack for ASGI applications with comprehensive observability, rate limiting, and structured logging capabilities
*   **Business Domain:** Web Infrastructure, API Middleware, Application Observability
*   **Key Features:** 
    - OpenTelemetry-based distributed tracing and metrics
    - SlowAPI rate limiting for FastAPI/Starlette applications
    - Structured logging with Loguru
    - Production-ready ASGI middleware components
    - Performance monitoring and security controls

## 2. Core Technologies & Stack
*   **Languages:** Python 3.12+ (minimum 3.8+ for compatibility)
*   **Frameworks & Runtimes:** Starlette ASGI framework, FastAPI (when applicable), Uvicorn/Hypercorn for ASGI servers
*   **Databases:** Redis (rate limiting backend), PostgreSQL (application data), time-series databases for metrics storage
*   **Key Libraries/Dependencies:** 
    - `starlette>=0.36,<1.0` - Core ASGI framework
    - `slowapi>=0.1.9` - Rate limiting middleware
    - `opentelemetry-api>=1.47.0` - Observability and tracing
    - `loguru>=0.7.0` - Structured logging
    - `uvicorn[standard]` - ASGI server
    - `redis>=4.3.0` - Rate limiting backend
*   **Platforms:** Linux containers, Kubernetes deployments, cloud platforms (AWS/GCP/Azure)
*   **Package Manager:** uv with `pyproject.toml` and `uv.lock`

## 3. Architectural Patterns & Structure
*   **Overall Architecture:** ASGI middleware stack with layered observability - security middleware first, then authentication, rate limiting, tracing, and finally application logic
*   **Directory Structure Philosophy:**
    *   `/src/middleware/`: Core middleware implementations
    *   `/src/observability/`: OpenTelemetry configuration and custom instrumentation
    *   `/src/logging/`: Loguru configuration and structured logging utilities  
    *   `/src/rate_limiting/`: SlowAPI configuration and custom key functions
    *   `/tests/`: Unit and integration tests with middleware testing patterns
    *   `/config/`: Environment-specific configuration files
    *   `/examples/`: Sample applications demonstrating middleware usage
*   **Module Organization:** Feature-based modules with separate concerns - each middleware component is independently configurable and testable
*   **Common Patterns & Idioms:**
    - **Pure ASGI Middleware:** Avoid BaseHTTPMiddleware, use function-based ASGI middleware for better performance
    - **Context Propagation:** Ensure trace context flows through async operations and service boundaries
    - **Lazy Evaluation:** Use brace formatting in logs to avoid expensive string operations when log level is disabled
    - **Resource Management:** Use context managers and proper cleanup in async operations

## 4. Coding Conventions & Style Guide
*   **Formatting:** Follow PEP 8, use Black formatter with 88-character line length, single quotes preferred
*   **Naming Conventions:** 
    - Variables, functions: `snake_case`
    - Classes: `PascalCase` 
    - Constants: `SCREAMING_SNAKE_CASE`
    - Files: `snake_case.py`
    - Async functions: prefix with `async_` when needed for clarity
*   **API Design:** 
    - Middleware should be composable and order-independent where possible
    - Use dependency injection for configuration
    - Provide both sync and async interfaces where applicable
    - Follow OpenTelemetry semantic conventions for observability
*   **Error Handling:** 
    - Use custom exception classes inheriting from appropriate base exceptions
    - Always propagate trace context in error scenarios
    - Log exceptions with full context using `logger.exception()`
    - Use HTTPException for expected HTTP errors with proper status codes

## 5. Key Files & Entrypoints
*   **Main Entrypoint:** `src/main.py` - Application factory with middleware configuration
*   **Configuration:** 
    - `config/settings.py` - Environment-based configuration using Pydantic BaseSettings
    - `.env` files for environment-specific values
    - `config/logging.py` - Loguru configuration
    - `config/telemetry.py` - OpenTelemetry setup
*   **CI/CD Pipeline:** `.github/workflows/test.yml` - Automated testing, linting, and security checks

## 6. Development & Testing Workflow
*   **Local Development Environment:**
    1. Install dependencies: `uv sync`
    2. Set up pre-commit hooks: `pre-commit install`
    3. Start Redis for rate limiting: `docker run -d -p 6379:6379 redis:7-alpine`
    4. Run application: `uv run uvicorn src.main:app --reload --log-level debug`
*   **Task Configuration:** Use Makefile or just commands for common tasks:
    - `make test` - Run full test suite with coverage
    - `make lint` - Run ruff linting and Black formatting
    - `make type-check` - Run mypy type checking
*   **Testing:** 
    - Use pytest with pytest-asyncio for async test support
    - Test middleware with Starlette TestClient and httpx AsyncClient
    - Mock external services to avoid network calls in tests
    - Maintain >90% test coverage, especially for middleware components
    - Test WebSocket middleware separately using `client.websocket_connect()`
*   **CI/CD Process:** 
    - Automated testing on Python 3.8, 3.9, 3.10, 3.11, 3.12
    - Security scanning with bandit and safety
    - Dependency vulnerability checking
    - Performance regression testing for middleware overhead

## 7. Specific Instructions for AI Collaboration

### OpenTelemetry Implementation
*   **Provider Configuration:** Always initialize TracerProvider, MeterProvider, and LoggerProvider during application startup before any business logic
*   **Span Management:** Use `with tracer.start_as_current_span()` context managers, check `span.is_recording()` before adding expensive attributes
*   **Sampling:** Configure appropriate sampling (1-10% for high-volume services) using TraceIdRatioBased sampler
*   **Collector Usage:** Always use OpenTelemetry Collector in production, never send telemetry directly to backends
*   **Context Propagation:** Ensure trace context flows through async operations and middleware layers

### SlowAPI Rate Limiting
*   **CRITICAL:** All rate-limited endpoints MUST include `request: Request` parameter or rate limiting will silently fail
*   **Decorator Order:** Route decorator (@app.get) MUST come before limit decorator (@limiter.limit)
*   **Middleware Integration:** Use SlowAPIASGIMiddleware instead of legacy SlowAPIMiddleware for better async performance
*   **Storage Backend:** Use Redis backend in production: `storage_uri="redis://localhost:6379/0"`
*   **Custom Key Functions:** Implement user-based or composite rate limiting with custom key functions

### Starlette Framework
*   **Middleware Order:** Security middleware first, then authentication, then application-specific middleware
*   **ASGI Middleware:** Avoid BaseHTTPMiddleware due to cancellation issues - use pure ASGI middleware functions
*   **Request Processing:** Use `await request.json()` for JSON, `await request.form()` for form data, stream large uploads
*   **Background Tasks:** Use `BackgroundTask` for post-response processing instead of fire-and-forget tasks
*   **WebSocket Handling:** Always `await websocket.accept()` before communication, handle disconnections gracefully

### Loguru Logging
*   **Configuration:** Always call `logger.remove()` before adding custom handlers to avoid duplicates
*   **Performance:** Use `enqueue=True` for async applications and multiprocessing safety
*   **Structured Logging:** Use `serialize=True` for JSON output, add context with `.bind()`
*   **Security:** Set `diagnose=False` in production to avoid exposing variable values
*   **Message Formatting:** Use brace formatting (`logger.info("User {name} logged in", name=username)`) for lazy evaluation

### Security & Performance
*   **Input Validation:** Use Pydantic models for all request/response validation
*   **Secrets Management:** All sensitive configuration via environment variables, never hardcode
*   **Rate Limiting:** Implement at multiple layers - global, per-user, per-endpoint
*   **Monitoring:** Expose health check endpoints, implement proper error handling with trace context
*   **Resource Management:** Configure connection pooling, set appropriate timeouts and retries

### Dependencies
*   **Adding Dependencies:** Update requirements.txt with pinned versions for production
*   **Version Compatibility:** Ensure compatible versions between Starlette, FastAPI, and middleware packages
*   **Redis Configuration:** Use connection pooling and appropriate timeout settings

### Commit Messages & Pull Requests
*   **Conventional Commits:** Use `feat:`, `fix:`, `docs:`, `perf:`, `refactor:` prefixes
*   **Breaking Changes:** Include `BREAKING CHANGE:` in commit body when applicable
*   **Testing:** All PRs must include tests for new middleware functionality

### Avoidances/Forbidden Actions
*   **NEVER use BaseHTTPMiddleware** - use pure ASGI middleware for better performance and cancellation handling
*   **NEVER read request.body() in middleware** without buffering and restoring for downstream handlers
*   **NEVER use synchronous exports** in OpenTelemetry - always use batch processors with enqueue=True
*   **NEVER log sensitive data** - implement sanitization functions for PII, credentials, and business data
*   **NEVER bypass rate limiting** - ensure all endpoints have proper request parameter inclusion
*   **NEVER disable security headers** in production - use TrustedHostMiddleware and HTTPSRedirectMiddleware

### Debugging Guidance
*   **Tracing Issues:** Enable debug logging with `OTEL_LOG_LEVEL=debug` and verify context propagation
*   **Rate Limiting Problems:** Test with curl/httpx to verify limiting behavior, check Redis connectivity
*   **Performance Issues:** Monitor middleware overhead, use profiling tools for hot path analysis
*   **WebSocket Issues:** Implement proper cleanup in disconnect handlers to prevent memory leaks

### Pass/Fail Criteria
*   **Tests must pass:** All unit, integration, and middleware-specific tests
*   **Coverage threshold:** Minimum 90% code coverage
*   **Performance benchmarks:** Middleware overhead must not exceed 5% of request processing time
*   **Security scans:** No high-severity vulnerabilities in dependency check
*   **Observability:** All spans must be properly ended, no trace context leaks

### Breaking Down Large Work
*   **Incremental Changes:** Implement one middleware component at a time
*   **Feature Flags:** Use configuration to enable/disable middleware components during development
*   **Testing Strategy:** Test each middleware layer independently before integration
*   **Documentation:** Update examples and README for each new middleware capability
