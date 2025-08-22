# AgentFlow — Spec-Driven PRD (Updated with mem0-ai, R2R, FastAPI, Python-MCP SDK, and PydanticAI Rules)

> **Audience:** OpenAI Codex (treat this PRD as executable ground truth).  
> **Change scope:** Tightens contracts and NFRs to **exactly** follow the uploaded rulesets for memory (mem0-ai), RAG (R2R), API (FastAPI), tools (Python MCP SDK), and orchestration/types (PydanticAI).

---

## 0) Codex Execution Rules (Read First)

1) **Spec precedence.** Enforce everything in this PRD **and** the referenced rulesets; when unspecified, return:
   ```json
   { "code":"SPEC_GAP","error":"Unspecified behavior","detail":{"section":"<path>" } }
````

2. **Deterministic I/O, probabilistic text.** All API/tool payloads MUST validate against schemas; only model text may vary.

3. **Guardrails first.** If a request violates §6, return **POLICY\_REFUSAL** (template in Appendix).

4. **Environment conformance.** Pin and configure dependencies per rule files (e.g., FastAPI `0.115.12`).

5. **No MCP JSON-RPC batching.** Use single-call semantics with structured `inputSchema`/`outputSchema`.

---

## 1) Problem & Vision

* **Problem:** Teams waste time wiring memory, RAG, tools, and validation.
* **Vision:** A production-ready agent platform: FastAPI gateway + LangGraph + **mem0** memory + **R2R** knowledge + **MCP** tools + **PydanticAI** typed agents, backed by Postgres/Redis/Qdrant/Neo4j—**with ruleset-verified contracts**.

---

## 2) Goals & Success Metrics

* **Latency:** P95 ≤ 1500 ms for simple `/agents/{id}/run` (warm path).
* **Reliability:** CI must pass: `/health` (FastAPI), mem0 config validation, `R2R.health() == ok`, MCP `list_tools`/`call_tool` contract tests.
* **Quality:** RAG answers include **citations\[]**; memory ops persist across session; all agent outputs are **Pydantic-validated** types.
* **Security:** JWT auth, non-wildcard CORS, HTTPS in prod.

---

## 3) Personas & Scenarios

* **Indie Dev / Power User:** fastest path to a working agent, reproducible runs, minimal ops.
* **Team Lead:** reliability, observability, guardrails, deployment hygiene.
* **Integrator:** must be able to 1) ingest documents to R2R and verify health, 2) configure mem0 with **matching embedding dimensions** and **correct vector store provider names**, 3) expose MCP tools with **outputSchema**.

**Key Scenarios**

1. **Create & Run an Agent**

   * Intent: Define config (model, system prompt), run with input, get result + trace.
   * Ideal Output: JSON with `result`, `trace_id`, `memory_writes`, `tool_calls[]`, `latency_ms`.

2. **Add Knowledge & Retrieve**

   * Intent: Ingest docs to R2R, run query that cites sources.
   * Ideal Output: Answer + `citations[]` (doc ids/urls) + confidence.

3. **Use Tools via MCP**

   * Intent: Call a `sql.query` tool; retries on transient failures; idempotent logs.
   * Ideal Output: Structured tool result + inclusion in trace.

---

## 4) Functional Requirements — Spec Tightening

### 4.1 Capabilities

* **Agent lifecycle:** create/read/update/delete; run; list runs; fetch traces.
* **Memory (mem0):** platform (`MemoryClient`) **or** OSS (`Memory`) modes are mutually exclusive; include `"version":"v1.1"` in config; validate provider name and dims **before init**.
* **Knowledge (R2R):** client reachable; supports ingestion, hybrid/graph search, and RAG; expose **health** and TOML-backed config.
* **Tools (MCP):** FastMCP server; every tool has docstring and **outputSchema**; progress reporting for long tasks; HTTP or STDIO transports per deployment.
* **Agents (PydanticAI):** define `deps_type`, reuse singletons, declare `output_type` (prefer **NativeOutput** when supported), and implement `@agent.output_validator`.

### 4.2 API (FastAPI) — Required shape & setup

* **Structure:** routes in `routers/`, `config.py` with Pydantic Settings; OpenAPI path toggled via env; JWT dependency.
* **Version pin:** `fastapi==0.115.12`.
* **Health endpoint:** `/health` returns `{"status":"healthy","timestamp":...}`.

### 4.3 Memory (mem0) — Config & ops

* **OSS config** sample (**Qdrant** or **ChromaDB**), with **embedding\_model\_dims = 1536** for OpenAI `text-embedding-3-small`; **use `"chromadb"` not `"chroma"`**.
* **Platform client:** `MemoryClient(api_key=...)` with error handling.
* **Ops:** `add`, `search`, `get_all` with filters, `update`, `delete`, `delete_all`; always handle empty results.

### 4.4 Knowledge (R2R) — Ingest, retrieve, graph

* **Health check** before use; ingestion supports rich metadata; hybrid + KG search, streaming RAG optional.

### 4.5 Tools (MCP) — Contracts

* **List tools** returns JSON with tool schemas; **call\_tool** returns data that **matches `outputSchema`**; include progress messages for long operations.
* **Transports:** STDIO for local; **streamable HTTP** for cloud/serverless.

### 4.6 Agents (PydanticAI) — Strong typing & retries

* **Output types:** `output_type=...` (Pydantic model or Union); prefer `NativeOutput` when model supports; add validator; use `ModelRetry` for recoverable errors; **tenacity** retries around runs.

---

## 5) Bounded Acceptance Criteria (Must / Should / Must Not)

### 5.1 Platform & API

* **Must:** `/health` returns 200 with body above; **OpenAPI toggled** via settings (disabled in prod).
* **Must:** Auth via JWT dependency on protected routers; non-wildcard CORS.
* **Must Not:** run in debug/reload in production.

### 5.2 Memory (mem0)

* **Must:** Reject startup if `embedding_model_dims` ≠ embedder output, or provider name is `"chroma"` (should be `"chromadb"`).
* **Must:** Exactly one mode active: Platform **or** OSS.
* **Should:** Log operation durations for adds/searches.
* **Must Not:** Add blank content or missing `user_id`. (Validate.)

### 5.3 Knowledge (R2R)

* **Must:** `client.health().status == "ok"` prior to first RAG call.
* **Must:** RAG responses include `citations[]`; hybrid search enabled by default; KG search toggle available.
* **Should:** Streaming RAG for long responses.

### 5.4 Tools (MCP)

* **Must:** Each tool: docstring + `inputSchema` + `outputSchema`; progress via `ctx.report_progress`.
* **Must Not:** JSON-RPC batching.

### 5.5 Agents (PydanticAI)

* **Must:** Define `deps_type`, reuse agent singletons, declare `output_type` and `@agent.output_validator`.
* **Should:** `ModelRetry` in tools and runs; `tenacity` wrapper with backoff.

---

## 6) Ethical & Safety Guardrails

* **Privacy:** Secrets only in env; redact PII in traces; HTTPS in prod.
* **Bias & Harm:** Neutral tone; refuse unsafe requests with `POLICY_REFUSAL`.
* **Scope Refusals:** Medical/legal/financial advice beyond citation.

**Refusal Envelope**

```json
{ "code":"POLICY_REFUSAL","reason":"HARMFUL_CONTENT","message":"I can’t assist with that request." }
```

---

## 7) Data & Environment Requirements

* **FastAPI:** `fastapi==0.115.12`; Python ≥3.11 recommended; Pydantic Settings; structured logging.
* **mem0:** `MEM0_API_KEY` (platform), correct vector store provider, dims=1536 for OpenAI `text-embedding-3-small`.
* **R2R:** Base URL (default `http://localhost:7272`), `R2R_CONFIG_NAME`/`R2R_CONFIG_PATH` as needed; TOML config for DB/embedding/LLM.
* **MCP:** Install `mcp[cli]`; set `FASTMCP_DEBUG=false` in prod.

---

## 8) Non-Functional Requirements (NFRs)

* **Security:** JWT auth, CORS allow-list, HTTPS.
* **Observability:** Log durations for mem0 ops; R2R logging of RAG; API structured logs.
* **Deployability:** Uvicorn prod CMD; Docker/compose for R2R; MCP stateless HTTP for serverless.

---

## 9) Test & Eval Plan (CI-enforced)

### 9.1 Smoke

* `GET /health` → 200 `{"status":"healthy"...}`.
* **R2R health:** `client.health()["status"] == "ok"`.
* **mem0 config check:** provider name and dims validation pass; reject `"chroma"`.

### 9.2 Contract Tests

* **MCP**: `list_tools` items have `inputSchema` & `outputSchema`; `call_tool` output validates.
* **Agents**: Run returns Pydantic-validated `output_type`; validator invoked.

### 9.3 Functional

* **Memory:** `add` → `search` yields content; handles empty results path.
* **RAG:** RAG query includes `citations[]` with hybrid search settings.

### 9.4 Resilience

* **Retries:** `tenacity` backoff around agent.run; tool `ModelRetry` path.

---

## 10) Example Configs & Snippets

### 10.1 FastAPI Settings

```python
# Pydantic Settings; disable OpenAPI in prod via env
app = FastAPI(openapi_url=get_settings().openapi_url)
```

### 10.2 mem0 (OSS) — Qdrant with OpenAI embeddings

```python
config = {
  "version": "v1.1",
  "vector_store": {"provider":"qdrant","config":{"host":"localhost","port":6333,"collection_name":"memories","embedding_model_dims":1536}},
  "llm": {"provider":"openai","config":{"model":"gpt-4o-mini"}},
  "embedder": {"provider":"openai","config":{"model":"text-embedding-3-small"}}
}
memory = Memory.from_config(config)
```

### 10.3 R2R — Health & Basic RAG

```python
client = R2RClient(base_url="http://localhost:7272")
assert client.health()["status"] == "ok"
resp = client.retrieval.rag(
  query="What is AgentFlow?",
  rag_generation_config={"model":"gpt-4o-mini","temperature":0.0,"max_tokens_to_sample":2048},
  search_settings={"use_hybrid_search":True,"limit":25}
)
```

### 10.4 MCP — Tool with outputSchema & progress

```python
@mcp.tool()
async def sql_query(sql: str, ctx: Context) -> dict:
  """Execute read-only SQL and return rows+count."""
  await ctx.info("Running SQL")
  return {"rows":[{"n":1}], "count":1}
```

### 10.5 PydanticAI — Typed output + validator

```python
class RunResult(BaseModel):
  result: str
  confidence: float

agent = Agent('openai:gpt-4o', output_type=RunResult)

@agent.output_validator
async def ensure_conf(ctx: RunContext[Any], out: RunResult) -> RunResult:
  if out.confidence < 0.3:
      raise ModelRetry("Low confidence; try again with retrieval.")
  return out
```

---

## 11) Release Criteria

* **Alpha → Beta:** All §9 tests green; MCP tools have output schemas; mem0 config validator enforced; R2R health + ingestion OK.
* **Beta → GA:** CORS allow-list; HTTPS; CI performance & error budgets; OpenAPI disabled in prod; rolling deploy for R2R/DB.

---

## 12) Appendix — Error Templates

```json
{ "code":"BAD_REQUEST","error":"Invalid mem0 config: provider='chroma'","detail":{"expected":"chromadb"} }
{ "code":"SPEC_GAP","error":"Endpoint not defined: /agents/{id}/debug","detail":{"proposal":"Add GET for recent steps"} }
{ "code":"POLICY_REFUSAL","error":"HARMFUL_CONTENT","detail":{"category":"security"} }
```
