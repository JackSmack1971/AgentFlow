# AgentFlow — AGENTS.md

<!-- AGENTS:SECTION id="purpose" v="1" -->
## Purpose & Scope

This file provides essential guidance for AI agents working with the AgentFlow codebase - a unified AI agent development platform that integrates six leading frameworks (LangGraph, MCP, Mem0, R2R, Pydantic AI, AG2) to reduce agent development time by 60-80%. 

**Boundaries**: This guide covers the entire AgentFlow platform including backend API, MCP server, Next.js frontend, shared packages, and infrastructure. Explicit user prompts override these guidelines when in conflict.

**Key Principle**: Evidence-first development - all claims must be supported by code evidence, Project Knowledge (PK), or marked as [Inference]/[Unverified].
<!-- /AGENTS:SECTION -->

<!-- AGENTS:SECTION id="project-overview" v="1" -->
## Project Overview & Structure

**Mission**: Unified AI agent development platform reducing development complexity through standardized interfaces, visual workflow orchestration, and enterprise-grade infrastructure with 99.5% uptime targets.

**Primary Languages**: Python 3.10.17 (pinned), TypeScript 5.x, JavaScript ES2023  
**Core Frameworks**: FastAPI 0.115.12, Next.js 14 (App Router), React 18, LangGraph, Mem0, R2R, Pydantic AI, MCP 1.13.0  
**Runtime Targets**: Linux containers (Docker), AWS/Azure/GCP cloud deployment

<!-- AGENTS:ANCHOR id="directory-map" type="table" -->
| Path | Purpose | Criticality | Owner |
|------|---------|-------------|-------|
| `apps/api/` | FastAPI Backend Service | High | Backend Team |
| `apps/mcp/` | Model Context Protocol Server | High | Integration Team |
| `frontend/` | Next.js 14 Frontend Application | High | Frontend Team |
| `packages/` | Shared utility packages | Medium | Platform Team |
| `tests/` | Comprehensive test suite | High | All Teams |
| `infra/` | Infrastructure as Code | Medium | DevOps Team |
| `scripts/` | Development/deployment scripts | Low | Platform Team |
| `pyproject.toml` | Python dependencies & config | High | Platform Team |
| `docker-compose.yml` | Local development services | Medium | DevOps Team |
<!-- end anchor -->
<!-- /AGENTS:SECTION -->

<!-- AGENTS:SECTION id="setup-commands" v="1" -->
## Setup & Common Commands

**Prerequisites**: Python 3.10+, Node.js 20+, Docker & Docker Compose, uv package manager

### Initial Setup
```bash
# Clone and setup environment
git clone https://github.com/your-org/agentflow.git
cd agentflow
cp .env.example .env  # Edit with your API keys

# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
cd apps/api && uv install
cd ../../frontend && npm install
```

### Development Workflow
```bash
# Start infrastructure services
docker compose -f docker-compose.dev.yml up -d

# Start backend API (Terminal 1)
cd apps/api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start MCP server (Terminal 2)  
cd apps/mcp
uv run python server.py

# Start frontend (Terminal 3)
cd frontend
npm run dev
```

### Verification
- Backend API: http://localhost:8000/docs (FastAPI docs)
- Frontend UI: http://localhost:3000
- Health Check: http://localhost:8000/health
<!-- /AGENTS:SECTION -->

<!-- AGENTS:SECTION id="coding-standards" v="1" -->
## Code Style & Conventions

### Python Standards (Backend/MCP)
- **Formatting**: Black (line length 88) + Ruff linting
- **Type Safety**: mypy with strict mode, comprehensive type hints required
- **Import Organization**: isort with profile=black
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Documentation**: Comprehensive docstrings for all public functions

### TypeScript/Frontend Standards  
- **Linting**: Biome for formatting and linting (replaces ESLint/Prettier)
- **Type Safety**: Strict TypeScript mode, `noUncheckedIndexedAccess` enabled
- **Components**: PascalCase.tsx files, default exports preferred
- **Styling**: Tailwind CSS utility classes, responsive design patterns
- **State Management**: React 18 concurrent features, custom hooks for complex state

### Quality Gates
- **Test Coverage**: >90% required, enforced in CI
- **Type Coverage**: 100% type annotations for Python, strict TS mode
- **Security**: Bandit security analysis, dependency vulnerability scanning
- **Performance**: p95 latency < 300ms for API endpoints
<!-- /AGENTS:SECTION -->

<!-- AGENTS:SECTION id="testing" v="1" -->
## Testing & Programmatic Checks

### Backend Testing (Python)
```bash
# Unit tests with coverage
pytest tests/ -v --cov=apps --cov-report=term-missing --cov-fail-under=90

# Integration tests
pytest tests/integration/ -v

# MCP protocol compliance tests
pytest tests/test_mcp.py -v

# Performance/load testing  
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

### Frontend Testing (TypeScript)
```bash
# Unit/component tests
npm run test -- --coverage --watchAll=false

# Type checking
npm run type-check

# End-to-end testing
npm run test:e2e
```

### Code Quality Checks
```bash
# Python linting & formatting
black apps/ tests/ && ruff check apps/ tests/ && mypy apps/

# TypeScript linting
cd frontend && npm run lint

# Security analysis
bandit -r apps/
```

### API Contract Testing
```bash
# Postman collections via Newman
newman run postman/collections/auth.postman_collection.json
```

**Critical**: Agents MUST execute these commands and resolve ALL failures before completing tasks. No exceptions for failing tests or linting violations.
<!-- /AGENTS:SECTION -->

<!-- AGENTS:SECTION id="agent-runtime" v="1" -->
## Agent Runtime & Tooling

### Model Families
- **Primary**: OpenAI GPT-4/GPT-3.5 (via OPENAI_API_KEY)
- **Secondary**: Anthropic Claude (via ANTHROPIC_API_KEY) 
- **Optional**: Perplexity, Exa for specialized search tasks
- **Local**: Ollama support for development/testing

### Tool Protocols
- **MCP (Model Context Protocol)**: Primary tool integration standard
- **FastAPI Functions**: Direct API endpoint calling
- **REST APIs**: External service integration patterns

### Memory Isolation & Context
- **User Scoping**: All memory operations require `user_id` parameter
- **Thread Isolation**: Conversation threads isolated via `thread_id`
- **Context Windows**: Optimized for GPT-4 (8K) and GPT-4-turbo (128K)
- **RAG Sources**: R2R knowledge base, Qdrant vector storage, Neo4j graphs

<!-- AGENTS:ANCHOR id="tools" type="table" -->
| Tool | Category | Entrypoint | Args Pattern | Env Keys |
|------|----------|------------|--------------|---------|
| uv | build | `uv install` | `[--dev] [package]` | - |
| pytest | test | `pytest tests/` | `[-v] [--cov=apps]` | - |  
| black | lint | `black apps/` | `[--check] [path]` | - |
| ruff | lint | `ruff check apps/` | `[--fix] [path]` | - |
| mypy | test | `mypy apps/` | `[--strict] [path]` | - |
| npm | build | `npm install` | `[--dev] [package]` | - |
| docker-compose | devex | `docker compose up` | `[-f file] [-d]` | - |
| newman | test | `newman run collection.json` | `[--environment env.json]` | - |
<!-- end anchor -->
<!-- /AGENTS:SECTION -->

<!-- AGENTS:SECTION id="ci-cd" v="1" -->
## CI/CD & PR Workflow

### GitHub Actions Pipeline
- **Provider**: GitHub Actions (`.github/workflows/lint.yml`)
- **Triggers**: Pull requests to main, push to main branch
- **Gates**: All checks must pass before merge approval

### Automated Checks
1. **Code Quality**: Black formatting, Ruff linting, mypy type checking
2. **Security**: Bandit analysis, dependency vulnerability scanning  
3. **Testing**: Unit tests (≥90% coverage), integration tests, API contract tests
4. **Performance**: Load testing for performance-critical changes
5. **Documentation**: Verify documentation updates for user-facing changes

### Commit/PR Conventions
- **Commit Format**: Conventional Commits (feat:, fix:, docs:, test:, refactor:)
- **PR Requirements**: 
  - At least one maintainer review required
  - All CI checks passing
  - Breaking changes documented and communicated
  - Relevant AGENTS.md files updated

### Failure Handling
- **Test Failures**: Must be resolved before merge, no exceptions
- **Security Issues**: P0/P1 security findings block deployment
- **Performance Regression**: p95 latency increases >10% require optimization
<!-- /AGENTS:SECTION -->

<!-- AGENTS:SECTION id="security" v="1" -->
## Security & Safety

### Secrets Management
- **Environment Variables**: All sensitive data in `.env` (never committed)
- **Production Secrets**: Docker secrets, cloud provider secret stores
- **Redaction**: Automatic PII/secret redaction in logs and error messages
- **API Keys**: Separate keys for each service, rotation strategy implemented

### Input Validation & Security
- **Pydantic Models**: All API inputs validated with comprehensive schemas
- **File Uploads**: Size/type restrictions, virus scanning, sandboxed processing
- **SQL Injection**: SQLAlchemy ORM prevents injection attacks
- **XSS Prevention**: React JSX escaping, CSP headers in production

### Authentication & Authorization
- **JWT Tokens**: Stateless authentication with refresh mechanism
- **RBAC**: Role-based access control with fine-grained permissions
- **2FA Support**: Optional two-factor authentication for admin accounts
- **Session Security**: Secure cookie settings, CSRF protection

### AI-Specific Security
- **Model Input Validation**: Comprehensive validation for AI model inputs (CWE-502)
- **Prompt Injection**: Input sanitization and output filtering
- **Resource Limits**: Memory/compute limits for AI operations
- **Sandboxing**: Isolated execution environments for agent workflows

### Threat Model Notes
- **Primary Threats**: Unauthorized access, data exfiltration, AI model abuse
- **Attack Vectors**: API endpoints, file uploads, AI prompt injection
- **Mitigations**: Input validation, rate limiting, monitoring, audit logging
<!-- /AGENTS:SECTION -->

<!-- AGENTS:SECTION id="examples" v="1" -->
## Canonical Examples

### Agent Creation Example
```python
# Create a new agent via API
agent_data = {
    "name": "Customer Support Agent",
    "description": "Handles customer inquiries with memory",
    "model_config": {
        "provider": "openai",
        "model": "gpt-4",
        "temperature": 0.7
    },
    "tools": ["web_search", "knowledge_base"],
    "memory_config": {
        "scope": "user",
        "ttl_days": 30
    }
}

# Expected output: Agent created with ID and ready for execution
response = await client.post("/api/v1/agents", json=agent_data)
# Returns: {"id": "agent-uuid", "status": "active", "created_at": "..."}
```

### Memory Operation Example  
```typescript
// Frontend hook for memory management
const { memories, addMemory, searchMemories } = useAgentMemory({
  userId: "user-123",
  agentId: "agent-456"
});

// Add memory with automatic persistence
await addMemory({
  content: "User prefers JSON responses",
  category: "preference",
  metadata: { source: "conversation" }
});

// Search with semantic similarity
const results = await searchMemories("user preferences", { limit: 5 });
```

### Tool Integration Example
```python
# MCP tool registration
@mcp.tool()
def search_knowledge_base(query: str, context: Context) -> dict:
    """Search internal knowledge base with hybrid search."""
    context.report_progress("Searching knowledge base...")
    
    # R2R hybrid search (vector + graph)
    results = r2r_client.search(
        query=query,
        search_type="hybrid",
        filters={"status": "active"}
    )
    
    return {
        "results": results.get("results", []),
        "total": len(results.get("results", [])),
        "query": query
    }
```
<!-- /AGENTS:SECTION -->

<!-- AGENTS:SECTION id="glossary" v="1" -->
## Glossary

- **Agent**: AI-powered workflow that combines LLMs, memory, tools, and knowledge
- **LangGraph**: Framework for building stateful, multi-actor applications with LLMs  
- **MCP**: Model Context Protocol - standardized interface for AI tool integration
- **Mem0**: Memory layer providing persistent, personalized context for AI applications
- **R2R**: RAG to Riches - production-ready retrieval-augmented generation system
- **Pydantic AI**: Type-safe framework for building production AI applications
- **AG2**: Multi-agent conversation framework (excluded from MVP scope)
- **Checkpointing**: LangGraph feature for persisting workflow state between runs
- **Hybrid Search**: Combination of vector similarity and keyword/graph search
- **Vector Store**: Database optimized for similarity search (Qdrant in our stack)
- **Knowledge Graph**: Graph database for entity relationships (Neo4j in our stack)
- **Tool Registry**: MCP-compliant catalog of available AI tools and functions
- **Correlation ID**: Unique identifier for tracing requests across service boundaries
- **Circuit Breaker**: Pattern for graceful degradation when external services fail
- **SLO**: Service Level Objective - measurable targets (e.g., p95 < 300ms)
- **PK**: Project Knowledge - documentation, ADRs, RFCs, runbooks
- **Evidence-First**: Principle requiring code/PK evidence for all architectural claims
<!-- /AGENTS:SECTION -->

---

## Key Performance Targets

- **Agent Creation Time**: ≤5 minutes (critical business requirement)
- **API Response Time**: p95 < 300ms for simple queries, < 2s for complex workflows  
- **Memory Operations**: <100ms retrieval, <500ms knowledge search
- **Test Coverage**: ≥90% across all codebases
- **Uptime**: 99.5% availability target
- **Concurrent Users**: 1000+ per instance support

## Critical Constraints

1. **Hard Docker Compose Rules**: No `version:` field, no `container_name:`, all services run non-root, healthchecks required
2. **Type Safety**: 100% type coverage for Python (mypy strict), TypeScript strict mode
3. **Test Coverage**: ≥90% coverage gate enforced in CI, no exceptions
4. **Security**: No hardcoded secrets, comprehensive input validation, security scanning in CI
5. **Performance**: All changes must meet p95 latency SLOs, load testing for critical paths
6. **Documentation**: All public functions documented, AGENTS.md files updated with changes

## Emergency Contacts & Resources

- **Repository**: https://github.com/your-org/agentflow
- **Documentation**: README.md, DEVELOPMENT.md, individual AGENTS.md files
- **API Documentation**: http://localhost:8000/docs (FastAPI interactive docs)
- **Issue Tracking**: GitHub Issues with labeled templates
- **CI/CD**: GitHub Actions workflows in `.github/workflows/`

---

*This document is the authoritative source for AI agent collaboration with AgentFlow. When in doubt, refer to the specific AGENTS.md files in each subdirectory for detailed module-specific guidance.*
