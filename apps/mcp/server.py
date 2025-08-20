import os, json
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("AgentFlow MCP", debug=False, log_level="INFO")

@mcp.tool()
async def ping(ctx: Context) -> str:
    """Health check tool for MCP server."""
    await ctx.info("pong")
    return "pong"

@mcp.tool()
async def rag_search(ctx: Context, query: str) -> dict:
    """Run an R2R hybrid+KG search and return raw results."""
    import httpx
    base = os.getenv("R2R_BASE_URL", "http://localhost:7272")
    headers = {"Authorization": f"Bearer {os.getenv('R2R_API_KEY','')}"}
    payload = {
        "query": query,
        "rag_generation_config": {"model": "gpt-4o-mini", "temperature": 0.0},
        "search_settings": {"use_hybrid_search": True, "use_kg_search": True, "limit": 25}
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{base}/api/retrieval/rag", json=payload, headers=headers)
        r.raise_for_status()
        return r.json()

if __name__ == "__main__":
    # STDIO by default; use `uv run server fastmcp stdio` in advanced setups
    mcp.run()
