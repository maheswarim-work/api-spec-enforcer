# Test Generation Skill

A reusable skill for generating pytest tests from OpenAPI specifications.

## Skill Description

This skill generates comprehensive pytest test suites for FastAPI applications based on their OpenAPI specifications. Generated tests use:
- `pytest` with `pytest-asyncio` for async support
- `httpx.AsyncClient` for async HTTP requests
- ASGI transport for testing without running a server

## When to Use

Use this skill when you need to:
- Bootstrap a test suite for a new API
- Ensure all spec endpoints have test coverage
- Generate regression tests after adding endpoints
- Create integration tests from API contracts

## Input Requirements

1. **Endpoints** - List of `EndpointInfo` objects from parsed spec
2. **Output Directory** - Where to write generated test files (default: `tests/generated/`)

## Generation Process

### Step 1: Parse Endpoints from Spec
```python
from core.openapi_parser import OpenAPIParser

parser = OpenAPIParser("spec/openapi.yaml")
parser.parse()

endpoints = parser.endpoints  # List of EndpointInfo
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

## Generated Test Structure

### File Header
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
```

### Test Function Pattern
```python
async def test_get_users(client: AsyncClient) -> None:
    """Test GET /users."""
    response = await client.get("/users")

    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert "total" in data
```

### POST Request Test
```python
async def test_post_users(client: AsyncClient) -> None:
    """Test POST /users."""
    payload = {
        "email": "test@example.com",
        "name": "name_value",
    }
    response = await client.post("/users", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "email" in data
```

### DELETE Request Test
```python
async def test_delete_users_user_id(client: AsyncClient) -> None:
    """Test DELETE /users/{user_id}."""
    response = await client.delete("/users/1")

    assert response.status_code == 204
```

## Test Categories

Generated tests validate:

| Category | What's Checked |
|----------|----------------|
| Status Code | Response matches spec (200, 201, 204, etc.) |
| Required Fields | All required fields present in response |
| Schema Structure | Response shape matches spec |
| Request Body | Correct payload for POST/PUT |

## Running Generated Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all generated tests
pytest tests/generated/ -v

# Run with coverage
pytest tests/generated/ --cov=services --cov-report=html

# Run specific endpoint test
pytest tests/generated/test_api_endpoints.py::test_get_users -v

# Run only POST tests
pytest tests/generated/ -v -k "post"
```

## Customization

The CodeGenerator can be extended for custom test patterns:

```python
from core.code_generator import CodeGenerator

class CustomGenerator(CodeGenerator):
    def generate_test(self, endpoint):
        # Override to add custom assertions
        base_test = super().generate_test(endpoint)
        # Add additional checks...
        return base_test
```

## Coverage Target

From `spec/non_functional_spec.md`:
- Minimum 80% code coverage for core modules
- 100% coverage for endpoint handlers
- One test function per endpoint minimum

## Integration with CI/CD

Example GitHub Actions workflow:
```yaml
- name: Run Generated Tests
  run: |
    python scripts/demo_generate_tests.py
    pytest tests/generated/ --cov=services --cov-fail-under=80
```
