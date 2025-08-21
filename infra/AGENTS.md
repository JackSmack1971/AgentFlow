# AGENTS.md: Infrastructure Collaboration Guide

<!-- This file provides specialized guidance for AI agents working on AgentFlow infrastructure, databases, deployment, and operational concerns. It supplements the root AGENTS.md with infrastructure-specific requirements. -->

## Component Scope

This AGENTS.md covers infrastructure components, database configurations, deployment automation, monitoring, and operational aspects of the AgentFlow platform. This includes container orchestration, database optimization, security configurations, and production deployment patterns.

## Mem0 Infrastructure Requirements

- **Qdrant** vector store for embeddings; set `QDRANT_URL` and `QDRANT_API_KEY`.
- **PostgreSQL** stores memory metadata via `POSTGRES_URL`.
- **Neo4j** *(optional)* for graph relationships; configure `NEO4J_URL`.
- Ensure TLS and connection pooling for all services.
- Monitor Qdrant latency (<50ms), index size, PostgreSQL connections/query time, and
  Neo4j query latency.

**Testing:** `pytest tests/services/test_memory.py -v`

## Database Architecture and Configuration

### PostgreSQL Optimization for AgentFlow
```yaml
# PostgreSQL configuration for production deployment
# docker-compose.override.yml or kubernetes ConfigMap
version: "3.8"
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: agentflow
      POSTGRES_USER: agentflow
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      # Performance tuning
      POSTGRES_SHARED_BUFFERS: 256MB
      POSTGRES_EFFECTIVE_CACHE_SIZE: 1GB
      POSTGRES_MAINTENANCE_WORK_MEM: 64MB
      POSTGRES_CHECKPOINT_COMPLETION_TARGET: 0.9
      POSTGRES_WAL_BUFFERS: 16MB
      POSTGRES_DEFAULT_STATISTICS_TARGET: 100
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infra/postgres/init:/docker-entrypoint-initdb.d
      - ./infra/postgres/conf:/etc/postgresql/conf.d
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U agentflow -d agentflow"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
```

### PostgreSQL Security Configuration
```sql
-- infra/postgres/init/01-security.sql
-- Create application-specific user with limited privileges
CREATE USER agentflow_api WITH PASSWORD 'secure_password';
CREATE USER agentflow_readonly WITH PASSWORD 'readonly_password';

-- Grant specific permissions
GRANT CONNECT ON DATABASE agentflow TO agentflow_api;
GRANT USAGE ON SCHEMA public TO agentflow_api;
GRANT CREATE ON SCHEMA public TO agentflow_api;

-- Read-only user for analytics
GRANT CONNECT ON DATABASE agentflow TO agentflow_readonly;
GRANT USAGE ON SCHEMA public TO agentflow_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO agentflow_readonly;

-- Enable row-level security for multi-tenant isolation
ALTER TABLE user_memories ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_isolation ON user_memories
    USING (user_id = current_setting('app.current_user_id')::uuid);

-- Audit logging
CREATE EXTENSION IF NOT EXISTS pgaudit;
ALTER SYSTEM SET pgaudit.log = 'write, ddl';
ALTER SYSTEM SET pgaudit.log_catalog = off;
```

### Redis Configuration for Session Management
```yaml
# Redis configuration for production
redis:
  image: redis:7-alpine
  command: redis-server /usr/local/etc/redis/redis.conf
  volumes:
    - ./infra/redis/redis.conf:/usr/local/etc/redis/redis.conf
    - redis_data:/data
  ports:
    - "6379:6379"
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 3s
    retries: 5
  deploy:
    resources:
      limits:
        memory: 512M
        cpus: '0.5'
```

```conf
# infra/redis/redis.conf
# Memory management
maxmemory 256mb
maxmemory-policy allkeys-lru

# Persistence for session data
save 900 1
save 300 10
save 60 10000

# Security
requirepass ${REDIS_PASSWORD}
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command DEBUG ""

# Network
bind 127.0.0.1
port 6379
timeout 300
tcp-keepalive 300

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log
```

### Qdrant Vector Database Configuration
```yaml
# Qdrant vector database for embeddings and semantic search
qdrant:
  image: qdrant/qdrant:latest
  ports:
    - "6333:6333"
    - "6334:6334"
  volumes:
    - qdrant_storage:/qdrant/storage
    - ./infra/qdrant/config.yaml:/qdrant/config/production.yaml
  environment:
    QDRANT__SERVICE__HTTP_PORT: 6333
    QDRANT__SERVICE__GRPC_PORT: 6334
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
    interval: 30s
    timeout: 10s
    retries: 3
  deploy:
    resources:
      limits:
        memory: 4G
        cpus: '2.0'
      reservations:
        memory: 2G
        cpus: '1.0'
```

```yaml
# infra/qdrant/config.yaml
service:
  http_port: 6333
  grpc_port: 6334
  max_request_size_mb: 32

storage:
  # Optimize for memory vs storage tradeoff
  on_disk_payload: true
  optimizers:
    # Automatic optimization for vector operations
    memmap_threshold: 200000
    indexing_threshold: 20000

cluster:
  enabled: false  # Set to true for multi-node deployment

# Performance tuning
hnsw_config:
  # Higher ef_construct for better accuracy, slower indexing
  ef_construct: 200
  # Lower m for memory efficiency
  m: 16

# Security (production)
api_key: ${QDRANT_API_KEY}
enable_tls: true
tls_config:
  cert_file: /etc/qdrant/tls/cert.pem
  key_file: /etc/qdrant/tls/key.pem
```

## Container Orchestration and Deployment

### Docker Multi-Stage Build Patterns
```dockerfile
# infra/docker/Dockerfile.api
# Multi-stage build for AgentFlow API
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
RUN pip install uv

# Set up virtual environment
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv sync --frozen

# Production stage
FROM python:3.11-slim as production

# Create non-root user
RUN groupadd -r agentflow && useradd -r -g agentflow agentflow

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
WORKDIR /app
COPY apps/api/ ./apps/api/
COPY packages/ ./packages/

# Set ownership and switch to non-root user
RUN chown -R agentflow:agentflow /app
USER agentflow

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Security: Run as non-root, read-only filesystem
EXPOSE 8000
CMD ["uvicorn", "apps.api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes Deployment Configuration
```yaml
# infra/k8s/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agentflow-api
  labels:
    app: agentflow-api
    version: v1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agentflow-api
  template:
    metadata:
      labels:
        app: agentflow-api
        version: v1
    spec:
      serviceAccountName: agentflow-api
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: api
        image: agentflow/api:latest
        ports:
        - containerPort: 8000
          protocol: TCP
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: agentflow-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: agentflow-secrets
              key: redis-url
        - name: QDRANT_URL
          value: "http://qdrant-service:6333"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop:
            - ALL
          readOnlyRootFilesystem: true
      restartPolicy: Always
---
apiVersion: v1
kind: Service
metadata:
  name: agentflow-api-service
spec:
  selector:
    app: agentflow-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

### Auto-Scaling Configuration
```yaml
# infra/k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agentflow-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agentflow-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
```

## Security and Compliance Infrastructure

### TLS/SSL Configuration
```yaml
# infra/tls/cert-manager.yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: security@agentflow.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: agentflow-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - api.agentflow.com
    secretName: agentflow-tls
  rules:
  - host: api.agentflow.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: agentflow-api-service
            port:
              number: 80
```

### Network Policies for Security
```yaml
# infra/k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: agentflow-api-policy
spec:
  podSelector:
    matchLabels:
      app: agentflow-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  # Allow DNS resolution
  - to: []
    ports:
    - protocol: UDP
      port: 53
  # Allow database connections
  - to:
    - podSelector:
        matchLabels:
          app: postgresql
    ports:
    - protocol: TCP
      port: 5432
  # Allow Redis connections
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
  # Allow external API calls (OpenAI, etc.)
  - to: []
    ports:
    - protocol: TCP
      port: 443
```

## Monitoring and Observability

### Prometheus Monitoring Configuration
```yaml
# infra/monitoring/prometheus.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    rule_files:
      - "/etc/prometheus/rules/*.yml"
    
    scrape_configs:
    - job_name: 'agentflow-api'
      static_configs:
      - targets: ['agentflow-api-service:80']
      metrics_path: /metrics
      scrape_interval: 10s
    
    - job_name: 'postgres-exporter'
      static_configs:
      - targets: ['postgres-exporter:9187']
    
    - job_name: 'redis-exporter'
      static_configs:
      - targets: ['redis-exporter:9121']
    
    - job_name: 'node-exporter'
      static_configs:
      - targets: ['node-exporter:9100']

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-rules
data:
  agentflow.yml: |
    groups:
    - name: agentflow
      rules:
      - alert: HighResponseTime
        expr: http_request_duration_seconds{quantile="0.95"} > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }}s"
      
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"
      
      - alert: DatabaseConnectionFailure
        expr: pg_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database connection failure"
          description: "PostgreSQL database is down"
```

### Grafana Dashboard Configuration
```json
{
  "dashboard": {
    "title": "AgentFlow Platform Metrics",
    "panels": [
      {
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ]
      },
      {
        "title": "Memory Operations Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(memory_operations_total[5m])",
            "legendFormat": "Operations per second"
          },
          {
            "expr": "histogram_quantile(0.95, rate(memory_operation_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile latency"
          }
        ]
      },
      {
        "title": "Database Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "pg_stat_database_numbackends",
            "legendFormat": "Active connections"
          }
        ]
      }
    ]
  }
}
```

### Logging Infrastructure with Fluentd
```yaml
# infra/logging/fluentd-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/containers/agentflow-api-*.log
      pos_file /var/log/fluentd-agentflow-api.log.pos
      tag kubernetes.agentflow.api
      format json
      time_key time
      time_format %Y-%m-%dT%H:%M:%S.%NZ
    </source>
    
    <source>
      @type tail
      path /var/log/containers/agentflow-mcp-*.log
      pos_file /var/log/fluentd-agentflow-mcp.log.pos
      tag kubernetes.agentflow.mcp
      format json
    </source>
    
    <filter kubernetes.agentflow.**>
      @type kubernetes_metadata
      @id filter_kube_metadata
    </filter>
    
    <filter kubernetes.agentflow.**>
      @type parser
      format json
      key_name log
      reserve_data true
    </filter>
    
    <match kubernetes.agentflow.**>
      @type elasticsearch
      host elasticsearch-service
      port 9200
      logstash_format true
      logstash_prefix agentflow
      <buffer>
        @type file
        path /var/log/fluentd-buffers/agentflow.buffer
        flush_mode interval
        retry_type exponential_backoff
        flush_thread_count 2
        flush_interval 5s
        retry_forever
        retry_max_interval 30
        chunk_limit_size 2M
        queue_limit_length 8
        overflow_action block
      </buffer>
    </match>
```

## Backup and Disaster Recovery

### Database Backup Strategy
```bash
#!/bin/bash
# infra/scripts/backup-postgres.sh
# Automated PostgreSQL backup with rotation

set -euo pipefail

# Configuration
BACKUP_DIR="/backups/postgres"
RETENTION_DAYS=30
S3_BUCKET="agentflow-backups"
POSTGRES_HOST="postgres-service"
POSTGRES_DB="agentflow"
POSTGRES_USER="backup_user"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate backup filename with timestamp
BACKUP_FILENAME="agentflow_$(date +%Y%m%d_%H%M%S).sql.gz"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_FILENAME"

# Create compressed backup
echo "Creating backup: $BACKUP_FILENAME"
PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
  -h "$POSTGRES_HOST" \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  --verbose \
  --no-owner \
  --no-privileges \
  | gzip > "$BACKUP_PATH"

# Verify backup integrity
echo "Verifying backup integrity..."
if ! gzip -t "$BACKUP_PATH"; then
  echo "ERROR: Backup file is corrupted"
  exit 1
fi

# Upload to S3
echo "Uploading to S3..."
aws s3 cp "$BACKUP_PATH" "s3://$S3_BUCKET/postgres/"

# Clean up old local backups
echo "Cleaning up old backups (older than $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "agentflow_*.sql.gz" -mtime +$RETENTION_DAYS -delete

# Clean up old S3 backups
aws s3 ls "s3://$S3_BUCKET/postgres/" | \
  awk '{print $4}' | \
  while read -r file; do
    file_date=$(echo "$file" | grep -o '[0-9]\{8\}')
    if [[ -n "$file_date" ]]; then
      days_old=$(( ($(date +%s) - $(date -d "$file_date" +%s)) / 86400 ))
      if [[ $days_old -gt $RETENTION_DAYS ]]; then
        echo "Deleting old backup: $file"
        aws s3 rm "s3://$S3_BUCKET/postgres/$file"
      fi
    fi
  done

echo "Backup completed successfully: $BACKUP_FILENAME"
```

### Disaster Recovery Procedures
```yaml
# infra/dr/postgres-restore.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: postgres-restore
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: restore
        image: postgres:16
        env:
        - name: PGPASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secrets
              key: password
        - name: BACKUP_FILE
          value: "agentflow_20250819_120000.sql.gz"
        command:
        - /bin/bash
        - -c
        - |
          set -euo pipefail
          
          # Download backup from S3
          aws s3 cp "s3://agentflow-backups/postgres/$BACKUP_FILE" /tmp/backup.sql.gz
          
          # Verify backup integrity
          gzip -t /tmp/backup.sql.gz
          
          # Drop existing database (WARNING: Data loss)
          psql -h postgres-service -U postgres -c "DROP DATABASE IF EXISTS agentflow;"
          psql -h postgres-service -U postgres -c "CREATE DATABASE agentflow;"
          
          # Restore database
          gunzip -c /tmp/backup.sql.gz | psql -h postgres-service -U postgres -d agentflow
          
          # Verify restore
          psql -h postgres-service -U postgres -d agentflow -c "SELECT COUNT(*) FROM information_schema.tables;"
          
          echo "Database restore completed successfully"
        volumeMounts:
        - name: aws-credentials
          mountPath: /root/.aws
          readOnly: true
      volumes:
      - name: aws-credentials
        secret:
          secretName: aws-credentials
```

## Performance Optimization

### Database Connection Pooling
```yaml
# infra/pgbouncer/pgbouncer.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: pgbouncer-config
data:
  pgbouncer.ini: |
    [databases]
    agentflow = host=postgres-service port=5432 dbname=agentflow
    
    [pgbouncer]
    listen_addr = 0.0.0.0
    listen_port = 5432
    auth_type = md5
    auth_file = /etc/pgbouncer/userlist.txt
    
    # Connection pool configuration
    pool_mode = transaction
    max_client_conn = 200
    default_pool_size = 20
    min_pool_size = 5
    reserve_pool_size = 5
    reserve_pool_timeout = 3
    max_db_connections = 100
    max_user_connections = 100
    
    # Performance tuning
    server_reset_query = DISCARD ALL
    server_check_delay = 10
    server_check_query = SELECT 1
    server_lifetime = 3600
    server_idle_timeout = 600
    
    # Logging
    log_connections = 1
    log_disconnections = 1
    log_pooler_errors = 1
    
  userlist.txt: |
    "agentflow_api" "md5<hash_of_password>"
    "agentflow_readonly" "md5<hash_of_password>"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pgbouncer
spec:
  replicas: 2
  selector:
    matchLabels:
      app: pgbouncer
  template:
    metadata:
      labels:
        app: pgbouncer
    spec:
      containers:
      - name: pgbouncer
        image: pgbouncer/pgbouncer:latest
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: config
          mountPath: /etc/pgbouncer
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
      volumes:
      - name: config
        configMap:
          name: pgbouncer-config
```

### Redis Clustering for High Availability
```yaml
# infra/redis/redis-cluster.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-cluster-config
data:
  redis.conf: |
    port 6379
    cluster-enabled yes
    cluster-config-file nodes.conf
    cluster-node-timeout 5000
    appendonly yes
    appendfsync everysec
    
    # Memory optimization
    maxmemory 512mb
    maxmemory-policy allkeys-lru
    
    # Security
    requirepass ${REDIS_PASSWORD}
    masterauth ${REDIS_PASSWORD}

---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis-cluster
spec:
  serviceName: redis-cluster
  replicas: 6
  selector:
    matchLabels:
      app: redis-cluster
  template:
    metadata:
      labels:
        app: redis-cluster
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
          name: client
        - containerPort: 16379
          name: gossip
        command:
        - redis-server
        - /usr/local/etc/redis/redis.conf
        volumeMounts:
        - name: conf
          mountPath: /usr/local/etc/redis
        - name: data
          mountPath: /data
      volumes:
      - name: conf
        configMap:
          name: redis-cluster-config
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 1Gi
```

## Security Hardening

### Pod Security Standards
```yaml
# infra/security/pod-security.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: agentflow
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted

---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: agentflow-api
  namespace: agentflow
automountServiceAccountToken: false

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: agentflow-api-role
  namespace: agentflow
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: agentflow-api-binding
  namespace: agentflow
subjects:
- kind: ServiceAccount
  name: agentflow-api
  namespace: agentflow
roleRef:
  kind: Role
  name: agentflow-api-role
  apiGroup: rbac.authorization.k8s.io
```

### Secret Management with External Secrets
```yaml
# infra/security/external-secrets.yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: agentflow
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-west-2
      auth:
        secretRef:
          accessKeyID:
            name: aws-credentials
            key: access-key-id
          secretAccessKey:
            name: aws-credentials
            key: secret-access-key

---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: agentflow-secrets
  namespace: agentflow
spec:
  refreshInterval: 15m
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: agentflow-secrets
    creationPolicy: Owner
  data:
  - secretKey: database-url
    remoteRef:
      key: agentflow/production
      property: database_url
  - secretKey: redis-url
    remoteRef:
      key: agentflow/production
      property: redis_url
  - secretKey: openai-api-key
    remoteRef:
      key: agentflow/production
      property: openai_api_key
```

## Development and Deployment Automation

### GitOps with ArgoCD
```yaml
# infra/gitops/application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: agentflow
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/agentflow/agentflow
    targetRevision: main
    path: infra/k8s
  destination:
    server: https://kubernetes.default.svc
    namespace: agentflow
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: false
    syncOptions:
    - CreateNamespace=true
    - PrunePropagationPolicy=foreground
    - PruneLast=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

### Infrastructure as Code with Terraform
```hcl
# infra/terraform/main.tf
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
}

# EKS Cluster
module "eks" {
  source = "terraform-aws-modules/eks/aws"
  
  cluster_name    = "agentflow-production"
  cluster_version = "1.28"
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  
  node_groups = {
    main = {
      desired_capacity = 3
      max_capacity     = 10
      min_capacity     = 3
      
      instance_types = ["t3.medium"]
      
      k8s_labels = {
        Environment = "production"
        Application = "agentflow"
      }
    }
  }
  
  tags = {
    Environment = "production"
    Project     = "agentflow"
  }
}

# RDS PostgreSQL
resource "aws_db_instance" "postgres" {
  identifier = "agentflow-postgres"
  
  engine         = "postgres"
  engine_version = "16"
  instance_class = "db.t3.medium"
  
  allocated_storage     = 100
  max_allocated_storage = 1000
  storage_type          = "gp3"
  storage_encrypted     = true
  
  db_name  = "agentflow"
  username = "agentflow"
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  deletion_protection = true
  skip_final_snapshot = false
  
  tags = {
    Environment = "production"
    Project     = "agentflow"
  }
}

# ElastiCache Redis
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "agentflow-redis"
  description                = "AgentFlow Redis cluster"
  
  node_type                  = "cache.t3.micro"
  port                       = 6379
  parameter_group_name       = aws_elasticache_parameter_group.redis.name
  
  num_cache_clusters         = 2
  automatic_failover_enabled = true
  multi_az_enabled          = true
  
  subnet_group_name = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = var.redis_auth_token
  
  tags = {
    Environment = "production"
    Project     = "agentflow"
  }
}
```

## Operational Procedures

### Health Check and Monitoring Scripts
```bash
#!/bin/bash
# infra/scripts/health-check.sh
# Comprehensive health check for AgentFlow platform

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
MCP_HEALTH_ENDPOINT="${MCP_HEALTH_ENDPOINT:-http://localhost:8001}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
REDIS_HOST="${REDIS_HOST:-localhost}"
QDRANT_HOST="${QDRANT_HOST:-localhost}"

echo "=== AgentFlow Platform Health Check ==="
echo "Timestamp: $(date)"
echo

# Function to check service health
check_service() {
    local service_name="$1"
    local check_command="$2"
    local expected_result="$3"
    
    echo -n "Checking $service_name... "
    
    if result=$(eval "$check_command" 2>/dev/null); then
        if [[ "$result" == *"$expected_result"* ]]; then
            echo -e "${GREEN}✓ Healthy${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠ Warning: $result${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ Failed${NC}"
        return 1
    fi
}

# Check API health
check_service "API Server" \
    "curl -s -f $API_URL/health | jq -r .status" \
    "healthy"

# Check MCP server
check_service "MCP Server" \
    "curl -s -f $MCP_HEALTH_ENDPOINT/health | jq -r .status" \
    "healthy"

# Check PostgreSQL
check_service "PostgreSQL" \
    "pg_isready -h $POSTGRES_HOST -p 5432" \
    "accepting connections"

# Check Redis
check_service "Redis" \
    "redis-cli -h $REDIS_HOST ping" \
    "PONG"

# Check Qdrant
check_service "Qdrant Vector DB" \
    "curl -s -f http://$QDRANT_HOST:6333/health | jq -r .status" \
    "ok"

# Performance checks
echo
echo "=== Performance Metrics ==="

# API response time
echo -n "API response time... "
response_time=$(curl -o /dev/null -s -w "%{time_total}" "$API_URL/health")
if (( $(echo "$response_time < 2.0" | bc -l) )); then
    echo -e "${GREEN}${response_time}s ✓${NC}"
else
    echo -e "${YELLOW}${response_time}s ⚠ (>2s)${NC}"
fi

# Database connection count
echo -n "Database connections... "
if command -v psql >/dev/null; then
    conn_count=$(psql -h "$POSTGRES_HOST" -U postgres -t -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null | tr -d ' ')
    echo -e "${GREEN}${conn_count} active${NC}"
else
    echo -e "${YELLOW}Unable to check (psql not available)${NC}"
fi

echo
echo "=== Health Check Complete ==="
```

### Maintenance and Update Procedures
```bash
#!/bin/bash
# infra/scripts/rolling-update.sh
# Safe rolling update procedure for AgentFlow

set -euo pipefail

NAMESPACE="agentflow"
DEPLOYMENT="agentflow-api"
NEW_IMAGE="$1"

if [[ -z "$NEW_IMAGE" ]]; then
    echo "Usage: $0 <new-image-tag>"
    exit 1
fi

echo "Starting rolling update to $NEW_IMAGE..."

# Pre-update health check
echo "Performing pre-update health check..."
kubectl get pods -n "$NAMESPACE" -l app=agentflow-api

# Update deployment
echo "Updating deployment image..."
kubectl set image deployment/"$DEPLOYMENT" api="$NEW_IMAGE" -n "$NAMESPACE"

# Wait for rollout to complete
echo "Waiting for rollout to complete..."
kubectl rollout status deployment/"$DEPLOYMENT" -n "$NAMESPACE" --timeout=600s

# Post-update health check
echo "Performing post-update health check..."
sleep 30  # Allow time for pods to be ready

# Check all pods are running
if kubectl get pods -n "$NAMESPACE" -l app=agentflow-api | grep -q "0/1"; then
    echo "ERROR: Some pods are not ready"
    kubectl get pods -n "$NAMESPACE" -l app=agentflow-api
    echo "Rolling back..."
    kubectl rollout undo deployment/"$DEPLOYMENT" -n "$NAMESPACE"
    exit 1
fi

# Test API health
echo "Testing API health..."
API_POD=$(kubectl get pod -n "$NAMESPACE" -l app=agentflow-api -o jsonpath="{.items[0].metadata.name}")
kubectl exec -n "$NAMESPACE" "$API_POD" -- curl -f http://localhost:8000/health

echo "Rolling update completed successfully!"
```

## Critical Infrastructure Rules

### Security Rules
- **NEVER** store secrets in container images or configuration files
- **NEVER** run containers as root in production
- **NEVER** disable TLS/SSL encryption for any service
- **NEVER** expose internal services directly to the internet
- **NEVER** use default passwords or credentials

### Database Rules  
- **NEVER** connect to databases without connection pooling
- **NEVER** skip database backups or recovery testing
- **NEVER** ignore database security configurations
- **NEVER** allow unlimited connections to databases
- **NEVER** deploy without proper database monitoring

### Deployment Rules
- **NEVER** deploy without health checks and readiness probes
- **NEVER** skip resource limits and requests
- **NEVER** deploy without proper logging and monitoring
- **NEVER** use latest tags in production deployments
- **NEVER** deploy without proper rollback procedures

### Monitoring Rules
- **NEVER** deploy without comprehensive monitoring
- **NEVER** ignore alert notifications or monitoring gaps
- **NEVER** skip performance baseline establishment
- **NEVER** deploy without proper log aggregation
- **NEVER** ignore security scanning and vulnerability management
