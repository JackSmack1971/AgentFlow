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

*   **Languages:** Python 3.11+, TypeScript 5.x, JavaScript ES2023
*   **Frameworks & Runtimes:** 
    - Backend: FastAPI 0.115.12+, Pydantic AI, LangGraph (orchestration), Mem0 (memory), R2R (RAG), AG2 (multi-agent)
    - Frontend: Next.js 14+ with App Router, React 18+, Tailwind CSS, Biome (linting/formatting)
*   **Databases:** PostgreSQL 12+ (primary), Redis 6+ (caching/sessions), Qdrant (vector database), Neo4j (knowledge graphs)
*   **Key Libraries/Dependencies:** 
    - Python: FastAPI, Pydantic v2, asyncio, pytest, black, isort, flake8, mypy, bandit
    - TypeScript: Zod (validation), Lucide React (icons), React Hook Form, MSW (testing mocks)
*   **Package Managers:** uv (Python - preferred), npm (JavaScript/TypeScript)
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
    - Python: Follow PEP 8, use Black for formatting, isort for imports, max line length 100 characters
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
    - Python: Use custom exception classes inheriting from `HTTPException`, implement proper error logging
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
    - Backend API: `apps/api/app/main.py` - FastAPI application with 7 routers
    - MCP Server: `apps/mcp/server.py` - MCP protocol implementation for tool integration
    - Frontend: `frontend/app/layout.tsx` - Next.js App Router root layout (to be implemented)
*   **Configuration:**
    - Python dependencies: `pyproject.toml` with uv package management
    - Frontend dependencies: `frontend/package.json` with npm/Biome configuration
    - Docker services: `docker-compose.yml` with 6 services (API, MCP, PostgreSQL, Redis, Qdrant, Neo4j)
    - Environment: `.env` files for local development (never commit secrets)
*   **CI/CD Pipeline:** `.github/workflows/lint.yml` - GitHub Actions with automated testing and linting

## 6. Development & Testing Workflow

*   **Local Development Environment:**
    1. Install Python 3.11+ and uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
    2. Install Node.js 20+ and npm for frontend development
    3. Start services: `docker compose -f docker-compose.dev.yml up -d`
    4. Backend setup: `cd apps/api && uv install && uvicorn app.main:app --reload`
    5. Frontend setup: `cd frontend && npm install && npm run dev`
    6. MCP server: `cd apps/mcp && python server.py`
*   **Build Commands:**
    - Backend: No build step required (Python interpreted)
    - Frontend: `cd frontend && npm run build` for production builds
    - Docker: `docker compose build` for containerized deployments
*   **Testing Commands:** **All new code requires corresponding unit tests.**
    - Backend tests: `pytest tests/ -v --cov=apps` (includes unit, integration, performance tests)
    - Frontend tests: `cd frontend && npm run test` (Jest with React Testing Library)
    - MCP tests: `pytest tests/test_mcp.py -v` for protocol compliance
    - **CRITICAL:** Tests must mock external dependencies (APIs, databases) using appropriate tools (pytest fixtures, MSW for frontend)
    - Load testing: `locust -f tests/performance/locustfile.py`
*   **Linting/Formatting Commands:** **All code MUST pass linting before committing.**
    - Python: `black apps/ tests/ && isort apps/ tests/ && flake8 apps/ tests/ && mypy apps/`
    - Frontend: `cd frontend && npm run lint` (Biome linting and formatting)
    - Security: `bandit -r apps/` for Python security analysis
*   **CI/CD Process:** GitHub Actions run automated tests, linting, type checking, and security scans on every pull request. All checks must pass before merge to main branch.

## 7. Specific Instructions for AI Collaboration

*   **Contribution Guidelines:**
    - Follow the existing code architecture and patterns established in each application
    - Ensure all new functionality includes comprehensive tests with >90% coverage
    - Submit pull requests against the `main` branch with descriptive commit messages
    - All code must pass automated quality checks (linting, type checking, tests, security scans)
*   **Security:** 
    - Implement proper input validation and sanitization for all user inputs
    - Use environment variables for all configuration and secrets
    - Follow OWASP security guidelines for web applications
    - Implement rate limiting, authentication, and authorization for all API endpoints
    - Validate all external tool integrations through MCP protocol security measures
*   **Dependencies:** 
    - Python: Add new dependencies via `uv add <package>` and update `pyproject.toml`
    - Frontend: Use `npm install <package>` and ensure TypeScript type definitions are available
    - Always review dependency licenses and security advisories before adding
    - Prefer established, well-maintained packages with active communities
*   **Commit Messages & Pull Requests:** 
    - Follow Conventional Commits specification: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`
    - Include clear description of what changed, why, and any breaking changes
    - Reference issue numbers and provide context for reviewers
    - Ensure commit messages are complete sentences ending with periods
*   **Avoidances/Forbidden Actions:**
    - **DO NOT** push directly to the main branch - always use pull requests
    - **DO NOT** commit secrets, API keys, or sensitive data to version control
    - **DO NOT** skip tests or lower test coverage requirements
    - **DO NOT** ignore TypeScript errors or Python type checking warnings
    - **DO NOT** bypass security validations or authentication requirements
    - **DO NOT** modify core framework integrations without thorough testing
*   **Performance Requirements:**
    - Agent creation must complete in <5 minutes (critical business requirement)
    - API responses must be <2 seconds for simple queries, <5 seconds for complex workflows
    - Memory retrieval operations must be <100ms, knowledge search <500ms
    - Support minimum 1000 concurrent users per instance with 99.5% uptime
*   **MCP Protocol Compliance:**
    - All tool integrations MUST follow MCP specification exactly
    - Implement proper STDIO transport communication patterns
    - Use standardized tool registration and discovery mechanisms
    - Handle protocol errors gracefully without breaking agent communication
    - Provide comprehensive tool metadata and documentation
*   **Memory System Requirements:**
    - Implement multi-level memory scoping (user/session/agent/global)
    - Support semantic search with vector embeddings for memory retrieval
    - Include contradiction resolution and memory consolidation features
    - Ensure memory operations are thread-safe and support concurrent access
*   **Frontend Development Standards:**
    - Use Next.js 14+ App Router exclusively (never Pages Router)
    - Implement strict TypeScript with proper type definitions
    - Follow accessibility guidelines (WCAG 2.1 AA compliance)
    - Ensure mobile responsiveness and cross-browser compatibility
    - Use server components by default, client components only when necessary
*   **Pass/Fail Criteria:** 
    - All tests must pass: `pytest tests/` and `npm run test`
    - Code must pass all linting and formatting checks
    - TypeScript compilation must succeed without errors
    - Security scans must pass without high-severity issues
    - Performance benchmarks must meet specified response time requirements
    - MCP protocol compliance tests must pass for tool integration features
