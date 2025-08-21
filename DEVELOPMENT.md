# DEVELOPMENT.md

## AgentFlow Development Guide

### Quick Start

```bash
# 1. Clone and setup
git clone <repository>
cd agentflow
./scripts/setup.sh

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Start development
./scripts/dev.sh
uvicorn apps.api.app.main:app --reload
python apps/mcp/server.py
```

### Development Workflow

#### Daily Development
1. **Start services**: `./scripts/dev.sh`
2. **Run tests**: `./scripts/test.sh`
3. **Format code**: `./scripts/format.sh`
4. **Debug issues**: `./scripts/debug.sh`

#### Creating New Features

1. **Create feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Add new router** (example):
   ```python
   # apps/api/app/routers/new_feature.py
   from fastapi import APIRouter, Depends
   from ..dependencies import get_current_user
   from ..models.schemas import NewFeatureSchema
   
   router = APIRouter()
   
   @router.post("/", summary="Create new feature")
   async def create_feature(
       data: NewFeatureSchema, 
       user = Depends(get_current_user)
   ):
       # Implementation
       pass
   ```

3. **Add to main app**:
   ```python
   # apps/api/app/main.py
   from .routers import new_feature
   
   app.include_router(
       new_feature.router, 
       prefix="/new-feature", 
       tags=["new-feature"]
   )
   ```

4. **Write tests**:
   ```python
   # tests/test_new_feature.py
   import pytest
   from fastapi.testclient import TestClient
   
   def test_create_feature(client: TestClient):
       response = client.post("/new-feature/", json={
           "field": "value"
       })
       assert response.status_code == 201
   ```

#### AI Framework Integration

##### Adding LangGraph Workflows
```python
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.postgres import PostgresSaver

def create_agent_workflow():
    builder = StateGraph(MessagesState)
    
    # Add nodes
    builder.add_node("process", process_node)
    builder.add_node("respond", respond_node)
    
    # Add edges
    builder.add_edge(START, "process")
    builder.add_edge("process", "respond")
    builder.add_edge("respond", END)
    
    # Compile with persistence
    checkpointer = PostgresSaver.from_conn_string(DATABASE_URL)
    graph = builder.compile(checkpointer=checkpointer)
    
    return graph
```

##### Adding Mem0 Memory Operations
```python
from mem0 import Memory

async def add_memory_with_scoping(
    text: str,
    user_id: str,
    agent_id: str = None,
    run_id: str = None
):
    result = await memory.add(
        text=text,
        user_id=user_id,
        agent_id=agent_id,
        run_id=run_id,
        metadata={"source": "conversation"}
    )
    return result
```

##### Adding R2R Knowledge Integration
```python
async def add_documents_to_knowledge_base(documents: list[str]):
    client = make_r2r_client()
    
    for doc in documents:
        result = await client.ingest_documents([doc])
        
    return {"processed": len(documents)}
```

#### Database Migrations

```python
# Always use dependency injection for database access
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Use in routes
@router.get("/")
async def get_items(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item))
    return result.scalars().all()
```

### Testing Strategy

#### Unit Tests
- Test each service method independently
- Mock external AI services and databases
- Focus on business logic validation

#### Integration Tests
- Test API endpoints end-to-end
- Use test database for data operations
- Validate AI framework integrations

#### Performance Tests
- Test response times under load
- Validate memory operation performance
- Monitor resource usage

### Debugging

#### Common Issues

1. **AI Service Timeouts**:
   ```python
   # Configure longer timeouts for AI operations
   async with httpx.AsyncClient(timeout=60) as client:
       response = await client.post(url, json=data)
   ```

2. **Memory System Errors**:
   ```python
   # Always handle memory operation failures
   try:
       result = await memory.add(text, user_id=user_id)
   except Exception as e:
       logger.error(f"Memory operation failed: {e}")
       # Implement fallback behavior
   ```

3. **Database Connection Issues**:
   ```bash
   # Check database connectivity
   ./scripts/debug.sh
   # Restart services if needed
   docker-compose restart postgres
   ```

#### Performance Optimization

1. **Database Queries**:
   - Use async operations throughout
   - Implement proper connection pooling
   - Monitor query performance

2. **AI Operations**:
   - Cache frequent AI service calls
   - Implement request batching
   - Monitor API rate limits

3. **Memory Operations**:
   - Optimize vector search queries
   - Implement memory pruning
   - Monitor memory usage patterns

### Code Quality

#### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.0.0
    hooks:
      - id: black
  
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.0
    hooks:
      - id: mypy
```

#### Code Review Checklist
- [ ] All tests pass
- [ ] Code formatted with Black
- [ ] Type hints included
- [ ] Error handling implemented
- [ ] Documentation updated
- [ ] Performance considered
- [ ] Security reviewed

---

# TROUBLESHOOTING.md

## AgentFlow Troubleshooting Guide

### Common Issues and Solutions

#### Environment Setup Issues

**Issue**: `uv` command not found
```bash
# Solution: Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

**Issue**: Docker services won't start
```bash
# Solution: Check Docker daemon and ports
docker --version
docker-compose ps
netstat -tulpn | grep :5432  # Check if ports are in use
```

**Issue**: Environment variables not loading
```bash
# Solution: Verify .env file exists and format
ls -la .env
cat .env | grep -v "^#" | grep "="
```

#### AI Service Integration Issues

**Issue**: OpenAI API key errors
```bash
# Check API key format and permissions
echo $OPENAI_API_KEY | wc -c  # Should be ~51 characters
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

**Issue**: Mem0 memory operations failing
```python
# Debug memory configuration
import os
from mem0 import Memory

config = {
    "vector_store": {"provider": "qdrant", "config": {"host": "localhost", "port": 6333}},
    "llm": {"provider": "openai", "config": {"api_key": os.getenv("OPENAI_API_KEY")}},
}

try:
    memory = Memory.from_config(config)
    result = memory.add("test memory")
    print(f"Memory test successful: {result}")
except Exception as e:
    print(f"Memory test failed: {e}")
```

**Issue**: R2R service connection errors
```bash
# Check R2R service status
curl http://localhost:7272/health
docker-compose logs r2r
```

#### Database Issues

**Issue**: PostgreSQL connection refused
```bash
# Check PostgreSQL status
docker-compose ps postgres
docker-compose logs postgres

# Test connection
psql -h localhost -U postgres -d agentflow -c "SELECT version();"
```

**Issue**: Redis connection errors
```bash
# Check Redis status
docker-compose ps redis
redis-cli ping

# Clear Redis cache if needed
redis-cli flushall
```

#### Performance Issues

**Issue**: Slow API responses
```python
# Add timing middleware
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

**Issue**: Memory operation timeouts
```python
# Optimize memory queries
memories = await memory.search(
    query="user query",
    user_id=user_id,
    limit=10,  # Limit results
    filters={"category": "relevant"}  # Add filters
)
```

### Monitoring and Debugging

#### Health Checks
```bash
# Run comprehensive health check
./scripts/debug.sh

# Individual service checks
curl http://localhost:8000/health        # API
curl http://localhost:7272/health        # R2R
docker-compose ps                        # All services
```

#### Log Analysis
```bash
# View application logs
docker-compose logs -f api

# View specific service logs
docker-compose logs --tail=50 postgres
docker-compose logs --tail=50 redis
docker-compose logs --tail=50 r2r
```

#### Performance Monitoring
```python
# Add performance logging
import logging
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        logging.info(f"{func.__name__} took {duration:.2f}s")
        return result
    return wrapper

@monitor_performance
async def slow_operation():
    # Your code here
    pass
```

### Emergency Procedures

#### Complete Environment Reset
```bash
# Stop all services
docker-compose down --volumes --remove-orphans

# Clean Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete

# Restart fresh
./scripts/setup.sh
```

#### Data Recovery
```bash
# Backup database
docker-compose exec postgres pg_dump -U postgres agentflow > backup.sql

# Restore database
docker-compose exec -T postgres psql -U postgres agentflow < backup.sql
```

### Getting Help

1. **Check logs first**: `./scripts/debug.sh`
2. **Verify configuration**: Ensure all environment variables are set
3. **Test dependencies**: Verify all external services are accessible
4. **Isolate the issue**: Test individual components
5. **Search documentation**: Check framework-specific documentation
6. **Create minimal reproduction**: Isolate the problem to smallest possible case

---

# CONTRIBUTING.md

## Contributing to AgentFlow

### Development Environment Setup

1. **Fork and clone the repository**
2. **Run setup script**: `./scripts/setup.sh`
3. **Configure environment**: Copy and edit `.env` file
4. **Start development**: Follow instructions in `DEVELOPMENT.md`

### Code Style Guidelines

- **Python**: Follow PEP 8, use Black for formatting
- **TypeScript**: Use Biome for formatting and linting
- **API Design**: RESTful principles with proper HTTP status codes
- **Documentation**: Include docstrings for all public functions
- **Type Safety**: Use type hints throughout Python code

### Testing Requirements

- **Unit tests**: Required for all new features
- **Integration tests**: Required for API endpoints
- **Mock external services**: No real API calls in tests
- **Performance tests**: For performance-critical features

### Pull Request Process

1. **Create feature branch**: `git checkout -b feature/description`
2. **Write tests**: Ensure comprehensive test coverage
3. **Format code**: Run `./scripts/format.sh`
4. **Run tests**: Ensure `./scripts/test.sh` passes
5. **Update documentation**: Include relevant documentation updates
6. **Submit PR**: Include clear description and link to issues

### Commit Message Format

Use Conventional Commits format:
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `test:` - Test additions or changes
- `refactor:` - Code refactoring
- `perf:` - Performance improvements

### AI Framework Integration Guidelines

- **LangGraph**: Use proper state management and checkpointing
- **Mem0**: Implement proper memory scoping and error handling
- **R2R**: Configure hybrid search for optimal performance
- **MCP**: Ensure protocol compliance and security
- **Pydantic AI**: Use type-safe configurations throughout

### Security Considerations

- **No hardcoded secrets**: Use environment variables
- **Input validation**: Use Pydantic models for all inputs
- **Error handling**: Don't expose internal details in errors
- **Dependencies**: Keep dependencies updated and secure
- **AI Security**: Implement proper sandboxing for AI operations
