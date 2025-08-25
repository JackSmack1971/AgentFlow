# AgentFlow System Architecture

## Overview

AgentFlow is a comprehensive AI agent orchestration platform built with modern distributed systems principles. The architecture emphasizes reliability, security, observability, and seamless integration of multiple AI frameworks and external services.

## Core Components

### 1. API Layer (FastAPI)
**Location**: `apps/api/app/`

The main application entry point that orchestrates all system components:

```python
# Main application structure
- FastAPI application with middleware stack
- RESTful API endpoints for all services
- Request/response handling with validation
- Error handling and response formatting
```

**Key Features**:
- **Security Middleware**: Authentication, rate limiting, request validation
- **Audit Middleware**: Request logging and compliance tracking
- **Correlation ID Middleware**: Distributed tracing support
- **Body Size Limiting**: Request payload protection

### 2. Service Layer
**Location**: `apps/api/app/services/`

Business logic abstraction with resilience patterns:

| Service | Purpose | Key Features |
|---------|---------|--------------|
| **AgentService** | AI agent orchestration | Pydantic AI integration, retry logic, timeout handling |
| **MemoryService** | Memory management | Mem0 integration, TTL support, event publishing |
| **AuthService** | Authentication & authorization | JWT tokens, TOTP 2FA, session management |
| **RAGService** | Retrieval Augmented Generation | R2R integration, document processing |
| **WorkflowService** | Workflow orchestration | LangGraph integration, state management |
| **CircuitBreaker** | Resilience management | Failure detection, automatic recovery |

### 3. External Services

The system integrates with multiple external services through Docker Compose:

```yaml
# Core Infrastructure Services
- PostgreSQL: Primary data persistence
- Redis: Caching, session storage, rate limiting
- Qdrant: Vector database for embeddings
- Neo4j: Graph database for relationships
- R2R: Document processing and RAG pipeline
```

### 4. Frontend Layer
**Location**: `frontend/`

Next.js-based user interface providing:
- Agent management dashboard
- Memory browser and search
- Authentication flows
- Real-time agent interactions

### 5. MCP Tools
**Location**: `apps/mcp/tools/`

Model Context Protocol tools for extended functionality:
- RAG search capabilities
- System monitoring
- Security validation
- Registry management

## Interfaces

### API Endpoints

The system exposes RESTful APIs organized by domain:

```
├── /auth
│   ├── POST /login - User authentication
│   ├── POST /register - User registration
│   ├── POST /refresh - Token refresh
│   └── POST /logout - Session termination
├── /agents
│   ├── GET / - List agents
│   ├── POST / - Create agent
│   ├── GET /{id} - Get agent details
│   └── POST /{id}/run - Execute agent
├── /memory
│   ├── GET / - List memory items
│   ├── POST / - Create memory item
│   ├── GET /{id} - Get memory item
│   ├── PUT /{id} - Update memory item
│   └── DELETE /{id} - Delete memory item
├── /rag
│   ├── POST /search - Document search
│   └── POST /ingest - Document ingestion
├── /workflow
│   ├── GET / - List workflows
│   ├── POST / - Create workflow
│   └── POST /{id}/execute - Execute workflow
└── /health
    └── GET / - Health check endpoint
```

### Service Interfaces

Each service exposes a consistent async interface:

```python
# Example service interface pattern
class BaseService:
    async def execute_operation(
        self,
        data: InputModel,
        *,
        timeout: float | None = None,
        retries: int | None = None
    ) -> OutputModel:
        """Execute operation with resilience patterns."""
```

### Data Contracts

Pydantic models ensure type safety across all interfaces:

```python
# Authentication models
class LoginRequest(BaseModel):
    username: str
    password: str

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

# Memory models
class MemoryItemCreate(BaseModel):
    text: str
    scope: MemoryScope
    user_id: str
    agent_id: str | None = None
    session_id: str | None = None
    tags: list[str] = []
    metadata: dict[str, Any] = {}
    ttl: int | None = None
```

## Data Flows

### 1. Agent Execution Flow

```
User Request → API Router → AgentService → Pydantic AI Agent
                                      ↓
                                External LLM API
                                      ↓
                                Response Processing
                                      ↓
                               Memory Storage (Optional)
                                      ↓
                               Response to User
```

### 2. Memory Management Flow

```
User Request → API Router → MemoryService → Mem0 Backend
                                      ↓
                                Qdrant Vector DB
                                      ↓
                                PostgreSQL (Metadata)
                                      ↓
                               Response with Embeddings
```

### 3. Authentication Flow

```
Login Request → API Router → AuthService → PostgreSQL (User Lookup)
                                      ↓
                                JWT Token Generation
                                      ↓
                               Redis (Session Storage)
                                      ↓
                               Auth Response with Tokens
```

### 4. RAG Pipeline Flow

```
Query Request → API Router → RAGService → R2R Service
                                      ↓
                                Document Processing
                                      ↓
                               Vector Search (Qdrant)
                                      ↓
                               Context Retrieval
                                      ↓
                               LLM Augmentation
                                      ↓
                               Response Generation
```

## Observability

### Monitoring Components

#### 1. Health Checks
- **Service Level**: Individual container health endpoints
- **Dependency Level**: External service connectivity checks
- **Application Level**: Business logic health validation

```python
# Health check response format
{
    "status": "healthy",
    "timestamp": "2024-01-01T00:00:00Z",
    "services": {
        "database": "healthy",
        "redis": "healthy",
        "qdrant": "healthy"
    }
}
```

#### 2. Metrics Collection
- **Performance Metrics**: Response times, throughput, error rates
- **Resource Metrics**: CPU, memory, disk usage
- **Business Metrics**: Agent executions, memory operations, user activity

#### 3. Distributed Tracing
- **OpenTelemetry Integration**: End-to-end request tracing
- **Correlation IDs**: Request tracking across services
- **Span Context**: Detailed operation timing and dependencies

### Logging Strategy

#### Log Levels and Structure
```json
{
    "timestamp": "2024-01-01T00:00:00Z",
    "level": "INFO",
    "service": "api",
    "correlation_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "user123",
    "operation": "agent_execution",
    "duration_ms": 1500,
    "message": "Agent execution completed successfully"
}
```

#### Audit Logging
- **Security Events**: Authentication, authorization, access patterns
- **Data Operations**: Create, read, update, delete operations
- **System Events**: Configuration changes, deployments, failures

### Alerting and Monitoring

#### Alert Categories
- **Availability**: Service downtime, high error rates
- **Performance**: Slow response times, resource exhaustion
- **Security**: Failed authentication, suspicious activity
- **Business**: Low agent utilization, memory usage patterns

#### Dashboard Views
- **Operational Dashboard**: Real-time service health and performance
- **Security Dashboard**: Authentication events and security metrics
- **Business Dashboard**: Usage patterns and system utilization

## Security Architecture

### Authentication & Authorization
- **JWT Tokens**: 5-minute access tokens with refresh tokens
- **Multi-Factor Authentication**: TOTP 2FA support
- **Role-Based Access Control**: Permission-based authorization
- **Session Management**: Redis-backed session storage

### Data Protection
- **Encryption**: AES-256 for data at rest, TLS for data in transit
- **Secrets Management**: Docker secrets for sensitive configuration
- **Input Validation**: Pydantic models with strict validation
- **Output Sanitization**: Response filtering and encoding

### Resilience Patterns
- **Circuit Breakers**: Automatic failure detection and recovery
- **Rate Limiting**: Redis-backed request throttling (100 req/min)
- **Retry Logic**: Exponential backoff with configurable limits
- **Timeout Handling**: Service-level timeout configuration

## Deployment Architecture

### Container Orchestration
```yaml
# Docker Compose service definitions
- api: FastAPI application container
- postgres: Primary database
- redis: Caching and session storage
- qdrant: Vector database
- neo4j: Graph database
- r2r: Document processing service
```

### Networking
- **Internal Network**: Secure communication between services
- **External Access**: Load balancer routing to API service
- **Service Discovery**: Docker Compose service naming
- **Health Checks**: Automated service health monitoring

### Configuration Management
- **Environment Variables**: Service-specific configuration
- **Secret Files**: Sensitive data through Docker secrets
- **Configuration Validation**: Startup-time config verification
- **Dynamic Reconfiguration**: Runtime configuration updates

## Scalability Considerations

### Horizontal Scaling
- **Stateless Services**: API services can be scaled horizontally
- **Shared Storage**: Database and object storage for state persistence
- **Load Balancing**: Request distribution across service instances

### Performance Optimization
- **Caching Strategy**: Redis for frequently accessed data
- **Connection Pooling**: Database connection optimization
- **Async Processing**: Non-blocking I/O operations
- **Resource Limits**: Container resource constraints

### Future Extensibility
- **Plugin Architecture**: MCP tools for additional capabilities
- **Service Mesh**: Advanced traffic management and observability
- **Event-Driven Processing**: Message queues for background tasks

## Development and Testing

### Development Environment
- **Hot Reload**: Code changes trigger automatic restarts
- **Debugging Support**: VSCode debugging configuration
- **Local Services**: Docker Compose for local development

### Testing Strategy
- **Unit Tests**: Service and component testing
- **Integration Tests**: API endpoint testing
- **E2E Tests**: Full user journey testing
- **Security Tests**: Authentication and authorization testing

---

This architecture document provides a comprehensive view of the AgentFlow system, designed for reliability, security, and scalability while maintaining developer productivity and operational excellence.