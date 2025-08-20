# AgentFlow Scaffold (MVP)

This is a production-leaning scaffold aligned with the AgentFlow PRD/FRD.

## Services
- **API (FastAPI)** — gateway + auth, memory ops, RAG, agent runs
- **MCP Server (FastMCP)** — standardized tool surface
- **R2R** — production RAG service (dockerized)
- **PostgreSQL, Redis, Qdrant** — persistence, sessions, vector store

## Quickstart
1) Copy `.env.example` to `.env` and fill values
2) `docker compose up -d` (starts infra + R2R)
3) `uvicorn apps.api.app.main:app --reload`
4) `python apps/mcp/server.py`

## Notes
- Follows FastAPI security & structure rules
- Uses Mem0 for multi-level memory (user/agent/session)
- Uses PydanticAI for typed agent interfaces
- R2R client is pre-wired for hybrid + KG search
