# Security-Focused Development Guidelines for AgentFlow FastAPI

## Security Standards
- All Docker services must run as non-root users
- JWT tokens: 1 hour access, 7 day refresh
- OTP secrets must be encrypted with Fernet
- Rate limiting: 100 requests/minute per IP
- Circuit breaker: 3 failures, 10 second reset
- All external service calls must use timeouts

## File Structure
- Docker configs: docker-compose.yml, Dockerfile
- Auth system: apps/api/app/auth/
- Security models: apps/api/app/db/models.py
- MCP tools: apps/mcp/tools/
- Services: apps/api/app/services/

## Validation Requirements
- Run `docker-compose config` to validate Docker syntax
- Execute `pytest tests/security/` for security test validation
- Use `safety check` for dependency vulnerability scanning
- Verify JWT tokens with `python -c "import jwt; print('JWT working')"`

## Security Testing
- Test authentication flows end-to-end
- Validate circuit breakers with simulated failures
- Confirm encrypted data storage/retrieval
- Check rate limiting under load
