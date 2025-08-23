# AGENTS.md: FastAPI Backend Guidelines

This document provides specific guidance for AI models working with the AgentFlow FastAPI backend service located in `/apps/api/`. These guidelines are derived from the FastAPI, FastAPI+Pydantic, SlowAPI middleware, and Python development rulesets.

## 1. Project Scope & Architecture
*   **Primary Purpose:** Production-ready FastAPI backend service for AgentFlow platform with router-based organization (auth, memory, rag, agents, health)
*   **Core Technologies:** FastAPI 0.115.12+, Pydantic v2, asyncio, PostgreSQL, Redis, Qdrant integration
*   **Architecture Pattern:** Router-based modular design with `/app/routers/` for endpoints, `/app/services/` for business logic, `/app/models/` for Pydantic schemas

## 2. FastAPI Development Standards

### Project Structure Requirements
*   **MANDATORY:** Use proper package structure with separate modules:
    ```
    app/
    ├── __init__.py
    ├── main.py           # FastAPI app instance
    ├── dependencies.py   # Shared dependencies
    ├── config.py        # Application settings
    ├── routers/         # API route modules
    │   ├── __init__.py
    │   ├── auth.py
    │   ├── agents.py
    │   ├── memory.py
    │   ├── rag.py
    │   └── health.py
    ├── services/        # Business logic layer
    ├── models/          # Pydantic schemas
    └── exceptions.py    # Custom exception classes
    ```

### Application Configuration
*   **REQUIRED:** Use Pydantic Settings for all configuration management
*   **CRITICAL:** Store ALL secrets in environment variables, never hardcode
*   **REQUIRED:** Use `@lru_cache()` decorator for singleton settings objects
*   **MANDATORY:** Configure OpenAPI conditionally for production security

```python
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    
    app_name: str = "AgentFlow API"
    database_url: str
    redis_url: str
    secret_key: str
    openapi_url: str = "/openapi.json"
```

### API Design Standards
*   **MANDATORY:** Use distinct Pydantic models for request (`*Create`, `*Update`) and response (`*Response`) to prevent data leakage
*   **REQUIRED:** Implement proper HTTP status codes (200, 201, 400, 401, 403, 404, 422, 500)
*   **CRITICAL:** Use custom exception classes inheriting from `HTTPException`
*   **REQUIRED:** Include comprehensive OpenAPI documentation with descriptions and examples
*   **MANDATORY:** Implement proper CORS configuration with explicit origins

### Pydantic Model Standards
*   **REQUIRED:** Use Pydantic v2 with `extra='forbid'` for all models
*   **MANDATORY:** Separate input vs response models for security
*   **REQUIRED:** Use proper type annotations and validation
*   **CRITICAL:** Never allow untyped free-text for API surfaces

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    model_config = {"extra": "forbid"}

class AgentResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
```

### Async Programming Requirements
*   **MANDATORY:** Use async/await for ALL I/O operations
*   **REQUIRED:** Use `httpx.AsyncClient` for all HTTP requests with proper timeout and retry logic
*   **CRITICAL:** Implement proper error handling with try/except blocks around async operations
*   **REQUIRED:** Use connection pooling for database and HTTP clients

### Security Requirements
*   **CRITICAL:** All endpoints MUST use Pydantic models for input validation
*   **MANDATORY:** Reject malformed data early with proper error messages
*   **REQUIRED:** Access secrets only via environment variables in `config.py`
*   **MANDATORY:** Implement JWT authentication for protected endpoints
*   **CRITICAL:** Use non-wildcard CORS origins in production

## 3. Rate Limiting with SlowAPI
*   **REQUIRED:** Pin SlowAPI version: `slowapi==0.1.9`
*   **MANDATORY:** Initialize Limiter with appropriate key function
*   **CRITICAL:** Register RateLimitExceeded exception handler

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

## 4. Database Integration
*   **REQUIRED:** Use async database drivers (asyncpg for PostgreSQL)
*   **MANDATORY:** Implement proper connection pooling
*   **CRITICAL:** Use TLS connections in production (`sslmode=verify-full`)
*   **REQUIRED:** Implement proper transaction management
*   **MANDATORY:** Use dependency injection for database sessions

## 5. Testing Standards
*   **MANDATORY:** Write comprehensive tests for ALL endpoints
*   **REQUIRED:** Use pytest with pytest-asyncio for async test support
*   **CRITICAL:** Mock external services to avoid network calls in tests
*   **REQUIRED:** Maintain >90% test coverage
*   **MANDATORY:** Test error conditions and edge cases

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_agent():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/agents", json={"name": "Test Agent"})
    assert response.status_code == 201
```

## 6. Performance Standards
*   **REQUIRED:** API response times: simple p95 <2s, complex p95 <5s
*   **MANDATORY:** Implement proper pagination for list endpoints
*   **REQUIRED:** Use efficient database queries with proper indexing
*   **CRITICAL:** Implement caching where appropriate (Redis)

## 7. Logging and Monitoring
*   **REQUIRED:** Use structured logging with proper log levels
*   **MANDATORY:** Log all errors with sufficient context for debugging
*   **REQUIRED:** Implement health check endpoints (`/health`, `/ready`)
*   **CRITICAL:** Never log sensitive information (passwords, tokens)

## 8. Deployment Requirements
*   **MANDATORY:** Use environment-based configuration
*   **REQUIRED:** Implement graceful shutdown handlers
*   **CRITICAL:** Use non-root users in containers
*   **REQUIRED:** Implement proper signal handling for clean shutdowns

## 9. Forbidden Patterns
*   **NEVER** hardcode secrets or configuration values
*   **NEVER** use synchronous I/O operations in async contexts
*   **NEVER** ignore error handling in async operations
*   **NEVER** expose internal error details to clients
*   **NEVER** use wildcard CORS origins in production
*   **NEVER** skip input validation on any endpoint
