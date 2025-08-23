# AGENTS.md: MCP Server Guidelines

This document provides specific guidance for AI models working with the AgentFlow Model Context Protocol (MCP) server located in `/apps/mcp/`. These guidelines are derived from the Python MCP SDK and MCP protocol specification rulesets.

## 1. Project Scope & Architecture
*   **Primary Purpose:** MCP protocol implementation for standardized tool integration in the AgentFlow platform
*   **Core Technologies:** Python MCP SDK, FastMCP server, JSONRPC protocol compliance
*   **Architecture Pattern:** Tool registration and discovery patterns following MCP specification

## 2. MCP Protocol Standards

### Installation and Dependencies
*   **REQUIRED:** Install MCP SDK: `pip install mcp[cli]`
*   **MANDATORY:** Pin version for production: `mcp>=0.1.0`
*   **CRITICAL:** Set `FASTMCP_DEBUG=false` in production environments

### Server Implementation
*   **MANDATORY:** Use FastMCP server for HTTP transport capability
*   **REQUIRED:** Implement both STDIO (local) and streamable HTTP (serverless) transports
*   **CRITICAL:** Follow protocol specifications with tool registration and discovery patterns

```python
from mcp.server.fastmcp import FastMCP
from mcp.server.context import Context

mcp = FastMCP("AgentFlow MCP Server")

@mcp.tool()
def example_tool(query: str, context: Context) -> dict:
    """Example tool with proper MCP compliance."""
    context.report_progress("Processing query...")
    return {"result": f"Processed: {query}"}
```

### Tool Definition Requirements
*   **MANDATORY:** Every tool MUST declare explicit `inputSchema` and `outputSchema`
*   **REQUIRED:** Use docstrings for tool descriptions and schema documentation
*   **CRITICAL:** Implement proper type validation for all tool inputs and outputs
*   **MANDATORY:** No MCP JSON-RPC batching - use single-call semantics only

```python
from pydantic import BaseModel, Field

class ToolInput(BaseModel):
    query: str = Field(..., description="The search query")
    limit: int = Field(10, description="Maximum results", ge=1, le=100)

class ToolOutput(BaseModel):
    results: list[str] = Field(..., description="Search results")
    count: int = Field(..., description="Number of results returned")

@mcp.tool(input_schema=ToolInput, output_schema=ToolOutput)
def search_tool(input: ToolInput, context: Context) -> ToolOutput:
    """Search tool with typed input/output."""
    results = perform_search(input.query, input.limit)
    return ToolOutput(results=results, count=len(results))
```

### Protocol Compliance
*   **CRITICAL:** Follow JSONRPC error specifications for all error responses
*   **MANDATORY:** Implement proper error handling without breaking agent communication
*   **REQUIRED:** Provide comprehensive tool metadata and documentation
*   **CRITICAL:** Handle protocol errors gracefully with appropriate error codes

### Progress Reporting Standards
*   **REQUIRED:** Use `context.report_progress()` for long-running operations
*   **MANDATORY:** Provide meaningful progress messages to users
*   **REQUIRED:** Implement proper logging with `context.info()`, `context.warning()`, `context.error()`

```python
@mcp.tool()
def long_running_tool(data: str, context: Context) -> dict:
    context.report_progress("Starting process...")
    
    for i, item in enumerate(data_chunks):
        context.report_progress(f"Processing item {i+1}/{len(data_chunks)}")
        process_item(item)
    
    context.info("Process completed successfully")
    return {"status": "completed"}
```

## 3. Security and Authentication
*   **REQUIRED:** Implement OAuth2.1 capability for secure tool access
*   **MANDATORY:** Validate all tool permissions before execution
*   **CRITICAL:** Implement audit logging for all tool usage
*   **REQUIRED:** Never expose internal system details through tool outputs

## 4. Transport Configuration
*   **REQUIRED:** Support both STDIO and HTTP transports
*   **MANDATORY:** Configure appropriate timeouts for HTTP transport
*   **REQUIRED:** Implement proper connection handling and cleanup
*   **CRITICAL:** Use TLS for HTTP transport in production

```python
# STDIO Transport (local development)
if __name__ == "__main__":
    mcp.run()

# HTTP Transport (production/serverless)
from fastapi import FastAPI
app = FastAPI()
app.include_router(mcp.router, prefix="/mcp")
```

## 5. Tool Discovery and Registry
*   **MANDATORY:** Implement tool discovery mechanisms for dynamic loading
*   **REQUIRED:** Provide tool schemas and documentation through discovery API
*   **CRITICAL:** Implement proper versioning for tool schemas
*   **REQUIRED:** Support tool permission management and access control

## 6. Error Handling Standards
*   **CRITICAL:** Use proper MCP error codes and messages
*   **MANDATORY:** Never expose stack traces or internal errors to clients
*   **REQUIRED:** Log all errors with sufficient context for debugging
*   **CRITICAL:** Implement graceful degradation for tool failures

```python
from mcp.server.exceptions import McpError

@mcp.tool()
def safe_tool(input: str, context: Context) -> dict:
    try:
        result = risky_operation(input)
        return {"result": result}
    except ValueError as e:
        context.error(f"Invalid input: {e}")
        raise McpError("INVALID_INPUT", str(e))
    except Exception as e:
        context.error(f"Unexpected error: {e}")
        raise McpError("INTERNAL_ERROR", "An unexpected error occurred")
```

## 7. Testing Requirements
*   **MANDATORY:** Test all tools with valid and invalid inputs
*   **REQUIRED:** Test protocol compliance with MCP specification
*   **CRITICAL:** Mock external dependencies to avoid side effects
*   **REQUIRED:** Implement integration tests for tool discovery and execution

```python
import pytest
from mcp.client.test import MockMcpClient

@pytest.mark.asyncio
async def test_tool_execution():
    client = MockMcpClient(mcp)
    result = await client.call_tool("example_tool", {"query": "test"})
    assert result["result"] == "Processed: test"
```

## 8. Performance Standards
*   **REQUIRED:** Tool execution should complete within reasonable timeouts
*   **MANDATORY:** Implement proper resource cleanup after tool execution
*   **CRITICAL:** Monitor tool performance and resource usage
*   **REQUIRED:** Implement caching for expensive operations where appropriate

## 9. Documentation Requirements
*   **MANDATORY:** Document all tools with comprehensive descriptions
*   **REQUIRED:** Provide examples for tool usage and expected outputs
*   **CRITICAL:** Maintain up-to-date schema documentation
*   **REQUIRED:** Document error conditions and troubleshooting steps

## 10. Forbidden Patterns
*   **NEVER** bypass MCP protocol specifications for tool integration
*   **NEVER** expose sensitive system information through tools
*   **NEVER** implement tools without proper input validation
*   **NEVER** ignore error handling in tool implementations
*   **NEVER** use batched JSONRPC calls (use single-call semantics only)
*   **NEVER** hardcode configuration or secrets in tool code
