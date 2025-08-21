# AGENTS.md: AI Collaboration Guide

This document provides essential context for AI models interacting with this project. Adhering to these guidelines will ensure consistency, maintain code quality, and optimize agent performance.

<!-- It is Friday, August 21, 2025. This guide is optimized for clarity, efficiency, and maximum utility for modern AI coding agents like OpenAI's Codex, GitHub Copilot Workspace, and Claude. -->

<!-- This file should be placed at the root of your repository. More deeply-nested AGENTS.md files (e.g., in subdirectories) will take precedence for specific sub-areas of the codebase. Direct user prompts will always override instructions in this file. -->

## 1. Project Overview & Purpose

*   **Primary Goal:** AgentFlow is a comprehensive AI agent development platform that unifies six leading AI frameworks (LangGraph, MCP, Mem0, R2R, Pydantic AI, AG2) to solve critical challenges in AI agent development: memory management, orchestration complexity, and tool integration.
*   **Business Domain:** AI Agent Development Platform, Conversational AI, Enterprise Automation, Developer Tools
*   **Key Features:** Multi-level memory management, visual workflow orchestration, knowledge base integration, MCP-compliant tool integration, deployment automation

## 2. Core Technologies & Stack

*   **Languages:** Python 3.10+, TypeScript 5.x, JavaScript ES2023
*   **Frameworks & Runtimes:** FastAPI 0.115.12, Uvicorn (ASGI server), Next.js (frontend), Pydantic v2, Docker
*   **Databases:** PostgreSQL (primary data), Redis (sessions/cache), Qdrant (vector database), Neo4j (knowledge graphs)
*   **Key Libraries/Dependencies:** 
    - **AI Frameworks:** LangGraph (orchestration), mem0-ai (memory management), R2R (RAG), MCP (tool integration), pydantic-ai-slim
    - **Core:** SQLAlchemy 2.0+, psycopg[binary], httpx, loguru, python-dotenv
    - **Infrastructure:** qdrant-client, redis 5.0.7+
*   **Platforms:** Linux containers, Multi-cloud (AWS, Azure, GCP), Docker/Kubernetes
*   **Package Manager:** uv (Python - preferred), pnpm (JavaScript/TypeScript)

## 3. Architectural Patterns & Structure

*   **Overall Architecture:** Microservices architecture with API Gateway pattern. FastAPI backend serves as the central API gateway with separate MCP server for tool integration. Multi-service orchestration combining stateful workflows (LangGraph), persistent memory (Mem0), and advanced RAG (R2R).
*   **Directory Structure Philosophy:**
    *   `/apps/api`: FastAPI backend application with routers, services, models, and dependencies
    *   `/apps/mcp`: MCP (Model Context Protocol) server for standardized tool integration
    *   `/packages`: Reusable packages and client libraries (e.g., R2R client)
    *   `/infra`: Infrastructure configuration files (Docker, R2R config)
    *   `/scripts`: Development and deployment automation scripts
    *   `/tests`: All unit and integration tests
*   **Module Organization:** FastAPI routers organized by feature domain (auth, memory, rag, agents). Services layer abstracts framework integrations. Pydantic models for type safety and validation.
*   **Common Patterns & Idioms:**
    *   **Dependency Injection:** Extensive use of FastAPI's dependency system for database sessions, authentication, settings
    *   **Type Safety:** Pydantic models for all data validation, strict type hints throughout
    *   **Async Operations:** All I/O operations use async/await patterns
    *   **Memory Management:** Multi-level memory scoping (user/agent/session/global) via Mem0
    *   **Metaprogramming:** Template-based agent configuration and workflow generation

## 4. Coding Conventions & Style Guide

*   **Formatting:** Python follows PEP 8 with Black formatting. Use 4-space indentation. Line length: 88 characters. TypeScript uses Biome for formatting and linting (migrated from ESLint).
*   **Naming Conventions:**
    *   Python: `snake_case` for variables/functions, `PascalCase` for classes, `SCREAMING_SNAKE_CASE` for constants
    *   TypeScript: `camelCase` for variables/functions, `PascalCase` for classes/interfaces/types
    *   Files: `snake_case.py` for Python, `camelCase.ts/tsx` for TypeScript
    *   APIs: RESTful resource naming (e.g., `/api/agents/{agent_id}/memory`)
*   **API Design Principles:** 
    *   RESTful design with proper HTTP methods and status codes
    *   Explicit Pydantic models for all request/response validation
    *   Dependency injection for cross-cutting concerns
    *   Async-first design for all I/O operations
    *   Comprehensive error handling with structured responses
*   **Documentation Style:** Use docstrings for all public functions and classes. Include type hints. API endpoints documented via FastAPI automatic documentation.
*   **Error Handling:** Use FastAPI's HTTPException with appropriate status codes. Structured error responses with detail messages. Async exception handling in services layer.
*   **Forbidden Patterns:** 
    *   **NEVER** use `mem0` package name - always use `mem0-ai`
    *   **NEVER** hardcode secrets or credentials
    *   **NEVER** use synchronous database operations
    *   **NEVER** bypass Pydantic validation for API requests/responses

## 5. Development & Testing Workflow

*   **Local Development Setup:**
    1. Install Python 3.10+ and ensure `uv` is available
    2. Copy `.env.example` to `.env` and configure required environment variables
    3. Run `./scripts/dev.sh` to start infrastructure services (PostgreSQL, Redis, Qdrant, Neo4j, R2R)
    4. Install dependencies: `uv install` (preferred) or `pip install -e .`
    5. Start API server: `uvicorn apps.api.app.main:app --reload`
    6. Start MCP server: `python apps/mcp/server.py`
*   **Build Commands:**
    *   Infrastructure: `docker compose up -d` starts all backing services
    *   API development: `uvicorn apps.api.app.main:app --reload`
    *   Production build: Configure via environment variables for deployment
*   **Testing Commands:** **All commits require corresponding unit tests.**
    *   `pytest` or `uv run pytest` (run all tests)
    *   `pytest tests/test_specific.py` (run specific test file)
    *   `pytest -v --tb=short` (verbose output with short traceback)
    *   **MUST** mock external dependencies (AI APIs, databases) to ensure tests don't make external calls
    *   Test filenames follow `test_*.py` convention
*   **Linting/Formatting Commands:** **All code MUST pass checks before committing.**
    *   Python: `black .` (formatting), `ruff check .` (linting)
    *   TypeScript: Biome handles both formatting and linting
    *   Type checking: `mypy .` for Python, `tsc --noEmit` for TypeScript
*   **CI/CD Process Overview:** Infrastructure services managed via Docker Compose. Deployment automation in progress - currently manual process.

## 6. Git Workflow & PR Instructions

*   **Pre-Commit Checks:** **ALWAYS** run tests and linting before committing. Ensure all environment variables properly configured.
*   **Branching Strategy:** Work on feature branches and submit pull requests against the `main` branch. **DO NOT** commit directly to main.
*   **Commit Messages:** Follow Conventional Commits specification (e.g., `feat:`, `fix:`, `docs:`). Include what changed, why, and any breaking changes.
*   **Pull Request (PR) Process:** 
    *   Ensure all tests pass and code is properly formatted
    *   Include clear description of changes and their purpose
    *   Reference any related issues or requirements
    *   Verify all AI framework integrations work correctly
*   **Force Pushes:** **NEVER** use `git push --force` on the `main` branch. Use `git push --force-with-lease` for feature branches if needed.
*   **Clean State:** **You MUST leave your worktree in a clean state after completing a task.**

## 7. Security Considerations

*   **General Security Practices:** **Be mindful of security** when handling AI APIs, user data, and external integrations.
*   **Sensitive Data Handling:** **DO NOT** hardcode secrets, API keys, or credentials. Use environment variables and secure storage.
*   **Input Validation:** Validate all user inputs using Pydantic models on both client and server sides.
*   **AI Security:** Implement proper sandboxing for MCP tools, validate AI-generated content, monitor for prompt injection attacks.
*   **Dependency Management:** Regular security updates for AI frameworks and dependencies.
*   **Principle of Least Privilege:** Ensure proper access controls for memory systems, knowledge bases, and agent capabilities.

## 8. Specific Agent Instructions & Known Issues

*   **Tool Usage:** 
    *   Use `uv add <library>` for adding Python dependencies instead of `pip`
    *   For AI frameworks: Use exact package names (`mem0-ai`, `pydantic-ai-slim`, etc.)
    *   Use async patterns throughout - no synchronous database operations
*   **Memory System Integration:**
    *   Always specify proper scoping (user_id, agent_id, run_id) for Mem0 operations
    *   Handle memory contradictions gracefully with user feedback
    *   Implement proper memory cleanup and retention policies
    *   Target <100ms for memory retrieval operations
*   **AI Framework Integration:**
    *   **LangGraph:** Use PostgreSQL checkpointing for production, Redis for development
    *   **R2R:** Configure hybrid search (vector + keyword + graph) for optimal results
    *   **MCP:** Ensure full protocol compliance and proper tool sandboxing
    *   **Pydantic AI:** Use for type-safe agent configurations and validation
*   **Performance Requirements:**
    *   Target <2s response time for simple queries
    *   Target <5s for complex multi-step workflows
    *   Memory operations must complete in <100ms
    *   Support 1000+ concurrent users per instance
*   **Quality Assurance & Verification:** After completing changes, **ALWAYS** verify:
    *   All tests pass (`pytest`)
    *   Code formatting is correct (`black .`, Biome for TypeScript)
    *   Type checking passes (`mypy .`, `tsc --noEmit`)
    *   AI framework integrations work correctly
    *   Performance requirements are met
*   **Project-Specific Quirks:**
    *   The system uses multi-level memory architecture - understand user/agent/session scoping
    *   MCP protocol is emerging standard - stay current with specification updates
    *   R2R requires specific configuration for knowledge graph features
    *   FastAPI dependency injection is used extensively - maintain this pattern
*   **Troubleshooting & Debugging:** 
    *   Use structured logging with loguru for debugging AI framework issues
    *   Include full context when reporting framework integration problems
    *   Check environment variable configuration first for integration issues
    *   Verify Docker services are running for local development problems

## 9. Framework-Specific Guidelines

### LangGraph Integration
*   Use proper state management with PostgreSQL/Redis persistence
*   Implement error handling and recovery for workflow execution
*   Monitor workflow performance and optimize bottlenecks
*   Use checkpointing for long-running agent workflows

### Mem0 Memory Management
*   Always use `mem0-ai` package, never `mem0`
*   Implement proper memory scoping (user/agent/session/global)
*   Handle memory contradictions with automatic and manual resolution
*   Monitor memory usage and implement cleanup policies

### R2R RAG System
*   Configure hybrid search for optimal retrieval performance
*   Implement knowledge graph construction for advanced queries
*   Monitor document processing pipelines for errors
*   Optimize vector indexing for large knowledge bases

### MCP Tool Integration
*   Ensure full MCP protocol compliance
*   Implement proper tool sandboxing and security
*   Monitor tool performance and usage patterns
*   Maintain tool marketplace and ecosystem integration

### Pydantic AI Configuration
*   Use type-safe agent configurations throughout
*   Implement proper validation for agent parameters
*   Monitor agent performance and behavior patterns
*   Maintain agent versioning and rollback capabilities        - API Server: `uvicorn apps.api.app.main:app --reload`
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
