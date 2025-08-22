# AGENTS.md: Infrastructure Collaboration Guide

<!-- Specialized guidance for AI agents working on AgentFlow infrastructure, data backends, deployment, and operations. This supplements the root AGENTS.md with infra-specific requirements. -->

## Component Scope

This guide covers: containerization (Docker & Compose), runtime topology, network segmentation, data backends (PostgreSQL, Redis, Qdrant), memory & workflow state (Mem0 + LangGraph), R2R (RAG service), security, observability, scaling, and operational runbooks.

---

## Architecture Overview

```

+-------------------+           +------------------+
\|  Frontend (Next)  |  HTTPS    |  API (FastAPI)   |
\|  :3000 (edge)     +---------->+  :8000           |
+---------+---------+           +---------+--------+
\|                                |
\| internal\:backend               | internal\:backend
v                                v
+-------+--------+               +-------+---------+
\| Redis 7 (HA)   |               | PostgreSQL 16/17|
\| sessions, sse  |               | app DB +        |
\| + LangGraph    |               | LangGraph CP/   |
\| checkpointer   |               | store (pg)      |
+-------+--------+               +-------+---------+
\                               /
\                             /
v                           v
+-------------------------+
\|  Qdrant (vectors)      |
\|  Mem0 memories index   |
+-------------------------+

```
         +-------------------------+
         |  R2R (RAG service) :7272|
         |  documents, search API  |
         +-------------------------+
```

````

---

## Compose Topology & Conventions (Authoritative)

**Compose file naming & syntax**
- Use `compose.yaml` (no `version:` field; Compose v2 deprecates it). Place at the repo root; use `compose.prod.yaml` for prod overlays. :contentReference[oaicite:0]{index=0}

**Service hygiene**
- Define healthchecks for _every_ service with realistic intervals and start periods. :contentReference[oaicite:1]{index=1}  
- Always set resource limits/requests to avoid OOM and noisy neighbors. :contentReference[oaicite:2]{index=2}  
- Run containers as non-root; drop capabilities and enable `no-new-privileges`. :contentReference[oaicite:3]{index=3}

**Networking**
- Segment networks: `public` (edge), `backend` (internal), `database` (internal). Mark internal networks `internal: true` and use service-name DNS. :contentReference[oaicite:4]{index=4} :contentReference[oaicite:5]{index=5}  
- Prefer `expose` for internal ports; only map ports for edge services. :contentReference[oaicite:6]{index=6}

**Configuration & secrets**
- Use `.env` only for non-sensitive config; mount secrets via Docker Secrets; never commit secrets. :contentReference[oaicite:7]{index=7} :contentReference[oaicite:8]{index=8}

---

## Data Backends (PostgreSQL, Redis, Qdrant)

### PostgreSQL (primary system of record)
- **TLS required** with `sslmode=verify-full` and proper CA chain; set minimum TLS1.2. :contentReference[oaicite:9]{index=9}  
- **Connection pooling mandatory** (PgBouncer or driver pool). Tune timeouts; monitor connects/disconnects. :contentReference[oaicite:10]{index=10}  
- Baseline tuning: shared_buffers≈25% RAM (≤8GB), autovacuum on, checkpoint completion 0.9. :contentReference[oaicite:11]{index=11}  
- Example secure DSN pattern (client-side certs supported): `…?sslmode=verify-full&sslcert=…&sslkey=…&sslrootcert=…`. :contentReference[oaicite:12]{index=12}

> **Common issue:** connection exhaustion → use pooling & monitor pool utilization; set timeouts. :contentReference[oaicite:13]{index=13}

### Redis 7 (sessions, short-lived state, LangGraph checkpointer option)
- Require auth & ACL; bind to explicit interfaces; enable TLS; protect with `protected-mode yes`. :contentReference[oaicite:14]{index=14}  
- Configure memory policy & persistence (AOF/RDB) per workload; set maxmemory & keepalives. :contentReference[oaicite:15]{index=15}

### Qdrant (vector store for Mem0 memories)
- Standard ports 6333 (HTTP) / 6334 (gRPC). Configure collection and **enforce embedding dimension match**. :contentReference[oaicite:16]{index=16}  
- For OpenAI `text-embedding-3-small`, dimension is **1536** (must match Qdrant collection). :contentReference[oaicite:17]{index=17}

---

## Memory & Workflow State

### Mem0 (agent/user/session memories)
- Use **correct provider names** (e.g., `"chromadb"`, not `"chroma"`); misnaming causes provider errors. :contentReference[oaicite:18]{index=18} :contentReference[oaicite:19]{index=19}  
- Ensure **embedding dims** match the embedder model; set `embedding_model_dims` explicitly. :contentReference[oaicite:20]{index=20}  
- Production reliability: set vector-store timeouts/retries; batch ops; monitor API usage. :contentReference[oaicite:21]{index=21} :contentReference[oaicite:22]{index=22}

### LangGraph (stateful workflows)
- **Production** must use persistent **checkpointer** (PostgreSQL or Redis), not in-memory. :contentReference[oaicite:23]{index=23}  
- Compile graphs with both `checkpointer` and durable `store` (Postgres/Redis) to preserve long-term memory. :contentReference[oaicite:24]{index=24}  
- Provide `thread_id` and `user_id` in runtime config for session persistence and cross-thread memory. :contentReference[oaicite:25]{index=25}  
- Prefer async backends for high concurrency (`AsyncPostgresSaver`, `AsyncRedisSaver`). :contentReference[oaicite:26]{index=26}

---

## R2R (RAG Service)

- Default base URL is `http://localhost:7272`; clients should health-check before use. :contentReference[oaicite:27]{index=27} :contentReference[oaicite:28]{index=28}  
- Production Compose maps `7272:7272` and depends on Postgres/Redis; ensure secrets/envs are set and distinct per env. :contentReference[oaicite:29]{index=29} :contentReference[oaicite:30]{index=30}

---

## Reference: Baseline `compose.yaml` (prod-ready pattern)

> Use overlays (`compose.prod.yaml`, `compose.dev.yaml`) to vary images and mounts. No `version:` key. Healthchecks, resources, networks, and secrets are **required**.

```yaml
services:
  api:
    image: agentflow/api:1.0.0
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      QDRANT_URL: http://qdrant:6333
      R2R_BASE_URL: http://r2r:7272
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      qdrant:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    user: "1000:1000"
    security_opt: ["no-new-privileges:true"]
    cap_drop: ["ALL"]
    deploy:
      resources:
        limits: { memory: 1G, cpus: "1.0" }
        reservations: { memory: 512M, cpus: "0.5" }
    networks: [backend]

  r2r:
    image: sciphi/r2r:stable
    environment:
      R2R_CONFIG_NAME: full
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    ports: ["7272:7272"] # edge exposure OK (ingress will front this in k8s)
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7272/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks: [backend]

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: agentflow
      POSTGRES_USER: agentflow
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - pg_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U agentflow -d agentflow"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks: [database]
    secrets:
      - db_password

  redis:
    image: redis:7-alpine
    command: ["redis-server", "/usr/local/etc/redis/redis.conf"]
    volumes:
      - ./infra/redis/redis.conf:/usr/local/etc/redis/redis.conf:ro
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    networks: [database]

  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant_storage:/qdrant/storage
    expose: ["6333","6334"] # internal only
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks: [database]

networks:
  backend:
    driver: bridge
    internal: true
  database:
    driver: bridge
    internal: true

volumes:
  pg_data:
  qdrant_storage:
  redis_data:

secrets:
  db_password:
    file: ./secrets/db_password.txt
````

**Why this matters**

* Healthchecks + `depends_on.condition: service_healthy` orchestrate reliable startup.&#x20;
* Non-root + capability drops & resource bounds harden and stabilize services.&#x20;
* Segmented internal networks reduce blast radius and exposure.&#x20;

---

## Observability & Health

**Storage health sweep (recommended pattern)**

* Implement per-backend async health checks and return a consolidated map for `/health`.&#x20;

**What to monitor (minimum)**

* Pool utilization, slow queries (Postgres); memory & eviction rate (Redis); search latency & QPS (Qdrant).&#x20;
* R2R: ingestion success rate, search latency, token usage, DB connection failures.&#x20;

---

## Security Hardening

* Enforce TLS in-flight for all DBs; never use `sslmode=disable` in production.&#x20;
* Secrets via engine-managed stores (Docker Secrets / K8s Secrets), not env vars.&#x20;
* Internal networks `internal: true`; only edge services map ports; prefer ingress at the platform layer. &#x20;

---

## Troubleshooting Playbooks

**Mem0**

* *Provider error* (`Unsupported VectorStore provider: chroma`) → rename to `chromadb`.&#x20;
* *Wrong vector dims* → set `embedding_model_dims` to match embedder (e.g., 1536 for OpenAI small).&#x20;

**Storage**

* *Connection exhaustion* → add PgBouncer/driver pooling and timeouts; monitor pool.&#x20;
* *Cross-system drift* → transactional patterns + retries; reconcile jobs.&#x20;

**R2R**

* *Unhealthy* → validate `:7272/health`; ensure DB/Redis up and reachable, env set per environment. &#x20;

---

## Acceptance Criteria (Infra Gate)

**Must**

1. Compose files follow v2 syntax (no `version:`), per service healthchecks, non-root users, resources configured.  &#x20;
2. PostgreSQL, Redis, Qdrant are TLS-protected with correct auth; pooling enabled for Postgres. &#x20;
3. Mem0 vector dims match embedder; provider names correct. &#x20;
4. LangGraph compiled with durable checkpointer + store (pg/redis) and `thread_id` provided. &#x20;

**Should**

* Segment networks with `internal: true`; only edge services map ports. &#x20;
* Implement consolidated storage health endpoint.&#x20;

**Must Not**

* Run containers as root or commit secrets to VCS. &#x20;

---

## K8s / Scaling Notes (Optional Path)

For cluster deployments, mirror the same constraints: liveness/readiness probes on API & R2R, secrets via K8s Secrets/ExternalSecrets, `readOnlyRootFilesystem`, and network policies restricting egress to DBs and clouds. (Compose rules remain the source of truth for port exposure, health probes, and least-privilege container settings.)

---

## Change Log Guidance

* Any change impacting: network exposure, secrets handling, TLS modes, pool sizing, or vector dims **requires** an infra PR with before/after diagrams and a smoke test plan.

---
