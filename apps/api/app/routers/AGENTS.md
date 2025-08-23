# AGENTS.md: Router Implementation Guidelines

This document provides specific guidance for AI models working with FastAPI routers in `/apps/api/app/routers/`. These guidelines are derived from the FastAPI development ruleset and API design standards.

## 1. Project Scope & Architecture
*   **Primary Purpose:** RESTful API endpoints organized by domain (auth, memory, rag, agents, health)
*   **Core Technologies:** FastAPI 0.115.12+, Pydantic v2, async/await patterns, dependency injection
*   **Architecture Pattern:** Domain-based router organization with clear separation of concerns

## 2. Router Organization Standards

### File Structure Requirements
*   **MANDATORY:** Organize routers by business domain:
    ```
    app/routers/
    ├── __init__.py
    ├── auth.py          # Authentication endpoints
    ├── agents.py        # Agent CRUD operations
    ├── memory.py        # Memory management endpoints
    ├── rag.py           # RAG and knowledge endpoints
    ├── health.py        # Health and monitoring endpoints
    ├── workflow.py      # Workflow orchestration
    └── tools.py         # Tool registry and management
    ```

### Router Declaration Standards
*   **REQUIRED:** Use consistent router instantiation with proper tags and prefixes
*   **MANDATORY:** Include comprehensive descriptions for OpenAPI documentation
*   **CRITICAL:** Implement proper dependency injection for shared services

```python
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from ..dependencies import get_current_user, get_db
from ..models.agents import AgentCreate, AgentResponse, AgentUpdate
from ..services.agent_service import AgentService

router = APIRouter(
    prefix="/agents",
    tags=["agents"],
    responses={
        404: {"description": "Agent not found"},
        401: {"description": "Authentication required"}
    }
)
```

## 3. Endpoint Design Standards [FastAPI Ruleset]

### HTTP Method Patterns
*   **REQUIRED:** Follow RESTful conventions for HTTP methods:
    - `GET` for retrieving data (collection and individual resources)
    - `POST` for creating new resources
    - `PUT` for full resource updates
    - `PATCH` for partial resource updates
    - `DELETE` for resource removal

### Path Parameter Standards
*   **MANDATORY:** Use descriptive path parameters with proper type annotations
*   **REQUIRED:** Implement proper validation for path parameters
*   **CRITICAL:** Use UUID format for resource identifiers where applicable

```python
@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str = Path(..., description="Unique agent identifier", regex=r"^[a-zA-Z0-9-_]+$"),
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
):
    """Retrieve a specific agent by ID."""
    agent = await agent_service.get_agent(agent_id, user_id=current_user.id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found"
        )
    return agent
```

## 4. Request/Response Model Standards

### Pydantic Model Requirements [Hard Constraint]
*   **CRITICAL:** Use separate Pydantic models for requests (`*Create`, `*Update`) and responses (`*Response`)
*   **MANDATORY:** Implement `extra='forbid'` for all input models to prevent data leakage
*   **REQUIRED:** Use proper type annotations and validation rules
*   **CRITICAL:** Never expose internal fields in response models

```python
# Request Models
class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Agent name")
    description: Optional[str] = Field(None, max_length=500, description="Agent description")
    model: str = Field(..., description="AI model to use")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Model temperature")
    
    class Config:
        extra = "forbid"

class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    
    class Config:
        extra = "forbid"

# Response Models
class AgentResponse(BaseModel):
    id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Agent name")
    description: Optional[str] = Field(None, description="Agent description")
    model: str = Field(..., description="AI model being used")
    temperature: float = Field(..., description="Model temperature")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    owner_id: str = Field(..., description="Owner user ID")
    
    class Config:
        from_attributes = True
```

## 5. HTTP Status Code Standards

### Status Code Requirements
*   **REQUIRED:** Use appropriate HTTP status codes consistently:
    - `200 OK` for successful GET requests
    - `201 Created` for successful POST requests
    - `204 No Content` for successful DELETE requests
    - `400 Bad Request` for validation errors
    - `401 Unauthorized` for authentication failures
    - `403 Forbidden` for authorization failures
    - `404 Not Found` for missing resources
    - `422 Unprocessable Entity` for Pydantic validation errors
    - `500 Internal Server Error` for unexpected server errors

### Error Response Standards
*   **MANDATORY:** Use custom HTTPException classes with consistent error formats
*   **REQUIRED:** Include detailed error messages and error codes
*   **CRITICAL:** Never expose internal system details in error responses

```python
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=AgentResponse)
async def create_agent(
    agent_data: AgentCreate,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
):
    """Create a new agent."""
    try:
        agent = await agent_service.create_agent(
            agent_data=agent_data,
            owner_id=current_user.id
        )
        return agent
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create agent"
        )
```

## 6. Authentication and Authorization

### Dependency Injection Patterns
*   **REQUIRED:** Use FastAPI dependency injection for authentication
*   **MANDATORY:** Implement proper user context propagation
*   **CRITICAL:** Validate user permissions for resource access
*   **REQUIRED:** Use consistent authentication patterns across all protected endpoints

```python
from ..dependencies import get_current_user, require_permission

@router.get("/", response_model=List[AgentResponse])
async def list_agents(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
):
    """List all agents accessible to the current user."""
    agents = await agent_service.list_agents(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return agents
```

## 7. Query Parameter Standards

### Pagination Requirements
*   **REQUIRED:** Implement consistent pagination patterns for list endpoints
*   **MANDATORY:** Use `skip` and `limit` parameters with proper validation
*   **CRITICAL:** Set reasonable default and maximum limits
*   **REQUIRED:** Include total count information where applicable

### Filtering and Sorting
*   **REQUIRED:** Implement optional filtering parameters with proper validation
*   **MANDATORY:** Use consistent naming conventions for filter parameters
*   **CRITICAL:** Sanitize and validate all filter inputs
*   **REQUIRED:** Support sorting with explicit sort parameter validation

```python
@router.get("/", response_model=List[AgentResponse])
async def list_agents(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum items to return"),
    search: Optional[str] = Query(None, max_length=100, description="Search term"),
    status: Optional[str] = Query(None, regex="^(active|inactive)$", description="Filter by status"),
    sort_by: Optional[str] = Query("created_at", regex="^(name|created_at|updated_at)$"),
    sort_order: Optional[str] = Query("desc", regex="^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
):
    """List agents with filtering and pagination."""
    # Implementation with proper parameter handling
```

## 8. Async Programming Requirements

### Async/Await Standards
*   **MANDATORY:** Use async/await for all I/O operations
*   **REQUIRED:** Properly handle async database sessions and HTTP clients
*   **CRITICAL:** Implement proper error handling for async operations
*   **REQUIRED:** Use async context managers for resource management

```python
@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent_update: AgentUpdate,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
):
    """Update an existing agent."""
    try:
        # Verify ownership
        existing_agent = await agent_service.get_agent(agent_id, user_id=current_user.id)
        if not existing_agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        # Perform update
        updated_agent = await agent_service.update_agent(
            agent_id=agent_id,
            update_data=agent_update,
            user_id=current_user.id
        )
        return updated_agent
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update agent"
        )
```

## 9. OpenAPI Documentation Standards

### Endpoint Documentation
*   **MANDATORY:** Include comprehensive docstrings for all endpoints
*   **REQUIRED:** Provide examples for request and response bodies
*   **CRITICAL:** Document all possible error responses
*   **REQUIRED:** Include parameter descriptions and constraints

```python
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=AgentResponse)
async def create_agent(
    agent_data: AgentCreate,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
):
    """
    Create a new agent.
    
    Creates a new AI agent with the specified configuration.
    The agent will be associated with the authenticated user.
    
    - **name**: Agent display name (required, 1-100 characters)
    - **description**: Optional description (max 500 characters)
    - **model**: AI model identifier (required)
    - **temperature**: Model temperature (0.0-2.0, default 0.7)
    
    Returns the created agent with system-generated fields like ID and timestamps.
    """
    # Implementation here
```

## 10. CORS Configuration

### CORS Requirements
*   **CRITICAL:** Implement proper CORS configuration with explicit origins
*   **MANDATORY:** Never use wildcard CORS origins in production
*   **REQUIRED:** Configure appropriate CORS methods and headers
*   **CRITICAL:** Include proper preflight request handling

## 11. Rate Limiting Integration

### SlowAPI Middleware Integration
*   **REQUIRED:** Apply appropriate rate limits to API endpoints
*   **MANDATORY:** Use different limits for authenticated vs anonymous users
*   **CRITICAL:** Implement proper rate limit error responses
*   **REQUIRED:** Configure rate limiting per endpoint sensitivity

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

# Apply rate limiting to sensitive endpoints
@router.post("/", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")  # Apply rate limit
async def create_agent(
    request: Request,  # Required for rate limiting
    agent_data: AgentCreate,
    current_user: User = Depends(get_current_user)
):
    """Create agent with rate limiting."""
    # Implementation
```

## 12. Logging and Monitoring

### Structured Logging
*   **REQUIRED:** Log all endpoint access and errors with structured format
*   **MANDATORY:** Include request IDs and user context in logs
*   **CRITICAL:** Never log sensitive information (passwords, tokens)
*   **REQUIRED:** Use appropriate log levels (INFO, WARNING, ERROR)

```python
import structlog

logger = structlog.get_logger(__name__)

@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service)
):
    """Delete an agent."""
    logger.info(
        "Agent deletion requested",
        agent_id=agent_id,
        user_id=current_user.id
    )
    
    try:
        await agent_service.delete_agent(agent_id, user_id=current_user.id)
        logger.info("Agent deleted successfully", agent_id=agent_id)
    except Exception as e:
        logger.error(
            "Agent deletion failed",
            agent_id=agent_id,
            error=str(e)
        )
        raise
```

## 13. Forbidden Patterns
*   **NEVER** expose internal database models directly as API responses
*   **NEVER** skip input validation on any endpoint
*   **NEVER** hardcode configuration values in router code
*   **NEVER** use synchronous I/O operations in async endpoints
*   **NEVER** ignore error handling in endpoint implementations
*   **NEVER** expose sensitive system information in error responses
*   **NEVER** use wildcard CORS origins in production
*   **NEVER** skip authentication/authorization for protected endpoints
