# AGENTS.md: MCP Server Collaboration Guide

<!-- This file provides specialized guidance for AI agents working on the AgentFlow MCP (Model Context Protocol) server. It supplements the root AGENTS.md with MCP-specific requirements. -->

## Component Scope

This AGENTS.md covers the MCP server implementation (`apps/mcp/`) which provides standardized tool integration following the Model Context Protocol specification. This server enables AgentFlow agents to access external tools and services through a secure, standardized interface.

## MCP Protocol Fundamentals

### Protocol Compliance Requirements
- **MUST** follow MCP specification exactly - protocol violations break agent communication
- **MUST** use proper STDIO transport for communication
- **MUST** implement standard tool registration and discovery patterns
- **MUST** handle protocol errors gracefully without breaking the connection
- **MUST** provide proper tool metadata and documentation

### Core MCP Server Pattern
```python
from mcp.server.fastmcp import FastMCP, Context
import os
import json

# Initialize MCP server with proper configuration
mcp = FastMCP(
    name="AgentFlow MCP",
    description="AgentFlow tool integration server",
    debug=False,  # Set to True only for development
    log_level="INFO"
)

# Tool registration pattern
@mcp.tool()
async def tool_name(ctx: Context, param1: str, param2: int = 10) -> dict:
    """Tool description for automatic documentation.
    
    Args:
        ctx: MCP context for logging and communication
        param1: Description of required parameter
        param2: Description of optional parameter with default
        
    Returns:
        dict: Structured response data
    """
    try:
        # Log tool execution for debugging
        await ctx.info(f"Executing tool_name with param1={param1}, param2={param2}")
        
        # Implement tool logic here
        result = await perform_tool_operation(param1, param2)
        
        # Return structured response
        return {
            "success": True,
            "data": result,
            "metadata": {
                "execution_time": "...",
                "tool_version": "1.0.0"
            }
        }
        
    except Exception as e:
        # Log error but don't break protocol
        await ctx.error(f"Tool execution failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }

# Server startup
if __name__ == "__main__":
    mcp.run()  # Uses STDIO transport by default
```

## Tool Development Patterns

### Tool Function Signatures
```python
# Simple tool with basic types
@mcp.tool()
async def ping(ctx: Context) -> str:
    """Health check tool for MCP server connectivity."""
    await ctx.info("ping requested")
    return "pong"

# Tool with complex parameters and validation
@mcp.tool()
async def search_knowledge(
    ctx: Context,
    query: str,
    max_results: int = 10,
    include_metadata: bool = False
) -> dict:
    """Search AgentFlow knowledge base with advanced options.
    
    Args:
        ctx: MCP context for logging
        query: Search query string (required)
        max_results: Maximum number of results to return (1-100)
        include_metadata: Whether to include document metadata
        
    Returns:
        dict: Search results with documents and metadata
    """
    # Input validation
    if not query.strip():
        raise ValueError("Query cannot be empty")
    
    if not 1 <= max_results <= 100:
        raise ValueError("max_results must be between 1 and 100")
    
    await ctx.info(f"Searching knowledge base: {query[:50]}...")
    
    # Tool implementation
    results = await knowledge_service.search(
        query=query,
        limit=max_results,
        include_metadata=include_metadata
    )
    
    return {
        "query": query,
        "total_results": len(results),
        "results": results,
        "execution_metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "server_version": "1.0.0"
        }
    }

# Tool that integrates with other AgentFlow services
@mcp.tool()
async def create_agent_memory(
    ctx: Context,
    memory_text: str,
    user_id: str,
    agent_id: str | None = None
) -> dict:
    """Create a new memory in the AgentFlow memory system.
    
    Args:
        ctx: MCP context
        memory_text: Text content for the memory
        user_id: User identifier for memory scoping
        agent_id: Optional agent identifier for scoping
        
    Returns:
        dict: Created memory information
    """
    import httpx
    
    await ctx.info(f"Creating memory for user {user_id}")
    
    # Call AgentFlow API
    payload = {
        "text": memory_text,
        "scope": "agent" if agent_id else "user",
        "agent_id": agent_id
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/memory/",
                json=payload,
                headers={"Authorization": f"Bearer {API_TOKEN}"}
            )
            response.raise_for_status()
            
            return {
                "success": True,
                "memory": response.json()
            }
            
    except httpx.HTTPError as e:
        await ctx.error(f"Failed to create memory: {e}")
        return {
            "success": False,
            "error": f"API call failed: {e}"
        }
```

### Tool Security Patterns
```python
import asyncio
import subprocess
from pathlib import Path

# Secure file access pattern
@mcp.tool()
async def read_safe_file(ctx: Context, file_path: str) -> dict:
    """Read file content with security restrictions."""
    # Validate file path
    safe_path = Path(file_path).resolve()
    allowed_directory = Path("/safe/data/directory").resolve()
    
    # Prevent directory traversal
    if not str(safe_path).startswith(str(allowed_directory)):
        raise PermissionError("File access outside allowed directory")
    
    # Check file exists and is readable
    if not safe_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not safe_path.is_file():
        raise ValueError("Path is not a file")
    
    try:
        # Read with size limit
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        if safe_path.stat().st_size > MAX_FILE_SIZE:
            raise ValueError("File too large")
        
        with open(safe_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "success": True,
            "content": content,
            "file_info": {
                "path": str(safe_path),
                "size": safe_path.stat().st_size
            }
        }
        
    except Exception as e:
        await ctx.error(f"File read error: {e}")
        raise

# Secure command execution pattern
@mcp.tool()
async def execute_safe_command(ctx: Context, command: str) -> dict:
    """Execute command with security restrictions."""
    # Whitelist of allowed commands
    ALLOWED_COMMANDS = ["ls", "pwd", "date", "whoami"]
    
    command_parts = command.split()
    if not command_parts or command_parts[0] not in ALLOWED_COMMANDS:
        raise PermissionError(f"Command not allowed: {command_parts[0] if command_parts else 'empty'}")
    
    try:
        # Execute with timeout and security limits
        result = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                *command_parts,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd="/safe/working/directory"
            ),
            timeout=30.0  # 30 second timeout
        )
        
        stdout, stderr = await result.communicate()
        
        return {
            "success": result.returncode == 0,
            "stdout": stdout.decode('utf-8'),
            "stderr": stderr.decode('utf-8'),
            "return_code": result.returncode
        }
        
    except asyncio.TimeoutError:
        await ctx.error("Command execution timed out")
        raise TimeoutError("Command execution timeout")
```

## Integration with AgentFlow Services

### Memory Service Integration
```python
@mcp.tool()
async def query_user_memories(
    ctx: Context,
    user_id: str,
    query: str,
    limit: int = 10
) -> dict:
    """Query user memories through AgentFlow memory service."""
    import httpx
    
    await ctx.info(f"Querying memories for user {user_id}")
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{API_BASE_URL}/memory/search",
                params={"q": query, "limit": limit},
                headers={"Authorization": f"Bearer {get_service_token()}"}
            )
            response.raise_for_status()
            
            memories = response.json()
            
            return {
                "success": True,
                "query": query,
                "total_found": len(memories),
                "memories": memories
            }
            
    except Exception as e:
        await ctx.error(f"Memory query failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
```

### RAG Service Integration
```python
@mcp.tool()
async def rag_search(ctx: Context, query: str, use_kg: bool = True) -> dict:
    """Run an R2R hybrid+KG search and return raw results."""
    import httpx
    
    base = os.getenv("R2R_BASE_URL", "http://localhost:7272")
    api_key = os.getenv("R2R_API_KEY", "")
    
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    payload = {
        "query": query,
        "rag_generation_config": {
            "model": "gpt-4o-mini",
            "temperature": 0.0
        },
        "search_settings": {
            "use_hybrid_search": True,
            "use_kg_search": use_kg,
            "limit": 25
        }
    }
    
    await ctx.info(f"Executing RAG search: {query[:50]}...")
    
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{base}/api/retrieval/rag",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            result = response.json()
            
            return {
                "success": True,
                "query": query,
                "answer": result.get("results", {}).get("completion", ""),
                "sources": result.get("results", {}).get("search_results", []),
                "metadata": {
                    "use_kg": use_kg,
                    "model": payload["rag_generation_config"]["model"]
                }
            }
            
    except Exception as e:
        await ctx.error(f"RAG search failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "query": query
        }
```

## Error Handling and Resilience

### Protocol Error Handling
```python
# Error handling that preserves MCP protocol
@mcp.tool()
async def resilient_tool(ctx: Context, param: str) -> dict:
    """Tool with comprehensive error handling."""
    try:
        # Tool logic here
        result = await perform_operation(param)
        
        return {
            "success": True,
            "data": result
        }
        
    except ValueError as e:
        # Client error - bad input
        await ctx.error(f"Invalid input: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": "validation_error",
            "recoverable": True
        }
        
    except ConnectionError as e:
        # Service error - may be temporary
        await ctx.error(f"Service connection failed: {e}")
        return {
            "success": False,
            "error": "Service temporarily unavailable",
            "error_type": "connection_error",
            "recoverable": True,
            "retry_after": 30
        }
        
    except Exception as e:
        # Unexpected error
        await ctx.error(f"Unexpected error: {e}")
        return {
            "success": False,
            "error": "Internal tool error",
            "error_type": "internal_error",
            "recoverable": False
        }

# Retry pattern for external service calls
async def call_external_service_with_retry(
    ctx: Context,
    operation: callable,
    max_retries: int = 3,
    backoff_factor: float = 1.0
) -> dict:
    """Call external service with exponential backoff retry."""
    import asyncio
    
    for attempt in range(max_retries + 1):
        try:
            result = await operation()
            return {"success": True, "data": result}
            
        except Exception as e:
            if attempt == max_retries:
                await ctx.error(f"Operation failed after {max_retries} retries: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "attempts": attempt + 1
                }
            
            wait_time = backoff_factor * (2 ** attempt)
            await ctx.info(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
            await asyncio.sleep(wait_time)
```

## Performance Optimization

### Tool Response Caching
```python
from functools import lru_cache
import json
import hashlib

# In-memory caching for expensive operations
@lru_cache(maxsize=128)
def cached_expensive_operation(param_hash: str) -> str:
    """Cache expensive operations using hash of parameters."""
    # This will be called only once per unique param_hash
    return perform_expensive_operation(param_hash)

@mcp.tool()
async def cached_tool(ctx: Context, query: str, options: dict = None) -> dict:
    """Tool with intelligent caching."""
    # Create cache key from parameters
    cache_key = hashlib.md5(
        json.dumps({"query": query, "options": options or {}}, sort_keys=True).encode()
    ).hexdigest()
    
    try:
        # Try cached result first
        result = cached_expensive_operation(cache_key)
        await ctx.info(f"Serving cached result for query: {query[:30]}...")
        
        return {
            "success": True,
            "data": json.loads(result),
            "cached": True
        }
        
    except Exception:
        # Cache miss or error - compute fresh result
        await ctx.info(f"Computing fresh result for query: {query[:30]}...")
        
        result = await perform_expensive_operation(query, options)
        
        return {
            "success": True,
            "data": result,
            "cached": False
        }
```

### Async Optimization Patterns
```python
import asyncio

@mcp.tool()
async def parallel_operations_tool(
    ctx: Context,
    queries: list[str]
) -> dict:
    """Perform multiple operations in parallel for better performance."""
    await ctx.info(f"Processing {len(queries)} queries in parallel")
    
    # Create tasks for parallel execution
    tasks = [
        process_single_query(query)
        for query in queries
    ]
    
    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results and handle any exceptions
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            await ctx.error(f"Query {i} failed: {result}")
            processed_results.append({
                "query": queries[i],
                "success": False,
                "error": str(result)
            })
        else:
            processed_results.append({
                "query": queries[i],
                "success": True,
                "data": result
            })
    
    successful_count = sum(1 for r in processed_results if r["success"])
    
    return {
        "total_queries": len(queries),
        "successful": successful_count,
        "failed": len(queries) - successful_count,
        "results": processed_results
    }
```

## Testing MCP Tools

### Tool Testing Framework
```python
import pytest
from unittest.mock import AsyncMock, patch
import json

@pytest.fixture
def mock_context():
    """Mock MCP context for testing."""
    ctx = AsyncMock()
    ctx.info = AsyncMock()
    ctx.error = AsyncMock()
    ctx.warn = AsyncMock()
    return ctx

@pytest.mark.asyncio
async def test_ping_tool(mock_context):
    """Test basic ping tool functionality."""
    from apps.mcp.server import ping
    
    result = await ping(mock_context)
    
    assert result == "pong"
    mock_context.info.assert_called_with("pong")

@pytest.mark.asyncio
async def test_rag_search_success(mock_context):
    """Test RAG search tool with successful response."""
    from apps.mcp.server import rag_search
    
    # Mock the HTTP response
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": {
                "completion": "Test answer",
                "search_results": ["doc1", "doc2"]
            }
        }
        mock_response.raise_for_status = AsyncMock()
        
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        result = await rag_search(mock_context, "test query")
        
        assert result["success"] is True
        assert result["answer"] == "Test answer"
        assert len(result["sources"]) == 2
        mock_context.info.assert_called()

@pytest.mark.asyncio
async def test_rag_search_error_handling(mock_context):
    """Test RAG search tool error handling."""
    from apps.mcp.server import rag_search
    
    # Mock HTTP error
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("Connection failed")
        
        result = await rag_search(mock_context, "test query")
        
        assert result["success"] is False
        assert "Connection failed" in result["error"]
        mock_context.error.assert_called()

# Integration testing with real MCP protocol
@pytest.mark.integration
async def test_mcp_protocol_compliance():
    """Test that tools work with actual MCP protocol."""
    import subprocess
    import json
    
    # Start MCP server as subprocess
    server_process = subprocess.Popen(
        ["python", "apps/mcp/server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Send MCP protocol messages
        initialize_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05"}
        }
        
        server_process.stdin.write(json.dumps(initialize_msg) + "\n")
        server_process.stdin.flush()
        
        # Read response
        response_line = server_process.stdout.readline()
        response = json.loads(response_line)
        
        assert response["result"]["protocolVersion"] == "2024-11-05"
        
    finally:
        server_process.terminate()
        server_process.wait()
```

## Development Workflow for MCP Server

### Local Development Commands
```bash
# Start MCP server for development
cd apps/mcp
python server.py

# Test MCP server with client
# Install MCP CLI if not available
pip install mcp

# Test tool discovery
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}' | python server.py

# Test specific tool
echo '{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "ping", "arguments": {}}}' | python server.py

# Run MCP-specific tests
pytest apps/mcp/tests/ -v

# Validate MCP protocol compliance
mcp validate apps/mcp/server.py
```

### Tool Development Checklist
- [ ] Tool function has proper docstring with Args and Returns sections
- [ ] Input parameters have appropriate type hints and validation
- [ ] Error handling returns structured error responses
- [ ] Tool logs meaningful information using ctx.info/error
- [ ] Security considerations implemented (input validation, file access restrictions)
- [ ] Performance optimizations applied (caching, async operations)
- [ ] Tests cover success and error scenarios
- [ ] Integration with AgentFlow services works correctly

### Debugging MCP Issues
```python
# Enable debug logging
mcp = FastMCP(
    name="AgentFlow MCP",
    debug=True,  # Enable debug output
    log_level="DEBUG"
)

# Add debug logging to tools
@mcp.tool()
async def debug_tool(ctx: Context, param: str) -> dict:
    """Tool with comprehensive debug logging."""
    await ctx.info(f"Tool called with param: {param}")
    
    try:
        # Log intermediate steps
        await ctx.info("Processing step 1...")
        result_1 = await step_1(param)
        
        await ctx.info("Processing step 2...")
        result_2 = await step_2(result_1)
        
        await ctx.info("Tool execution completed successfully")
        return {"success": True, "data": result_2}
        
    except Exception as e:
        await ctx.error(f"Tool execution failed at step: {e}")
        # Include stack trace in debug mode
        import traceback
        await ctx.error(f"Stack trace: {traceback.format_exc()}")
        raise

# Protocol debugging
import json
import sys

def debug_mcp_protocol():
    """Debug MCP protocol messages."""
    print("=== MCP Protocol Debug Mode ===", file=sys.stderr)
    
    while True:
        try:
            line = input()
            print(f"Received: {line}", file=sys.stderr)
            
            # Process message
            message = json.loads(line)
            # ... handle message ...
            
            response = {"jsonrpc": "2.0", "id": message.get("id"), "result": "..."}
            response_json = json.dumps(response)
            
            print(f"Sending: {response_json}", file=sys.stderr)
            print(response_json)
            
        except Exception as e:
            print(f"Protocol error: {e}", file=sys.stderr)
```

## Security Best Practices

### Input Validation and Sanitization
```python
import re
from pathlib import Path

def validate_tool_input(param_name: str, value: any, validation_rules: dict) -> any:
    """Centralized input validation for MCP tools."""
    rules = validation_rules.get(param_name, {})
    
    # Type validation
    expected_type = rules.get('type')
    if expected_type and not isinstance(value, expected_type):
        raise ValueError(f"{param_name} must be of type {expected_type.__name__}")
    
    # String validation
    if isinstance(value, str):
        # Length validation
        min_len = rules.get('min_length', 0)
        max_len = rules.get('max_length', 10000)
        if not min_len <= len(value) <= max_len:
            raise ValueError(f"{param_name} length must be between {min_len} and {max_len}")
        
        # Pattern validation
        pattern = rules.get('pattern')
        if pattern and not re.match(pattern, value):
            raise ValueError(f"{param_name} does not match required pattern")
        
        # Sanitization
        if rules.get('sanitize'):
            import bleach
            value = bleach.clean(value, tags=[], strip=True)
    
    # Numeric validation
    if isinstance(value, (int, float)):
        min_val = rules.get('min_value')
        max_val = rules.get('max_value')
        if min_val is not None and value < min_val:
            raise ValueError(f"{param_name} must be >= {min_val}")
        if max_val is not None and value > max_val:
            raise ValueError(f"{param_name} must be <= {max_val}")
    
    return value

@mcp.tool()
async def secure_tool_example(
    ctx: Context,
    user_input: str,
    file_path: str,
    count: int = 10
) -> dict:
    """Example tool with comprehensive input validation."""
    
    # Define validation rules
    validation_rules = {
        'user_input': {
            'type': str,
            'min_length': 1,
            'max_length': 1000,
            'sanitize': True
        },
        'file_path': {
            'type': str,
            'pattern': r'^[a-zA-Z0-9/_.-]+,  # Safe file path characters only
            'max_length': 255
        },
        'count': {
            'type': int,
            'min_value': 1,
            'max_value': 100
        }
    }
    
    # Validate all inputs
    try:
        user_input = validate_tool_input('user_input', user_input, validation_rules)
        file_path = validate_tool_input('file_path', file_path, validation_rules)
        count = validate_tool_input('count', count, validation_rules)
    except ValueError as e:
        await ctx.error(f"Input validation failed: {e}")
        return {"success": False, "error": str(e)}
    
    # Additional security checks
    safe_path = Path(file_path).resolve()
    allowed_directory = Path("/safe/data").resolve()
    
    if not str(safe_path).startswith(str(allowed_directory)):
        await ctx.error(f"File access denied: {file_path}")
        return {"success": False, "error": "File access denied"}
    
    # Tool logic here...
    return {"success": True, "data": "processed"}
```

### Resource Management and Limits
```python
import asyncio
import resource
import psutil
from contextlib import asynccontextmanager

class ResourceManager:
    """Manage resource usage for MCP tools."""
    
    def __init__(self, max_memory_mb: int = 500, max_cpu_time: int = 30):
        self.max_memory_mb = max_memory_mb
        self.max_cpu_time = max_cpu_time
    
    @asynccontextmanager
    async def resource_limits(self):
        """Context manager for resource-limited execution."""
        # Set CPU time limit
        resource.setrlimit(resource.RLIMIT_CPU, (self.max_cpu_time, self.max_cpu_time))
        
        # Monitor memory usage
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        try:
            yield
        finally:
            # Check final memory usage
            final_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_used = final_memory - initial_memory
            
            if memory_used > self.max_memory_mb:
                raise MemoryError(f"Tool exceeded memory limit: {memory_used}MB > {self.max_memory_mb}MB")

resource_manager = ResourceManager()

@mcp.tool()
async def resource_limited_tool(ctx: Context, data: str) -> dict:
    """Tool with resource limits to prevent abuse."""
    try:
        async with resource_manager.resource_limits():
            # Tool logic with resource monitoring
            result = await process_large_data(data)
            
            return {"success": True, "data": result}
            
    except (MemoryError, OSError) as e:
        await ctx.error(f"Resource limit exceeded: {e}")
        return {
            "success": False,
            "error": "Resource limit exceeded",
            "error_type": "resource_limit"
        }
```

## Monitoring and Observability

### Tool Performance Monitoring
```python
import time
from functools import wraps

def monitor_tool_performance(func):
    """Decorator to monitor tool performance."""
    @wraps(func)
    async def wrapper(ctx: Context, *args, **kwargs):
        start_time = time.time()
        tool_name = func.__name__
        
        await ctx.info(f"Tool {tool_name} started")
        
        try:
            result = await func(ctx, *args, **kwargs)
            
            execution_time = time.time() - start_time
            await ctx.info(f"Tool {tool_name} completed in {execution_time:.2f}s")
            
            # Add performance metadata to response
            if isinstance(result, dict):
                result.setdefault("metadata", {})["execution_time"] = execution_time
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            await ctx.error(f"Tool {tool_name} failed after {execution_time:.2f}s: {e}")
            raise
    
    return wrapper

# Apply monitoring to tools
@mcp.tool()
@monitor_tool_performance
async def monitored_tool(ctx: Context, param: str) -> dict:
    """Tool with automatic performance monitoring."""
    # Tool implementation
    result = await some_operation(param)
    return {"success": True, "data": result}
```

### Health Monitoring for MCP Server
```python
@mcp.tool()
async def mcp_health_check(ctx: Context) -> dict:
    """Comprehensive health check for MCP server and dependencies."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Check memory usage
    memory_info = psutil.Process().memory_info()
    memory_mb = memory_info.rss / 1024 / 1024
    health_status["checks"]["memory"] = {
        "status": "healthy" if memory_mb < 1000 else "warning",
        "memory_mb": memory_mb
    }
    
    # Check AgentFlow API connectivity
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{API_BASE_URL}/health")
            if response.status_code == 200:
                health_status["checks"]["agentflow_api"] = {"status": "healthy"}
            else:
                health_status["checks"]["agentflow_api"] = {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
    except Exception as e:
        health_status["checks"]["agentflow_api"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check R2R service
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{R2R_BASE_URL}/health")
            health_status["checks"]["r2r_service"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy"
            }
    except Exception as e:
        health_status["checks"]["r2r_service"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Determine overall status
    unhealthy_checks = [
        check for check in health_status["checks"].values()
        if check["status"] == "unhealthy"
    ]
    
    if unhealthy_checks:
        health_status["status"] = "unhealthy"
    elif any(check["status"] == "warning" for check in health_status["checks"].values()):
        health_status["status"] = "warning"
    
    await ctx.info(f"Health check completed: {health_status['status']}")
    return health_status
```

## Critical MCP Development Rules

### Protocol Compliance Rules
- **NEVER** break MCP protocol format - agents depend on exact compliance
- **NEVER** modify tool signatures without updating documentation
- **NEVER** ignore protocol errors - they indicate serious issues
- **NEVER** use synchronous operations that block the event loop
- **NEVER** return inconsistent response formats

### Security Rules
- **NEVER** execute user input as code without validation
- **NEVER** access files outside designated safe directories
- **NEVER** expose internal service credentials through tool responses
- **NEVER** skip input validation for any tool parameter
- **NEVER** allow unlimited resource consumption

### Performance Rules
- **NEVER** implement tools without timeout mechanisms
- **NEVER** make unlimited external API calls
- **NEVER** load large datasets without memory management
- **NEVER** skip caching for expensive repeated operations
- **NEVER** ignore tool execution monitoring and logging

### Integration Rules
- **NEVER** hardcode AgentFlow service URLs - use environment variables
- **NEVER** ignore service authentication and authorization
- **NEVER** assume external services are always available
- **NEVER** skip error handling for service integration
- **NEVER** expose sensitive AgentFlow internal data through MCP tools

---
trigger: model_decision
description: Comprehensive rules for developing Model Context Protocol (MCP) servers and clients using the Python MCP SDK. Covers FastMCP framework, low-level server APIs, authentication, deployment, and best practices.
globs: 
  - "**/*mcp*.py"
  - "**/server*.py" 
  - "**/client*.py"
  - "**/fastmcp*.py"
---

# Python MCP SDK Rules

## Installation and Environment Setup

### Package Installation
- **ALWAYS** install MCP with CLI tools: `uv add "mcp[cli]"` or `pip install "mcp[cli]"`
- **ALWAYS** use virtual environments for dependency isolation: `python -m venv .venv` or `uv venv`
- **RECOMMENDED** use `uv` for faster package management and dependency resolution
- **REQUIRED** Python 3.8+ for compatibility with MCP SDK

### Environment Configuration
- **STORE** sensitive credentials in environment variables, never in code
- **USE** `.env` files for local development configuration
- **SET** `FASTMCP_DEBUG=false` in production environments
- **CONFIGURE** log levels appropriately: `FASTMCP_LOG_LEVEL=INFO` (production) or `DEBUG` (development)

## FastMCP Framework (Recommended Approach)

### Server Creation and Configuration
```python
from mcp.server.fastmcp import FastMCP

# Basic server creation
mcp = FastMCP("My Server Name")

# Production configuration
mcp = FastMCP(
    "Production Server",
    host="0.0.0.0",  # Allow external connections
    port=8000,
    debug=False,     # Disable debug in production
    log_level="INFO"
)
```

### Tool Definition Best Practices
```python
@mcp.tool()
def calculate_sum(a: int, b: int) -> int:
    """Add two numbers together."""  # REQUIRED: Descriptive docstring
    return a + b

# Async tools for I/O operations
@mcp.tool()
async def fetch_data(url: str, ctx: Context) -> str:
    """Fetch data with progress reporting."""
    await ctx.info(f"Fetching data from {url}")
    # Implementation here
    return result
```

### Resource Definition Patterns
```python
# Static resources
@mcp.resource("config://settings")
def get_settings() -> str:
    """Return application configuration."""
    return json.dumps({"theme": "dark", "version": "1.0"})

# Dynamic resources with parameters
@mcp.resource("file://documents/{name}")
def read_document(name: str) -> str:
    """Read document by name with validation."""
    # ALWAYS validate input parameters
    if not name.replace("_", "").replace("-", "").isalnum():
        raise ValueError("Invalid document name")
    return f"Content of {name}"
```

### Context and Progress Reporting
```python
from mcp.server.fastmcp import Context

@mcp.tool()
async def long_running_task(task_name: str, ctx: Context, steps: int = 5) -> str:
    """Execute task with proper progress reporting."""
    await ctx.info(f"Starting: {task_name}")
    
    for i in range(steps):
        progress = (i + 1) / steps
        await ctx.report_progress(
            progress=progress,
            total=1.0,
            message=f"Step {i + 1}/{steps}"
        )
        await ctx.debug(f"Completed step {i + 1}")
    
    return f"Task '{task_name}' completed"
```

## Low-Level Server API

### Server Initialization and Lifespan Management
```python
import asyncio
from mcp.server.lowlevel import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio

# Create server with lifespan management
server = Server("example-server")

@asynccontextmanager
async def server_lifespan(_server: Server):
    """Manage server startup and shutdown."""
    # Initialize resources
    db = await Database.connect()
    try:
        yield {"db": db}
    finally:
        # Cleanup
        await db.disconnect()

server = Server("example-server", lifespan=server_lifespan)
```

### Handler Registration Patterns
```python
@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools with proper schema definition."""
    return [
        types.Tool(
            name="query_db",
            description="Query the database",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SQL query"}
                },
                "required": ["query"]
            },
            # NEW: Output schema for structured results
            outputSchema={
                "type": "object",
                "properties": {
                    "rows": {"type": "array", "description": "Query results"},
                    "count": {"type": "number", "description": "Row count"}
                }
            }
        )
    ]

@server.call_tool()
async def handle_tool_call(name: str, arguments: dict) -> dict:
    """Handle tool calls with structured output."""
    if name == "query_db":
        # Access lifespan context
        ctx = server.request_context
        db = ctx.lifespan_context["db"]
        
        # Return structured data matching output schema
        return {
            "rows": [{"id": 1, "name": "example"}],
            "count": 1
        }
    
    raise ValueError(f"Unknown tool: {name}")
```

## Client Development

### STDIO Client Pattern
```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_client():
    """Standard client connection pattern."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "server", "fastmcp_quickstart", "stdio"],
        env={"UV_INDEX": os.environ.get("UV_INDEX", "")}
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize connection
            await session.initialize()
            
            # List and use resources
            resources = await session.list_resources()
            if resources.resources:
                content = await session.read_resource(resources.resources[0].uri)
                
            # Call tools
            tools = await session.list_tools()
            if tools.tools:
                result = await session.call_tool("tool_name", {"param": "value"})
```

### HTTP Client with Authentication
```python
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.auth import OAuthClientProvider

# OAuth authentication setup
oauth_auth = OAuthClientProvider(
    server_url="http://localhost:8001",
    client_metadata=OAuthClientMetadata(
        client_name="My MCP Client",
        redirect_uris=[AnyUrl("http://localhost:3000/callback")],
        grant_types=["authorization_code", "refresh_token"],
        response_types=["code"],
        scope="user"
    ),
    storage=TokenStorage(),  # Implement secure token storage
    redirect_handler=handle_redirect,
    callback_handler=handle_callback
)

async with streamablehttp_client("http://localhost:8001/mcp", auth=oauth_auth) as (read, write, _):
    async with ClientSession(read, write) as session:
        await session.initialize()
        # Use authenticated session
```

## Transport Configuration

### Transport Selection Rules
- **STDIO**: Default for local development and CLI tools
- **Streamable HTTP**: REQUIRED for cloud deployment and remote access
- **SSE**: Legacy transport, use only for backward compatibility

### Streamable HTTP Configuration
```python
# For cloud deployment
mcp = FastMCP("CloudServer", stateless_http=True)

# Custom endpoint mounting
from starlette.applications import Starlette
from starlette.routing import Mount

app = Starlette(routes=[
    Mount("/mcp", app=mcp.streamable_http_app()),
    Mount("/health", app=health_check_app())
])

# Multiple server mounting
github_mcp = FastMCP("GitHub API")
github_mcp.settings.mount_path = "/github"

app = Starlette(routes=[
    Mount("/github", app=github_mcp.sse_app()),
    Mount("/search", app=search_mcp.sse_app("/search"))
])
```

## Authentication and Security

### OAuth 2.1 Resource Server Setup
```python
from mcp.server.auth.provider import TokenVerifier, AccessToken
from mcp.server.auth.settings import AuthSettings

class ProductionTokenVerifier(TokenVerifier):
    """Production-grade token verification."""
    
    async def verify_token(self, token: str) -> AccessToken | None:
        """Verify OAuth token with proper validation."""
        # REQUIRED: Implement actual token validation
        # - Verify token signature
        # - Check expiration
        # - Validate scopes
        # - Rate limiting checks
        pass

# Server with authentication
mcp = FastMCP(
    "Secure Weather Service",
    token_verifier=ProductionTokenVerifier(),
    auth=AuthSettings(
        issuer_url=AnyHttpUrl("https://auth.example.com"),
        resource_server_url=AnyHttpUrl("http://localhost:3001"),
        required_scopes=["user", "data.read"]
    )
)
```

### Security Best Practices
- **NEVER** hard-code credentials in source code
- **ALWAYS** validate and sanitize external input
- **USE** HTTPS in production deployments
- **IMPLEMENT** proper rate limiting for public endpoints
- **STORE** tokens securely with encryption at rest
- **VALIDATE** OAuth scopes for each protected resource

## Development and Testing

### Development Workflow
```bash
# Install dependencies with development tools
uv sync --frozen --all-extras --dev

# Run in development mode with hot reload
uv run mcp dev server.py

# Add dependencies for development
uv run mcp dev server.py --with pandas --with numpy

# Install server for Claude Desktop
uv run mcp install server.py --name "My Analytics Server"
```

### Testing Patterns
```python
import pytest
from mcp.server.fastmcp import FastMCP

@pytest.fixture
async def test_server():
    """Create test server instance."""
    mcp = FastMCP("Test Server", debug=True)
    
    @mcp.tool()
    def test_tool(input_data: str) -> str:
        return f"Processed: {input_data}"
    
    return mcp

@pytest.mark.asyncio
async def test_tool_functionality(test_server):
    """Test tool execution."""
    # Test implementation here
    pass
```

### Pre-commit Configuration
```bash
# Install pre-commit hooks
uv tool install pre-commit --with pre-commit-uv --force-reinstall

# Run formatting and linting
uv run ruff format .
uv run ruff check . --fix
uv run pyright  # Type checking
```

## Error Handling and Logging

### Exception Management
```python
import logging

logger = logging.getLogger(__name__)

@mcp.tool()
async def safe_operation(data: str, ctx: Context) -> str:
    """Tool with proper error handling."""
    try:
        # Operation logic
        result = process_data(data)
        await ctx.info(f"Successfully processed {len(data)} characters")
        return result
    
    except ValueError as e:
        logger.exception("Invalid input data")
        await ctx.error(f"Invalid input: {str(e)}")
        raise
    
    except (ConnectionError, TimeoutError) as e:
        logger.exception("Network operation failed")
        await ctx.warning("Retrying operation...")
        # Implement retry logic
        raise
    
    except Exception as e:
        logger.exception("Unexpected error in safe_operation")
        await ctx.error("Internal server error")
        raise
```

### Progress and Status Reporting
```python
@mcp.tool()
async def batch_processor(items: list[str], ctx: Context) -> dict:
    """Process items with detailed progress reporting."""
    total_items = len(items)
    processed = []
    failed = []
    
    for i, item in enumerate(items):
        try:
            # Report progress
            await ctx.report_progress(
                progress=(i + 1) / total_items,
                total=1.0,
                message=f"Processing item {i + 1}/{total_items}"
            )
            
            result = await process_item(item)
            processed.append(result)
            await ctx.debug(f"Successfully processed item {i + 1}")
            
        except Exception as e:
            await ctx.warning(f"Failed to process item {i + 1}: {str(e)}")
            failed.append({"item": item, "error": str(e)})
    
    return {
        "processed_count": len(processed),
        "failed_count": len(failed),
        "results": processed,
        "failures": failed
    }
```

## Performance Optimization

### Async Best Practices
- **USE** `async`/`await` for all I/O operations
- **IMPLEMENT** connection pooling for database/HTTP clients
- **SET** appropriate timeouts using float values for precision
- **BATCH** operations when possible to reduce overhead

### Memory Management
```python
@mcp.tool()
async def large_data_processor(data_source: str, ctx: Context) -> str:
    """Process large datasets efficiently."""
    # Stream processing for large datasets
    total_processed = 0
    
    async for batch in stream_data_batches(data_source, batch_size=1000):
        # Process in chunks to manage memory
        processed_batch = await process_batch(batch)
        total_processed += len(processed_batch)
        
        # Report progress periodically
        if total_processed % 5000 == 0:
            await ctx.info(f"Processed {total_processed} records")
    
    return f"Successfully processed {total_processed} records"
```

## Known Issues and Mitigations

### ENOENT Errors on macOS
- **CAUSE**: Python path issues after Homebrew upgrades
- **FIX**: Rebuild virtual environment and reinstall dependencies
```bash
# Remove old virtual environment
rm -rf .venv

# Create new virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Reinstall dependencies
pip install "mcp[cli]"
```

### Connection Timeout Issues
- **USE** float timeouts for precise control: `timeout_ms=5.5`
- **IMPLEMENT** exponential backoff for retries
- **MONITOR** connection health with heartbeat messages

### Memory Leaks in Long-Running Servers
- **CLOSE** database connections properly in lifespan context
- **CLEAR** cached data periodically
- **USE** weak references for circular dependencies

## Deployment Considerations

### Production Deployment Checklist
- [ ] **Environment**: Set `debug=False` and appropriate log levels
- [ ] **Security**: Enable HTTPS, validate OAuth tokens, sanitize inputs
- [ ] **Monitoring**: Implement health checks and error tracking
- [ ] **Performance**: Configure connection pooling and timeouts
- [ ] **Scaling**: Use stateless HTTP for horizontal scaling

### Cloud Platform Configuration
```python
# For serverless/cloud deployment
mcp = FastMCP(
    "Production API",
    stateless_http=True,  # Required for serverless
    json_response=True,   # Disable SSE for some platforms
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 8000))
)

# Health check endpoint
@mcp.tool()
def health_check() -> dict:
    """Health check for load balancers."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
```

## Version Compatibility and Migration

### Current Protocol Version: 2025-06-18
- **REMOVED**: JSON-RPC batching (deprecated from 2025-03-26)
- **NEW**: Structured tool outputs with schema validation
- **ENHANCED**: OAuth security requirements
- **ADDED**: Audio content support

### Migration Guidelines
- **UPDATE** to latest SDK version: Check GitHub releases
- **REMOVE** any JSON-RPC batching code
- **IMPLEMENT** structured output schemas for tools
- **UPGRADE** OAuth implementation to meet security requirements
- **TEST** thoroughly after protocol version updates

### Backward Compatibility
- **MAINTAIN** support for clients on older protocol versions when possible
- **DOCUMENT** breaking changes in release notes
- **PROVIDE** migration scripts for major version updates
