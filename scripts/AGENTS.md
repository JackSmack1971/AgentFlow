# AGENTS.md: Scripts and Automation Guidelines

This document provides specific guidance for AI models working with the AgentFlow automation scripts located in `/scripts/`. These guidelines cover development and deployment automation standards.

## 1. Project Scope & Architecture
*   **Primary Purpose:** Development and deployment automation scripts for the AgentFlow platform
*   **Core Technologies:** Shell scripts (bash), Python automation, CI/CD helpers, deployment utilities
*   **Architecture Pattern:** Modular script organization with clear separation of concerns

## 2. Script Organization Standards

### Directory Structure
*   **REQUIRED:** Organize scripts by function and environment:
    ```
    scripts/
    ├── dev/                # Development utilities
    │   ├── setup.sh       # Environment setup
    │   ├── lint.sh        # Code linting
    │   └── test.sh        # Test execution
    ├── deploy/            # Deployment scripts
    │   ├── build.sh       # Build automation
    │   ├── deploy.sh      # Deployment automation
    │   └── rollback.sh    # Rollback procedures
    ├── db/                # Database management
    │   ├── migrate.py     # Database migrations
    │   ├── backup.sh      # Backup procedures
    │   └── restore.sh     # Restore procedures
    ├── monitoring/        # Monitoring and health checks
    └── utilities/         # General utilities
    ```

### Script Naming Conventions
*   **REQUIRED:** Use descriptive, action-oriented names
*   **MANDATORY:** Use kebab-case for shell scripts: `setup-environment.sh`
*   **REQUIRED:** Use snake_case for Python scripts: `database_migration.py`
*   **CRITICAL:** Include file extensions for all scripts

## 3. Shell Script Standards

### Script Headers and Documentation
*   **MANDATORY:** Include shebang and script metadata:
```bash
#!/usr/bin/env bash
#
# Script: setup-environment.sh
# Purpose: Set up development environment for AgentFlow
# Usage: ./setup-environment.sh [--production]
# Author: AgentFlow Team
# Version: 1.0.0
# Dependencies: Docker, uv, Node.js 20+

set -euo pipefail  # Fail fast and safe
```

### Error Handling and Safety
*   **CRITICAL:** Always use `set -euo pipefail` for safety
*   **MANDATORY:** Check for required dependencies before execution
*   **REQUIRED:** Implement proper error messages and exit codes
*   **CRITICAL:** Use input validation for all parameters

```bash
#!/usr/bin/env bash
set -euo pipefail

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" >&2
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Check dependencies
check_dependencies() {
    local deps=("docker" "uv" "node")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_error "Required dependency '$dep' is not installed"
            exit 1
        fi
    done
}

# Main execution
main() {
    log_info "Starting environment setup..."
    check_dependencies
    
    # Setup logic here
    setup_python_environment
    setup_node_environment
    setup_docker_services
    
    log_info "Environment setup completed successfully"
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

### Environment and Configuration
*   **REQUIRED:** Use environment variables for configuration
*   **MANDATORY:** Provide sensible defaults for optional parameters
*   **CRITICAL:** Never hardcode secrets or credentials
*   **REQUIRED:** Support both development and production modes

```bash
# Environment configuration with defaults
readonly ENVIRONMENT="${ENVIRONMENT:-development}"
readonly DATABASE_URL="${DATABASE_URL:-postgresql://localhost:5432/agentflow}"
readonly REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
readonly LOG_LEVEL="${LOG_LEVEL:-info}"

# Production safety checks
if [[ "$ENVIRONMENT" == "production" ]]; then
    log_warn "Running in PRODUCTION mode"
    read -p "Are you sure you want to continue? (yes/no): " -r
    if [[ ! "$REPLY" =~ ^[Yy][Ee][Ss]$ ]]; then
        log_info "Operation cancelled"
        exit 0
    fi
fi
```

## 4. Python Automation Scripts

### Script Structure and Standards
*   **REQUIRED:** Use proper Python project structure with type hints
*   **MANDATORY:** Include comprehensive docstrings and error handling
*   **CRITICAL:** Use click or argparse for command-line interfaces
*   **REQUIRED:** Implement proper logging configuration

```python
#!/usr/bin/env python3
"""
Database migration utility for AgentFlow.

This script handles database schema migrations, data migrations,
and provides rollback capabilities.

Usage:
    python database_migration.py migrate --version latest
    python database_migration.py rollback --version previous
    python database_migration.py status
"""

import sys
import logging
import click
from typing import Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """AgentFlow Database Migration Tool."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose

@cli.command()
@click.option('--version', default='latest', help='Migration version to apply')
@click.option('--dry-run', is_flag=True, help='Show what would be done without executing')
@click.pass_context
def migrate(ctx: click.Context, version: str, dry_run: bool) -> None:
    """Apply database migrations."""
    try:
        logger.info(f"Starting migration to version: {version}")
        
        if dry_run:
            logger.info("DRY RUN MODE - No changes will be applied")
            show_migration_plan(version)
        else:
            apply_migrations(version)
            
        logger.info("Migration completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)

def apply_migrations(version: str) -> None:
    """Apply database migrations to specified version."""
    # Migration logic here
    pass

if __name__ == '__main__':
    cli()
```

### Database Management Scripts
*   **CRITICAL:** Implement proper backup procedures before migrations
*   **MANDATORY:** Support rollback capabilities for all migrations
*   **REQUIRED:** Validate database state before and after operations
*   **CRITICAL:** Use connection pooling and proper transaction handling

### Deployment Automation
*   **REQUIRED:** Implement proper pre-deployment validation
*   **MANDATORY:** Support multiple deployment environments
*   **CRITICAL:** Include rollback procedures in deployment scripts
*   **REQUIRED:** Generate deployment reports and logs

## 5. CI/CD Integration Scripts

### GitHub Actions Helpers
*   **REQUIRED:** Create reusable scripts for common CI/CD tasks
*   **MANDATORY:** Implement proper exit codes for CI/CD integration
*   **CRITICAL:** Support parallel execution where possible
*   **REQUIRED:** Generate artifacts and reports for CI/CD systems

```bash
#!/usr/bin/env bash
# ci/run-tests.sh - Test execution script for CI/CD

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Test configuration
readonly TEST_TIMEOUT="${TEST_TIMEOUT:-300}"
readonly COVERAGE_THRESHOLD="${COVERAGE_THRESHOLD:-90}"

run_backend_tests() {
    log_info "Running backend tests..."
    cd "$PROJECT_ROOT/apps/api"
    
    # Install dependencies
    uv install
    
    # Run tests with coverage
    pytest tests/ \
        --cov=app \
        --cov-report=xml \
        --cov-report=html \
        --cov-fail-under="$COVERAGE_THRESHOLD" \
        --timeout="$TEST_TIMEOUT" \
        --verbose
}

run_frontend_tests() {
    log_info "Running frontend tests..."
    cd "$PROJECT_ROOT/frontend"
    
    # Install dependencies
    npm ci
    
    # Run tests
    npm run test -- --coverage --watchAll=false
    
    # Run type checking
    npm run type-check
}

main() {
    log_info "Starting test suite..."
    
    # Run tests in parallel
    run_backend_tests &
    local backend_pid=$!
    
    run_frontend_tests &
    local frontend_pid=$!
    
    # Wait for both test suites
    wait $backend_pid && wait $frontend_pid
    
    log_info "All tests completed successfully"
}

main "$@"
```

## 6. Monitoring and Health Check Scripts

### Health Check Utilities
*   **REQUIRED:** Implement comprehensive service health checks
*   **MANDATORY:** Support both simple and detailed health reporting
*   **CRITICAL:** Include dependency health verification
*   **REQUIRED:** Generate machine-readable health status

```python
#!/usr/bin/env python3
"""
Health check utility for AgentFlow services.

Performs comprehensive health checks across all services
and dependencies, suitable for monitoring systems.
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

class HealthStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"

@dataclass
class HealthResult:
    service: str
    status: HealthStatus
    latency_ms: float
    details: Dict[str, Any]

class HealthChecker:
    def __init__(self, services: Dict[str, str]):
        self.services = services
        self.timeout = aiohttp.ClientTimeout(total=5)
    
    async def check_service(self, name: str, url: str) -> HealthResult:
        """Check health of a single service."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{url}/health") as response:
                    latency = (asyncio.get_event_loop().time() - start_time) * 1000
                    
                    if response.status == 200:
                        details = await response.json()
                        return HealthResult(
                            service=name,
                            status=HealthStatus.HEALTHY,
                            latency_ms=latency,
                            details=details
                        )
                    else:
                        return HealthResult(
                            service=name,
                            status=HealthStatus.UNHEALTHY,
                            latency_ms=latency,
                            details={"error": f"HTTP {response.status}"}
                        )
                        
        except Exception as e:
            latency = (asyncio.get_event_loop().time() - start_time) * 1000
            return HealthResult(
                service=name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                details={"error": str(e)}
            )
    
    async def check_all(self) -> List[HealthResult]:
        """Check health of all services."""
        tasks = [
            self.check_service(name, url) 
            for name, url in self.services.items()
        ]
        return await asyncio.gather(*tasks)

async def main():
    services = {
        "api": "http://localhost:8000",
        "mcp": "http://localhost:8001",
        "frontend": "http://localhost:3000"
    }
    
    checker = HealthChecker(services)
    results = await checker.check_all()
    
    overall_status = HealthStatus.HEALTHY
    if any(r.status == HealthStatus.UNHEALTHY for r in results):
        overall_status = HealthStatus.UNHEALTHY
    elif any(r.status == HealthStatus.DEGRADED for r in results):
        overall_status = HealthStatus.DEGRADED
    
    report = {
        "overall_status": overall_status.value,
        "timestamp": asyncio.get_event_loop().time(),
        "services": [
            {
                "name": r.service,
                "status": r.status.value,
                "latency_ms": r.latency_ms,
                "details": r.details
            }
            for r in results
        ]
    }
    
    print(json.dumps(report, indent=2))
    
    # Exit with non-zero code if unhealthy
    if overall_status == HealthStatus.UNHEALTHY:
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

## 7. Security and Validation

### Security Standards
*   **CRITICAL:** Never include secrets or credentials in scripts
*   **MANDATORY:** Validate all inputs and parameters
*   **REQUIRED:** Use secure file permissions (755 for executables)
*   **CRITICAL:** Implement proper access controls for sensitive scripts

### Input Validation
*   **REQUIRED:** Validate environment variables and parameters
*   **MANDATORY:** Sanitize user inputs to prevent injection attacks
*   **CRITICAL:** Use allowlists for acceptable values where possible
*   **REQUIRED:** Implement proper error handling for invalid inputs

## 8. Documentation and Maintenance

### Script Documentation
*   **MANDATORY:** Include comprehensive usage documentation
*   **REQUIRED:** Document all parameters and environment variables
*   **CRITICAL:** Provide examples for common use cases
*   **REQUIRED:** Document prerequisites and dependencies

### Version Control and Maintenance
*   **REQUIRED:** Version control all scripts with appropriate permissions
*   **MANDATORY:** Include changelog for significant script updates
*   **CRITICAL:** Regular security review and updates
*   **REQUIRED:** Test scripts in development before production use

## 9. Forbidden Patterns
*   **NEVER** hardcode secrets or credentials in scripts
*   **NEVER** ignore errors or use unsafe shell options
*   **NEVER** run scripts with unnecessary privileges
*   **NEVER** skip input validation for user-provided parameters
*   **NEVER** use `rm -rf` without proper safety checks
*   **NEVER** expose sensitive information in logs
*   **NEVER** use deprecated or insecure shell features
