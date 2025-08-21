# AGENTS.md: AI Collaboration Guide

This document provides essential context for AI models interacting with this project. Adhering to these guidelines will ensure consistency, maintain code quality, and optimize agent performance.

<!-- It is Tuesday, August 19, 2025. This guide is optimized for clarity, efficiency, and maximum utility for modern AI coding agents working on the AgentFlow platform. -->

<!-- This file should be placed at the root of your repository. More deeply-nested AGENTS.md files (e.g., in subdirectories) will take precedence for specific sub-areas of the codebase. Direct user prompts will always override instructions in this file. -->

## 1. Project Overview & Purpose

*   **Primary Goal:** AgentFlow is a comprehensive AI agent development platform that unifies six leading frameworks (LangGraph, MCP, Mem0, R2R, Pydantic AI, AG2) to solve the three critical challenges in AI agent development: reliable orchestration, persistent memory management, and structured knowledge integration. The platform aims to reduce agent development time by 60-80% compared to custom integration approaches.
*   **Business Domain:** AI/ML Platform Development, specifically focused on autonomous agent development tools and enterprise AI infrastructure.
*   **Key Features:** Multi-level memory management, visual workflow orchestration, standardized tool integration via MCP protocol, advanced RAG capabilities, and production-ready deployment automation.
*   **Mem0 Purpose:** Provides persistent vector memory with user, session, and
    agent scopes. Lookups must complete in under 50ms.

## 2. Core Technologies & Stack

*   **Languages:** Python 3.10+, TypeScript (for frontend components), JavaScript (Node.js for some tooling)
*   **Frameworks & Runtimes:** FastAPI 0.115.12, Uvicorn ASGI server, Pydantic v2, LangGraph, Mem0, R2R, MCP (Model Context Protocol)
*   **Databases:** PostgreSQL 16 (primary data store), Redis 7 (caching and sessions), Qdrant (vector database), Neo4j 5 (knowledge graphs)
*   **Key Libraries/Dependencies:** 
    - `pydantic-ai-slim[openai]` for typed agent interfaces
    - `mcp[cli]` for tool integration protocol
    - `mem0` for multi-level memory management
    - `r2r` for production RAG capabilities
    - `langgraph-checkpoint-postgres` and `langgraph-checkpoint-redis` for workflow persistence
    - `httpx` for async HTTP client operations
    - `loguru` for structured logging
*   **Platforms:** Linux containers (Docker), Kubernetes for orchestration, Multi-cloud support (AWS, Azure, GCP)
*   **Package Manager:** `uv` (preferred modern Python package manager), fallback to `pip` for compatibility

## 3. Architectural Patterns

*   **Overall Architecture:** Multi-service platform with API gateway pattern. FastAPI serves as the central API gateway coordinating between specialized services: MCP server for tool integration, memory services (Mem0), RAG services (R2R), and workflow orchestration (LangGraph). The architecture follows microservices principles with clear separation of concerns.
*   **Directory Structure Philosophy:**
    *   `/apps`: Application services - contains the main API service and MCP server
    *   `/scripts`: Development and deployment automation scripts
    *   `/tests`: All unit and integration tests (currently minimal, needs expansion)
    *   `/infra`: Infrastructure configuration files (R2R configs, etc.)
    *   `/packages`: Shared libraries and utilities (e.g., R2R client wrapper)
    *   Root level: Project configuration, documentation, and environment setup
*   **Module Organization:** FastAPI application follows domain-driven design with routers organized by feature (auth, memory, rag, agents), services layer for business logic, and models for data schemas. Each major framework integration (LangGraph, Mem0, R2R) has dedicated service modules.

## 4. Coding Conventions & Style Guide

*   **Formatting:** Follows Python PEP 8 with modern enhancements. Use Black for code formatting, isort for import sorting, and flake8 for linting. Line length: 88 characters (Black default). Use double quotes for strings.
*   **Naming Conventions:** 
    - Variables, functions, modules: `snake_case`
    - Classes, Pydantic models: `PascalCase`
    - Constants: `SCREAMING_SNAKE_CASE`
    - Files: `snake_case.py`
    - API endpoints: `/kebab-case` for URLs
*   **API Design:** RESTful API design with clear resource hierarchies. Use Pydantic models for all request/response schemas. Implement proper HTTP status codes, consistent error responses, and comprehensive input validation. Follow async/await patterns throughout.
*   **Common Patterns & Idioms:**
    - **Dependency Injection:** Use FastAPI's dependency system for database sessions, authentication, and service injection
    - **Type Safety:** Extensive use of Python type hints and Pydantic models for data validation
    - **Async Programming:** Consistent async/await usage, avoid blocking operations
    - **Configuration:** Environment-based configuration using Pydantic Settings
    - **Memory Management:** Multi-level scoping (user/agent/session) via Mem0 integration
    - **Error Handling:** Structured error responses with HTTPException and proper logging
*   **Error Handling:** Use FastAPI's HTTPException for API errors with appropriate status codes. Implement global exception handlers for consistent error responses. Log errors with structured context using loguru. Validate all inputs with Pydantic models and handle ValidationError appropriately.

## 5. Key Files & Entrypoints

*   **Main Entrypoint:** `apps/api/app/main.py` - FastAPI application with router configuration and middleware setup
*   **MCP Server:** `apps/mcp/server.py` - Standalone MCP protocol server for tool integration
*   **Configuration:** 
    - `.env` and `.env.example` - Environment variables (copy example to .env for local development)
    - `apps/api/app/config.py` - Pydantic Settings for application configuration
    - `docker-compose.yml` - Infrastructure services (PostgreSQL, Redis, Qdrant, Neo4j, R2R)
*   **Development Setup:** `scripts/dev.sh` - Automated development environment setup script

## 6. Development & Testing Workflow

*   **Local Development Environment:**
    1. **Prerequisites:** Install Python 3.10+, Docker, and Docker Compose
    2. **Environment Setup:** Run `scripts/dev.sh` to copy `.env.example` to `.env` and start infrastructure services
    3. **Package Installation:** Use `uv install` for dependency management (preferred) or `pip install -e .`
    4. **Start Services:**
        - Infrastructure: `docker compose up -d` (automatically done by dev script)
        - API Server: `uvicorn apps.api.app.main:app --reload`
        - MCP Server: `python apps/mcp/server.py`
*   **Task Configuration:** No custom task system currently configured. Standard Python project workflow with uv/pip commands.
*   **Testing:**
    - **Framework:** pytest (implied, currently minimal test setup)
    - **Command:** `pytest tests/` (expand from current placeholder)
    - **Requirements:** All new code MUST include corresponding unit tests
    - **Mocking:** Use pytest fixtures and mocks for external dependencies (databases, APIs, external services)
    - **File Naming:** `test_*.py` or `*_test.py` under `/tests` directory
    - **Integration Tests:** Test framework integrations (LangGraph, Mem0, R2R, MCP) with proper mocking
    - **Memory Validation:** `pytest tests/services/test_memory.py -v`
*   **CI/CD Process:** Currently not configured. Recommended: GitHub Actions workflow with automated testing, linting, security scanning, and deployment automation.

## 7. Specific Instructions for AI Collaboration

*   **Framework Integration Priorities:**
    - **LangGraph:** Use PostgreSQL checkpointing for production, Redis for development. Follow stateful workflow patterns with proper error handling
    - **Mem0:** Persistent memory engine for agent knowledge. Supports user, session, and
        agent scopes with <50ms lookup targets
    - **R2R:** Configure for hybrid search (vector + keyword + graph). Support document processing pipeline with proper chunking
    - **MCP Protocol:** Ensure full specification compliance. Implement secure tool execution with sandboxing
    - **Pydantic AI:** Use for typed agent interfaces and configuration validation
*   **Security Best Practices:**
    - **NEVER** hardcode API keys, secrets, or credentials - use environment variables
    - Always validate user inputs with Pydantic models on both client and server
    - Implement proper authentication and authorization for all API endpoints
    - Use connection pooling and secure configurations for all database connections
    - Follow principle of least privilege for all system access
*   **Dependencies Management:**
    - **Preferred:** Use `uv add <package>` for adding new dependencies
    - **Fallback:** Edit `pyproject.toml` manually and run `uv lock` to update lock file
    - **Database Dependencies:** Use async variants (asyncpg, redis-py with async support)
    - **Version Pinning:** Pin major versions for framework dependencies to ensure stability
*   **Performance Requirements:**
    - Simple agent queries: <2 seconds response time
    - Memory operations: <50ms retrieval time
    - Complex workflows: <5 seconds completion time
    - Support 1000+ concurrent users per instance
*   **Code Quality Standards:**
    - Use type hints for all function parameters and return values
    - Follow async/await patterns consistently (never mix sync/async inappropriately)
    - Implement comprehensive error handling with proper logging context
    - Use dependency injection for all external service interactions
    - Write self-documenting code with clear variable and function names

## 8. Avoidances/Forbidden Actions

*   **Code Patterns:**
    - **NEVER** mix sync and async operations (use async/await consistently)
    - **NEVER** ignore Pydantic ValidationError exceptions
    - **NEVER** use mutable defaults in function parameters or Pydantic models
    - **NEVER** expose internal error details or stack traces to API users
    - **NEVER** bypass input validation or sanitization
*   **Security:**
    - **NEVER** hardcode secrets, API keys, or credentials in source code
    - **NEVER** disable SSL/TLS verification in production code
    - **NEVER** use `eval()` or `exec()` on user input
    - **NEVER** expose database connection strings or internal service URLs
*   **Database Operations:**
    - **NEVER** use raw SQL queries without parameterization
    - **NEVER** ignore database connection pooling best practices
    - **NEVER** perform blocking database operations in async contexts
*   **Dependencies:**
    - **NEVER** add dependencies without updating `pyproject.toml` and lock files
    - **NEVER** install packages globally when working on the project
    - **NEVER** commit lock files with unresolved conflicts

## 9. Testing & Quality Assurance

*   **Testing Requirements:**
    - All new functionality MUST include corresponding unit tests
    - Integration tests required for framework integrations (LangGraph, Mem0, R2R, MCP)
    - API endpoints must have comprehensive test coverage including error cases
    - Use mocks/fixtures for external dependencies to ensure test isolation
*   **Test Organization:**
    - Mirror source code structure in test directory
    - Group related tests in test classes
    - Use descriptive test method names that explain the scenario being tested
*   **Performance Testing:**
    - Validate response time requirements (<2s for simple queries, <5s for complex workflows)
    - Test memory lookup performance (<50ms retrieval)
    - Load testing for concurrent user requirements (1000+ users)
*   **Quality Gates:**
    - All tests must pass before code integration
    - Code coverage should be >80% for new functionality
    - Linting and type checking must pass without errors
    - Security scanning should identify no critical vulnerabilities

## 10. Deployment & Production Considerations

*   **Environment Configuration:**
    - Use environment-specific `.env` files (never commit `.env` with secrets)
    - Validate all required environment variables on application startup
    - Use secure secret management systems in production (AWS Secrets Manager, Azure Key Vault)
*   **Database Setup:**
    - PostgreSQL with connection pooling and SSL enabled
    - Redis with proper memory policies and persistence configuration
    - Qdrant with appropriate vector dimensions and indexing settings
    - Regular backup and disaster recovery procedures
*   **Monitoring & Observability:**
    - Implement comprehensive logging with structured formats
    - Monitor key performance metrics (response times, error rates, resource usage)
    - Set up alerting for critical system failures and performance degradation
    - Use distributed tracing for complex workflow debugging
*   **Scalability:**
    - Design for horizontal scaling with stateless application instances
    - Use Redis for shared session management
    - Implement proper caching strategies for frequently accessed data
    - Monitor and optimize database query performance
