# AgentFlow — Functional Requirements Document (FRD)

**Aligned to AGENTS.md & canonical rulesets**

> This FRD supersedes the prior draft and binds functionality to the repository’s **AGENTS.md** and the 15 ground-truth rulesets (FastAPI, FastAPI+Pydantic, LangGraph, Pydantic-AI, Mem0, R2R, Python MCP SDK, Storage Backends, Next.js+TypeScript, TypeScript 5.x, React 18, Docker Compose, Postman, Biome, GitHub Workflows). Items tagged **\[Hard Constraint]** are non-negotiable gates enforced by CI and code review.

---

## Document Information

| Field                | Value                                                  |
| -------------------- | ------------------------------------------------------ |
| **Document Title**   | AgentFlow Functional Requirements Document (FRD)       |
| **Document ID**      | FRD-AGENTFLOW-2025-001                                 |
| **Version**          | **1.1**                                                |
| **Date**             | **August 21, 2025**                                    |
| **Status**           | Draft for Approval                                     |
| **Project**          | AgentFlow AI Agent Development Platform                |
| **Source Documents** | **AGENTS.md (root)**, PRD v1.1 (aligned), Rulesets x15 |
| **Approval**         | Pending                                                |

## Document Control

| Role         | Name                | Date         | Signature |
| ------------ | ------------------- | ------------ | --------- |
| **Author**   | Development Team    | Aug 21, 2025 |           |
| **Reviewer** | Technical Lead      |              |           |
| **Approver** | Product Manager     |              |           |
| **Approver** | Engineering Manager |              |           |

### Change Log (since v1.0)

* Removed **AG2** from MVP scope; standardized on **LangGraph, Pydantic-AI, Mem0, R2R, MCP, FastAPI, Next.js/TS**.
* Codified **\[Hard Constraint]** sections: TypeScript strict + **Biome-only** lint/format; **Docker Compose hygiene**; **TLS everywhere**; **LangGraph checkpointing**; **structured outputs**; **Postman/Newman** CI gates.
* Replaced Elasticsearch dependency with **R2R hybrid/KG retrieval** and **Qdrant** vectors.
* Upgraded infra baselines: **PostgreSQL 17.x**, **Redis 7.x**, **Qdrant (HTTPS)**.

---

## 0) Executive Summary (scope alignment)

AgentFlow delivers a typed, production-grade agent platform unifying **LangGraph (stateful orchestration + checkpoints)**, **Pydantic-AI (typed agents + tools)**, **Mem0 (multi-level long-term memory)**, **R2R (hybrid/KG RAG)**, and **MCP (standardized tools)** behind a **FastAPI** backend and **Next.js/React 18 + TS 5.x** frontend. Performance SLOs mirror AGENTS.md: **simple p95 <2s**, **complex p95 <5s**, **memory read p95 <100ms**, **RAG p95 <500ms**.

---

## 1) Scope and Objectives

### 1.1 Business Objectives

* Reduce dev time **60–80%** vs. custom integration.
* Meet **p95 latency** & **99.5% uptime** SLOs; unlock enterprise pilots and production use.

### 1.2 System Scope (MVP)

* Agent Builder (visual LangGraph nodes + typed outputs)
* Runs & Traces (streaming + debug)
* Multi-level Memory (Mem0: user/session/agent; contradiction handling)
* Knowledge Base (R2R ingestion, hybrid search, optional KG, provenance)
* MCP Tooling (registry, test console, permissions)
* AuthZ/AuthN (API Keys + JWT, RBAC)
* Deployment & Monitoring (Compose, health, metrics)
* CI Quality Gates (Biome, tsc, Python tests, Newman)

**Out of MVP / Post-MVP:** Multi-agent teams, SSO (SAML/OIDC), marketplace, advanced compliance packs.

### 1.3 Core Problem Resolution

* Memory isolation & correctness; low-latency retrieval
* Resumable, checkpointed workflows with error recovery
* Tool standardization via MCP + permissions/audit
* RAG with attribution and relevance scores

---

## 2) Functional Requirements

### FR-1000: Identity, Organizations & RBAC

**FR-1001 Authentication & Sessions** — **Must**

* Email verification; password policy; API keys; JWT tokens.
* **SLO:** auth response <**500ms**.
* **\[Hard Constraint]** All secrets in **env/secret stores**; TLS 1.2+ (target 1.3).
* **Acceptance:** registration <30s; reset email <2m; session timeout configurable.

**FR-1002 Organizations & Roles** — **Should**

* Orgs with RBAC: Admin/Developer/Viewer + **custom roles**.
* Resource-scoped permissions for **agents, KBs, tools, runs, memories**.
* Real-time usage/billing per org.
* **Acceptance:** per-resource ACL checks <**100ms**.

---

### FR-2000: Agent Creation, Configuration & Testing

**FR-2001 Agent Builder (Visual)** — **Must**

* Node-based editor for LangGraph: conditions, branches, tool calls.
* Guided wizard; personality/prompt controls; environment bindings.
* **SLO:** UI load <**2s**; create basic agent <**5m**.
* **\[Hard Constraint]** Graph must be compiled with **persistent checkpointer** in non-test contexts.

**FR-2002 Template Library** — **Must**

* ≥10 templates (support, research, analyst, etc.); preview; derive & save.
* Deploy from template <**2m**.

**FR-2003 Config & Environments** — **Must**

* Dev/Staging/Prod separation; config validation; API key vaulting; import/export (JSON/YAML).
* **\[Hard Constraint]** Pydantic v2: **separate input vs response** models, `extra='forbid'`.
* Invalid configs **blocked** at save time.

**FR-2004 Testing & Debug** — **Must**

* Live test console; streaming; step-by-step traces; automated scenario tests; perf profiler.
* Shareable test sessions (URL).
* **SLO:** test round-trip <**2s** (simple).

**FR-2005 Structured Outputs** — **Must**

* **Pydantic-AI** agents emit **typed** outputs (`NativeOutput` when supported).
* Output validators + **retry on recoverables**.
* Contract tests per agent.
* **\[Hard Constraint]** No untyped free-text for API surfaces.

---

### FR-3000: Memory (Mem0)

**FR-3001 Multi-Level Scopes** — **Must**

* Scopes: **user, session, agent**; isolation by default; inheritance rules explicit.
* Namespacing: `("memories", user_id)` in Store.
* **SLO:** retrieval p95 <**100ms**; writes p95 <**200ms**.

**FR-3002 CRUD & Semantic Search** — **Must**

* Auto-extraction (high-signal facts); manual edit; tags; bulk import/export.
* Semantic search over memories; dedupe.
* Clear failure modes + idempotency.

**FR-3003 Contradiction Handling** — **Must**

* Detect conflicting facts; confidence scoring; auto-resolve policy + manual review; version history.
* Notify on high-impact changes.

**FR-3004 Analytics & Retention** — **Should**

* Usage heatmaps; effectiveness scoring; cleanup recommendations; retention/TTL policies; reports (CSV/JSON, PDF).

---

### FR-4000: Orchestration (LangGraph)

**FR-4001 Visual Workflow Editor** — **Must**

* Drag-drop nodes, branching, parallel fan-out/fan-in; real-time validation.
* Simulation with **execution path** and timings.

**FR-4002 State & Checkpointing** — **Must**

* Persistent state via **Postgres/Redis** savers; resume after restart; rollback/replay.
* **\[Hard Constraint]** Every run **requires** `{user_id, thread_id}` in config.
* **SLO:** recovery <**5s**.

**FR-4003 Errors & Recovery** — **Must**

* Retries (exponential backoff), fallbacks, human-in-the-loop hooks, graceful degradation, alerts.

**FR-4004 Multi-Agent Patterns** — **Could** (Post-MVP)

* Delegation/handoff; team metrics; hierarchical supervisors.

---

### FR-5000: Knowledge Base (R2R)

**FR-5001 Upload & Processing** — **Must**

* Drag-drop **PDF/DOCX/TXT/MD/HTML**; progress bars; batch ingest; metadata extraction.
* **SLO:** 100 MB doc set processed ≤ **5m** (parallelized).

**FR-5002 Retrieval & RAG** — **Must**

* **Hybrid search (BM25 + vectors)** by default; **KG search** optional.
* Responses include **source attributions** + **relevance scores**.
* **SLA:** p95 <**500ms** (warm cache).
* No dependency on Elasticsearch; use **R2R index + Qdrant** vectors.

**FR-5003 Organization & Access** — **Must**

* Folders, tags, collections; org-level sharing; per-folder/Doc ACLs.

**FR-5004 External Connectors** — **Should**

* Notion/Confluence/SharePoint/Drive sync; webhooks; selective filters; near-real-time updates.

**FR-5005 Knowledge Graph** — **Should**

* Entity/relationship extraction; incremental updates; graph queries (<**1s**); visualization.

---

### FR-6000: Tools (MCP)

**FR-6001 MCP Protocol** — **Must**

* **Full MCP** compliance; tool discovery/registration; STDIO + **streamable HTTP**; OAuth2.1-ready.
* Registry UI; health tools.

**FR-6002 Custom Tools** — **Must**

* SDK for code-first tools; visual builder for simple wrappers; versioning/rollback; test harness; docs generation.

**FR-6003 Tool Security** — **Must**

* Sandboxed execution; fine-grained permissions; audit logs; rate limits/quotas; org/user scoping.
* Enforcement <**1s** from violation to block.

**FR-6004 Tool Performance** — **Should**

* Parallelism; result caching (TTL); prioritization/queues; perf dashboards.

---

### FR-7000: Deployment, Ops & Monitoring

**FR-7001 Infrastructure (Local & Cloud)** — **Must**

* **Docker Compose** baseline for local: **no `version:`**, **no `container_name`**, **non-root `user`**, **healthchecks mandatory**, internal networks, resource limits, secrets. **\[Hard Constraint]**
* Baselines: **PostgreSQL 17.x (TLS verify-full)**, **Redis 7.x (TLS + ACL)**, **Qdrant (HTTPS + API key)**, **R2R service**.
* Disaster recovery: daily backups; 30-day retention.

**FR-7002 App Deployment** — **Must**

* One-click deploy (per env); canary; rollback <**2m**; pipeline blocks on CI gates.

**FR-7003 Health & Observability** — **Must**

* Liveness `/health`, readiness `/ready`; metrics/logs/traces; SLA monitoring; alerting (email/Slack/webhook).

**FR-7004 Performance Management** — **Must**

* Load balancing + horizontal scale; caching layers; capacity planning; chaos drills.

---

### FR-8000: Analytics & Reporting

**FR-8001 Usage & Product Analytics** — **Must**

* Real-time dashboards (<**3s** load); agent KPIs (latency, accuracy proxies, satisfaction inputs); export (CSV/JSON/API).

**FR-8002 Business Intelligence** — **Should**

* ARR/MRR, cohort retention, predictive 90-day forecasts; executive dashboards (daily refresh).

**FR-8003 System Observability** — **Must**

* Distributed tracing across API→Graph→Memory→RAG→Tools; error budgets; 90-day retention.

---

### FR-9000: Security, Privacy & Compliance

**FR-9001 Security Framework** — **Must**

* **AES-256 at rest**, **TLS 1.2+ (target 1.3)** in transit; KMS/Key Vault; input validation; quarterly pentest with no criticals.

**FR-9002 RBAC & Authorization** — **Must**

* Org roles + custom roles; per-resource ACLs; session policies; audit trails; **decision time <100ms**.

**FR-9003 Compliance & Governance** — **Should**

* GDPR/CCPA: export/rectify/erase; retention policies; auto reports; DPIA templates.

**FR-9004 Privacy Controls** — **Must**

* Data minimization; pseudonymization for analytics/logs; consent management; DSAR ≤ **30 days**.

---

## 3) Integration Requirements

**INT-001 Framework Integration (MVP)** — **Must**

* **LangGraph** (checkpoint: Postgres/Redis; Store API).
* **Pydantic-AI** (typed outputs, validators, retries).
* **Mem0** (user/session/agent scopes; contradiction resolution).
* **R2R** (ingestion, hybrid/KG retrieval, streaming RAG).
* **MCP** (protocol compliance, tool registry).
* **Note:** **AG2 excluded** from MVP.

**Acceptance:** end-to-end runs pass integration tests; data contracts stable; perf within each component SLA.

**INT-002 External Services (Optional)** — **Should**

* External LLMs (OpenAI/Anthropic/others) via provider abstraction; costs & quotas surfaced.
* Research connectors (e.g., web search) **post-MVP** and sandboxed.

**INT-003 Data Layer** — **Must**

* **PostgreSQL 17.x**, **Redis 7.x**, **Qdrant**; file storage for uploads; monthly backup drills with documented RTO/RPO.

---

## 4) User Interface Requirements (Next.js / React 18 / TS 5.x)

**UI-001 Responsive & Accessible** — **Must**

* Desktop/tablet/mobile; WCAG 2.1 AA; keyboard nav; semantic HTML; alt text.

**UI-002 Performance** — **Must**

* Initial load <**3s** (simulated mid-tier); interactions <**100ms**; virtualization for 1000+ items; progress indicators >2s ops.

**UI-003 App Router & Strict TS** — **\[Hard Constraint]**

* App Router; Server Components by default; `'use client'` only when necessary; error/loading boundaries; Suspense streaming.
* **TypeScript**: `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitOverride`, `useDefineForClassFields`, `verbatimModuleSyntax`, `import type`.

**UI-004 Lint/Format** — **\[Hard Constraint]**

* **Biome** is single source of truth; warnings in protected paths **fail CI**.

---

## 5) Performance Requirements

**PERF-001 Latency SLOs** — **Must**

* Simple p95 <**2s**; complex p95 <**5s**; memory read p95 <**100ms**; RAG p95 <**500ms**; UI actions <**100ms**.

**PERF-002 Throughput** — **Must**

* 1000+ concurrent users per instance (target 2000+); 10k+ memory ops/sec (target 50k); 100GB+ KB (target 1TB).

**PERF-003 Availability** — **Must**

* 99.5% uptime (target 99.9%); MTTR <**1h**; auto-failover within **5m**; durability 99.999%.

---

## 6) DevEx & CI/CD Quality Gates

**CI-9001 Lint & Type** — **\[Hard Constraint]**

* **Biome** (TS/JS) → **tsc --noEmit** → Python lint/type (ruff/pyright if configured). Any failure blocks merge.

**CI-9002 API & E2E** — **\[Hard Constraint]**

* **Postman/Newman** suites with status/schema/latency thresholds; artifacts uploaded.
* E2E: conversation scripts validate memory writes, RAG provenance, typed outputs.

**CI-9003 Compose Smoke** — **Should**

* Spin up stack; all **healthchecks green** before pass.

---

## 7) Acceptance Criteria Summary

* **Time-to-First-Agent:** <**5m** (template → deploy).
* **Structured Outputs:** all agent APIs return **Pydantic-typed** payloads; validators active.
* **LangGraph:** runs require `{user_id, thread_id}`; checkpoints visible; resume/rollback works.
* **Memory:** scoped reads/writes; contradiction logs; read p95 <**100ms**.
* **RAG:** hybrid default; provenance + relevance in responses; p95 <**500ms** (warm).
* **MCP:** tools discoverable; permissions enforced; audit entries complete.
* **Security:** TLS enforced to Postgres/Redis/Qdrant; secrets not in code.
* **CI:** Biome + tsc + Newman all green.

---

## 8) Traceability Matrix (key items)

| Requirement ID    | PRD Section | Priority | Phase     |
| ----------------- | ----------- | -------- | --------- |
| FR-2001/2005      | 5.1.1       | Must     | Phase 2   |
| FR-3001/3003      | 4.2.1       | Must     | Phase 1–2 |
| FR-4002           | 4.2.2       | Must     | Phase 1   |
| FR-5001/5002      | 4.2.4       | Must     | Phase 2   |
| FR-6001/6003      | 4.2.3       | Must     | Phase 1   |
| FR-7001/7002/7003 | 5.1.5       | Must     | Phase 1–2 |
| CI-9001/9002      | 8.0         | Must     | Phase 1   |

*(Full matrix maintained in repo `/docs/traceability.xlsx`.)*

---

## 9) Dependencies & Constraints

* **Frameworks:** LangGraph, Pydantic-AI, Mem0, R2R, MCP.
* **Infra:** **PostgreSQL 17.x**, **Redis 7.x**, **Qdrant (TLS)**, R2R service, FastAPI 0.115+, Python 3.11+.
* **Frontend:** Next.js (App Router), React 18, TypeScript 5.x, Biome.
* **Constraints:** Compose hygiene rules; TLS everywhere; no secrets in code; typed surfaces only.

---

## 10) Risks & Mitigations

* **Framework updates** → lock versions; renovate; contract tests; canaries.
* **Memory scale** → early load tests; summarization/TTL; vector sharding.
* **MCP variance** → ship core tools; strict schemas; fallbacks.
* **Perf SLOs** → caching, queues, warmup, pool sizing; regular drills.

---

## 11) Approval & Sign-off

**Gate to Approve FRD 1.1:**

* All **\[Hard Constraint]** items accepted.
* MVP scope excludes AG2; Elasticsearch removed.
* CI pipeline updates merged to enforce gates.

---

### Appendix A — API Surface (illustrative, bound to AGENTS.md)

* `GET /health`, `GET /ready`
* `/agents` (CRUD) – typed models; publish/draft; versioning
* `/runs` – start/stream/inspect; **requires `{user_id, thread_id}`**
* `/memory` – search/list/put/delete; scopes; export
* `/kb` – upload/progress/list/index/search; provenance in responses
* `/tools` – MCP registry; permissions; dry-run
* `/auth` – login, API keys, token introspection

### Appendix B — Docker Compose Norms (**\[Hard Constraint]**)

* No `version:` / `container_name`; **non-root** users; **healthchecks required**; internal networks; resource limits; `secrets:`; TLS endpoints.

---

**This FRD is the build contract.** If code or docs diverge from **AGENTS.md** or the rulesets, update the implementation to comply—or open a PR modifying this FRD and **AGENTS.md** together with rationale.
