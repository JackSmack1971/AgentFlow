# AGENTS.md: Testing Guidelines

This document provides specific guidance for AI models working with the AgentFlow test suite located in `/tests/`. These guidelines cover unit, integration, and performance testing standards derived from GitHub Workflows and testing best practices rulesets.

## 1. Project Scope & Architecture
*   **Primary Purpose:** Comprehensive test suite with unit, integration, and performance tests for the entire AgentFlow platform
*   **Core Technologies:** pytest (Python), Jest + React Testing Library (Frontend), MSW (Mock Service Worker), Locust (Performance)
*   **Test Organization:** Parallel structure to source code with clear separation of test types

## 2. Test Structure Requirements

### Directory Organization
*   **MANDATORY:** Maintain parallel structure to source code:
    ```
    tests/
    ├── unit/                # Unit tests
    │   ├── api/            # FastAPI unit tests
    │   ├── mcp/            # MCP server unit tests
    │   └── services/       # Service layer tests
    ├── integration/        # Integration tests
    │   ├── api/            # API integration tests
    │   ├── database/       # Database integration tests
    │   └── end-to-end/     # Full workflow tests
    ├── performance/        # Performance and load tests
    │   ├── locustfile.py   # Load testing scenarios
    │   └── benchmarks/     # Performance benchmarks
    ├── fixtures/           # Test data and fixtures
    └── conftest.py        # Pytest configuration
    ```

## 3. Python Testing Standards (pytest)

### Test Configuration
*   **REQUIRED:** Use pytest with pytest-asyncio for async support
*   **MANDATORY:** Configure coverage reporting with >90% threshold
*   **CRITICAL:** Use pytest fixtures for setup and teardown
*   **REQUIRED:** Implement proper test isolation

```python
# conftest.py
import pytest
import asyncio
from httpx import AsyncClient
from app.main import app

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def mock_database():
    # Setup test database
    yield db_session
    # Cleanup
```

### Unit Test Requirements
*   **MANDATORY:** Test all public functions and methods
*   **REQUIRED:** Test error conditions and edge cases
*   **CRITICAL:** Mock ALL external dependencies
*   **REQUIRED:** Use descriptive test names that explain behavior

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.services.agent_service import AgentService

@pytest.mark.asyncio
async def test_create_agent_success():
    """Should create agent with valid data and return agent ID."""
    mock_db = AsyncMock()
    service = AgentService(mock_db)
    
    agent_data = {"name": "Test Agent", "description": "Test"}
    result = await service.create_agent(agent_data)
    
    assert result.id is not None
    assert result.name == "Test Agent"
    mock_db.save.assert_called_once()

@pytest.mark.asyncio
async def test_create_agent_invalid_data():
    """Should raise ValidationError for invalid agent data."""
    service = AgentService(AsyncMock())
    
    with pytest.raises(ValidationError):
        await service.create_agent({"name": ""})  # Invalid empty name
```

### Integration Test Standards
*   **REQUIRED:** Test complete request/response cycles
*   **MANDATORY:** Use test database with proper cleanup
*   **CRITICAL:** Test authentication and authorization
*   **REQUIRED:** Verify database state changes

```python
@pytest.mark.asyncio
async def test_agent_crud_workflow(client, test_db):
    """Should support complete CRUD operations for agents."""
    # Create
    create_response = await client.post("/agents", json={
        "name": "Integration Test Agent",
        "description": "Test agent for integration testing"
    })
    assert create_response.status_code == 201
    agent_id = create_response.json()["id"]
    
    # Read
    get_response = await client.get(f"/agents/{agent_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Integration Test Agent"
    
    # Update
    update_response = await client.put(f"/agents/{agent_id}", json={
        "name": "Updated Agent Name"
    })
    assert update_response.status_code == 200
    
    # Delete
    delete_response = await client.delete(f"/agents/{agent_id}")
    assert delete_response.status_code == 204
```

## 4. Frontend Testing Standards (Jest + RTL)

### Component Testing
*   **MANDATORY:** Use React Testing Library for component tests
*   **REQUIRED:** Test user interactions, not implementation details
*   **CRITICAL:** Mock all API calls using MSW
*   **REQUIRED:** Test accessibility features

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import { AgentList } from './AgentList';

const server = setupServer(
  rest.get('/api/agents', (req, res, ctx) => {
    return res(ctx.json([
      { id: '1', name: 'Test Agent', description: 'Test description' }
    ]));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

test('should display agents and handle selection', async () => {
  render(<AgentList />);
  
  // Wait for agents to load
  await waitFor(() => {
    expect(screen.getByText('Test Agent')).toBeInTheDocument();
  });
  
  // Test interaction
  fireEvent.click(screen.getByText('Test Agent'));
  expect(screen.getByText('Agent Details')).toBeInTheDocument();
});
```

### Mock Service Worker Configuration
*   **CRITICAL:** Mock ALL network requests in tests
*   **REQUIRED:** Use realistic response data
*   **MANDATORY:** Test both success and error scenarios
*   **REQUIRED:** Reset handlers between tests

```typescript
// mocks/handlers.ts
import { rest } from 'msw';

export const handlers = [
  rest.post('/api/agents', (req, res, ctx) => {
    return res(ctx.status(201), ctx.json({ id: 'new-id', ...req.body }));
  }),
  
  rest.get('/api/agents/:id', (req, res, ctx) => {
    const { id } = req.params;
    if (id === 'not-found') {
      return res(ctx.status(404), ctx.json({ error: 'Agent not found' }));
    }
    return res(ctx.json({ id, name: 'Mock Agent' }));
  })
];
```

## 5. Performance Testing Standards

### Load Testing with Locust
*   **REQUIRED:** Implement comprehensive load testing scenarios
*   **MANDATORY:** Test critical user journeys under load
*   **CRITICAL:** Monitor response times and error rates
*   **REQUIRED:** Define performance SLOs and test against them

```python
# performance/locustfile.py
from locust import HttpUser, task, between
import json

class AgentFlowUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Authenticate user before running tasks."""
        self.login()
    
    def login(self):
        response = self.client.post("/auth/login", json={
            "username": "test@example.com",
            "password": "testpassword"
        })
        self.auth_token = response.json()["access_token"]
        self.client.headers.update({"Authorization": f"Bearer {self.auth_token}"})
    
    @task(3)
    def list_agents(self):
        """Test listing agents (most common operation)."""
        with self.client.get("/agents", catch_response=True) as response:
            if response.elapsed.total_seconds() > 2.0:
                response.failure(f"Response too slow: {response.elapsed.total_seconds()}s")
    
    @task(1)
    def create_agent(self):
        """Test creating new agent."""
        agent_data = {
            "name": f"Load Test Agent {self.get_unique_id()}",
            "description": "Generated during load testing"
        }
        self.client.post("/agents", json=agent_data)
```

## 6. Test Data Management

### Fixtures and Test Data
*   **REQUIRED:** Use consistent test data across all test suites
*   **MANDATORY:** Implement proper data cleanup between tests
*   **CRITICAL:** Never use production data in tests
*   **REQUIRED:** Create realistic but anonymized test datasets

```python
# fixtures/agent_fixtures.py
import pytest
from datetime import datetime

@pytest.fixture
def sample_agent_data():
    return {
        "name": "Test Agent",
        "description": "Agent for testing purposes",
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 1000
    }

@pytest.fixture
def sample_agents_list():
    return [
        {
            "id": "agent-1",
            "name": "Agent One",
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": "agent-2", 
            "name": "Agent Two",
            "created_at": datetime.utcnow().isoformat()
        }
    ]
```

## 7. CI/CD Integration

### GitHub Actions Requirements
*   **MANDATORY:** All tests must pass before merge to main branch
*   **REQUIRED:** Run tests on multiple Python versions (3.10, 3.11, 3.12)
*   **CRITICAL:** Generate and store test coverage reports
*   **REQUIRED:** Run security scans alongside tests

```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Run tests
        run: |
          pytest tests/ -v --cov=apps --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## 8. Testing Best Practices

### Test Writing Standards
*   **REQUIRED:** Follow AAA pattern (Arrange, Act, Assert)
*   **MANDATORY:** One assertion per test when possible
*   **CRITICAL:** Test the happy path and error conditions
*   **REQUIRED:** Use descriptive test names that explain the scenario

### Test Maintenance
*   **REQUIRED:** Keep tests up to date with code changes
*   **MANDATORY:** Remove obsolete tests when features are removed
*   **CRITICAL:** Refactor tests when they become difficult to maintain
*   **REQUIRED:** Document complex test scenarios

## 9. Performance and Reliability
*   **CRITICAL:** Tests must run consistently across environments
*   **REQUIRED:** Total test suite should complete in under 10 minutes
*   **MANDATORY:** Implement proper test parallelization where possible
*   **REQUIRED:** Monitor test flakiness and fix unstable tests

## 10. Forbidden Patterns
*   **NEVER** commit tests that depend on external services
*   **NEVER** use real API keys or credentials in tests
*   **NEVER** write tests that modify production data
*   **NEVER** ignore failing tests (fix or skip with explanation)
*   **NEVER** use sleep() for timing in tests (use proper waits)
*   **NEVER** test implementation details (test behavior, not internals)
