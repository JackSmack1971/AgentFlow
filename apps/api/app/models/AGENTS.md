# AGENTS.md: Pydantic Schema Guidelines

This document provides specific guidance for AI models working with Pydantic models in `/apps/api/app/models/`. These guidelines are derived from the FastAPI+Pydantic ruleset and data validation standards.

## 1. Project Scope & Architecture
*   **Primary Purpose:** Pydantic v2 schemas for API request/response validation and data contracts
*   **Core Technologies:** Pydantic v2, type annotations, runtime validation, serialization
*   **Architecture Pattern:** Schema-first API design with separate models for input and output

## 2. Model Organization Standards

### File Structure Requirements
*   **MANDATORY:** Organize models by domain matching router structure:
    ```
    app/models/
    ├── __init__.py          # Export all models
    ├── base.py              # Base model classes
    ├── auth.py              # Authentication models
    ├── agents.py            # Agent-related schemas
    ├── memory.py            # Memory management schemas
    ├── rag.py               # RAG and knowledge schemas
    ├── workflow.py          # Workflow orchestration schemas
    ├── tools.py             # Tool registry schemas
    └── common.py            # Shared utility models
    ```

### Model Naming Conventions [Hard Constraint]
*   **CRITICAL:** Use distinct models for input and output to prevent data leakage
*   **MANDATORY:** Follow consistent naming patterns:
    - `*Create` for creation requests
    - `*Update` for update requests  
    - `*Response` for API responses
    - `*Filter` for query filters
    - `*Config` for configuration models

## 3. Pydantic v2 Standards [Hard Constraint]

### Base Model Configuration
*   **CRITICAL:** Use `extra='forbid'` for ALL input models
*   **MANDATORY:** Enable `validate_assignment=True` for runtime validation
*   **REQUIRED:** Use `from_attributes=True` for ORM integration
*   **CRITICAL:** Never expose sensitive fields in response models

```python
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict, validator, root_validator
from enum import Enum

class BaseAgentFlowModel(BaseModel):
    """Base model with common configuration."""
    
    model_config = ConfigDict(
        extra='forbid',  # CRITICAL: Prevent additional fields
        validate_assignment=True,
        use_enum_values=True,
        populate_by_name=True
    )

class BaseCreateModel(BaseAgentFlowModel):
    """Base for all creation models."""
    
    model_config = ConfigDict(
        extra='forbid',  # CRITICAL: Strict input validation
    )

class BaseResponseModel(BaseAgentFlowModel):
    """Base for all response models."""
    
    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM integration
    )
```

### Field Validation Standards
*   **REQUIRED:** Use comprehensive Field validation with descriptions
*   **MANDATORY:** Set appropriate constraints (min/max length, value ranges)
*   **CRITICAL:** Include descriptive field documentation
*   **REQUIRED:** Use proper type annotations for all fields

```python
from pydantic import Field, EmailStr, SecretStr
from typing import Annotated

# String validation patterns
AgentName = Annotated[str, Field(min_length=1, max_length=100, description="Agent display name")]
AgentDescription = Annotated[Optional[str], Field(max_length=500, description="Agent description")]
UserEmail = Annotated[EmailStr, Field(description="User email address")]

# Numeric validation patterns
Temperature = Annotated[float, Field(ge=0.0, le=2.0, description="Model temperature")]
TokenLimit = Annotated[int, Field(ge=1, le=32000, description="Maximum tokens")]

class AgentCreate(BaseCreateModel):
    """Model for agent creation requests."""
    
    name: AgentName
    description: AgentDescription = None
    model: str = Field(..., description="AI model identifier", regex=r'^[a-zA-Z0-9-_]+$')
    temperature: Temperature = Field(default=0.7)
    max_tokens: TokenLimit = Field(default=1000)
    system_prompt: Optional[str] = Field(None, max_length=2000, description="System prompt")
    tools: List[str] = Field(default_factory=list, description="List of available tools")
    tags: List[str] = Field(default_factory=list, max_items=10, description="Agent tags")
    
    @validator('tags')
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate and normalize tags."""
        if len(v) > 10:
            raise ValueError('Maximum 10 tags allowed')
        return [tag.lower().strip() for tag in v if tag.strip()]
    
    @validator('tools')
    @classmethod
    def validate_tools(cls, v: List[str]) -> List[str]:
        """Validate tool identifiers."""
        if len(v) > 20:
            raise ValueError('Maximum 20 tools allowed')
        for tool in v:
            if not tool.strip():
                raise ValueError('Tool names cannot be empty')
        return v
```

### Enum Usage Standards
*   **REQUIRED:** Use string enums for status fields and categorization
*   **MANDATORY:** Provide clear enum values that are API-friendly
*   **CRITICAL:** Document enum choices with descriptions
*   **REQUIRED:** Use enum validation in Pydantic models

```python
from enum import Enum

class AgentStatus(str, Enum):
    """Agent operational status."""
    ACTIVE = "active"
    INACTIVE = "inactive" 
    TRAINING = "training"
    ERROR = "error"
    ARCHIVED = "archived"

class ModelProvider(str, Enum):
    """Supported AI model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"

class MemoryScope(str, Enum):
    """Memory access scope levels."""
    USER = "user"
    SESSION = "session" 
    AGENT = "agent"
    GLOBAL = "global"

# Usage in models
class AgentResponse(BaseResponseModel):
    """Complete agent information for API responses."""
    
    id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Agent display name")
    description: Optional[str] = Field(None, description="Agent description")
    status: AgentStatus = Field(..., description="Current agent status")
    model_provider: ModelProvider = Field(..., description="AI model provider")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    owner_id: str = Field(..., description="Owner user ID")
    run_count: int = Field(default=0, description="Total number of runs")
    
    # NEVER include sensitive fields like API keys or internal configs
```

## 4. Request/Response Model Separation [Hard Constraint]

### Input Model Standards
*   **CRITICAL:** Separate models for different operations (Create vs Update)
*   **MANDATORY:** Use `extra='forbid'` to prevent additional fields
*   **REQUIRED:** Validate all input thoroughly with custom validators
*   **CRITICAL:** Never include computed or system fields in input models

```python
class AgentUpdate(BaseCreateModel):
    """Model for agent update requests."""
    
    # All fields optional for partial updates
    name: Optional[AgentName] = None
    description: Optional[AgentDescription] = None
    temperature: Optional[Temperature] = None
    max_tokens: Optional[TokenLimit] = None
    system_prompt: Optional[str] = Field(None, max_length=2000)
    tools: Optional[List[str]] = None
    tags: Optional[List[str]] = Field(None, max_items=10)
    status: Optional[AgentStatus] = None
    
    @root_validator
    @classmethod
    def validate_at_least_one_field(cls, values):
        """Ensure at least one field is provided for update."""
        if not any(v is not None for v in values.values()):
            raise ValueError('At least one field must be provided for update')
        return values
    
    @validator('tools')
    @classmethod
    def validate_tools_update(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate tools for update operations."""
        if v is not None:
            if len(v) > 20:
                raise ValueError('Maximum 20 tools allowed')
            return [tool.strip() for tool in v if tool.strip()]
        return v
```

### Response Model Standards
*   **REQUIRED:** Include all relevant fields for client consumption
*   **MANDATORY:** Use computed fields for derived values
*   **CRITICAL:** Never expose sensitive internal data
*   **REQUIRED:** Include metadata fields (timestamps, counts, etc.)

```python
from pydantic import computed_field

class AgentResponse(BaseResponseModel):
    """Complete agent response model."""
    
    id: str
    name: str
    description: Optional[str]
    status: AgentStatus
    model_provider: ModelProvider
    temperature: float
    max_tokens: int
    system_prompt: Optional[str]
    tools: List[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    owner_id: str
    run_count: int
    last_run_at: Optional[datetime] = None
    
    @computed_field
    @property
    def is_active(self) -> bool:
        """Computed field indicating if agent is active."""
        return self.status == AgentStatus.ACTIVE
    
    @computed_field
    @property
    def age_days(self) -> int:
        """Computed field for agent age in days."""
        return (datetime.utcnow() - self.created_at).days
    
    # NEVER include: internal_config, api_keys, secrets, database_id
```

## 5. Nested Model Patterns

### Complex Object Modeling
*   **REQUIRED:** Use nested models for complex data structures
*   **MANDATORY:** Maintain proper validation hierarchy
*   **CRITICAL:** Ensure nested models follow same standards
*   **REQUIRED:** Use forward references for circular dependencies

```python
class MemoryEntry(BaseResponseModel):
    """Individual memory entry model."""
    
    id: str = Field(..., description="Memory entry ID")
    text: str = Field(..., description="Memory content")
    scope: MemoryScope = Field(..., description="Memory access scope")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Memory confidence score")
    created_at: datetime = Field(..., description="Memory creation time")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class MemorySearchResponse(BaseResponseModel):
    """Response model for memory search operations."""
    
    query: str = Field(..., description="Original search query")
    memories: List[MemoryEntry] = Field(..., description="Found memory entries")
    total_count: int = Field(..., description="Total number of matching memories")
    search_time_ms: float = Field(..., description="Search execution time")
    
    @validator('memories')
    @classmethod
    def validate_memories_limit(cls, v: List[MemoryEntry]) -> List[MemoryEntry]:
        """Validate memory result limits."""
        if len(v) > 100:
            raise ValueError('Memory results exceed maximum limit of 100')
        return v

class AgentWithMemories(AgentResponse):
    """Agent response including memory information."""
    
    recent_memories: List[MemoryEntry] = Field(default_factory=list, max_items=10)
    memory_count: int = Field(default=0, description="Total memory count")
```

## 6. Filter and Query Models

### Search and Filter Patterns
*   **REQUIRED:** Create specific models for query parameters
*   **MANDATORY:** Use appropriate validation for filter values
*   **CRITICAL:** Implement pagination and sorting parameters
*   **REQUIRED:** Provide sensible defaults for optional parameters

```python
from typing import Literal

SortOrder = Literal['asc', 'desc']
AgentSortField = Literal['name', 'created_at', 'updated_at', 'run_count']

class AgentFilter(BaseAgentFlowModel):
    """Filter model for agent queries."""
    
    # Pagination
    skip: int = Field(default=0, ge=0, description="Number of items to skip")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum items to return")
    
    # Sorting
    sort_by: AgentSortField = Field(default='created_at', description="Field to sort by")
    sort_order: SortOrder = Field(default='desc', description="Sort order")
    
    # Filtering
    status: Optional[AgentStatus] = Field(None, description="Filter by agent status")
    model_provider: Optional[ModelProvider] = Field(None, description="Filter by model provider")
    search: Optional[str] = Field(None, max_length=100, description="Search in name/description")
    tags: Optional[List[str]] = Field(None, max_items=10, description="Filter by tags (OR logic)")
    owner_id: Optional[str] = Field(None, description="Filter by owner")
    
    # Date filtering
    created_after: Optional[datetime] = Field(None, description="Created after timestamp")
    created_before: Optional[datetime] = Field(None, description="Created before timestamp")
    
    @validator('tags')
    @classmethod
    def normalize_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Normalize tag filters."""
        if v:
            return [tag.lower().strip() for tag in v if tag.strip()]
        return v
```

## 7. Configuration Models

### Settings and Config Patterns
*   **REQUIRED:** Use Pydantic for all configuration models
*   **MANDATORY:** Include validation for configuration values
*   **CRITICAL:** Use environment variable integration
*   **REQUIRED:** Provide clear documentation for config options

```python
from pydantic_settings import BaseSettings

class Mem0Config(BaseSettings):
    """Configuration for Mem0 integration."""
    
    # Platform mode settings
    api_key: Optional[str] = Field(None, description="Mem0 Platform API key")
    
    # OSS mode settings  
    qdrant_host: str = Field(default="localhost", description="Qdrant host")
    qdrant_port: int = Field(default=6333, ge=1, le=65535, description="Qdrant port")
    postgres_url: Optional[str] = Field(None, description="PostgreSQL connection URL")
    neo4j_url: Optional[str] = Field(None, description="Neo4j connection URL")
    
    # Embedding settings
    embedding_model: str = Field(default="text-embedding-3-small", description="Embedding model")
    embedding_dims: int = Field(default=1536, description="Embedding dimensions")
    
    class Config:
        env_prefix = "MEM0_"
        env_file = ".env"
    
    @root_validator
    @classmethod
    def validate_mode_exclusivity(cls, values):
        """Ensure exactly one mode (Platform OR OSS) is configured."""
        has_api_key = bool(values.get('api_key'))
        has_oss_config = bool(values.get('postgres_url')) or bool(values.get('qdrant_host') != 'localhost')
        
        if has_api_key and has_oss_config:
            raise ValueError('Cannot use both Platform API key and OSS configuration')
        if not has_api_key and not has_oss_config:
            raise ValueError('Must provide either Platform API key or OSS configuration')
        
        return values

class AgentConfig(BaseAgentFlowModel):
    """Runtime configuration for agent execution."""
    
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=1, le=32000)
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    memory_enabled: bool = Field(default=True)
    tools_enabled: bool = Field(default=True)
    streaming: bool = Field(default=False)
    
    # Advanced settings
    retry_attempts: int = Field(default=3, ge=0, le=10)
    context_window: int = Field(default=4000, ge=100, le=32000)
    
    @validator('context_window')
    @classmethod
    def validate_context_window(cls, v: int, values: Dict[str, Any]) -> int:
        """Ensure context window is larger than max tokens."""
        max_tokens = values.get('max_tokens', 1000)
        if v <= max_tokens:
            raise ValueError('Context window must be larger than max_tokens')
        return v
```

## 8. Error Response Models

### Standardized Error Schemas
*   **REQUIRED:** Define consistent error response formats
*   **MANDATORY:** Include proper error codes and messages
*   **CRITICAL:** Provide helpful error details without exposing internals
*   **REQUIRED:** Support different error severity levels

```python
class ValidationErrorDetail(BaseModel):
    """Individual validation error details."""
    
    field: str = Field(..., description="Field name that failed validation")
    message: str = Field(..., description="Validation error message")
    invalid_value: Any = Field(..., description="The invalid value provided")

class ErrorResponse(BaseModel):
    """Standard error response format."""
    
    error: str = Field(..., description="Error category")
    message: str = Field(..., description="Human-readable error message")
    code: str = Field(..., description="Error code for programmatic handling")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error context")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None, description="Request correlation ID")

class ValidationErrorResponse(ErrorResponse):
    """Validation-specific error response."""
    
    error: str = Field(default="validation_error")
    validation_errors: List[ValidationErrorDetail] = Field(..., description="Detailed validation failures")
```

## 9. API Contract Testing

### Schema Validation Testing
*   **REQUIRED:** Test all model validation rules
*   **MANDATORY:** Verify input/output model separation
*   **CRITICAL:** Test edge cases and boundary conditions
*   **REQUIRED:** Validate serialization/deserialization

```python
# Example test patterns (for reference, not in models)
"""
def test_agent_create_validation():
    # Test valid data
    valid_data = {
        "name": "Test Agent",
        "model": "gpt-4",
        "temperature": 0.7
    }
    agent = AgentCreate(**valid_data)
    assert agent.name == "Test Agent"
    
    # Test invalid data
    with pytest.raises(ValidationError):
        AgentCreate(name="", model="gpt-4")  # Empty name
    
    with pytest.raises(ValidationError):
        AgentCreate(name="Test", model="gpt-4", temperature=3.0)  # Invalid temperature
"""
```

## 10. Forbidden Patterns
*   **NEVER** use mutable default arguments (use `default_factory`)
*   **NEVER** expose internal database IDs or sensitive fields in response models
*   **NEVER** skip input validation with `extra='allow'` on input models
*   **NEVER** use the same model for both input and output operations
*   **NEVER** hardcode enum values without proper validation
*   **NEVER** ignore field validation errors or bypass Pydantic validation
*   **NEVER** use `Any` type without proper validation constraints
*   **NEVER** create circular imports between model modules
