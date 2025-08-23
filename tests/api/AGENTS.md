# AGENTS.md: API Testing Patterns & FastAPI Validation Guide

This document provides essential context for AI models working on API-specific testing for the AgentFlow FastAPI backend. These guidelines ensure comprehensive endpoint testing, middleware validation, and HTTP client integration patterns.

## 1. Project Overview & Purpose
*   **Primary Goal:** Comprehensive API testing framework for AgentFlow's FastAPI backend, covering endpoint validation, middleware behavior, authentication flows, rate limiting, and HTTP client integration patterns for AI agent workflows
*   **Business Domain:** API Testing, HTTP Protocol Validation, Middleware Testing, FastAPI Endpoint Testing
*   **Key Features:** 
    - FastAPI TestClient integration with dependency override patterns
    - Middleware testing for correlation IDs, audit logging, rate limiting, and error handling
    - HTTP client retry logic and timeout validation with external service mocking
    - Authentication and authorization testing across multi-tenant scenarios
    - Request/response validation with Pydantic models and structured logging verification

## 2. Core Technologies & Stack
*   **Languages:** Python 3.10+ with async/await patterns, SQL for database validation
*   **Testing Framework:** 
    - pytest 7.x+ with pytest-asyncio for async endpoint testing
    - FastAPI TestClient for synchronous HTTP testing with dependency override support
    - httpx AsyncClient for async HTTP operations and streaming response testing
*   **HTTP & Middleware Testing:** 
    - respx for HTTP request/response mocking and external service simulation
    - Starlette TestClient for low-level ASGI middleware testing
    - pytest-mock for dependency injection and service layer mocking
*   **Key Libraries/Dependencies:** 
    - `fastapi[all]>=0.115.12` - Web framework with automatic OpenAPI generation
    - `httpx>=0.24.0` - Async HTTP client with retry logic and timeout configuration
    - `respx>=0.20.0` - HTTP request mocking for external service integration testing
    - `pytest-mock` - Mock objects and dependency injection for isolated testing
    - `loguru` - Structured logging validation and audit trail testing
*   **Database Testing:** Async SQLAlchemy with test database isolation via session fixtures
*   **Authentication:** JWT token validation, session management, and multi-tenant testing patterns
*   **Package Manager:** uv (Python dependency management with fast resolution)

## 3. API Testing Architecture & Patterns
*   **Overall Architecture:** Layered API testing approach - unit tests for individual endpoints, integration tests for middleware chains, and system tests for complete request flows. Tests validate both successful operations and error conditions with proper HTTP status codes.
*   **API Testing Structure Philosophy:**
    *   `/tests/api/` - FastAPI endpoint testing organized by router modules
    *   `/tests/api/middleware/` - ASGI middleware testing with request/response validation
    *   `/tests/api/auth/` - Authentication and authorization testing patterns
    *   `/tests/api/integration/` - Cross-service API integration with external dependencies
    *   `/tests/api/validation/` - Pydantic model validation and error response testing
*   **Testing Layer Organization:** 
    - Router-level testing mirrors FastAPI app structure (`/app/routers/` → `/tests/api/routers/`)
    - Middleware testing focuses on ASGI middleware chain behavior and error propagation
    - Service integration testing validates business logic layer with database transactions
*   **Common API Testing Patterns:**
    - **Dependency Override:** Using `app.dependency_overrides` to inject test configurations and mock services
    - **Request/Response Validation:** Structured testing of Pydantic request models and response schemas
    - **Error Response Testing:** Validating HTTP status codes, error message format, and Problem Detail compliance
    - **Middleware Chain Testing:** Testing correlation ID propagation, audit logging, and error handling across middleware layers
    - **Authentication Flow Testing:** JWT token validation, session management, and route protection patterns

## 4. API Testing Conventions & Style Guide
*   **Formatting:** Python code follows PEP 8 with Black formatting. Test functions use descriptive names that clearly indicate the scenario being tested
*   **Naming Conventions:** 
    - Test files: `test_{router_name}.py` (e.g., `test_agents.py`, `test_memory.py`, `test_auth.py`)
    - Test functions: `test_{endpoint}_{scenario}_{expected_outcome}` (e.g., `test_create_agent_valid_data_success`)
    - Test classes: `Test{FeatureName}` for grouped related tests (e.g., `TestAgentWorkflows`, `TestMemoryOperations`)
    - Fixtures: `{resource}_fixture` (e.g., `auth_client`, `test_organization`, `mock_ai_service`)
*   **FastAPI TestClient Pattern:**
    ```python
    # test_agents.py
    import pytest
    from fastapi.testclient import TestClient
    from sqlalchemy.ext.asyncio import AsyncSession
    
    from apps.api.app.main import app
    from apps.api.app.dependencies import get_current_user, get_session
    from apps.api.app.db.models import User, Organization
    
    @pytest.fixture
    def client_with_auth(session: AsyncSession) -> TestClient:
        """Provide TestClient with authenticated user override"""
        async def fake_get_current_user() -> User:
            return User(id="test-user", email="test@example.com", roles=["admin"])
        
        async def fake_get_session():
            yield session
        
        app.dependency_overrides[get_current_user] = fake_get_current_user
        app.dependency_overrides[get_session] = fake_get_session
        
        client = TestClient(app, raise_server_exceptions=False)
        yield client
        
        # Cleanup
        app.dependency_overrides.clear()
    
    def test_create_agent_valid_data_success(client_with_auth: TestClient):
        """Test successful agent creation with valid input data"""
        agent_data = {
            "name": "Test Agent",
            "prompt": "You are a helpful assistant",
            "is_active": True
        }
        
        response = client_with_auth.post("/agents/", json=agent_data)
        
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["name"] == agent_data["name"]
        assert response_data["prompt"] == agent_data["prompt"]
        assert "id" in response_data
        assert "created_at" in response_data
    ```
*   **Error Response Testing Pattern:** Validate both HTTP status codes and response body structure for consistent error handling

## 5. Key API Testing Files & Middleware Validation
*   **Core API Test Files:**
    - `test_agents.py` - Agent CRUD operations, workflow execution, and streaming response testing
    - `test_memory.py` - Memory search, update operations, and real-time streaming validation
    - `test_auth.py` - Authentication endpoints, token validation, and session management
    - `test_knowledge.py` - Document upload, processing status, and retrieval operations
*   **Middleware Testing Files:**
    - `test_middleware.py` - Comprehensive middleware chain testing with correlation ID and audit logging
    - `test_rate_limiting.py` - Rate limit enforcement and retry-after header validation
    - `test_error_handling.py` - Error response formatting and problem detail compliance
*   **HTTP Client Integration Testing:**
    ```python
    # test_http_client_retries.py
    import httpx
    import pytest
    import respx
    from apps.api.app.deps import http
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_http_client_retries(monkeypatch):
        """Test HTTP client retry logic with external service failures"""
        monkeypatch.setenv("HTTP_MAX_RETRIES", "3")
        await http.startup_http_client()
        
        # Mock external service responses: 429, 500, then success
        responses = [
            httpx.Response(429),  # Rate limited
            httpx.Response(500),  # Server error
            httpx.Response(200, json={"success": True})  # Success
        ]
        route = respx.get("https://api.external.com/").mock(side_effect=responses)
        
        response = await http.request("GET", "https://api.external.com/")
        
        assert response.status_code == 200
        assert route.call_count == 3  # Validates retry attempts
        await http.shutdown_http_client()
    ```
*   **Audit Logging Validation:**
    ```python
    # test_audit_log_validation.py
    import json
    import uuid
    from loguru import logger
    
    def test_audit_middleware_logs_request_details():
        """Validate that audit middleware captures required request information"""
        app = FastAPI()
        app.add_middleware(CorrelationIdMiddleware)
        app.add_middleware(AuditMiddleware)
        
        captured_logs = []
        logger.remove()
        logger.add(lambda message: captured_logs.append(message), serialize=True)
        
        client = TestClient(app)
        request_id = str(uuid.uuid4())
        response = client.get("/test", headers={"X-Request-ID": request_id})
        
        # Validate audit log structure
        log_record = json.loads(captured_logs[0])["record"]["extra"]
        assert log_record["request_id"] == request_id
        assert log_record["route"] == "/test"
        assert log_record.get("actor") is not None
        assert "tools_called" in log_record
        assert "egress" in log_record
    ```

## 6. API Testing Execution & Configuration
*   **Local Development API Testing:** 
    1. Setup test environment: `uv install --group test`
    2. Start test services: `docker compose -f docker-compose.test.yml up -d`
    3. Run API tests: `pytest tests/api/ -v --cov=apps.api`
    4. Test specific routers: `pytest tests/api/test_agents.py -v`
*   **Test Database Configuration:**
    ```python
    # conftest.py - API testing configuration
    import pytest
    from fastapi.testclient import TestClient
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    
    from apps.api.app.main import app
    from apps.api.app.db.base import Base
    
    @pytest_asyncio.fixture
    async def api_session() -> AsyncSession:
        """Provide isolated test database session for API tests"""
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        Session = async_sessionmaker(engine, expire_on_commit=False)
        async with Session() as session:
            yield session
        await engine.dispose()
    ```
*   **Authentication Testing Setup:**
    ```python
    # Auth testing utilities
    @pytest.fixture
    def auth_headers(test_user: User) -> dict:
        """Generate authentication headers for test requests"""
        token = create_test_jwt_token(test_user.id)
        return {"Authorization": f"Bearer {token}"}
    
    def test_protected_endpoint_requires_auth(client: TestClient):
        """Validate that protected endpoints reject unauthenticated requests"""
        response = client.get("/agents/")
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers
    
    def test_protected_endpoint_accepts_valid_token(client: TestClient, auth_headers: dict):
        """Validate that protected endpoints accept valid authentication"""
        response = client.get("/agents/", headers=auth_headers)
        assert response.status_code == 200
    ```

## 7. API Testing Best Practices & AI Collaboration Guidelines
*   **Dependency Override Patterns:**
    - **Always clean up dependency overrides** after tests to prevent test interference
    - **Use fixture-scoped overrides** for consistent test isolation
    - **Mock external services completely** - never make real HTTP calls to external APIs
    - **Override database dependencies** with test database sessions for data isolation
*   **Request/Response Validation:**
    ```python
    def test_agent_creation_input_validation(client: TestClient):
        """Test comprehensive input validation for agent creation endpoint"""
        invalid_payloads = [
            {},  # Missing required fields
            {"name": ""},  # Empty name
            {"name": "Test", "prompt": ""},  # Empty prompt
            {"name": "A" * 1000, "prompt": "Valid"},  # Name too long
            {"name": "Valid", "prompt": "A" * 10000},  # Prompt too long
            {"name": 123, "prompt": "Valid"},  # Invalid type
        ]
        
        for payload in invalid_payloads:
            response = client.post("/agents/", json=payload)
            assert response.status_code == 422  # Validation error
            error_detail = response.json()["detail"]
            assert isinstance(error_detail, list)  # FastAPI validation error format
    ```
*   **HTTP Status Code Testing:**
    - **Test all expected HTTP status codes** for each endpoint (200, 201, 400, 401, 403, 404, 422, 500)
    - **Validate error response format** follows Problem Detail standard or FastAPI conventions
    - **Test edge cases** like malformed JSON, oversized payloads, and invalid content types
    - **Verify rate limiting responses** include appropriate Retry-After headers
*   **Middleware Chain Testing:**
    ```python
    def test_middleware_execution_order():
        """Validate that middleware executes in correct order with proper context propagation"""
        app = create_test_app_with_middleware()
        execution_log = []
        
        # Add middleware that logs execution order
        app.add_middleware(LoggingMiddleware, log_list=execution_log)
        app.add_middleware(CorrelationIdMiddleware)
        app.add_middleware(AuditMiddleware)
        
        client = TestClient(app)
        response = client.get("/test")
        
        # Validate middleware execution order and context propagation
        assert len(execution_log) > 0
        assert "correlation_id" in execution_log[0]
        assert "audit_context" in execution_log[1]
    ```
*   **Async Endpoint Testing:**
    - **Use AsyncClient for streaming responses** and long-running operations
    - **Test timeout behavior** for endpoints that may take extended time
    - **Validate concurrent request handling** without resource conflicts
    - **Test background task integration** with proper error handling
*   **Database Transaction Testing:**
    ```python
    @pytest.mark.asyncio
    async def test_agent_creation_database_transaction(api_session: AsyncSession):
        """Test that agent creation properly handles database transactions"""
        from apps.api.app.services.agents import create_agent
        from apps.api.app.db.models import Agent
        
        agent_data = {"name": "Test Agent", "prompt": "Test prompt"}
        
        # Test successful creation
        agent = await create_agent(api_session, agent_data)
        await api_session.commit()
        
        # Verify database state
        db_agent = await api_session.get(Agent, agent.id)
        assert db_agent is not None
        assert db_agent.name == agent_data["name"]
    ```
*   **Error Response Consistency:**
    - **Standardize error response format** across all endpoints
    - **Include correlation IDs** in error responses for traceability
    - **Provide actionable error messages** for client applications
    - **Log all error conditions** with sufficient context for debugging
*   **Security Testing Patterns:**
    ```python
    def test_input_sanitization(client: TestClient, auth_headers: dict):
        """Test that endpoints properly sanitize potentially malicious input"""
        malicious_inputs = [
            {"name": "<script>alert('xss')</script>", "prompt": "test"},
            {"name": "'; DROP TABLE agents; --", "prompt": "test"},
            {"name": "test", "prompt": "{{ config.__class__ }}"},  # Template injection
        ]
        
        for payload in malicious_inputs:
            response = client.post("/agents/", json=payload, headers=auth_headers)
            # Should either reject input or sanitize it
            if response.status_code == 201:
                agent_data = response.json()
                # Verify data was sanitized
                assert "<script>" not in agent_data["name"]
                assert "DROP TABLE" not in agent_data["name"]
    ```
*   **Rate Limiting Validation:**
    - **Test rate limit enforcement** with burst requests exceeding limits
    - **Validate Retry-After headers** provide accurate timing information
    - **Test rate limit reset behavior** after time windows expire
    - **Verify rate limiting doesn't affect authenticated vs. anonymous users incorrectly**
*   **Forbidden API Testing Practices:**
    - **NEVER test against production APIs** - use dedicated test environments
    - **NEVER skip cleanup** of test data or dependency overrides
    - **NEVER hardcode sensitive data** in tests - use environment variables or fixtures
    - **NEVER make real external API calls** - mock all external dependencies
    - **NEVER ignore async/await patterns** in async endpoint testing
*   **Integration with Business Logic Testing:**
    - **Test complete user workflows** spanning multiple endpoints
    - **Validate data consistency** across related operations
    - **Test error propagation** from service layer to HTTP response
    - **Verify audit logging** captures all significant operations

## 8. API Testing Validation Checklist
Before completing any API testing work, ensure:

- [ ] All endpoints tested for success scenarios with valid input data and proper authentication
- [ ] Error conditions tested with appropriate HTTP status codes and structured error responses
- [ ] Dependency overrides properly configured and cleaned up to prevent test interference
- [ ] Middleware chain tested with correlation ID propagation and audit logging validation
- [ ] Rate limiting and security features validated with edge cases and malicious input
- [ ] Database transactions tested for data consistency and proper isolation
- [ ] HTTP client integration tested with retry logic, timeouts, and external service mocking
- [ ] Authentication and authorization tested across different user roles and permissions
- [ ] Request/response validation tested with Pydantic models and schema compliance
- [ ] Performance characteristics validated for critical endpoints under normal load conditions
