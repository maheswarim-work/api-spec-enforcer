# OpenAPI Compliance Skill

A comprehensive skill for analyzing API implementation compliance against OpenAPI specifications and generating tests.

## Skill Description

This skill enables analysis of FastAPI applications against their OpenAPI specifications and automated test generation. It combines:
- **Compliance Analysis**: Parse specs, inspect code, generate reports
- **Test Generation**: Create pytest suites from API contracts

## Capabilities

### Compliance Analysis
- Parse OpenAPI 3.0 YAML specifications
- Inspect FastAPI route definitions via AST analysis
- Compare implemented endpoints against spec requirements
- Generate detailed compliance reports

### Test Generation
- Generate async pytest test functions
- Create test fixtures for httpx AsyncClient
- Validate response status codes and schemas
- Support for CRUD operation test patterns

## When to Use

Use this skill when you need to:
- Audit an API implementation for spec compliance
- Identify missing or mismatched endpoints
- Validate response schemas match the spec
- Bootstrap a test suite for a new API
- Ensure all spec endpoints have test coverage
- Generate regression tests after adding endpoints

## Input Requirements

1. **OpenAPI Spec** - Path to a valid OpenAPI 3.0 YAML file
2. **Service Path** - Path to a FastAPI service directory containing:
   - `main.py` or `app.py` with FastAPI application
   - `routes.py` with route definitions
   - `schemas.py` with Pydantic models

## Compliance Analysis Process

### Step 1: Parse OpenAPI Specification
```python
from core.openapi_parser import OpenAPIParser

parser = OpenAPIParser("spec/openapi.yaml")
parser.parse()

print(f"API: {parser.title} v{parser.version}")
print(f"Endpoints: {len(parser.endpoints)}")
print(f"Schemas: {len(parser.schemas)}")
```

### Step 2: Inspect Implementation
```python
from core.fastapi_inspector import FastAPIInspector

inspector = FastAPIInspector("services/user_service")
inspector.inspect()

for endpoint in inspector.endpoints:
    print(f"{endpoint.method} {endpoint.path}")
```

### Step 3: Run Compliance Check
```python
from core.compliance_checker import ComplianceChecker

checker = ComplianceChecker(parser, inspector)
report = checker.check()

print(report.format_report())
```

## Test Generation Process

### Step 1: Parse Endpoints from Spec
```python
from core.openapi_parser import OpenAPIParser

parser = OpenAPIParser("spec/openapi.yaml")
parser.parse()

endpoints = parser.endpoints
```

### Step 2: Generate Tests
```python
from agents.test_agent import TestAgent

test_agent = TestAgent()
result = test_agent.execute(endpoints=endpoints)

print(f"Generated {result.output.test_count} tests")
```

### Step 3: Write Test File
```python
content = test_agent.write_tests(result.output, dry_run=False)
print(f"Written to: {result.output.output_file}")
```

## Output Formats

### Compliance Report
```
============================================================
API COMPLIANCE REPORT
============================================================
Spec: User Management API v1.0.0
------------------------------------------------------------
Endpoints in spec:        5
Endpoints implemented:    2
Compliant endpoints:      2
Compliance:               40.0%
------------------------------------------------------------
Errors:   3
Warnings: 0
------------------------------------------------------------
ISSUES:
  [ERROR] Missing endpoint: POST /users
  [ERROR] Missing endpoint: PUT /users/{user_id}
  [ERROR] Missing endpoint: DELETE /users/{user_id}
============================================================
```

### Issue Categories
| Type | Severity | Description |
|------|----------|-------------|
| `MISSING_ENDPOINT` | ERROR | Spec endpoint not implemented |
| `EXTRA_ENDPOINT` | WARNING | Implemented but not in spec |
| `SCHEMA_MISMATCH` | WARNING | Response schema differences |
| `MISSING_FIELD` | ERROR | Required field not in schema |

### Generated Test Structure
```python
"""Auto-generated API tests."""

import pytest
from httpx import AsyncClient, ASGITransport
from services.user_service.main import app

@pytest.fixture
async def client():
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

async def test_get_users(client: AsyncClient) -> None:
    """Test GET /users."""
    response = await client.get("/users")

    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert "total" in data
```

## Running Tests

```bash
# Run all generated tests
pytest tests/generated/ -v

# Run with coverage
pytest tests/generated/ --cov=services --cov-report=html

# Run specific endpoint test
pytest tests/generated/test_api_endpoints.py::test_get_users -v
```

## Integration with MCP

This skill uses the MCP context provider for selective context:
```python
from mcp.context_provider import ContextProvider, ContextType

provider = ContextProvider(".")
context = provider.get_context([ContextType.SPEC, ContextType.SERVICE])

# Only spec and service files are loaded - not the entire repo
print(f"Context items: {len(context.items)}")
print(f"Estimated tokens: {context.total_tokens_estimate}")
```

## Compliance Rules

Based on `spec/non_functional_spec.md`:
1. All spec endpoints must be implemented
2. Existing endpoints must not be modified (non-breaking)
3. Response schemas must match exactly
4. All handlers must use `async def`
5. Type hints required on all functions
6. Minimum 80% code coverage for core modules
7. 100% coverage for endpoint handlers
