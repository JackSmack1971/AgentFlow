# AGENTS.md: Shared Packages Guidelines

This document provides specific guidance for AI models working with the AgentFlow shared utility packages located in `/packages/`. These guidelines cover shared configurations, utilities, and cross-cutting concerns.

## 1. Project Scope & Architecture
*   **Primary Purpose:** Shared utility packages and configurations used across the AgentFlow platform
*   **Core Technologies:** Python utilities, configuration management, shared types and schemas
*   **Architecture Pattern:** Modular package organization with clear dependency management and versioning

## 2. Package Organization Standards

### Directory Structure
*   **REQUIRED:** Organize packages by functional domain:
    ```
    packages/
    ├── common/               # Common utilities and types
    │   ├── __init__.py
    │   ├── types.py         # Shared type definitions
    │   ├── constants.py     # Application constants
    │   └── exceptions.py    # Common exceptions
    ├── config/              # Configuration management
    │   ├── __init__.py
    │   ├── settings.py      # Base settings classes
    │   └── validation.py    # Config validation
    ├── database/            # Database utilities
    │   ├── __init__.py
    │   ├── connection.py    # Connection management
    │   └── migrations.py    # Migration utilities
    ├── auth/                # Authentication utilities
    │   ├── __init__.py
    │   ├── jwt_handler.py   # JWT token handling
    │   └── permissions.py   # Permission utilities
    ├── monitoring/          # Observability utilities
    │   ├── __init__.py
    │   ├── logging.py       # Structured logging
    │   └── metrics.py       # Metrics collection
    └── r2r/                 # R2R integration utilities
        ├── __init__.py
        ├── config.py        # R2R configuration
        └── client.py        # R2R client wrapper
    ```

### Package Naming and Versioning
*   **REQUIRED:** Use semantic versioning for all packages
*   **MANDATORY:** Include proper `__init__.py` files with version info
*   **CRITICAL:** Maintain backward compatibility within major versions
*   **REQUIRED:** Document API changes in CHANGELOG.md files

## 3. Python Package Standards

### Package Configuration
*   **MANDATORY:** Use `pyproject.toml` for package configuration
*   **REQUIRED:** Include comprehensive metadata and dependencies
*   **CRITICAL:** Pin dependency versions appropriately
*   **REQUIRED:** Configure proper build system and tools

```toml
# packages/common/pyproject.toml
[project]
name = "agentflow-common"
version = "0.1.0"
description = "Common utilities for AgentFlow platform"
requires-python = ">=3.10"
authors = [
    {name = "AgentFlow Team", email = "team@agentflow.io"}
]
keywords = ["agentflow", "utilities", "common"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = [
    "pydantic>=2.8.0",
    "loguru>=0.7.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "black>=23.0",
    "ruff>=0.1.0",
    "mypy>=1.5",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Type Definitions and Schemas
*   **REQUIRED:** Define shared types and schemas in dedicated modules
*   **MANDATORY:** Use Pydantic v2 for all data models
*   **CRITICAL:** Implement proper validation and serialization
*   **REQUIRED:** Export types through package `__init__.py`

```python
# packages/common/types.py
"""Shared type definitions for AgentFlow platform."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from enum import Enum

class AgentStatus(str, Enum):
    """Agent status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TRAINING = "training"
    ERROR = "error"

class BaseAgentFlowModel(BaseModel):
    """Base model for all AgentFlow entities."""
    
    class Config:
        extra = "forbid"
        validate_assignment = True
        use_enum_values = True

class AgentMetadata(BaseAgentFlowModel):
    """Agent metadata schema."""
    
    id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    status: AgentStatus = Field(default=AgentStatus.INACTIVE)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags list."""
        if len(v) > 10:
            raise ValueError("Maximum 10 tags allowed")
        return [tag.lower().strip() for tag in v]

# Export types
__all__ = [
    "AgentStatus",
    "BaseAgentFlowModel", 
    "AgentMetadata"
]
```

### Exception Handling
*   **REQUIRED:** Define custom exceptions for different error types
*   **MANDATORY:** Include proper error messages and context
*   **CRITICAL:** Implement proper exception hierarchy
*   **REQUIRED:** Document exception usage patterns

```python
# packages/common/exceptions.py
"""Common exceptions for AgentFlow platform."""

class AgentFlowError(Exception):
    """Base exception for all AgentFlow errors."""
    
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}

class ValidationError(AgentFlowError):
    """Raised when data validation fails."""
    pass

class ConfigurationError(AgentFlowError):
    """Raised when configuration is invalid."""
    pass

class DatabaseError(AgentFlowError):
    """Raised when database operations fail."""
    pass

class AuthenticationError(AgentFlowError):
    """Raised when authentication fails."""
    pass

class AuthorizationError(AgentFlowError):
    """Raised when authorization fails."""
    pass

class ExternalServiceError(AgentFlowError):
    """Raised when external service calls fail."""
    
    def __init__(self, service: str, message: str, status_code: Optional[int] = None):
        super().__init__(f"{service}: {message}")
        self.service = service
        self.status_code = status_code
```

## 4. Configuration Management

### Settings Classes
*   **REQUIRED:** Use Pydantic Settings for configuration management
*   **MANDATORY:** Implement environment-based configuration
*   **CRITICAL:** Validate all configuration values
*   **REQUIRED:** Support multiple environments (dev, staging, prod)

```python
# packages/config/settings.py
"""Configuration management for AgentFlow platform."""

from typing import Optional, List
from pydantic import Field, validator, AnyHttpUrl
from pydantic_settings import BaseSettings

class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    url: str = Field(..., description="Database connection URL")
    pool_size: int = Field(default=10, ge=1, le=100)
    max_overflow: int = Field(default=20, ge=0, le=100)
    pool_timeout: int = Field(default=30, ge=1, le=300)
    echo_queries: bool = Field(default=False)
    
    class Config:
        env_prefix = "DATABASE_"

class RedisSettings(BaseSettings):
    """Redis configuration settings."""
    
    url: str = Field(default="redis://localhost:6379/0")
    pool_size: int = Field(default=10, ge=1, le=100)
    socket_timeout: int = Field(default=5, ge=1, le=60)
    
    class Config:
        env_prefix = "REDIS_"

class R2RSettings(BaseSettings):
    """R2R configuration settings."""
    
    base_url: AnyHttpUrl = Field(default="http://localhost:7272")
    api_key: Optional[str] = Field(default=None)
    timeout: int = Field(default=30, ge=1, le=300)
    
    class Config:
        env_prefix = "R2R_"

class AgentFlowSettings(BaseSettings):
    """Main application settings."""
    
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    secret_key: str = Field(...)
    allowed_hosts: List[str] = Field(default_factory=list)
    cors_origins: List[str] = Field(default_factory=list)
    
    # Component settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    r2r: R2RSettings = Field(default_factory=R2RSettings)
    
    @validator('environment')
    def validate_environment(cls, v):
        allowed = ['development', 'staging', 'production']
        if v not in allowed:
            raise ValueError(f'Environment must be one of: {allowed}')
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        allowed = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed:
            raise ValueError(f'Log level must be one of: {allowed}')
        return v.upper()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
```

## 5. R2R Integration Package

### R2R Client Wrapper
*   **REQUIRED:** Provide simplified R2R client interface
*   **MANDATORY:** Handle authentication and configuration
*   **CRITICAL:** Implement proper error handling and retries
*   **REQUIRED:** Support both development and production modes

```python
# packages/r2r/client.py
"""R2R client wrapper for AgentFlow integration."""

import os
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path
from .config import R2RConfig, load_config

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

class R2RClient:
    """Simplified R2R client for AgentFlow."""
    
    def __init__(self, config: Optional[R2RConfig] = None):
        self.config = config or load_config()
        self._client = None
    
    @property
    def client(self):
        """Lazy initialization of R2R client."""
        if self._client is None:
            try:
                from r2r import R2RClient as _R2RClient
                self._client = _R2RClient(
                    base_url=str(self.config.base_url),
                    api_key=self.config.api_key
                )
            except ImportError:
                raise ImportError(
                    "R2R client not available. Install with: pip install r2r"
                )
        return self._client
    
    async def health_check(self) -> bool:
        """Check if R2R service is healthy."""
        try:
            health = await self.client.health()
            return health.get("status") == "ok"
        except Exception:
            return False
    
    async def ingest_document(
        self, 
        file_path: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Ingest a document into R2R."""
        try:
            result = await self.client.documents.create(
                file_path=file_path,
                metadata=metadata or {}
            )
            return result
        except Exception as e:
            raise ExternalServiceError("R2R", f"Document ingestion failed: {e}")
    
    async def search(
        self, 
        query: str, 
        limit: int = 10,
        use_hybrid: bool = True,
        use_kg: bool = False
    ) -> Dict[str, Any]:
        """Search documents in R2R."""
        try:
            results = await self.client.retrieval.search(
                query=query,
                limit=limit,
                hybrid_search=use_hybrid,
                knowledge_graph_search=use_kg
            )
            return results
        except Exception as e:
            raise ExternalServiceError("R2R", f"Search failed: {e}")
    
    async def generate_response(
        self, 
        query: str, 
        stream: bool = False,
        include_citations: bool = True
    ) -> Dict[str, Any]:
        """Generate RAG response using R2R."""
        try:
            response = await self.client.retrieval.rag(
                query=query,
                stream=stream,
                include_citations=include_citations
            )
            return response
        except Exception as e:
            raise ExternalServiceError("R2R", f"RAG generation failed: {e}")
```

## 6. Monitoring and Logging Utilities

### Structured Logging
*   **REQUIRED:** Implement structured logging with Loguru
*   **MANDATORY:** Include correlation IDs and request context
*   **CRITICAL:** Filter sensitive information from logs
*   **REQUIRED:** Support multiple output formats and destinations

```python
# packages/monitoring/logging.py
"""Structured logging utilities for AgentFlow."""

import sys
import json
from typing import Dict, Any, Optional
from loguru import logger
from contextvars import ContextVar

# Context variables for request tracking
request_id_context: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_context: ContextVar[Optional[str]] = ContextVar('user_id', default=None)

def setup_logging(
    level: str = "INFO",
    format_json: bool = False,
    include_context: bool = True
) -> None:
    """Configure structured logging for AgentFlow."""
    
    # Remove default handler
    logger.remove()
    
    def format_record(record: Dict[str, Any]) -> str:
        """Format log record with context information."""
        if include_context:
            record["extra"]["request_id"] = request_id_context.get()
            record["extra"]["user_id"] = user_id_context.get()
        
        if format_json:
            # JSON format for production
            log_entry = {
                "timestamp": record["time"].isoformat(),
                "level": record["level"].name,
                "logger": record["name"],
                "message": record["message"],
                "module": record["module"],
                "function": record["function"],
                "line": record["line"],
                **record.get("extra", {})
            }
            if record.get("exception"):
                log_entry["exception"] = record["exception"]["repr"]
            
            return json.dumps(log_entry)
        else:
            # Human-readable format for development
            format_str = (
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            )
            
            if include_context and request_id_context.get():
                format_str += f"<yellow>req:{request_id_context.get()}</yellow> | "
            
            format_str += "<level>{message}</level>"
            return format_str
    
    # Add handler with custom format
    logger.add(
        sys.stdout,
        level=level,
        format=format_record,
        colorize=not format_json,
        serialize=format_json
    )

# Utility functions for context management
def set_request_context(request_id: str, user_id: Optional[str] = None) -> None:
    """Set request context for logging."""
    request_id_context.set(request_id)
    if user_id:
        user_id_context.set(user_id)

def get_contextual_logger(name: str) -> Any:
    """Get logger with contextual information."""
    return logger.bind(logger_name=name)
```

## 7. Database Utilities

### Connection Management
*   **REQUIRED:** Implement async database connection pooling
*   **MANDATORY:** Support multiple database backends
*   **CRITICAL:** Implement proper connection health monitoring
*   **REQUIRED:** Handle connection failures gracefully

```python
# packages/database/connection.py
"""Database connection utilities for AgentFlow."""

import asyncio
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool
from ..config.settings import DatabaseSettings
from ..common.exceptions import DatabaseError

class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self, settings: DatabaseSettings):
        self.settings = settings
        self._engine = None
        self._session_factory = None
    
    @property
    def engine(self):
        """Get or create database engine."""
        if self._engine is None:
            self._engine = create_async_engine(
                self.settings.url,
                poolclass=QueuePool,
                pool_size=self.settings.pool_size,
                max_overflow=self.settings.max_overflow,
                pool_timeout=self.settings.pool_timeout,
                echo=self.settings.echo_queries,
            )
        return self._engine
    
    @property
    def session_factory(self):
        """Get or create session factory."""
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
        return self._session_factory
    
    @asynccontextmanager
    async def get_session(self):
        """Get database session with proper cleanup."""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            async with self.get_session() as session:
                await session.execute("SELECT 1")
                return True
        except Exception:
            return False
    
    async def close(self):
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()

# Global database manager instance
_db_manager: Optional[DatabaseManager] = None

def get_database_manager(settings: Optional[DatabaseSettings] = None) -> DatabaseManager:
    """Get global database manager instance."""
    global _db_manager
    if _db_manager is None:
        if settings is None:
            raise DatabaseError("Database settings required for initialization")
        _db_manager = DatabaseManager(settings)
    return _db_manager
```

## 8. Testing Utilities

### Test Base Classes and Fixtures
*   **REQUIRED:** Provide base test classes for common scenarios
*   **MANDATORY:** Include database test fixtures and cleanup
*   **CRITICAL:** Support async testing patterns
*   **REQUIRED:** Mock external service dependencies

```python
# packages/testing/base.py
"""Base testing utilities for AgentFlow packages."""

import pytest
import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from ..database.connection import DatabaseManager, DatabaseSettings

class BaseAsyncTest:
    """Base class for async tests."""
    
    @pytest.fixture(scope="session")
    def event_loop(self):
        """Create event loop for async tests."""
        loop = asyncio.new_event_loop()
        yield loop
        loop.close()

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide test database session."""
    test_settings = DatabaseSettings(
        url="postgresql+asyncpg://test:test@localhost/test_agentflow"
    )
    db_manager = DatabaseManager(test_settings)
    
    async with db_manager.get_session() as session:
        yield session
    
    await db_manager.close()

@pytest.fixture
def mock_r2r_client():
    """Provide mocked R2R client."""
    mock = AsyncMock()
    mock.health.return_value = {"status": "ok"}
    mock.documents.create.return_value = {"id": "test-doc-id"}
    mock.retrieval.search.return_value = {
        "results": [],
        "metadata": {"total": 0}
    }
    return mock
```

## 9. Package Distribution and Versioning

### Publishing Standards
*   **REQUIRED:** Use semantic versioning for all package releases
*   **MANDATORY:** Include comprehensive CHANGELOG.md files
*   **CRITICAL:** Test packages in isolation before publishing
*   **REQUIRED:** Maintain backward compatibility within major versions

### Dependency Management
*   **REQUIRED:** Pin dependencies with appropriate version ranges
*   **MANDATORY:** Regularly update dependencies for security
*   **CRITICAL:** Test compatibility across supported Python versions
*   **REQUIRED:** Document dependency requirements clearly

## 10. Forbidden Patterns
*   **NEVER** include secrets or credentials in package code
*   **NEVER** use mutable default arguments in function definitions
*   **NEVER** ignore type hints or validation in shared utilities
*   **NEVER** create circular dependencies between packages
*   **NEVER** expose internal implementation details in public APIs
*   **NEVER** skip error handling in utility functions
*   **NEVER** use global state without proper initialization patterns
