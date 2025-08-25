# AgentFlow

> **Unified AI Agent Development Platform** - Reduce agent development time by 60-80% through standardized interfaces, visual workflow orchestration, and enterprise-grade infrastructure.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python Version](https://img.shields.io/badge/python-3.11+-green.svg)
![TypeScript](https://img.shields.io/badge/typescript-5.x-blue.svg)
![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)
![Test Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen.svg)

---

## 📋 Table of Contents

- [Quick Reference](#quick-reference)
- [Visual Architecture](#visual-architecture)
- [Installation Guide](#installation-guide)
- [Service Health Checks](#service-health-checks)
- [Usage Instructions](#usage-instructions)
- [Project Structure](#project-structure)
- [Development Guide](#development-guide)
- [Performance & SLOs](#performance--slos)
- [Contributing](#contributing)
- [License & Documentation](#license--documentation)

## 🚀 Quick Reference

AgentFlow is a comprehensive AI agent development platform that unifies six leading frameworks (LangGraph, MCP, Mem0, R2R, Pydantic AI, AG2) to create production-ready AI agents with enterprise-grade security and 99.5% uptime targets.

### ✨ Key Features

- **Multi-level Memory Management** - Persistent context with contradiction resolution and semantic search
- **Visual Workflow Orchestration** - Stateful agent workflows with error recovery and checkpointing
- **Standardized Tool Integration** - MCP-compliant tool ecosystem with discovery and permissions
- **Advanced Knowledge Management** - Hybrid search with knowledge graphs and source attribution
- **Production-Ready Deployment** - Enterprise security, monitoring, and scalable infrastructure
- **Type-Safe Development** - Comprehensive TypeScript and Pydantic validation
- **Real-time Operations** - Streaming responses with progress tracking and error handling

### 🛠️ Technology Stack

![FastAPI](https://img.shields.io/badge/FastAPI-0.115.12-009688.svg)
![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)
![React](https://img.shields.io/badge/React-18-61DAFB.svg)
![Python](https://img.shields.io/badge/Python-3.11.8-3776AB.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17.x-336791.svg)
![Redis](https://img.shields.io/badge/Redis-7.x-DC382D.svg)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)

## 🏗️ Visual Architecture

### High-Level System Architecture

```mermaid
flowchart TB
    subgraph "Frontend Layer"
        UI[Next.js 14 Frontend<br/>React 18 + TypeScript 5.x]
        DASH[Agent Dashboard]
        WORK[Workflow Editor]
        MEM[Memory Browser]
        KB[Knowledge Base UI]
    end
    
    subgraph "API Gateway"
        GW[FastAPI 0.115.12<br/>Authentication & Rate Limiting]
    end
    
    subgraph "Core Services"
        API[Backend API Service<br/>Python 3.11.8]
        MCP[MCP Server<br/>Tool Integration]
        AGENT[Agent Orchestration<br/>LangGraph + Pydantic AI]
        MEMORY[Memory Service<br/>Mem0 Integration]
        RAG[Knowledge Service<br/>R2R Integration]
    end
    
    subgraph "Data Layer"
        PG[(PostgreSQL 17<br/>Primary Database)]
        REDIS[(Redis 7<br/>Caching & Sessions)]
        QD[(Qdrant<br/>Vector Database)]
        NEO[(Neo4j<br/>Knowledge Graph)]
    end
    
    UI --> GW
    DASH --> GW
    WORK --> GW
    MEM --> GW
    KB --> GW
    
    GW --> API
    GW --> MCP
    
    API --> AGENT
    API --> MEMORY
    API --> RAG
    
    AGENT --> PG
    AGENT --> REDIS
    MEMORY --> PG
    MEMORY --> QD
    RAG --> PG
    RAG --> QD
    RAG --> NEO
    
    MCP --> AGENT
```

### Agent Workflow Architecture

```mermaid
flowchart LR
    subgraph "Agent Execution Flow"
        START([User Request]) --> AUTH[Authentication]
        AUTH --> PARSE[Request Parsing]
        PARSE --> ROUTE[Route to Agent]
        
        subgraph "LangGraph Orchestration"
            ROUTE --> PLAN[Planning Node]
            PLAN --> TOOL[Tool Selection]
            TOOL --> EXEC[Execution Node]
            EXEC --> MEM[Memory Update]
            MEM --> CHECK{Checkpoint}
            CHECK -->|Continue| TOOL
            CHECK -->|Complete| RESP[Response Node]
        end
        
        RESP --> STREAM[Stream Response]
        STREAM --> END([Complete])
    end
    
    subgraph "Memory System"
        MEM --> USER_MEM[(User Memory)]
        MEM --> SESS_MEM[(Session Memory)]
        MEM --> AGENT_MEM[(Agent Memory)]
    end
    
    subgraph "Knowledge & Tools"
        TOOL --> SEARCH[R2R Search]
        TOOL --> VECTOR[Vector Similarity]
        TOOL --> GRAPH[Graph Query]
        TOOL --> MCP_TOOLS[MCP Tools]
    end
```

### Data Flow and Component Relationships

```mermaid
classDiagram
    class Agent {
        +String id
        +String name
        +AgentStatus status
        +Configuration config
        +execute(request)
        +checkpoint()
        +resume(checkpoint_id)
    }
    
    class Memory {
        +String scope
        +Dict context
        +store(key, value)
        +retrieve(query)
        +contradict_resolution()
    }
    
    class KnowledgeBase {
        +String id
        +List documents
        +ingest(document)
        +search(query, type)
        +get_sources()
    }
    
    class Tool {
        +String name
        +Schema parameters
        +execute(params)
        +validate_permissions()
    }
    
    class Workflow {
        +Graph graph
        +String state
        +List checkpoints
        +run()
        +pause()
        +resume()
    }
    
    Agent --> Memory : uses
    Agent --> KnowledgeBase : queries
    Agent --> Tool : executes
    Agent --> Workflow : orchestrates
    
    Memory --> KnowledgeBase : enriches
    Workflow --> Agent : manages
```

### Deployment Architecture

```mermaid
flowchart TB
    subgraph "Load Balancer"
        LB[NGINX/ALB]
    end
    
    subgraph "Application Tier"
        subgraph "API Instances"
            API1[API Instance 1]
            API2[API Instance 2]
            API3[API Instance N]
        end
        
        subgraph "MCP Services"
            MCP1[MCP Server 1]
            MCP2[MCP Server 2]
        end
        
        subgraph "Frontend"
            FE[Next.js Static/SSG]
        end
    end
    
    subgraph "Data Tier"
        subgraph "Primary Storage"
            PG_MASTER[(PostgreSQL Master)]
            PG_REPLICA[(PostgreSQL Replica)]
        end
        
        subgraph "Caching Layer"
            REDIS_MASTER[(Redis Master)]
            REDIS_REPLICA[(Redis Replica)]
        end
        
        subgraph "Vector & Graph"
            QDRANT[(Qdrant Cluster)]
            NEO4J[(Neo4j Cluster)]
        end
    end
    
    LB --> API1
    LB --> API2
    LB --> API3
    LB --> FE
    
    API1 --> PG_MASTER
    API2 --> PG_REPLICA
    API3 --> PG_MASTER
    
    API1 --> REDIS_MASTER
    API2 --> REDIS_MASTER
    API3 --> REDIS_MASTER
    
    API1 --> QDRANT
    API2 --> QDRANT
    API3 --> QDRANT
    
    MCP1 --> NEO4J
    MCP2 --> NEO4J
```

## 📦 Installation Guide

### Prerequisites

Ensure you have the following installed on your system:

- **Python 3.11+** (pinned to 3.11.8 for consistency)
- **Node.js 20+** for frontend development
- **Docker & Docker Compose** for containerized services
- **uv package manager** for Python dependency management
- **Git** for version control

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 8GB | 16GB+ |
| CPU | 4 cores | 8+ cores |
| Storage | 50GB | 100GB+ SSD |
| Network | Broadband | High-speed internet |

### Quick Start Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/JackSmack1971/AgentFlow.git
   cd AgentFlow
   ```

2. **Environment Setup**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit with your API keys and configuration
   nano .env  # or your preferred editor
   ```

3. **Install uv Package Manager** (if not already installed)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source ~/.bashrc  # or restart terminal
   ```

4. **Run Setup Script**
   ```bash
   # Automated setup script handles everything
   ./scripts/setup.sh
   ```

5. **Verify Installation**
   ```bash
   # Check all services are running
   ./scripts/health-check.sh
   
   # Access the application
   # Frontend: http://localhost:3000
   # API: http://localhost:8000
   # API Docs: http://localhost:8000/docs
   ```

### Manual Installation (Advanced)

<details>
<summary>Click to expand manual installation steps</summary>

#### Backend Setup

```bash
# Install Python dependencies
uv sync --frozen

# Setup database
docker-compose up -d postgres redis qdrant neo4j

# Run database migrations
uv run alembic upgrade head

# Start backend services
uv run uvicorn apps.api.app.main:app --reload --host 0.0.0.0 --port 8000 &
uv run python apps/mcp/server.py &
```

#### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Build and start frontend
npm run build
npm run start
```

#### Configuration Verification

```bash
# Test API endpoints
curl http://localhost:8000/health

# Test MCP server
curl http://localhost:8001/health

# Test frontend
curl http://localhost:3000
```

</details>

### Docker Compose Deployment

For production deployment:

```bash
# Production deployment with all services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Monitor logs
docker-compose logs -f

# Scale API instances
docker-compose up -d --scale api=3
```

### Troubleshooting Installation

| Issue | Solution |
|-------|----------|
| Port conflicts | Change ports in `.env` file |
| Permission errors | Check Docker permissions: `sudo usermod -aG docker $USER` |
| Database connection | Verify PostgreSQL is running and credentials are correct |
| Memory issues | Increase Docker memory limit to 8GB+ |
| uv not found | Install uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

## 🩺 Service Health Checks

Ensure core services are responding before development or integration.

```bash
# Backend API
curl http://localhost:8000/health

# MCP server
curl http://localhost:8001/health

# Frontend
curl http://localhost:3000
```

Run the combined health‑check script:

```bash
./scripts/dev/health-check.sh
```

## 💻 Usage Instructions

### Basic Agent Creation

Create your first AI agent in under 5 minutes:

```python
from agentflow import AgentBuilder, Memory, Tools

# Initialize agent builder
builder = AgentBuilder(
    name="Customer Support Agent",
    description="Helps customers with product inquiries"
)

# Configure memory
memory = Memory(
    scope="user",  # user, session, or agent scope
    retention_days=30
)

# Add tools
tools = Tools()
tools.add_search_tool("knowledge_base")
tools.add_email_tool("support@company.com")

# Build and deploy
agent = builder.build(memory=memory, tools=tools)
agent_id = agent.deploy()

print(f"Agent deployed with ID: {agent_id}")
```

### Visual Workflow Creation

Use the web interface for complex workflows:

1. **Access the Dashboard**
   ```bash
   # Open in browser
   http://localhost:3000/dashboard
   ```

2. **Create New Agent**
   - Click "New Agent" button
   - Choose from templates or start from scratch
   - Configure personality and objectives

3. **Design Workflow**
   - Drag and drop nodes in the visual editor
   - Connect conditional logic and tool calls
   - Set up memory management and checkpointing

4. **Test and Deploy**
   - Use the test console to validate behavior
   - Review execution traces and debug
   - Deploy to production environment

### API Usage Examples

#### Authentication

```python
import requests

# Get API token
auth_response = requests.post("http://localhost:8000/auth/login", {
    "email": "user@example.com",
    "password": "secure_password"
})
token = auth_response.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}
```

#### Agent Management

```python
# Create new agent
agent_data = {
    "name": "Data Analyst Agent",
    "description": "Analyzes data and generates insights",
    "config": {
        "model": "gpt-4",
        "temperature": 0.1,
        "max_tokens": 2000
    }
}

response = requests.post(
    "http://localhost:8000/agents/", 
    json=agent_data,
    headers=headers
)
agent = response.json()

# Execute agent
execution_request = {
    "prompt": "Analyze the latest sales data trends",
    "context": {"user_id": "user_123"}
}

execution = requests.post(
    f"http://localhost:8000/agents/{agent['id']}/execute",
    json=execution_request,
    headers=headers
)

print(execution.json()["response"])
```

#### Memory Operations

```python
# Store user memory
memory_data = {
    "key": "user_preferences",
    "value": {"theme": "dark", "notifications": True},
    "scope": "user",
    "user_id": "user_123"
}

requests.post(
    "http://localhost:8000/memory/",
    json=memory_data,
    headers=headers
)

# Retrieve memory
memory_response = requests.get(
    "http://localhost:8000/memory/search",
    params={"query": "preferences", "scope": "user", "user_id": "user_123"},
    headers=headers
)

preferences = memory_response.json()["results"]
```

#### Knowledge Base Management

```python
# Upload document
with open("company_policy.pdf", "rb") as f:
    files = {"file": f}
    upload_response = requests.post(
        "http://localhost:8000/knowledge/upload",
        files=files,
        headers=headers
    )

document_id = upload_response.json()["document_id"]

# Search knowledge base
search_response = requests.get(
    "http://localhost:8000/knowledge/search",
    params={
        "query": "vacation policy",
        "search_type": "hybrid",  # vector + keyword search
        "limit": 5
    },
    headers=headers
)

results = search_response.json()["results"]
for result in results:
    print(f"Score: {result['score']}, Source: {result['source']}")
    print(f"Content: {result['content'][:200]}...")
```

### Configuration Options

#### Environment Variables

```bash
# Core Configuration
APP_NAME=AgentFlow
DEBUG=false
SECRET_KEY=your-super-secure-secret-key

# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost/agentflow
REDIS_URL=redis://localhost:6379/0

# AI Model Configuration
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-qdrant-key

# Monitoring and Logging
LOG_LEVEL=INFO
SENTRY_DSN=https://your-sentry-dsn
```

#### Advanced Configuration

```yaml
# config/production.yaml
agent_settings:
  default_timeout: 30
  max_concurrent_executions: 100
  checkpoint_interval: 10

memory_settings:
  max_context_length: 32000
  contradiction_resolution: true
  automatic_pruning: true

knowledge_settings:
  chunk_size: 512
  chunk_overlap: 50
  embedding_model: "text-embedding-3-large"
  enable_graph_search: true

performance:
  cache_ttl: 300
  rate_limit_per_minute: 1000
  connection_pool_size: 20
```

### Streaming and Real-time Features

```python
import asyncio
import aiohttp

async def stream_agent_response():
    """Stream agent responses in real-time."""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8000/agents/stream",
            json={
                "agent_id": "agent_123",
                "prompt": "Generate a comprehensive report",
                "stream": True
            },
            headers=headers
        ) as response:
            async for line in response.content:
                if line:
                    data = json.loads(line.decode())
                    if data["type"] == "token":
                        print(data["content"], end="", flush=True)
                    elif data["type"] == "progress":
                        print(f"\nProgress: {data['step']}")
                    elif data["type"] == "complete":
                        print(f"\nCompleted in {data['duration']}s")
                        break

# Run the streaming example
asyncio.run(stream_agent_response())
```

## 📁 Project Structure

### Directory Overview

```
AgentFlow/
├── apps/                          # Application services
│   ├── api/                       # FastAPI backend service
│   │   ├── app/                   # Application code
│   │   │   ├── routers/           # API route handlers
│   │   │   │   ├── auth.py        # Authentication endpoints
│   │   │   │   ├── agents.py      # Agent management
│   │   │   │   ├── memory.py      # Memory operations
│   │   │   │   ├── rag.py         # Knowledge & RAG
│   │   │   │   └── health.py      # Health checks
│   │   │   ├── services/          # Business logic layer
│   │   │   ├── models/            # Pydantic schemas
│   │   │   ├── dependencies.py    # FastAPI dependencies
│   │   │   └── main.py           # FastAPI application
│   │   └── Dockerfile            # API containerization
│   └── mcp/                      # Model Context Protocol server
│       ├── server.py             # MCP implementation
│       ├── tools/                # Tool definitions
│       └── protocols/            # Protocol handlers
├── frontend/                     # Next.js 14 frontend
│   ├── app/                      # App Router structure
│   │   ├── (auth)/               # Authentication routes
│   │   ├── (dashboard)/          # Main application
│   │   │   ├── agents/           # Agent management UI
│   │   │   ├── memory/           # Memory browser
│   │   │   ├── knowledge/        # Knowledge base UI
│   │   │   └── settings/         # Configuration
│   │   ├── layout.tsx            # Root layout
│   │   └── page.tsx             # Landing page
│   ├── components/               # Reusable components
│   │   ├── ui/                   # Base UI components
│   │   ├── agents/               # Agent-specific components
│   │   ├── memory/               # Memory components
│   │   └── layout/               # Layout components
│   ├── lib/                      # Utility libraries
│   ├── styles/                   # CSS and styling
│   └── package.json             # Node.js dependencies
├── packages/                     # Shared utility packages
│   ├── common/                   # Common utilities
│   ├── config/                   # Configuration management
│   ├── database/                 # Database utilities
│   ├── auth/                     # Authentication utilities
│   ├── monitoring/               # Observability
│   └── r2r/                      # R2R integration
├── tests/                        # Comprehensive test suite
│   ├── api/                      # API tests
│   │   ├── routers/              # Router tests
│   │   ├── services/             # Service tests
│   │   └── integration/          # Integration tests
│   ├── frontend/                 # Frontend tests
│   ├── mcp/                      # MCP server tests
│   └── e2e/                      # End-to-end tests
├── infra/                        # Infrastructure as code
│   ├── docker/                   # Docker configurations
│   ├── kubernetes/               # K8s manifests
│   ├── terraform/                # Infrastructure definitions
│   └── monitoring/               # Monitoring configs
├── scripts/                      # Development scripts
│   ├── setup.sh                  # Environment setup
│   ├── test.sh                   # Test runner
│   ├── deploy.sh                 # Deployment script
│   └── health-check.sh           # Health validation
├── pyproject.toml               # Python dependencies & config
├── docker-compose.yml           # Local development services
├── .env.example                 # Environment template
├── Makefile                     # Build automation
└── README.md                    # This file
```

### Key Files and Their Purposes

| File/Directory | Purpose | Criticality |
|----------------|---------|-------------|
| `apps/api/app/main.py` | FastAPI application entry point | High |
| `apps/mcp/server.py` | MCP protocol server implementation | High |
| `frontend/app/layout.tsx` | Next.js root layout component | High |
| `pyproject.toml` | Python dependencies and configuration | High |
| `docker-compose.yml` | Local development environment | Medium |
| `packages/common/` | Shared utilities across services | Medium |
| `tests/` | Comprehensive test suite (≥90% coverage) | High |
| `infra/` | Production deployment configurations | Medium |
| `scripts/setup.sh` | Automated environment setup | Low |

### Code Organization Principles

#### Backend Architecture (FastAPI)

- **Router-based Organization**: Each business domain has its own router
- **Service Layer Pattern**: Business logic separated from HTTP concerns  
- **Dependency Injection**: FastAPI's built-in DI for database sessions and services
- **Pydantic Models**: Strict input/output validation and serialization
- **Async-First**: All I/O operations use async/await patterns

#### Frontend Architecture (Next.js)

- **App Router**: Next.js 14+ file-based routing system
- **Server Components**: Server-side rendering by default for performance
- **Feature-based Structure**: Components organized by business domain
- **Type Safety**: Comprehensive TypeScript coverage
- **Progressive Enhancement**: Works without JavaScript, enhanced with it

#### Shared Packages

- **Domain-Driven**: Packages organized by functional domain
- **Minimal Dependencies**: Each package has focused responsibilities
- **Version Management**: Semantic versioning with backward compatibility
- **Documentation**: Comprehensive docstrings and README files

## 🔧 Development Guide

### Development Environment Setup

#### Prerequisites Installation

```bash
# Install Python 3.11+ (recommended: pyenv)
pyenv install 3.11.8
pyenv local 3.11.8

# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Node.js 20+ (recommended: nvm)
nvm install 20
nvm use 20

# Install Docker Desktop
# Visit: https://docker.com/products/docker-desktop
```

#### Project Setup

```bash
# Clone and enter project
git clone https://github.com/JackSmack1971/AgentFlow.git
cd AgentFlow

# Setup Python environment
uv sync --dev  # Install all dependencies including dev tools

# Setup frontend
cd frontend && npm install && cd ..

# Setup environment variables
cp .env.example .env
# Edit .env with your API keys and configuration

# Start development services
docker-compose up -d postgres redis qdrant neo4j

# Run database migrations
uv run alembic upgrade head

# Verify setup
./scripts/health-check.sh
```

### Development Workflow

#### Backend Development

```bash
# Start backend with auto-reload
uv run uvicorn apps.api.app.main:app --reload --host 0.0.0.0 --port 8000

# Start MCP server
uv run python apps/mcp/server.py

# Run tests
uv run pytest --cov=apps --cov-report=html

# Format code
uv run black apps/ tests/
uv run isort apps/ tests/

# Type checking
uv run mypy apps/

# Security scanning
uv run bandit -r apps/
```

#### Frontend Development

```bash
cd frontend

# Start development server
npm run dev

# Run tests
npm test

# Type checking
npm run type-check

# Linting and formatting (Biome)
npm run lint
npm run format

# Build for production
npm run build
```

### Code Style and Standards

#### Python Standards

- **Formatter**: Black (line length: 88)
- **Import Sorting**: isort
- **Linting**: Ruff with comprehensive rule set
- **Type Checking**: mypy in strict mode
- **Security**: Bandit for security analysis

```python
# Example: Proper Python service implementation
from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

class AgentService:
    """Service for managing AI agents."""
    
    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session
    
    async def create_agent(
        self, 
        agent_data: AgentCreate,
        user_id: str
    ) -> AgentResponse:
        """Create a new agent with validation."""
        # Implementation with proper error handling
        pass
    
    async def list_agents(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[AgentResponse]:
        """List user's agents with pagination."""
        # Implementation with proper database queries
        pass
```

#### TypeScript Standards

- **Formatter**: Biome (2-space indentation)
- **Linting**: Biome with strict rules
- **Type Safety**: Strict TypeScript configuration
- **Component Style**: React 18 with hooks and Server Components

```tsx
// Example: Proper TypeScript component
import { ReactNode } from 'react';

interface AgentCardProps {
  id: string;
  name: string;
  status: 'active' | 'inactive' | 'training' | 'error';
  onEdit: (id: string) => void;
  children?: ReactNode;
}

export default function AgentCard({ 
  id, 
  name, 
  status, 
  onEdit,
  children 
}: AgentCardProps): JSX.Element {
  return (
    <div className="agent-card">
      <h3>{name}</h3>
      <span className={`status ${status}`}>
        {status}
      </span>
      <button onClick={() => onEdit(id)}>
        Edit Agent
      </button>
      {children}
    </div>
  );
}
```

### Testing Standards

#### Test Coverage Requirements

- **Minimum Coverage**: 90% across all codebases
- **Unit Tests**: Individual functions and components
- **Integration Tests**: API endpoints and service interactions
- **End-to-End Tests**: Complete user workflows

#### Backend Testing

```python
# Example: FastAPI endpoint test
import pytest
from httpx import AsyncClient
from apps.api.app.main import app

@pytest.mark.asyncio
async def test_create_agent():
    """Test agent creation endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        agent_data = {
            "name": "Test Agent",
            "description": "Test description",
            "config": {"model": "gpt-4"}
        }
        
        response = await client.post(
            "/agents/",
            json=agent_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Agent"
        assert "id" in data
```

#### Frontend Testing

```tsx
// Example: React component test
import { render, screen, fireEvent } from '@testing-library/react';
import AgentCard from '../components/agents/agent-card';

describe('AgentCard', () => {
  it('renders agent information correctly', () => {
    const mockOnEdit = jest.fn();
    
    render(
      <AgentCard
        id="agent-1"
        name="Test Agent"
        status="active"
        onEdit={mockOnEdit}
      />
    );
    
    expect(screen.getByText('Test Agent')).toBeInTheDocument();
    expect(screen.getByText('active')).toBeInTheDocument();
    
    fireEvent.click(screen.getByText('Edit Agent'));
    expect(mockOnEdit).toHaveBeenCalledWith('agent-1');
  });
});
```

### Build and Deployment

#### Local Development

```bash
# Start all services
docker-compose up -d

# Or start individual services
docker-compose up -d postgres redis  # Just databases
uvicorn apps.api.app.main:app --reload  # API server
npm run dev  # Frontend (in frontend/ directory)
```

#### Production Build

```bash
# Build Docker images
docker build -t agentflow/api:latest -f apps/api/Dockerfile .
docker build -t agentflow/mcp:latest -f apps/mcp/Dockerfile .
docker build -t agentflow/frontend:latest -f frontend/Dockerfile ./frontend

# Deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Or deploy to Kubernetes
kubectl apply -f infra/kubernetes/
```

#### CI/CD Pipeline

The project includes automated GitHub Actions workflows:

- **Code Quality**: Linting, formatting, type checking
- **Testing**: Unit, integration, and E2E tests
- **Security**: Dependency scanning and security analysis
- **Build**: Docker image building and registry push
- **Deployment**: Automated deployment to staging and production

### Performance Optimization

#### Backend Performance

- **Database Optimization**: Connection pooling, query optimization, indexing
- **Caching Strategy**: Redis for session data and frequently accessed information
- **Async Operations**: Non-blocking I/O for all external service calls
- **Rate Limiting**: SlowAPI middleware for API protection

#### Frontend Performance

- **Server Components**: Minimize client-side JavaScript
- **Code Splitting**: Automatic route-based code splitting
- **Image Optimization**: Next.js built-in image optimization
- **Caching**: Aggressive caching strategies for static assets

### Debugging and Monitoring

#### Development Debugging

```bash
# View logs
docker-compose logs -f api
docker-compose logs -f mcp

# Debug with breakpoints
uv run python -m debugpy --listen 5678 --wait-for-client apps/api/app/main.py

# Database inspection
docker-compose exec postgres psql -U postgres -d agentflow
```

#### Production Monitoring

- **Health Endpoints**: `/health` endpoints on all services
- **Metrics Collection**: Prometheus metrics integration
- **Log Aggregation**: Structured logging with correlation IDs
- **Error Tracking**: Sentry integration for error monitoring
- **Performance Monitoring**: APM integration for request tracing

## ⚡ Performance & SLOs

### Service Level Objectives (SLOs)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Agent Creation Time** | ≤5 minutes | P95 end-to-end workflow |
| **API Response Time** | P95 < 300ms | Simple queries |
| **Complex Workflow Time** | P95 < 2s | Multi-step agent execution |
| **Memory Operations** | <100ms | Retrieval operations |
| **Knowledge Search** | <500ms | Hybrid search queries |
| **System Uptime** | 99.5% | Monthly availability |
| **Concurrent Users** | 1000+ | Per instance support |
| **Test Coverage** | ≥90% | Across all codebases |

### Performance Targets

#### Response Time Breakdown

```mermaid
gantt
    title Agent Execution Performance Timeline
    dateFormat X
    axisFormat %Lms
    
    section Request Processing
    Authentication    :0, 50
    Request Parsing   :50, 100
    
    section Agent Execution
    Memory Retrieval  :100, 200
    Tool Selection    :200, 400
    Execution         :400, 1500
    
    section Response
    Memory Update     :1500, 1600
    Response Format   :1600, 1700
    Stream Response   :1700, 2000
```

#### Scalability Metrics

- **Horizontal Scaling**: Auto-scaling based on CPU/memory usage
- **Database Performance**: 1000+ concurrent connections
- **Vector Search**: Sub-second similarity search on 1M+ vectors
- **Memory Efficiency**: <2GB RAM per API instance
- **Storage Growth**: Linear scaling with document ingestion

### Monitoring and Alerting

#### Key Performance Indicators

```python
# Example: Performance monitoring integration
import time
from functools import wraps
from prometheus_client import Counter, Histogram, Gauge

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests')
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')
ACTIVE_AGENTS = Gauge('active_agents_total', 'Number of active agents')

def monitor_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        REQUEST_COUNT.inc()
        
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            REQUEST_LATENCY.observe(time.time() - start_time)
    
    return wrapper
```

#### Alert Thresholds

- **High Latency**: P95 response time > 5s
- **Error Rate**: >5% error rate over 5 minutes
- **Memory Usage**: >80% memory utilization
- **Database Connections**: >80% connection pool utilization
- **Disk Space**: <20% available storage

### Optimization Strategies

#### Database Optimization

```sql
-- Example: Optimized database indexes
CREATE INDEX CONCURRENTLY idx_agents_user_status 
ON agents(user_id, status) 
WHERE status IN ('active', 'training');

CREATE INDEX CONCURRENTLY idx_memory_user_scope_created 
ON memories(user_id, scope, created_at DESC);

CREATE INDEX CONCURRENTLY idx_documents_embedding 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

#### Caching Strategy

```python
# Example: Multi-level caching implementation
import redis.asyncio as redis
from functools import wraps
import json

class CacheManager:
    def __init__(self):
        self.redis_client = redis.from_url(os.getenv("REDIS_URL"))
        self.local_cache = {}
    
    async def get_cached(self, key: str, ttl: int = 300):
        """Get from cache with fallback."""
        # Check local cache first (fastest)
        if key in self.local_cache:
            return self.local_cache[key]
        
        # Check Redis cache (fast)
        cached_data = await self.redis_client.get(key)
        if cached_data:
            data = json.loads(cached_data)
            self.local_cache[key] = data  # Populate local cache
            return data
        
        return None
    
    async def set_cached(self, key: str, data: dict, ttl: int = 300):
        """Set in both caches."""
        self.local_cache[key] = data
        await self.redis_client.setex(key, ttl, json.dumps(data))
```

## 🤝 Contributing

We welcome contributions from the community! Please follow these guidelines to ensure smooth collaboration.

### Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a feature branch** from `main`
4. **Make your changes** following our coding standards
5. **Write tests** for new functionality
6. **Submit a pull request** with a clear description

### Development Process

#### Setting Up for Contributions

```bash
# Fork and clone your fork
git clone https://github.com/yourusername/AgentFlow.git
cd AgentFlow

# Add upstream remote
git remote add upstream https://github.com/JackSmack1971/AgentFlow.git

# Create feature branch
git checkout -b feature/your-feature-name

# Setup development environment
./scripts/setup.sh
```

#### Making Changes

1. **Code Changes**: Follow existing patterns and conventions
2. **Documentation**: Update relevant documentation and comments
3. **Tests**: Add comprehensive tests for new functionality
4. **Commit Messages**: Use conventional commit format

```bash
# Example commit messages
feat: add memory contradiction resolution
fix: resolve database connection timeout
docs: update API documentation
test: add integration tests for agent execution
refactor: simplify memory service architecture
perf: optimize vector search performance
```

#### Pull Request Process

1. **Update Documentation**: Ensure README and docs are current
2. **Run Quality Checks**: All linting and tests must pass
3. **Write Clear PR Description**: Explain what, why, and how
4. **Request Review**: Tag relevant maintainers
5. **Address Feedback**: Respond promptly to review comments

### Code Quality Standards

#### Required Checks

All pull requests must pass these automated checks:

- ✅ **Linting**: Python (Ruff) and TypeScript (Biome)
- ✅ **Formatting**: Black (Python) and Biome (TypeScript)  
- ✅ **Type Checking**: mypy (Python) and tsc (TypeScript)
- ✅ **Testing**: ≥90% code coverage maintained
- ✅ **Security**: Bandit security analysis passes
- ✅ **Dependencies**: No security vulnerabilities

#### Manual Review Criteria

- **Architecture**: Changes align with overall system design
- **Performance**: No degradation of SLO targets
- **Security**: Proper input validation and authorization
- **Usability**: Clear APIs and user-friendly interfaces
- **Documentation**: Comprehensive and accurate documentation

### Contribution Areas

We especially welcome contributions in these areas:

- **Framework Integrations**: Additional AI framework support
- **Tool Development**: New MCP-compliant tools
- **Performance Optimization**: Database, caching, or algorithm improvements
- **UI/UX Improvements**: Frontend components and user experience
- **Documentation**: Tutorials, examples, and API documentation
- **Testing**: Additional test coverage and testing infrastructure
- **Infrastructure**: Deployment and monitoring improvements

### Community Guidelines

- **Be Respectful**: Treat all contributors with respect and kindness
- **Be Collaborative**: Work together to find the best solutions
- **Be Patient**: Allow time for review and discussion
- **Be Clear**: Communicate clearly and provide context
- **Be Constructive**: Provide helpful feedback and suggestions

### Getting Help

- **Documentation**: Check existing documentation first
- **Issues**: Search existing issues before creating new ones
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Discord**: Join our community Discord for real-time chat
- **Email**: Contact maintainers at team@agentflow.io

## 📄 License & Documentation

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Documentation Links

- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI)
- **Framework Documentation**:
  - [LangGraph Documentation](https://langraph-doc.readthedocs.io/)
  - [Pydantic AI Documentation](https://ai.pydantic.dev/)
  - [Mem0 Documentation](https://docs.mem0.ai/)
  - [R2R Documentation](https://r2r-docs.sciphi.ai/)
  - [MCP Documentation](https://modelcontextprotocol.io/)
- **Deployment Guides**: [./docs/deployment/](./docs/deployment/)
- **Architecture Decision Records**: [./docs/adr/](./docs/adr/)

### Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed release notes and version history.

---

**Generated on**: August 23, 2025  
**Analysis Timestamp**: Latest project state as of analysis  
**Project Version**: 0.1.0 (MVP Release)  
**Maintainer**: AgentFlow Development Team

---

> 🚀 **Ready to get started?** Run `./scripts/setup.sh` and have your first AI agent running in under 5 minutes!

[⬆️ Back to top](#agentflow)
