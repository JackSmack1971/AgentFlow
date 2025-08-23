# AGENTS.md: API Testing Standards

This document provides specific guidance for AI models working with AgentFlow API testing using Postman collections located in `/postman/`. These guidelines are derived from the Postman testing ruleset and GitHub Workflows integration standards.

## 1. Project Scope & Architecture
*   **Primary Purpose:** API testing collections and environments for AgentFlow platform with CI/CD integration via Newman
*   **Core Technologies:** Postman collections, Newman CLI, environment variables, automated API testing
*   **Architecture Pattern:** Collection-based testing with environment separation and CI/CD automation

## 2. Collection Organization Standards

### Directory Structure
*   **REQUIRED:** Store collections and environments under `/postman/`:
    ```
    postman/
    ├── collections/
    │   ├── auth.postman_collection.json
    │   ├── agents.postman_collection.json
    │   ├── memory.postman_collection.json
    │   ├── rag.postman_collection.json
    │   └── health.postman_collection.json
    ├── environments/
    │   ├── development.postman_environment.json
    │   ├── staging.postman_environment.json
    │   └── production.postman_environment.json
    └── data/
        ├── test-users.json
        └── sample-agents.json
    ```

### Collection Structure Requirements
*   **MANDATORY:** Organize requests by feature domain matching API router structure
*   **REQUIRED:** Use descriptive folder names that match `/app/routers/` organization
*   **CRITICAL:** Include both success and failure test scenarios for each endpoint
*   **REQUIRED:** Implement proper request dependencies and sequencing

## 3. Environment Management

### Variable Configuration
*   **CRITICAL:** Use separate environments for development, staging, and production
*   **MANDATORY:** Store sensitive data only in "current value" field, keep "initial value" empty
*   **REQUIRED:** Use `{{baseUrl}}` variable for all API endpoints
*   **CRITICAL:** Implement proper variable scoping (global, collection, environment)

```json
{
  "name": "development",
  "values": [
    {
      "key": "baseUrl",
      "value": "http://localhost:8000",
      "enabled": true
    },
    {
      "key": "api_key",
      "value": "",
      "enabled": true
    }
  ]
}
```

### Security Requirements
*   **CRITICAL:** Never hardcode API keys, passwords, or tokens in collections
*   **MANDATORY:** Use environment variables for all sensitive authentication data
*   **REQUIRED:** Implement token refresh logic in pre-request scripts for long-running test suites
*   **CRITICAL:** Mask sensitive variables in CI/CD environments

## 4. Request and Response Patterns

### Request Structure Standards
*   **REQUIRED:** Use consistent header patterns across all requests
*   **MANDATORY:** Include proper `Content-Type` headers for POST/PUT requests
*   **CRITICAL:** Implement proper authentication patterns (Bearer tokens, API keys)
*   **REQUIRED:** Use variables for dynamic data instead of hardcoded values

```javascript
// Pre-request script example
pm.environment.set("timestamp", Date.now());
pm.environment.set("requestId", pm.variables.replaceIn("{{$guid}}"));
```

### Response Validation
*   **MANDATORY:** Use `pm.test()` with descriptive names and `pm.expect()` for assertions
*   **REQUIRED:** Validate response status codes, headers, and body structure
*   **CRITICAL:** Include performance assertions with reasonable thresholds
*   **REQUIRED:** Extract and store response data for subsequent requests

```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response time is acceptable", function () {
    pm.expect(pm.response.responseTime).to.be.below(2000);
});

pm.test("Response has required fields", function () {
    const responseJson = pm.response.json();
    pm.expect(responseJson).to.have.property("id");
    pm.expect(responseJson).to.have.property("name");
});
```

## 5. Authentication Testing Patterns

### Token Management
*   **REQUIRED:** Implement automatic token refresh logic
*   **MANDATORY:** Test authentication scenarios: valid auth, expired tokens, unauthorized access
*   **CRITICAL:** Validate proper security headers in responses
*   **REQUIRED:** Test CORS configuration and policies

```javascript
// Authentication pre-request script
const tokenExpiry = pm.environment.get("token_expiry");
const currentTime = Date.now();

if (!tokenExpiry || currentTime >= tokenExpiry) {
    // Refresh token logic
    pm.sendRequest({
        url: pm.environment.get("baseUrl") + "/auth/refresh",
        method: "POST",
        header: {
            "Content-Type": "application/json"
        },
        body: {
            mode: "raw",
            raw: JSON.stringify({
                refresh_token: pm.environment.get("refresh_token")
            })
        }
    }, function(err, response) {
        if (response.code === 200) {
            const tokens = response.json();
            pm.environment.set("access_token", tokens.access_token);
            pm.environment.set("token_expiry", currentTime + (tokens.expires_in * 1000));
        }
    });
}
```

## 6. Schema Validation Standards

### JSON Schema Validation
*   **REQUIRED:** Use JSON schema validation for complex response structures
*   **MANDATORY:** Maintain schemas for all API response models
*   **CRITICAL:** Validate both success and error response schemas
*   **REQUIRED:** Update schemas when API contracts change

```javascript
const responseSchema = {
    type: "object",
    required: ["id", "name", "status", "created_at"],
    properties: {
        id: { type: "string", format: "uuid" },
        name: { type: "string", minLength: 1, maxLength: 100 },
        status: { type: "string", enum: ["active", "inactive"] },
        created_at: { type: "string", format: "date-time" }
    }
};

pm.test("Response schema is valid", function() {
    pm.response.to.have.jsonSchema(responseSchema);
});
```

## 7. Newman CLI Integration

### CI/CD Configuration
*   **MANDATORY:** Include Newman execution in GitHub Actions workflows
*   **REQUIRED:** Use appropriate reporter formats for CI environments
*   **CRITICAL:** Set proper exit codes and error handling
*   **REQUIRED:** Generate HTML reports as CI artifacts

```bash
# Newman execution in CI
newman run postman/collections/auth.postman_collection.json \
    --environment postman/environments/staging.postman_environment.json \
    --reporters cli,junit,html \
    --reporter-junit-export results/auth-results.xml \
    --reporter-html-export results/auth-report.html \
    --timeout-request 10000 \
    --timeout-script 5000
```

### Performance Thresholds
*   **REQUIRED:** Set response time thresholds for critical endpoints
*   **MANDATORY:** Monitor and alert on performance degradation
*   **CRITICAL:** Include latency assertions in test scripts
*   **REQUIRED:** Use environment-specific performance baselines

## 8. Data Management

### Test Data Organization
*   **REQUIRED:** Use external data files for complex test scenarios
*   **MANDATORY:** Implement proper test data cleanup procedures
*   **CRITICAL:** Avoid using production data in test environments
*   **REQUIRED:** Create realistic but anonymized test datasets

```javascript
// Using external data file
const testData = pm.iterationData.get("agent_data");
pm.request.body.raw = JSON.stringify({
    name: testData.name,
    description: testData.description,
    model: testData.model
});
```

## 9. Error Testing Patterns

### Error Scenario Coverage
*   **MANDATORY:** Test all documented error conditions
*   **REQUIRED:** Validate error response formats and codes
*   **CRITICAL:** Test edge cases and boundary conditions
*   **REQUIRED:** Verify proper error message formats

```javascript
pm.test("Error response format is correct", function() {
    if (pm.response.code !== 200) {
        const errorResponse = pm.response.json();
        pm.expect(errorResponse).to.have.property("error");
        pm.expect(errorResponse).to.have.property("message");
        pm.expect(errorResponse).to.have.property("code");
    }
});
```

## 10. Collection Maintenance Standards

### Version Control
*   **REQUIRED:** Export collections and environments to JSON files
*   **MANDATORY:** Use semantic versioning for collection releases
*   **CRITICAL:** Document API changes in collection descriptions
*   **REQUIRED:** Maintain backward compatibility within major versions

### Documentation Requirements
*   **MANDATORY:** Include comprehensive request descriptions
*   **REQUIRED:** Document expected responses and error conditions
*   **CRITICAL:** Provide usage examples for complex endpoints
*   **REQUIRED:** Keep documentation synchronized with API changes

## 11. SSL/TLS Requirements [Hard Constraint]
*   **CRITICAL:** SSL/TLS must be enabled in production environments
*   **MANDATORY:** Use `--insecure` flag only in development environments
*   **REQUIRED:** Test certificate validation in staging environments
*   **CRITICAL:** Never ignore SSL errors in production Newman runs

## 12. Forbidden Patterns
*   **NEVER** hardcode sensitive data in collection files
*   **NEVER** ignore SSL certificate errors in production
*   **NEVER** rely on specific execution order between unrelated tests
*   **NEVER** use production credentials in non-production environments
*   **NEVER** skip error scenario testing
*   **NEVER** commit environment files with sensitive current values
*   **NEVER** use deprecated Postman features or legacy formats
