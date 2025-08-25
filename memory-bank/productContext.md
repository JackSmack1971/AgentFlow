# AgentFlow Product Context

## Project Overview
**AgentFlow** is a developer-first, production-grade platform for building **stateful, typed, memory-aware AI agents**. The system integrates multiple advanced technologies including LangGraph, Pydantic-AI, Mem0, R2R, and MCP (standardized tools), with a FastAPI backend and Next.js/React+TypeScript frontend.

## Vision
To provide developers with a robust, scalable platform for creating sophisticated AI agents that maintain state, memory, and context across interactions while ensuring production reliability and performance.

## Stakeholders
- **Primary Users**: Developers building AI agent applications
- **Secondary Users**: DevOps teams managing deployments
- **End Users**: Organizations deploying AI agents in production

## Constraints
- **Performance Requirements**:
  - p95 < 2s (simple operations)
  - p95 < 5s (complex operations)
  - Memory read p95 < 100ms
  - Memory write p95 < 200ms
  - RAG retrieval p95 < 500ms (warm)
  - UI initial load/TTI < 2.5-3.0s
  - UI interactions < 100ms

## Current State

### System Architecture Overview
AgentFlow is a comprehensive, production-ready AI agent development platform that unifies six leading AI frameworks (LangGraph, MCP, Mem0, R2R, Pydantic AI, AG2) under a single, enterprise-grade infrastructure. The system implements a sophisticated multi-layered architecture with:

- **Frontend Layer**: Next.js 14 + React 18 + TypeScript 5.x dashboard with visual workflow orchestration
- **API Gateway**: FastAPI 0.115.12 with authentication, rate limiting, and security middleware
- **Core Services**: Modular backend with router-based organization (auth, memory, rag, agents, health)
- **Data Layer**: PostgreSQL 17 (primary), Redis 7 (caching/sessions), Qdrant (vector DB), Neo4j (knowledge graph)
- **Infrastructure**: Docker Compose with internal network isolation, health checks, and non-root users

### Control Plane Status
The repository is currently under SPARC (Structured Process for Advanced Requirements and Collaboration) orchestration:
- **Current Phase**: Repository Inventory & Specification (spec phase)
- **Next Phase**: Research Claims (pending)
- **Project Status**: Initial adoption with draft sprint and empty backlog
- **Control Files**: Complete SPARC workflow graph with 14 defined phases

## Discovered Artifacts & Technologies

### Backend Technologies
- **Core Framework**: FastAPI 0.115.12 with async/await patterns
- **AI Frameworks**: LangGraph, Pydantic-AI 0.7.4, Mem0 0.1.116, R2R 3.6.6, AG2 integration
- **Security**: JWT tokens (HS256), Fernet encryption, bcrypt password hashing, TOTP 2FA
- **Database**: PostgreSQL 17 with asyncpg, SQLAlchemy 2.0.43, Alembic migrations
- **Caching**: Redis 7 with connection pooling and health checks
- **Vector Database**: Qdrant for semantic search and memory storage
- **Knowledge Graph**: Neo4j for relationship mapping and graph queries
- **Development Tools**: uv package manager, pytest, mypy, ruff, black

### Frontend Technologies
- **Framework**: Next.js 14 with App Router, React 18, TypeScript 5.x
- **Styling**: Tailwind CSS 3.4.1, Lucide React icons
- **Forms**: React Hook Form with Zod validation
- **Testing**: Jest, React Testing Library, TypeScript coverage
- **Code Quality**: Biome for linting and formatting

### Infrastructure & DevOps
- **Containerization**: Docker Compose with multi-stage builds
- **Security**: Non-root users, secret management, internal network isolation
- **CI/CD**: GitHub Actions with linting workflows
- **Health Monitoring**: Comprehensive health checks for all services
- **Development**: Hot reload, environment-based configuration

### Security Implementation
- **Authentication**: JWT access/refresh tokens with 15min/7day expiration
- **Authorization**: RBAC with organization-based permissions
- **Encryption**: AES-256 for sensitive data, Fernet for OTP secrets
- **Rate Limiting**: 100 requests/minute per IP with Redis-backed tracking
- **Security Middleware**: Penetration detection, IP banning, security headers
- **Compliance**: OWASP Top 10 coverage, GDPR considerations

### Testing & Quality Assurance
- **Test Structure**: Comprehensive test suites across all modules
- **Coverage Areas**: API endpoints, security, database, services, frontend components
- **Tools**: pytest with async support, coverage reporting, hypothesis for property testing
- **Security Testing**: Bandit for static analysis, security-specific test suites

### Documentation & Specifications
- **API Documentation**: OpenAPI/Swagger integration with FastAPI
- **Security Documentation**: Comprehensive security architecture guide
- **Development Guidelines**: AGENTS.md files with framework-specific rules
- **Control Plane**: SPARC workflow with standardized handoff contracts
- **Contract Schemas**: JSON Schema definitions for backlog, sprint, state, handoff
- **Architecture Diagrams**: Mermaid diagrams for system, workflow, and deployment views

### Performance & Scalability
- **Performance Targets**: p95 < 2s (simple), < 5s (complex)
- **Memory Performance**: Read p95 < 100ms, Write p95 < 200ms
- **RAG Performance**: Retrieval p95 < 500ms (warm)
- **UI Performance**: Initial load/TTI < 2.5-3.0s, interactions < 100ms
- **Scalability**: Horizontal scaling with load balancing, database replication

## Critical Non-Functional Requirements
- **Security-First Design**: JWT tokens, encryption, rate limiting, circuit breakers
- **Production Reliability**: 99.5% uptime target with comprehensive monitoring
- **Enterprise Scalability**: Multi-tenant architecture with resource isolation
- **Developer Experience**: Type-safe development with comprehensive validation
- **Operational Excellence**: Structured logging, health checks, graceful degradation

---

*Repository inventory completed by SPARC specification-writer on 2025-08-24*
