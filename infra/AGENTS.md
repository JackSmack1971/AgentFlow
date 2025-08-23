# AGENTS.md: Infrastructure Guidelines

This document provides specific guidance for AI models working with the AgentFlow infrastructure code located in `/infra/`. These guidelines are derived from the Docker Compose, deployment, and infrastructure as code rulesets.

## 1. Project Scope & Architecture
*   **Primary Purpose:** Infrastructure as code (Docker, Kubernetes, Terraform) for AgentFlow platform deployment and orchestration
*   **Core Technologies:** Docker Compose, Kubernetes, Terraform, container orchestration, service mesh
*   **Architecture Pattern:** Microservices infrastructure with clear service boundaries and networking

## 2. Docker Compose Standards [Hard Constraint]

### Compose File Requirements
*   **CRITICAL:** NO `version:` field in compose files (deprecated)
*   **MANDATORY:** NO `container_name:` fields (let Docker auto-generate)
*   **REQUIRED:** ALL services MUST run as non-root users
*   **CRITICAL:** ALL services MUST have healthchecks defined
*   **MANDATORY:** Use internal networks for service communication
*   **REQUIRED:** Implement proper resource limits

```yaml
# docker-compose.yml - Correct format
services:
  api:
    build: .
    user: "1001:1001"  # Non-root user
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    resources:
      limits:
        memory: 512M
        cpus: "0.5"
    networks:
      - backend
    environment:
      - DATABASE_URL
    depends_on:
      postgres:
        condition: service_healthy

  postgres:
    image: postgres:16
    user: "999:999"  # postgres user
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 5s
      timeout: 5s
      retries: 5
    secrets:
      - postgres_password
    networks:
      - backend
    volumes:
      - postgres_data:/var/lib/postgresql/data

networks:
  backend:
    driver: bridge
    internal: true

volumes:
  postgres_data:
    driver: local

secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt
```

### Security Requirements
*   **CRITICAL:** TLS endpoints for ALL external-facing services
*   **MANDATORY:** Use Docker secrets for sensitive data
*   **REQUIRED:** Implement proper network segmentation
*   **CRITICAL:** NO secrets or credentials in environment variables

### Service Configuration
*   **REQUIRED:** Use multi-stage Dockerfiles for optimization
*   **MANDATORY:** Implement proper init systems in containers
*   **CRITICAL:** Use specific image tags, never `:latest` in production
*   **REQUIRED:** Implement proper logging configuration

```dockerfile
# Multi-stage Dockerfile example
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim as runtime
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 3. Kubernetes Deployment Standards

### Manifest Requirements
*   **REQUIRED:** Use namespace isolation for environment separation
*   **MANDATORY:** Implement proper resource quotas and limits
*   **CRITICAL:** Use NetworkPolicies for service communication
*   **REQUIRED:** Implement proper health and readiness probes

```yaml
# k8s/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agentflow-api
  namespace: agentflow
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agentflow-api
  template:
    metadata:
      labels:
        app: agentflow-api
    spec:
      serviceAccountName: agentflow-api
      securityContext:
        runAsNonRoot: true
        runAsUser: 1001
        fsGroup: 1001
      containers:
      - name: api
        image: agentflow/api:v1.0.0
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
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
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: agentflow-secrets
              key: database_url
```

### Service Mesh Integration
*   **REQUIRED:** Implement proper service discovery
*   **MANDATORY:** Use mTLS for service-to-service communication
*   **CRITICAL:** Implement proper traffic routing and load balancing
*   **REQUIRED:** Monitor service health and performance

## 4. Terraform Infrastructure as Code

### Resource Management
*   **REQUIRED:** Use proper state management with remote backends
*   **MANDATORY:** Implement resource tagging and naming conventions
*   **CRITICAL:** Use least privilege principle for IAM roles
*   **REQUIRED:** Implement proper environment separation

```hcl
# terraform/main.tf
terraform {
  required_version = ">= 1.0"
  backend "s3" {
    bucket = "agentflow-terraform-state"
    key    = "infrastructure/terraform.tfstate"
    region = "us-east-1"
    encrypt = true
  }
}

resource "aws_ecs_cluster" "agentflow" {
  name = "agentflow-${var.environment}"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  
  tags = {
    Environment = var.environment
    Project     = "agentflow"
    ManagedBy   = "terraform"
  }
}

resource "aws_ecs_service" "api" {
  name            = "agentflow-api"
  cluster         = aws_ecs_cluster.agentflow.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.api_replica_count
  
  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.api.id]
    assign_public_ip = false
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "agentflow-api"
    container_port   = 8000
  }
}
```

## 5. Database Infrastructure

### PostgreSQL Configuration
*   **CRITICAL:** Use TLS with `sslmode=verify-full` in production
*   **MANDATORY:** Implement proper backup and recovery procedures
*   **REQUIRED:** Use connection pooling (PgBouncer)
*   **CRITICAL:** Implement proper access controls and RBAC

### Redis Configuration
*   **REQUIRED:** Enable authentication and TLS
*   **MANDATORY:** Configure appropriate eviction policies
*   **CRITICAL:** Implement proper persistence settings
*   **REQUIRED:** Monitor memory usage and performance

### Vector Database (Qdrant)
*   **CRITICAL:** Use HTTPS with API key authentication
*   **REQUIRED:** Configure appropriate collection settings
*   **MANDATORY:** Implement proper resource monitoring
*   **REQUIRED:** Set appropriate timeouts and retry logic

## 6. Monitoring and Observability

### Metrics and Logging
*   **REQUIRED:** Implement centralized logging with structured logs
*   **MANDATORY:** Set up comprehensive metrics collection
*   **CRITICAL:** Implement proper alerting for critical services
*   **REQUIRED:** Use distributed tracing for request flow

### Health Checks and Monitoring
*   **MANDATORY:** Implement health endpoints for all services
*   **REQUIRED:** Set up uptime monitoring and alerting
*   **CRITICAL:** Monitor resource utilization and performance
*   **REQUIRED:** Implement proper SLA monitoring

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'agentflow-api'
    static_configs:
      - targets: ['agentflow-api:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']
```

## 7. Security and Compliance

### Network Security
*   **CRITICAL:** Implement proper network segmentation
*   **MANDATORY:** Use firewalls and security groups appropriately
*   **REQUIRED:** Implement VPN or bastion access for management
*   **CRITICAL:** Regular security scanning of container images

### Secrets Management
*   **MANDATORY:** Use dedicated secrets management systems
*   **CRITICAL:** Never store secrets in configuration files
*   **REQUIRED:** Implement proper secret rotation procedures
*   **CRITICAL:** Audit secret access and usage

### Compliance
*   **REQUIRED:** Implement proper data encryption at rest and in transit
*   **MANDATORY:** Set up audit logging for compliance
*   **CRITICAL:** Implement data retention and deletion policies
*   **REQUIRED:** Regular security assessments and penetration testing

## 8. Deployment and CI/CD

### Deployment Strategies
*   **REQUIRED:** Implement blue-green or rolling deployments
*   **MANDATORY:** Use proper deployment validation and rollback
*   **CRITICAL:** Implement proper pre-deployment testing
*   **REQUIRED:** Automate deployment processes

### Pipeline Configuration
*   **REQUIRED:** Implement proper build and test stages
*   **MANDATORY:** Use infrastructure as code for all deployments
*   **CRITICAL:** Implement proper security scanning in pipelines
*   **REQUIRED:** Use proper artifact management and versioning

## 9. Disaster Recovery and Backup

### Backup Strategies
*   **CRITICAL:** Implement automated backup procedures
*   **MANDATORY:** Test backup restoration procedures regularly
*   **REQUIRED:** Implement cross-region backup replication
*   **CRITICAL:** Document recovery procedures and RTO/RPO targets

### High Availability
*   **REQUIRED:** Implement multi-AZ deployment for critical services
*   **MANDATORY:** Use load balancing for service distribution
*   **CRITICAL:** Implement proper failover mechanisms
*   **REQUIRED:** Regular disaster recovery testing

## 10. Forbidden Patterns
*   **NEVER** use `version:` field in Docker Compose files
*   **NEVER** use `container_name:` in compose services
*   **NEVER** run containers as root user
*   **NEVER** skip healthchecks for services
*   **NEVER** expose secrets in environment variables
*   **NEVER** use `:latest` tags in production
*   **NEVER** deploy without proper resource limits
*   **NEVER** skip TLS for external endpoints
