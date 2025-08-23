# AGENTS.md: Business Logic Layer Guidelines

This document provides specific guidance for AI models working with service layer classes in `/apps/api/app/services/`. These guidelines are derived from the FastAPI development ruleset and async programming patterns.

## 1. Project Scope & Architecture
*   **Primary Purpose:** Business logic layer implementing core domain operations and external service integration
*   **Core Technologies:** AsyncIO patterns, dependency injection, external API integration (Mem0, R2R, MCP)
*   **Architecture Pattern:** Service layer pattern with clear separation between routers and data access

## 2. Service Organization Standards

### File Structure Requirements
*   **MANDATORY:** Organize services by business domain matching router structure:
    ```
    app/services/
    ├── __init__.py
    ├── auth_service.py      # Authentication and user management
    ├── agent_service.py     # Agent lifecycle operations
    ├── memory_service.py    # Mem0 integration and memory management
    ├── rag_service.py       # R2R knowledge and retrieval
    ├── workflow_service.py  # LangGraph workflow orchestration
    ├── tool_service.py      # MCP tool integration
    └── base_service.py      # Base service class with common patterns
    ```

### Service Class Structure
*   **REQUIRED:** Use consistent service class patterns with dependency injection
*   **MANDATORY:** Implement proper async patterns for all I/O operations
*   **CRITICAL:** Include comprehensive error handling and logging
*   **REQUIRED:** Use type hints for all method parameters and return values

```python
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.agents import AgentCreate, AgentUpdate, AgentResponse
from ..core.logging import get_logger

logger = get_logger(__name__)

class BaseService(ABC):
    """Base service class with common patterns."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def _handle_service_error(self, operation: str, error: Exception) -> None:
        """Standard error handling for service operations."""
        logger.error(f"Service error in {operation}: {str(error)}", exc_info=True)
        # Additional error handling logic

class AgentService(BaseService):
    """Service for agent-related business operations."""
    
    def __init__(self, db_session: AsyncSession, memory_service: 'MemoryService'):
        super().__init__(db_session)
        self.memory_service = memory_service
```

## 3. Async Programming Standards

### AsyncIO Requirements [Hard Constraint]
*   **MANDATORY:** Use async/await for ALL I/O operations
*   **REQUIRED:** Implement proper async context management
*   **CRITICAL:** Use async database sessions and HTTP clients with proper timeouts
*   **REQUIRED:** Handle async exceptions properly with try/except blocks

```python
import asyncio
import httpx
from contextlib import asynccontextmanager
from typing import AsyncGenerator

class ExternalAPIService(BaseService):
    """Service for external API integrations."""
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        self.client_timeout = httpx.Timeout(30.0, connect=5.0)
    
    @asynccontextmanager
    async def _get_http_client(self) -> AsyncGenerator[httpx.AsyncClient, None]:
        """Get async HTTP client with proper configuration."""
        async with httpx.AsyncClient(timeout=self.client_timeout) as client:
            yield client
    
    async def call_external_api(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Call external API with proper error handling."""
        try:
            async with self._get_http_client() as client:
                response = await client.post(endpoint, json=data)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            await self._handle_service_error("external_api_call", e)
            raise ExternalServiceError(f"API call failed: {str(e)}")
        except Exception as e:
            await self._handle_service_error("external_api_call", e)
            raise
```

### Connection Pooling and Resource Management
*   **REQUIRED:** Use connection pooling for database and HTTP connections
*   **MANDATORY:** Implement proper resource cleanup with context managers
*   **CRITICAL:** Configure appropriate timeouts and retry logic
*   **REQUIRED:** Monitor connection pool health and performance

## 4. Memory Service Integration [Mem0 Ruleset]

### Mem0 Configuration Standards
*   **CRITICAL:** Support both hosted (Platform) and OSS modes mutually exclusively
*   **MANDATORY:** Use environment variables for all configuration
*   **REQUIRED:** Implement proper scoping (user/session/agent) for memory operations
*   **CRITICAL:** Handle empty results and missing records gracefully

```python
import os
from typing import Union, List, Optional
from mem0 import MemoryClient, Memory

class MemoryService(BaseService):
    """Service for Mem0 memory management integration."""
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        self.client = self._initialize_mem0_client()
    
    def _initialize_mem0_client(self) -> Union[MemoryClient, Memory]:
        """Initialize Mem0 client based on configuration mode."""
        api_key = os.getenv("MEM0_API_KEY")
        
        if api_key:
            # Platform mode
            logger.info("Initializing Mem0 Platform client")
            return MemoryClient(api_key=api_key)
        else:
            # OSS mode - requires additional configuration
            config = {
                "vector_store": {
                    "provider": "qdrant",
                    "config": {
                        "host": os.getenv("QDRANT_HOST", "localhost"),
                        "port": int(os.getenv("QDRANT_PORT", "6333")),
                    }
                },
                "embedding": {
                    "provider": "openai",
                    "config": {
                        "model": "text-embedding-3-small",
                        "embedding_dims": 1536
                    }
                }
            }
            logger.info("Initializing Mem0 OSS client")
            return Memory.from_config(config)
    
    async def add_memory(
        self, 
        text: str, 
        user_id: str, 
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add memory with proper scoping."""
        try:
            memory_data = {
                "text": text,
                "user_id": user_id,
                "metadata": metadata or {}
            }
            
            if agent_id:
                memory_data["agent_id"] = agent_id
            if session_id:
                memory_data["session_id"] = session_id
            
            result = await self.client.add(**memory_data)
            logger.info(f"Memory added successfully", user_id=user_id, agent_id=agent_id)
            return result
            
        except Exception as e:
            await self._handle_service_error("add_memory", e)
            raise MemoryServiceError(f"Failed to add memory: {str(e)}")
    
    async def search_memories(
        self, 
        query: str, 
        user_id: str, 
        agent_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search memories with scoping."""
        try:
            search_params = {
                "query": query,
                "user_id": user_id,
                "limit": limit
            }
            
            if agent_id:
                search_params["agent_id"] = agent_id
            
            results = await self.client.search(**search_params)
            return results if results else []
            
        except Exception as e:
            await self._handle_service_error("search_memories", e)
            raise MemoryServiceError(f"Memory search failed: {str(e)}")
```

## 5. Database Transaction Management

### Transaction Patterns
*   **REQUIRED:** Use database transactions for multi-step operations
*   **MANDATORY:** Implement proper rollback on errors
*   **CRITICAL:** Use async context managers for transaction management
*   **REQUIRED:** Handle connection errors and retries appropriately

```python
from sqlalchemy.exc import SQLAlchemyError
from ..models.database import Agent, User

class AgentService(BaseService):
    """Service for agent lifecycle management."""
    
    async def create_agent(
        self, 
        agent_data: AgentCreate, 
        owner_id: str
    ) -> AgentResponse:
        """Create new agent with transaction management."""
        try:
            async with self.db.begin():  # Transaction context
                # Create database entity
                db_agent = Agent(
                    name=agent_data.name,
                    description=agent_data.description,
                    model=agent_data.model,
                    temperature=agent_data.temperature,
                    owner_id=owner_id
                )
                
                self.db.add(db_agent)
                await self.db.flush()  # Get ID without committing
                
                # Initialize agent memory
                await self.memory_service.add_memory(
                    text=f"Agent {agent_data.name} created",
                    user_id=owner_id,
                    agent_id=db_agent.id,
                    metadata={"event": "agent_created"}
                )
                
                # Transaction commits automatically
                logger.info(f"Agent created successfully", agent_id=db_agent.id)
                return AgentResponse.from_orm(db_agent)
                
        except SQLAlchemyError as e:
            await self._handle_service_error("create_agent", e)
            raise DatabaseError(f"Database error creating agent: {str(e)}")
        except Exception as e:
            await self._handle_service_error("create_agent", e)
            raise AgentServiceError(f"Failed to create agent: {str(e)}")
```

## 6. Error Handling Standards

### Custom Exception Classes
*   **REQUIRED:** Define service-specific exception classes
*   **MANDATORY:** Include proper error messages and context
*   **CRITICAL:** Implement proper exception hierarchy
*   **REQUIRED:** Log errors with sufficient context for debugging

```python
from ..core.exceptions import AgentFlowError

class ServiceError(AgentFlowError):
    """Base service error."""
    pass

class AgentServiceError(ServiceError):
    """Agent service specific errors."""
    pass

class MemoryServiceError(ServiceError):
    """Memory service specific errors."""
    pass

class ExternalServiceError(ServiceError):
    """External service integration errors."""
    
    def __init__(self, service_name: str, message: str, status_code: Optional[int] = None):
        super().__init__(f"{service_name}: {message}")
        self.service_name = service_name
        self.status_code = status_code

class DatabaseError(ServiceError):
    """Database operation errors."""
    pass
```

## 7. External Service Integration

### HTTP Client Configuration
*   **REQUIRED:** Use httpx.AsyncClient with proper timeout configuration
*   **MANDATORY:** Implement retry logic for transient failures
*   **CRITICAL:** Handle different error scenarios appropriately
*   **REQUIRED:** Log all external service calls and responses

```python
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

class RAGService(BaseService):
    """Service for R2R knowledge integration."""
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        self.r2r_base_url = os.getenv("R2R_BASE_URL", "http://localhost:7272")
        self.r2r_api_key = os.getenv("R2R_API_KEY")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def search_knowledge(
        self, 
        query: str, 
        limit: int = 10,
        use_hybrid: bool = True
    ) -> Dict[str, Any]:
        """Search R2R knowledge base with retry logic."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {}
                if self.r2r_api_key:
                    headers["Authorization"] = f"Bearer {self.r2r_api_key}"
                
                response = await client.post(
                    f"{self.r2r_base_url}/retrieval/search",
                    json={
                        "query": query,
                        "limit": limit,
                        "hybrid_search": use_hybrid
                    },
                    headers=headers
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"R2R search completed", query_length=len(query), results_count=len(result.get("results", [])))
                return result
                
        except httpx.HTTPError as e:
            logger.warning(f"R2R search failed: {str(e)}")
            raise ExternalServiceError("R2R", f"Search failed: {str(e)}", getattr(e.response, 'status_code', None))
```

## 8. Caching and Performance

### Caching Strategies
*   **REQUIRED:** Implement appropriate caching for expensive operations
*   **MANDATORY:** Use Redis for shared cache when available
*   **CRITICAL:** Implement cache invalidation strategies
*   **REQUIRED:** Monitor cache hit rates and performance

```python
import json
from typing import Optional
import redis.asyncio as redis

class CachedService(BaseService):
    """Base service with caching capabilities."""
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        self.redis_client = self._get_redis_client()
        self.cache_ttl = 300  # 5 minutes default
    
    def _get_redis_client(self) -> Optional[redis.Redis]:
        """Get Redis client if available."""
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            return redis.from_url(redis_url)
        return None
    
    async def _get_cached(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache."""
        if not self.redis_client:
            return None
        
        try:
            cached_data = await self.redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        return None
    
    async def _set_cache(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Set data in cache."""
        if not self.redis_client:
            return
        
        try:
            await self.redis_client.setex(
                key,
                ttl or self.cache_ttl,
                json.dumps(data, default=str)
            )
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
```

## 9. Service Dependency Injection

### FastAPI Dependency Pattern
*   **REQUIRED:** Use FastAPI dependency injection for service instantiation
*   **MANDATORY:** Implement proper service lifecycle management
*   **CRITICAL:** Handle service dependencies and circular imports
*   **REQUIRED:** Use consistent dependency naming conventions

```python
# In dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .database import get_db
from .services.agent_service import AgentService
from .services.memory_service import MemoryService

async def get_memory_service(db: AsyncSession = Depends(get_db)) -> MemoryService:
    """Get memory service instance."""
    return MemoryService(db)

async def get_agent_service(
    db: AsyncSession = Depends(get_db),
    memory_service: MemoryService = Depends(get_memory_service)
) -> AgentService:
    """Get agent service instance."""
    return AgentService(db, memory_service)
```

## 10. Validation and Business Rules

### Business Logic Validation
*   **REQUIRED:** Implement business rule validation in service layer
*   **MANDATORY:** Use clear error messages for validation failures
*   **CRITICAL:** Validate data integrity across service boundaries
*   **REQUIRED:** Document business rules and constraints

```python
from ..core.exceptions import ValidationError

class AgentService(BaseService):
    """Agent service with business rule validation."""
    
    async def update_agent(
        self, 
        agent_id: str, 
        update_data: AgentUpdate, 
        user_id: str
    ) -> AgentResponse:
        """Update agent with business rule validation."""
        # Validate ownership
        agent = await self._get_agent_with_ownership_check(agent_id, user_id)
        
        # Business rule: Cannot change model if agent has active sessions
        if update_data.model and update_data.model != agent.model:
            active_sessions = await self._check_active_sessions(agent_id)
            if active_sessions > 0:
                raise ValidationError(
                    "Cannot change model while agent has active sessions"
                )
        
        # Apply updates
        try:
            for field, value in update_data.dict(exclude_unset=True).items():
                setattr(agent, field, value)
            
            await self.db.commit()
            await self.db.refresh(agent)
            
            return AgentResponse.from_orm(agent)
            
        except Exception as e:
            await self.db.rollback()
            raise AgentServiceError(f"Failed to update agent: {str(e)}")
```

## 11. Forbidden Patterns
*   **NEVER** perform database operations without proper transaction management
*   **NEVER** ignore errors from external service calls
*   **NEVER** hardcode configuration values in service classes
*   **NEVER** use synchronous I/O operations in async service methods
*   **NEVER** expose internal service implementation details to routers
*   **NEVER** skip validation of user permissions in service methods
*   **NEVER** log sensitive information (passwords, API keys, tokens)
*   **NEVER** use shared mutable state across service instances
