# AGENTS.md: AI Collaboration Guide

This document provides essential context for AI models interacting with the AgentFlow project. Adhering to these guidelines will ensure consistency, maintain code quality, and optimize agent performance for building production-ready AI agents.

## 1. Project Overview & Purpose
*   **Primary Goal:** AgentFlow is a comprehensive AI agent development platform that unifies six leading frameworks (LangGraph, MCP, Mem0, R2R, Pydantic AI, AG2) to reduce AI agent development time by 60-80% compared to custom integration approaches.
*   **Business Domain:** Enterprise AI Development Platform, Conversational AI, Agent Orchestration, Knowledge Management
*   **Key Features:** 
    - Multi-level memory management with persistent context and contradiction resolution
    - Visual workflow orchestration with stateful agent workflows and error recovery
    - Standardized tool integration via MCP-compliant tool ecosystem
    - Advanced knowledge management with hybrid search and knowledge graphs
    - Production-ready deployment with enterprise security and 99.5% uptime targets

## 2. Core Technologies & Stack
*   **Languages:** Python 3.10+ (minimum 3.8+ for compatibility), TypeScript 5.x, JavaScript ES2023
*   **Frameworks & Runtimes:** 
    - Backend: FastAPI 0.115.12+, Pydantic AI, LangGraph (orchestration), Mem0 (memory), R2R (RAG), AG2 (multi-agent)
    - Frontend: Next.js 14+ with App Router, React 18+, Tailwind CSS, Biome (linting/formatting)
*   **Databases:** PostgreSQL 16+ (primary), Redis 7+ (caching/sessions), Qdrant (vector database), Neo4j (knowledge graphs)
*   **Key Libraries/Dependencies:** 
    - Python: FastAPI, Pydantic v2, asyncio, pytest, black, isort, mypy, bandit, langgraph, mem0-ai, r2r, qdrant-client, psycopg[binary], httpx, loguru
    - TypeScript: Zod (validation), Lucide React (icons), React Hook Form, MSW (testing mocks), Jest, React Testing Library
*   **Package Managers:** uv (Python - preferred for performance), npm (JavaScript/TypeScript)
*   **Platforms:** Linux containers, Docker, Kubernetes, AWS/Azure/GCP deployment support

## 3. Architectural Patterns & Structure
*   **Overall Architecture:** Microservices architecture with clear separation of concerns. FastAPI backend serving Next.js frontend, with specialized MCP server for tool integration. Follows domain-driven design principles with feature-based module organization.
*   **Directory Structure Philosophy:**
    *   `/apps/api/` - FastAPI backend with router-based organization (auth, memory, rag, agents, health)
    *   `/apps/mcp/` - MCP (Model Context Protocol) server for standardized tool integration
    *   `/frontend/` - Next.js 14+ App Router frontend (component-based architecture)
    *   `/tests/` - Comprehensive test suite with unit, integration, and performance tests
    *   `/infra/` - Infrastructure as code (Docker, Kubernetes, Terraform)
    *   `/scripts/` - Development and deployment automation scripts
    *   `/packages/` - Shared utility packages and configurations
*   **Module Organization:** 
    - Backend uses FastAPI router pattern with `/app/routers/` for endpoints, `/app/services/` for business logic, `/app/models/` for Pydantic schemas
    - Frontend uses Next.js App Router with feature-based component organization (`/components/agents/`, `/components/memory/`, etc.)
    - MCP server follows protocol specifications with tool registration and discovery patterns
*   **Common Patterns & Idioms:**
    - **Async/Await:** Heavy use of asyncio for concurrent operations and non-blocking I/O
    - **Dependency Injection:** FastAPI's dependency system for database sessions, authentication, and external services
    - **Type Safety:** Strict TypeScript with Pydantic v2 for runtime validation and API contracts
    - **Protocol Compliance:** MCP specification adherence for tool integration standardization
    - **Memory Management:** Multi-level scoping (user/session/agent) with semantic search and contradiction resolution

## 4. Coding Conventions & Style Guide
*   **Formatting:** 
    - Python: Follow PEP 8, use Black for formatting (88 char line length), isort for imports, max line length 88 characters
    - TypeScript/JavaScript: Use Biome for linting and formatting, 2-space indentation, single quotes, trailing commas
*   **Naming Conventions:**
    - Python: `snake_case` for variables, functions, methods, and files; `PascalCase` for classes; `SCREAMING_SNAKE_CASE` for constants
    - TypeScript: `camelCase` for variables, functions, methods; `PascalCase` for components, types, interfaces; `kebab-case` for file names
    - API Routes: RESTful patterns (`/agents`, `/memory`, `/rag`) with consistent HTTP verb usage
*   **API Design Principles:** 
    - Follow FastAPI best practices with automatic OpenAPI documentation
    - Use distinct Pydantic models for request (`*Create`, `*Update`) and response (`*Response`) to prevent data leakage
    - Implement proper HTTP status codes and error handling with custom exception types
    - Ensure idempotent operations where applicable and include proper CORS configuration
*   **Documentation Style:** 
    - Python: Use comprehensive docstrings following Google style with type hints
    - TypeScript: Use JSDoc comments for all public functions, components, and complex logic
    - API endpoints: Auto-generated documentation via FastAPI with detailed descriptions and examples
*   **Error Handling:** 
    - Python: Use custom exception classes inheriting from `HTTPException`, implement proper error logging with loguru
    - TypeScript: Use `Result<T, E>` types for fallible operations, implement error boundaries in React
    - MCP: Follow protocol error specifications with proper JSONRPC error responses
*   **Forbidden Patterns:**
    - **NEVER** use `any` type in TypeScript unless explicitly justified with comments
    - **NEVER** use `@ts-ignore` or `@ts-expect-error` to suppress TypeScript errors
    - **NEVER** hardcode secrets, API keys, or sensitive configuration in code
    - **NEVER** skip input validation on both client and server sides
    - **NEVER** use `dangerouslySetInnerHTML` without proper sanitization
    - **NEVER** bypass MCP protocol specifications for tool integration

## 5. Key Files & Entrypoints
*   **Main Entrypoints:**
    - Backend API: `apps/api/app/main.py` - FastAPI application with 7 routers (auth, memory, rag, agents, health, workflow, tools)
    - MCP Server: `apps/mcp/server.py` - MCP protocol implementation for tool integration
    - Frontend: `frontend/app/layout.tsx` - Next.js App Router root layout
*   **Configuration:**
    - Python dependencies: `pyproject.toml` with uv package management and comprehensive dev dependencies
    - Frontend dependencies: `frontend/package.json` with npm/Biome configuration
    - Docker services: `docker-compose.yml` with 7 services (API, MCP, PostgreSQL, Redis, Qdrant, Neo4j, R2R)
    - Development services: `docker-compose.dev.yml` includes test databases and utilities
    - Environment: `.env` files for local development (never commit secrets)
*   **CI/CD Pipeline:** `.github/workflows/lint.yml` - GitHub Actions with automated testing, linting, type checking, and security scanning

## 6. Development & Testing Workflow
*   **Local Development Environment:**
    1. Install Python 3.10+ and uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
    2. Install Node.js 20+ and npm for frontend development
    3. Start infrastructure services: `docker compose -f docker-compose.dev.yml up -d`
    4. Backend setup: `cd apps/api && uv install && uvicorn app.main:app --reload --port 8000`
    5. Frontend setup: `cd frontend && npm install && npm run dev`
    6. MCP server: `cd apps/mcp && uv run python server.py`
*   **Build Commands:**
    - Backend: No build step required (Python interpreted)
    - Frontend: `cd frontend && npm run build` for production builds
    - Docker: `docker compose build` for containerized deployments
    - Development script: `./scripts/dev.sh` to start all services quickly
*   **Testing Commands:** **All new code requires corresponding unit tests with >90% coverage.**
    - Backend tests: `pytest tests/ -v --cov=apps --cov-report=term-missing` (includes unit, integration, performance tests)
    - Frontend tests: `cd frontend && npm run test` (Jest with React Testing Library)
    - MCP tests: `pytest tests/test_mcp.py -v` for protocol compliance
    - **CRITICAL:** Tests must mock external dependencies (APIs, databases) using appropriate tools (pytest fixtures, MSW for frontend)
    - Load testing: `locust -f tests/performance/locustfile.py`
*   **Linting/Formatting Commands:** **All code MUST pass linting before committing.**
    - Python: `black apps/ tests/ && isort apps/ tests/ && ruff check apps/ tests/ && mypy apps/`
    - Frontend: `cd frontend && npm run lint` (Biome linting and formatting)
    - Security: `bandit -r apps/` for Python security analysis
*   **CI/CD Process:** GitHub Actions run automated tests, linting, type checking, and security scans on every pull request. All checks must pass before merge to main branch. Includes dependency vulnerability scanning and code quality gates.

## 7. Specific Instructions for AI Collaboration
*   **Contribution Guidelines:** 
    - Follow the existing code structure and patterns established in the codebase
    - Ensure all new functionality includes comprehensive tests with proper mocking
    - Update documentation for any user-facing changes or new APIs
    - Submit pull requests against the `main` branch with descriptive commit messages
*   **Security:** 
    - Be mindful of security when handling file I/O, external resources, and user inputs
    - Never hardcode secrets, API keys, or sensitive configuration in code
    - Always validate inputs on both client and server sides to prevent injection attacks
    - Use environment variables and secure configuration management for sensitive data
    - Follow OWASP security guidelines for web applications
*   **Dependencies:** 
    - When adding new Python dependencies, use `uv add <dependency>` and update the lock file
    - For frontend dependencies, use `npm install <package>` and ensure package-lock.json is updated
    - Prefer well-maintained, security-audited packages with active communities
    - Document the purpose of new dependencies in commit messages
*   **Commit Messages & Pull Requests:** 
    - Follow Conventional Commits specification (e.g., `feat:`, `fix:`, `docs:`, `refactor:`, `test:`)
    - Include clear descriptions of what changed and why
    - Reference any breaking changes in commit messages
    - Ensure pull request titles and descriptions are descriptive and complete
*   **Avoidances/Forbidden Actions:**
    - **NEVER** push directly to the main branch - always use pull requests
    - **NEVER** commit secrets, API keys, or sensitive configuration files
    - **NEVER** ignore TypeScript errors or bypass type checking with any/ignore
    - **NEVER** skip writing tests for new features or bug fixes
    - **NEVER** modify lock files (uv.lock, package-lock.json) unless adding/removing dependencies
    - **NEVER** use `git push --force` on shared branches - use `--force-with-lease` if absolutely necessary
*   **Debugging Guidance:** 
    - For backend issues, check logs in `uvicorn` output and use FastAPI's automatic error handling
    - For frontend issues, use browser developer tools and React DevTools
    - For MCP issues, verify protocol compliance and check server logs
    - Always include full stack traces when reporting bugs for faster resolution
*   **Performance Considerations:**
    - Monitor API response times: simple operations should be <2s p95, complex operations <5s p95
    - Memory operations should maintain <100ms p95 response times
    - RAG operations should achieve <500ms p95 response times
    - Use async/await patterns for I/O operations to maintain concurrency
*   **Pass/Fail Criteria:** 
    - All tests must pass (pytest for backend, Jest for frontend)
    - All linting and formatting checks must be green (Black, Biome, mypy)
    - TypeScript compilation must complete without errors
    - Security scans must not introduce new vulnerabilities
    - Code coverage must maintain >90% threshold
*   **Breaking Down Large Work:** 
    - Break large features into small, focused pull requests (typically <500 lines of changes)
    - Each PR should represent a single, complete, testable unit of work
    - Ensure each step includes its own tests and documentation updates
    - Consider feature flags for gradual rollouts of major changes
