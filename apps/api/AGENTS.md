# AGENTS.md: FastAPI API Collaboration Guide

<!-- Guidance for contributors working on the AgentFlow FastAPI backend. -->

## Scope

This guide covers the API service located in [`app/`](app/) and supplements the root `AGENTS.md` with backend‑specific rules.

## Endpoint Structure

- **Entry point:** [`app/main.py`](app/main.py) initializes the FastAPI application and mounts routers.
- **Routers:** Place feature routers in [`app/routers/`](app/routers/). Keep paths RESTful and group by domain (auth, memory, agents, rag, health).
- **Services:** Business logic lives in [`app/services/`](app/services/). Memory operations use Mem0 via [`services/memory.py`](app/services/memory.py).
- **Schemas:** Define all request and response models in [`app/models/`](app/models/). Use Pydantic for strict input validation.

## Authentication

- Authentication routes are implemented in [`routers/auth.py`](app/routers/auth.py) with helpers in [`services/auth.py`](app/services/auth.py).
- Load tokens and secret keys from environment variables through [`config.py`](app/config.py). **Never** hardcode credentials.
- Use FastAPI dependencies for user context and permission checks.

## Mem0 Usage

- Mem0 provides multi‑level (user/agent/session) memory. Interact with it through [`services/memory.py`](app/services/memory.py) and models in [`memory/models.py`](app/memory/models.py).
- Validate incoming data before memory reads/writes and handle missing records gracefully.

## Security Requirements

- **Input Validation:** All endpoints must use Pydantic models; reject malformed data early.
- **Timeout & Retry:** Wrap outbound HTTP calls with `httpx.AsyncClient` and configure timeouts and retry logic.
- **Environment Secrets:** Access API keys, database URLs, and other secrets only via environment variables exposed in [`config.py`](app/config.py).
- **Async Error Handling:** Use `try/except` blocks around async operations and raise custom exceptions from [`exceptions.py`](app/exceptions.py) as needed.

## Testing

- Add unit tests under `tests/api/` mirroring router and service structure.
- Each new endpoint must include tests for success and error cases.
