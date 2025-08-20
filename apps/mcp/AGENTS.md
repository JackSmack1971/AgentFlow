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
