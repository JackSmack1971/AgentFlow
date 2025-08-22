# AgentFlow

> **Unified AI Agent Development Platform** - Reducing agent development time by 60-80% through seamless framework integration

[![Build Status](https://github.com/agentflow/agentflow/workflows/CI/badge.svg)](https://github.com/agentflow/agentflow/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![TypeScript](https://img.shields.io/badge/typescript-5.x-blue.svg)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.12-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14+-black.svg)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Overview

AgentFlow is a comprehensive AI agent development platform that unifies six leading frameworks (**LangGraph**, **MCP**, **Mem0**, **R2R**, **Pydantic AI**, **AG2**) into a single, cohesive development environment. By providing standardized interfaces, visual workflow orchestration, and enterprise-grade infrastructure, AgentFlow enables developers to build production-ready AI agents in minutes rather than weeks.

### ✨ Key Features

- **🧠 Multi-level Memory Management** - Persistent context with semantic search and contradiction resolution
- **🔄 Visual Workflow Orchestration** - Stateful agent workflows with automatic error recovery
- **🛠️ Standardized Tool Integration** - MCP-compliant tool ecosystem with 100+ pre-built integrations
- **📚 Advanced Knowledge Management** - Hybrid search capabilities with knowledge graphs and vector storage
- **🚀 Production-Ready Deployment** - Enterprise security, monitoring, and 99.5% uptime targets
- **⚡ Rapid Development** - Agent creation in ≤5 minutes with intuitive UI wizard

## 🏗️ Architecture Overview

AgentFlow follows a microservices architecture with clear separation of concerns:

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[Next.js 14 App Router]
        Components[React 18 Components]
    end
    
    subgraph "API Layer"
        API[FastAPI Backend]
        Auth[Authentication Service]
        Workflow[Workflow Engine]
    end
    
    subgraph "Integration Layer"
        MCP[MCP Server]
        Tools[Tool Registry]
    end
    
    subgraph "AI Services"
        Memory[Mem0 Memory]
        RAG[R2R Knowledge]
        Agents[LangGraph Orchestration]
        PydanticAI[Pydantic AI]
        AG2[AG2 Multi-Agent]
    end
    
    subgraph "Data Layer"
        PG[(PostgreSQL)]
        Redis[(Redis)]
        Qdrant[(Qdrant Vector DB)]
        Neo4j[(Neo4j Graph DB)]
    end
    
    UI --> API
    Components --> API
    API --> MCP
    API --> Memory
    API --> RAG
    API --> Agents
    MCP --> Tools
    Memory --> Qdrant
    Memory --> PG
    RAG --> Qdrant
    RAG --> Neo4j
    API --> Redis
    API --> PG
```

### 🗂️ Project Structure

```
agentflow/
├── 📁 apps/
│   ├── 📁 api/                    # FastAPI Backend Service
│   │   ├── 📁 app/
│   │   │   ├── 📁 routers/        # API endpoints (auth, memory, rag, agents)
│   │   │   ├── 📁 services/       # Business logic layer
│   │   │   ├── 📁 models/         # Pydantic schemas
│   │   │   ├── 📁 core/           # Configuration and settings
│   │   │   └── 📄 main.py         # FastAPI application entry point
│   │   └── 📄 AGENTS.md           # Backend-specific guidelines
│   └── 📁 mcp/                    # Model Context Protocol Server
│       ├── 📄 server.py           # MCP protocol implementation
│       └── 📄 AGENTS.md           # MCP-specific guidelines
├── 📁 frontend/                   # Next.js 14 Frontend Application
│   ├── 📁 app/                    # App Router pages and layouts
│   │   ├── 📁 (auth)/            # Authentication routes
│   │   ├── 📁 (dashboard)/       # Main application interface
│   │   └── 📄 layout.tsx         # Root layout component
│   ├── 📁 components/             # Reusable UI components
│   │   ├── 📁 ui/                # Base UI components
│   │   ├── 📁 agents/            # Agent-specific components
│   │   ├── 📁 memory/            # Memory management UI
│   │   └── 📁 layout/            # Layout components
│   ├── 📁 hooks/                 # Custom React hooks
│   ├── 📁 lib/                   # Utilities and configurations
│   └── 📄 AGENTS.md              # Frontend-specific guidelines
├── 📁 tests/                     # Comprehensive test suite
│   ├── 📁 api/                   # Backend API tests
│   ├── 📁 frontend/              # Frontend component tests
│   └── 📁 integration/           # End-to-end integration tests
├── 📁 infra/                     # Infrastructure as Code
├── 📁 scripts/                   # Development and deployment scripts
├── 📄 pyproject.toml             # Python dependencies and configuration
├── 📄 docker-compose.yml         # Local development services
└── 📄 AGENTS.md                  # Root project guidelines
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+** with `uv` package manager
- **Node.js 20+** with npm
- **Docker & Docker Compose** for local services
- **Git** for version control

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/agentflow.git
   cd agentflow
   ```

2. **Install Python dependencies**
   ```bash
   # Install uv package manager
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Install Python dependencies
   cd apps/api
   uv install
   ```

3. **Install Frontend dependencies**
   ```bash
   cd frontend
   npm install
   ```

4. **Configure Environment Variables**
   ```bash
   # Copy example environment file
   cp .env.example .env
   
   # Edit .env with your API keys and configuration
   # Required: SECRET_KEY, DATABASE_URL, REDIS_URL, QDRANT_URL
   ```

5. **Start Development Services**
   ```bash
   # Start supporting services (PostgreSQL, Redis, Qdrant, Neo4j)
   docker compose -f docker-compose.dev.yml up -d
   
   # Start backend API
   cd apps/api
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Start MCP server (in new terminal)
   cd apps/mcp
   python server.py
   
   # Start frontend (in new terminal)
   cd frontend
   npm run dev
   ```

6. **Verify Installation**
   - Backend API: http://localhost:8000/docs (FastAPI docs)
   - Frontend UI: http://localhost:3000
   - Health Check: http://localhost:8000/health

## 🔧 Core Concepts & Architecture

### Memory Management System

AgentFlow implements a sophisticated multi-level memory system using **Mem0**:

```mermaid
graph LR
    subgraph "Memory Scopes"
        User[User Memory]
        Session[Session Memory]
        Agent[Agent Memory]
    end
    
    subgraph "Storage Backends"
        Vector[Qdrant Vector Store]
        Graph[Neo4j Knowledge Graph]
        SQL[PostgreSQL Metadata]
    end
    
    User --> Vector
    Session --> Vector
    Agent --> Vector
    User --> Graph
    Vector --> SQL
```

**Memory Operations:**
- **Add**: Store conversational context with semantic indexing
- **Search**: Retrieve relevant memories using hybrid search
- **Update**: Modify existing memories with conflict resolution
- **Delete**: Remove obsolete or incorrect information

### Workflow Orchestration

Built on **LangGraph**, the workflow engine provides:

```mermaid
stateDiagram-v2
    [*] --> Planning
    Planning --> Execution
    Execution --> Memory_Update
    Memory_Update --> Tool_Integration
    Tool_Integration --> Response_Generation
    Response_Generation --> [*]
    
    Execution --> Error_Recovery
    Error_Recovery --> Execution
    Tool_Integration --> Error_Recovery
```

### Tool Integration via MCP

The **Model Context Protocol (MCP)** server standardizes tool access:

```mermaid
sequenceDiagram
    participant Agent
    participant MCP as MCP Server
    participant Tool as External Tool
    
    Agent->>MCP: Request tool list
    MCP-->>Agent: Available tools
    Agent->>MCP: Call tool with params
    MCP->>Tool: Execute operation
    Tool-->>MCP: Return result
    MCP-->>Agent: Structured response
```

## 📖 API Reference

### Core Endpoints

#### Authentication
```python
# POST /auth/register
{
  "email": "user@example.com",
  "password": "secure_password"
}
# Response: {"otp_secret": "...", "status": "ok"}

# POST /auth/login
{
  "email": "user@example.com", 
  "password": "secure_password",
  "otp_code": "123456"
}
# Response: {"access_token": "...", "refresh_token": "...", "token_type": "bearer"}
```

#### Memory Management
```python
# POST /memory/items
{
  "text": "User prefers morning meetings",
  "tags": ["preference", "scheduling"],
  "metadata": {"importance": "high"}
}

# GET /memory/items/search?q=morning&limit=10
# Response: [{"id": "...", "text": "...", "score": 0.95}]
```

#### Agent Operations
```python
# POST /agents/run
{
  "prompt": "Schedule a team meeting for next week",
  "agent_id": "scheduler_agent",
  "context": {"user_timezone": "PST"}
}
# Response: {"result": "Meeting scheduled for Tuesday 2PM PST"}
```

#### Workflow Execution
```python
# POST /workflow/run
{
  "workflow_id": "customer_support_flow",
  "inputs": {
    "customer_query": "Need help with billing",
    "priority": "high"
  }
}
```

### Key Service Classes

#### Memory Service
```python
from apps.api.app.services.memory import MemoryService

# Initialize service
memory_service = MemoryService()

# Add memory item
item_id = await memory_service.add_item(
    text="Customer prefers email notifications",
    user_id="user123",
    agent_id="support_agent",
    tags=["preference", "communication"]
)

# Search memories
results = await memory_service.search(
    query="notification preferences",
    user_id="user123",
    limit=5
)
```

#### Workflow Service
```python
from apps.api.app.services.workflow import WorkflowService

# Execute workflow
workflow_service = WorkflowService()
result = await workflow_service.execute(
    workflow_id="data_analysis_flow",
    inputs={"dataset_url": "https://...", "analysis_type": "sentiment"}
)
```

## 🧪 Development Guide

### Running Tests

```bash
# Backend tests with coverage
pytest tests/ -v --cov=apps --cov-report=term-missing

# Frontend tests
cd frontend && npm run test

# Integration tests
pytest tests/integration/ -v

# Load testing
locust -f tests/performance/locustfile.py
```

### Code Quality

```bash
# Python formatting and linting
black apps/ tests/
isort apps/ tests/
flake8 apps/ tests/
mypy apps/

# Frontend linting
cd frontend && npm run lint

# Security scanning
bandit -r apps/
```

### Adding New Features

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/new-agent-capability
   ```

2. **Add Backend Router**
   ```python
   # apps/api/app/routers/new_feature.py
   from fastapi import APIRouter, Depends
   from ..models.schemas import FeatureSchema
   
   router = APIRouter()
   
   @router.post("/", response_model=FeatureResponse)
   async def create_feature(data: FeatureSchema):
       # Implementation
       pass
   ```

3. **Register Router**
   ```python
   # apps/api/app/main.py
   from .routers import new_feature
   
   app.include_router(
       new_feature.router,
       prefix="/new-feature",
       tags=["new-feature"]
   )
   ```

4. **Add Frontend Components**
   ```typescript
   // frontend/components/new-feature/FeatureComponent.tsx
   'use client'
   
   import { useState } from 'react'
   
   export function FeatureComponent() {
     const [data, setData] = useState(null)
     // Component implementation
   }
   ```

5. **Write Tests**
   ```python
   # tests/api/test_new_feature.py
   import pytest
   from httpx import AsyncClient
   
   @pytest.mark.asyncio
   async def test_create_feature():
       # Test implementation
       pass
   ```

### Environment Configuration

Create `.env` file with required variables:

```bash
# Application
SECRET_KEY=your-secret-key-here
APP_NAME=AgentFlow API
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/agentflow
REDIS_URL=redis://localhost:6379/0

# Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_PORT=6333

# Knowledge Graph (Optional)
NEO4J_URL=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# AI Services
OPENAI_API_KEY=your-openai-key
MEM0_API_KEY=your-mem0-key-for-hosted-mode

# R2R Configuration
R2R_BASE_URL=http://localhost:7272
R2R_API_KEY=your-r2r-key
```

## 🔐 Security & Production

### Security Features

- **Input Validation**: All endpoints use Pydantic models for strict validation
- **Authentication**: JWT tokens with refresh mechanism and 2FA support
- **Authorization**: Role-based access control with fine-grained permissions
- **Rate Limiting**: Configurable rate limits per endpoint and user
- **CORS**: Proper CORS configuration for cross-origin requests
- **Environment Secrets**: All sensitive data stored in environment variables

### Production Deployment

```bash
# Build production images
docker compose build

# Deploy with production configuration
docker compose -f docker-compose.prod.yml up -d

# Monitor services
docker compose logs -f api
docker compose logs -f mcp
```

### Performance Targets

- **Agent Creation**: ≤5 minutes (critical business requirement)
- **API Response Time**: <2s simple queries, <5s complex workflows
- **Memory Operations**: <100ms retrieval, <500ms knowledge search
- **Concurrent Users**: 1000+ per instance with 99.5% uptime

## 🤝 Contributing

### Contribution Guidelines

1. **Fork the repository** and create feature branches
2. **Follow coding conventions** defined in `AGENTS.md` files
3. **Write comprehensive tests** with >90% coverage requirement
4. **Update documentation** for any new features or changes
5. **Submit pull requests** against the `main` branch

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new agent workflow orchestration
fix: resolve memory leak in MCP server
docs: update API documentation
refactor: improve error handling in auth service
test: add integration tests for workflow engine
```

### Code Review Process

- All PRs require review from at least one maintainer
- Automated checks must pass (tests, linting, security scans)
- Breaking changes require discussion and approval
- Documentation updates required for user-facing changes

## 📚 Additional Resources

- **[API Documentation](http://localhost:8000/docs)** - Interactive FastAPI documentation
- **[Development Guide](DEVELOPMENT.md)** - Detailed development workflow
- **[Architecture Deep Dive](docs/architecture.md)** - Technical architecture details
- **[Contributing Guidelines](CONTRIBUTING.md)** - How to contribute to the project
- **[Changelog](CHANGELOG.md)** - Version history and breaking changes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **LangGraph** - Workflow orchestration framework
- **MCP** - Model Context Protocol for tool integration
- **Mem0** - Memory management and persistence
- **R2R** - Retrieval-augmented generation
- **Pydantic AI** - Type-safe AI framework
- **AG2** - Multi-agent systems

---

**⭐ Star this repository** if AgentFlow helps accelerate your AI agent development!

For questions, issues, or feature requests, please [open an issue](https://github.com/your-org/agentflow/issues).

*Built with ❤️ for the AI developer community*
