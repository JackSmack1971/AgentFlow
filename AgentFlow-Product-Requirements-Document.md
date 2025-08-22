# AgentFlow — Product Requirements Document (Aligned with AGENTS.md & Rulesets)

> **Ground truth alignment:** This PRD is harmonized with the repository’s operating standard defined in **AGENTS.md** and the 15 canonical rulesets (FastAPI, FastAPI+Pydantic, LangGraph, Pydantic-AI, Mem0, R2R, Python MCP SDK, Storage Backends, Next.js+TypeScript, TypeScript 5.x, React 18, Docker Compose, Postman, Biome, GitHub Workflows). Sections marked **\[Hard Constraint]** are non-negotiable engineering constraints enforced by CI and code review.

---

## 0) Executive Summary

**Market**: The AI agent development platform market is rapidly expanding (multi-\$B today with strong CAGR). Enterprises are actively piloting autonomous and semi-autonomous agents.

**Product Vision**: AgentFlow is a developer-first, production-grade platform unifying **LangGraph (stateful orchestration)**, **Pydantic-AI (typed agents)**, **Mem0 (multi-level long-term memory)**, **R2R (advanced RAG)**, **MCP (standardized tools)**—all surfaced through a modern **Next.js/React 18 + TypeScript** UI and **FastAPI** backend.

**Business Case**: By standardizing infra, memory, orchestration, and RAG under typed, validated interfaces, AgentFlow eliminates 60–80% of glue work and de-risks enterprise deployment.

**Positioning**: Unlike fragmented stacks, AgentFlow is **opinionated and integrated** with strict security, CI gates, and production patterns encoded as rulesets.

> **Note on scope correction:** Previous references to “AG2” are **removed** from the MVP scope. Only frameworks with first-class rulesets are in scope: **LangGraph, Pydantic-AI, Mem0, R2R, MCP, FastAPI, Next.js/TS**. (AG2 may be evaluated post-MVP.)

---

## 1) Problem Statement & Market Validation

### 1.1 Core Problems

1. **Memory Management**: durable user/session/agent memory; contradiction handling; isolation; low-latency retrieval.
2. **Workflow Orchestration**: stateful, resumable, checkpointed agent graphs; error recovery; streaming UX.
3. **Tool Standardization**: unified tool protocol (MCP), discovery, permissions, auditability.
4. **Knowledge Integration**: robust ingestion, hybrid & KG search, provenance, freshness control.

### 1.2 Validation Signals

* Enterprise pilots emphasize **security, auditability, isolation**, and **typed interfaces** over experimentation-only stacks.
* Developer surveys cite **memory correctness**, **integration complexity**, and **prod readiness** as top blockers.

---

## 2) Product Vision & Objectives

### 2.1 Vision

> **“The definitive, typed, production-grade platform for building stateful, memory-aware AI agents—secure by default, fast by design, and governed by code.”**

### 2.2 12-Month Objectives

* **Productivity**: 60–80% dev-time reduction vs. custom integration.
* **Performance SLOs**: p95 < **2s** simple flows; < **5s** complex multi-step; memory reads p95 < **100ms**; RAG fetch p95 < **500ms**.
* **Reliability**: 99.5% uptime (target 99.9%).
* **Adoption**: 10k developers, 500+ prod deployments.

---

## 3) Users & Journeys

### 3.1 Personas

* **Senior AI/ML Engineer** (primary): needs typed agents, reliable memory, strong CI gates.
* **Technical PM / Platform Eng**: prioritizes templates, audit logs, deployment sanity.
* **R\&D Teams**: require safe sandboxes with reproducible experiments.

### 3.2 First-Agent Critical Path (Target ≤ 45 min)

1. **Bootstrap** (5m): clone + `compose up` → healthchecks pass.
2. **Template** (10m): choose “Support Agent” template (typed outputs).
3. **Memory** (10m): enable Mem0 scopes (user/session/agent), isolation verified.
4. **RAG** (10m): upload docs; ingestion shows progress; test hybrid search.
5. **Deploy & Test** (10m): run Postman suite; publish internal URL.

---

## 4) System Architecture (Authoritative)

### 4.1 High-Level Diagram

```
Next.js (App Router, React 18, TS 5.x, Biome)
   └─ UI: Chat, Agent Builder, Memory Browser, KB Manager
FastAPI (Pydantic v2) + MCP Server
   └─ Routers: /agents, /runs, /memory, /kb, /tools, /health
LangGraph Orchestrator (checkpoint: Postgres/Redis; store: Store API)
Pydantic-AI Agents (typed outputs, tool registry, validators, retries)
Mem0 (user/session/agent scopes, contradiction resolution)
R2R (ingestion APIs, hybrid/KG retrieval, streaming RAG)
Storage: PostgreSQL (durable), Redis 7 (ephemeral/queues), Qdrant (vectors)
Ops: Docker Compose (healthchecks, non-root), GH Actions CI, Postman/Newman
```

### 4.2 **\[Hard Constraint]** Backend Patterns (FastAPI + Pydantic v2)

* Strict separation: request (`*Create`, `*Update`) vs. response (`*Response`) models.
* Centralized `dependencies.py` (settings via `BaseSettings` + `@lru_cache`).
* Global exception handlers; precise `HTTPException` codes.
* Async I/O only; pooled DB/HTTP clients; pagination; CORS/Middleware hygiene.

### 4.3 **\[Hard Constraint]** Orchestration (LangGraph)

* **Typed** `StateGraph` with invariants; **persistent** checkpointer (Postgres/Redis) in prod.
* **Store** for cross-thread memories; namespace: `("memories", user_id)`.
* `configurable={user_id, thread_id}` mandatory; stream via `stream_mode="values|updates|debug"`.
* Node resiliency (try/except, partial state); summarize/prune long histories.

### 4.4 Agents (Pydantic-AI)

* Module-scope construction; tools with docstrings and typed args.
* **Structured outputs** (Pydantic models or `NativeOutput`); `@agent.output_validator` + `ModelRetry` for recoverables.
* Multi-provider fallback; streaming outputs; deterministic tests.

### 4.5 Memory (Mem0)

* Scopes: **user / session / agent** with isolation; contradiction resolution; explicit retention/erasure.
* Write only high-signal memories; dedupe; summarize.
* Reads and writes occur **inside graph nodes/tools** with policy hooks.

### 4.6 Knowledge (R2R)

* Ingestion: PDF/DOCX/TXT/MD/HTML; batch ingest + progress tracking.
* Retrieval: **hybrid (BM25+vector)** by default; optional **KG search** when relationships matter.
* RAG responses include **source attributions** & **relevance scores**; stream tokens for UX.

### 4.7 Tools (MCP)

* Python MCP SDK or FastMCP server; **streamable HTTP** transport for cloud; OAuth2.1 capable.
* Tool discovery, schemas, permissions, audit.
* Progress reporting: `ctx.report_progress()`; `ctx.info()/warning()/error()`.

### 4.8 **\[Hard Constraint]** Storage & Security

* **PostgreSQL**: TLS (`sslmode=verify-full`), SCRAM-SHA-256 auth; pooled connections.
* **Redis 7**: TLS, ACLs, sensible expirations; queues/rate-limits.
* **Qdrant**: HTTPS + API key; HNSW tuned; indexing thresholds; memory monitoring.
* **Secrets** never in code; env/secret stores only.

---

## 5) Functional Requirements

### 5.1 MVP Features

* **Agent Builder**: visual nodes (LangGraph) + typed outputs (Pydantic-AI).
* **Runs & Traces**: streaming outputs, step traces, errors with fix hints.
* **Memory Browser**: scoped views (user/session/agent), search, dedupe, redact/delete.
* **Knowledge Base**: upload → parse → chunk → embed → index; progress UI; re-indexing on updates.
* **Tooling**: MCP tool registry, permissioning, test console.
* **Auth**: API keys + JWT; role-based access to agents, KB, tools.
* **Ops UI**: health, queues, checkpoint stats, DB/vector status.

### 5.2 Post-MVP

* Multi-agent teams (supervisor/handoff patterns).
* Enterprise SSO (SAML/OIDC), audit trails, data residency.
* Template marketplace; organization workspaces.

---

## 6) Non-Functional Requirements (Bound to Rulesets)

### 6.1 Performance SLOs

* **Simple** flows p95 < **2s**; **complex** p95 < **5s**.
* Mem reads p95 < **100ms**; writes p95 < **200ms**.
* RAG retrieval p95 < **500ms** on warm cache.
* Frontend TTI < **2.5s** on mid-tier laptop.

### 6.2 Reliability & Scalability

* 99.5% uptime (target 99.9%); horizontal scaling; resilient restarts (checkpointed).
* Back-pressure on queues; exponential backoff on external calls.

### 6.3 Security & Compliance

* TLS 1.2+ everywhere (target 1.3); mTLS where required.
* RBAC; audit logging of memory/KB/tool access.
* GDPR/CCPA controls: export, rectification, erasure; privacy by default.

---

## 7) Frontend Requirements (Next.js, React 18, TS 5.x)

* **App Router**; **Server Components** by default; `'use client'` only when necessary.
* **TypeScript Strict**: `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitOverride`, `useDefineForClassFields`, `verbatimModuleSyntax`, `import type`.
* Error/loading boundaries per route; Suspense streaming; `next/image` + `next/font`; dynamic imports for heavy charts.
* Biome is **single source of truth** for lint/format. **\[Hard Constraint]**

---

## 8) DevEx, Tooling & CI/CD (Quality Gates)

### 8.1 Local

* `compose.yaml` brings up Postgres/Redis/Qdrant/R2R/API/Frontend; **healthchecks mandatory**; non-root users. **\[Hard Constraint]**
* Uvicorn auto-reload in dev; Next.js dev server with strict TS.

### 8.2 CI (GitHub Actions) — **Fail the build on any gate**

1. **Biome** lint/format (warnings in protected dirs = fail).
2. **Type-check**: `tsc --noEmit`.
3. **Python**: ruff (if configured), unit tests, mypy/pyright (if configured).
4. **API Tests**: Postman/Newman with thresholds; HTML report artifact.
5. **Builds**: Next.js build; optional bundle analyzer.
6. **Compose Smoke** (optional): healthchecks green before pass.

### 8.3 Postman / Newman

* Collections + environments stored under `/postman`; **SSL/TLS on** in prod; environment secrets masked; threshold assertions per route (status, schema, latency).

---

## 9) API Surface (Illustrative)

* `GET /health` (liveness), `GET /ready` (readiness).
* `/agents`: CRUD agent definitions (typed), publish/draft flags.
* `/runs`: start/stream/inspect runs; `user_id`, `thread_id` are **required**.
* `/memory`: search/list/write/delete by scope; export.
* `/kb`: upload with progress; list docs; reindex.
* `/tools`: MCP registry, permissions, dry-run.
* `/auth`: login, token introspection, API keys.

---

## 10) Testing Strategy

* **Unit**: node/tool functions, validators, schemas, auth deps.
* **Contract**: Pydantic models (I/O) and MCP tool schemas.
* **API**: Postman suites (success + error paths), latency gates.
* **E2E**: scripted conversations verifying memory writes, RAG provenance, structured outputs, retries.
* **Load**: warm-cache p95 validation on hot endpoints; Redis/Qdrant pool sizing.

---

## 11) Implementation Plan (16 Weeks)

**Phase 1 — Foundation (W1–W4)**

* FastAPI skeleton, settings/DI, health/ready, auth.
* LangGraph base graph with Postgres/Redis checkpointer + Store.
* Mem0 minimal wiring (scoped memory) and policies.
* Compose stack with healthchecks; TLS in dev where practical.
* Basic Next.js shell (App Router) + Biome + strict TS.
* Postman collections scaffold; CI gates wired.

**Gate A (W4):** graph checkpointing works; memory isolation proven; Postman suite green.

**Phase 2 — Core Features (W5–W8)**

* Agent Builder (typed outputs + validators); streaming runs & traces.
* KB ingest (R2R) with progress; hybrid search; basic KG toggle.
* Memory Browser (search/dedupe/redact).
* MCP registry + test console.
* E2E tests; performance pass on warm cache.

**Gate B (W8):** MVP feature-complete; all CI gates enforced.

**Phase 3 — Polish & Enterprise (W9–W12)**

* Multi-agent patterns; error recovery UX; admin dashboards.
* SSO (OIDC), RBAC, audit logs; export/erase flows.
* Deployment guides; observability (metrics/logs/traces).

**Gate C (W12):** Beta-ready; security review no criticals; perf SLOs met.

**Phase 4 — Launch Prep (W13–W16)**

* Scalability tuning; rate limits; chaos tests.
* Docs/videos; template gallery; pilot onboarding.

**Gate D (W16):** Launch decision.

---

## 12) Metrics & KPIs

**Performance**: p95 latency, memory/RAG timings, stream start time, queue depth.
**Reliability**: uptime, error budgets, restart recovery times.
**Quality**: CI pass rate, lint debt, typed-output conformance, Postman success %.
**Adoption**: TTF-Agent, weekly active developers, deployed agents, KB size, tool count.

---

## 13) Risks & Mitigations

* **Integration Drift** (framework updates): lock versions; renovate rules; contract tests; canary CI.
* **Memory Scale**: early load tests; summarization + TTL; vector sharding; observability.
* **MCP Ecosystem Variance**: ship core tools in-house; strict schemas; fallbacks for non-MCP APIs.
* **Security Posture**: TLS by default; secrets scanning; quarterly pentests; incident drillbooks.

---

## 14) Compliance & Security (Operationalized)

* **Data rights**: export/rectify/erase endpoints; admin workflows.
* **Encryption**: AES-256 at rest; **TLS 1.2+** in transit; KMS-backed keys.
* **Access**: RBAC, API keys, JWT; least-privilege; audit trails.
* **Infra**: non-root containers; read-only FS where possible; `no-new-privileges`; Compose **without** `version:` or `container_name`; **healthchecks required**. **\[Hard Constraint]**

---

## 15) Design Constraints (from AGENTS.md & Rulesets)

1. **Typed Everything**: Pydantic v2 models, TS strict, typed tool I/O, typed LangGraph state.
2. **Checkpointed by Default**: Postgres/Redis checkpointer; in-memory only for unit tests.
3. **Memory Isolation**: user/session/agent scopes; contradiction resolution; erase on request.
4. **RAG Provenance**: source attributions + relevance scores in responses.
5. **MCP Standard**: tool discovery, schemas, permissions, audit; streamable HTTP for cloud.
6. **Compose Hygiene**: healthchecks, non-root, secrets, internal networks, resource limits.
7. **CI Gates**: Biome → tsc → Python tests → Newman → builds; any failure = block merge.

---

## 16) Acceptance Criteria (Key Epics)

### Epic A: First Agent

* [ ] Template creates a **typed** agent (Pydantic-AI) with streaming.
* [ ] LangGraph run uses `{user_id, thread_id}`; checkpoint saved; resume works.
* [ ] Postman tests pass with p95 < 2s (simple).
* [ ] Biome/tsc gates green.

### Epic B: Memory

* [ ] Mem0 reads/writes by scope; contradiction test passes.
* [ ] Memory browser can search/dedupe/redact; GDPR erase flow works.
* [ ] Mem read p95 < 100ms (warm).

### Epic C: Knowledge

* [ ] Upload supports PDF/DOCX/TXT/MD/HTML; progress visible.
* [ ] Hybrid search default; KG toggle; provenance + relevance in responses.
* [ ] RAG fetch p95 < 500ms (warm).

### Epic D: Tools

* [ ] MCP tool registry; docstring-based schema; permission prompts.
* [ ] Tool dry-run console with request/response capture.
* [ ] Audit log entries for tool usage.

---

## 17) Roadmap After Launch (Guided by Rulesets)

* **Teams & Marketplace**: multi-agent templates; sharing; versioned artifacts.
* **Deeper Observability**: per-node timings; memory/RAG hits; tool SLIs.
* **Enterprise**: SAML/SOC2 pathways; private KB syncers; DLP policies.
* **Multimodal**: vision/audio tools with typed outputs; streaming UI upgrades.

---

## 18) Document Control

* **Version**: 1.1 (Aligned to AGENTS.md / rulesets)
* **Last Updated**: August 21, 2025
* **Next Review**: September 21, 2025
* **Change Log**:

  * 1.1 — Removed AG2 from MVP scope; added hard constraints; expanded CI gates and Compose rules; tightened storage security to TLS/verify-full; clarified typed outputs & MCP requirements.

---

### Alignment Notes (Traceability to AGENTS.md)

* **§4.2 / §4.3 / §4.8** map to AGENTS.md **Backend/Orchestration/Storage** non-negotiables.
* **§7** reflects Next.js/React/TS strictness and Biome primacy.
* **§8** encodes GitHub Actions + Postman/Newman gates.
* **§6** mirrors SLOs and performance thresholds in AGENTS.md.
* **§10 / §14 / §15** consolidate security/compliance and Compose rules into acceptance gates.

> If any real repository code contradicts this PRD, **update the code to match the rulesets**. If a ruleset is outdated, **open a PR to update the ruleset and this PRD together**, citing the rationale.
