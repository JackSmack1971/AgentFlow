### .roo/rules-git-manager/03-comprehensive-testing.md
```markdown
# Comprehensive Testing and Validation

## Multi-Language Test Execution

### Python Testing Strategies
```
# Comprehensive Python validation
python -m pytest --cov=. --cov-report=html
python -m black . --check
python -m isort . --check-only
python -m mypy .
python -m bandit -r .
python -m safety check

# Dependency management
pip-audit
pip check

JavaScript/TypeScript Testing
bash# Full JS/TS validation pipeline
npm test -- --coverage
npm run lint
npm run type-check
npx prettier --check .
npm audit
npm run build

# Alternative package managers
yarn test
pnpm test
Rust Testing Excellence
bash# Comprehensive Rust validation
cargo test --all-features
cargo clippy -- -D warnings  
cargo fmt --check
cargo audit
cargo outdated
cargo build --release

# Documentation testing
cargo test --doc
Go Testing Standards
bash# Complete Go validation
go test -v -race -cover ./...
go vet ./...
go fmt ./...
golint ./...
go mod verify
go mod tidy

# Security scanning
gosec ./...
Java Testing (Maven/Gradle)
bash# Maven workflow
mvn clean test
mvn verify
mvn spotbugs:check
mvn checkstyle:check

# Gradle workflow  
./gradlew test
./gradlew check
./gradlew spotbugsMain
Pre-commit Integration
Universal Pre-commit Configuration
yaml# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer  
      - id: check-yaml
      - id: check-json
      - id: check-merge-conflict
      - id: check-case-conflict

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.44.0
    hooks:
      - id: eslint
Hook Failure Recovery
```bash
# When pre-commit hooks fail:
git status  
# Check what failed
# Fix the issues
git add -A
git commit -m "fix: resolve pre-commit hook failures"

# Emergency bypass (document reason)
git commit --no-verify -m "emergency: bypass hooks for critical fix"
Build Verification Workflows
Multi-Platform Build Testing
bash# Node.js builds
npm run build
npm run build:production

# Python builds  
python setup.py build
python -m build

# Rust builds
cargo build --release --all-features

# Go builds
go build ./...
CGO_ENABLED=0 GOOS=linux go build

# Docker builds
docker build -t app:test .
docker run --rm app:test npm test
Continuous Integration Simulation
```
Run the same checks that CI will run
Test multiple environments when possible
Validate configuration files (YAML, JSON, TOML)
Check for secrets or sensitive data exposure