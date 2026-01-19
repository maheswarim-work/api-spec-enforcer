# Test Generator Agent

A sub-agent that generates pytest tests for API endpoints defined in the OpenAPI specification.

## Purpose

Automatically create comprehensive test suites that validate API implementations against their specifications, ensuring correct status codes, response schemas, and required fields.

## Capabilities

- Generate async pytest test functions
- Create test fixtures for httpx AsyncClient
- Validate response status codes
- Check required fields in responses
- Support parameterized test generation

## Required Context

- `spec/openapi.yaml` - Endpoint definitions and expected responses
- `services/*/main.py` - FastAPI app for test client

## Usage

```python
from pathlib import Path
from core.openapi_parser import OpenAPIParser
from agents import TestAgent

# Parse spec
parser = OpenAPIParser(Path("spec/openapi.yaml"))
parser.parse()

# Generate tests
test_agent = TestAgent()
result = test_agent.execute(endpoints=parser.endpoints)

# Preview
print(test_agent.format_output())

# Write to file
test_agent.write_tests(result.output, dry_run=False)
```

## Output

Generates a `TestResult` containing:
- List of `GeneratedTest` objects
- Output file path
- Count of tests and endpoints covered

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

### Test Function Template

```python
async def {{test_name}}(client: AsyncClient) -> None:
    """Test {{method}} {{path}}."""
    {{setup}}
    response = await client.{{method_lower}}("{{url}}"{{payload}})

    assert response.status_code == {{status_code}}
    {{assertions}}
```

### Template Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `test_name` | Test function name | `test_get_users` |
| `method` | HTTP method | `GET`, `POST` |
| `method_lower` | HTTP method (lowercase) | `get`, `post` |
| `path` | URL path | `/users` |
| `url` | URL with test values | `/users/1` |
| `payload` | Request payload | `, json=payload` |
| `status_code` | Expected status | `200`, `201`, `204` |
| `setup` | Setup code | Create test data |
| `assertions` | Response assertions | Field checks |

## Test Examples

### GET List Test
```python
async def test_get_users(client: AsyncClient) -> None:
    """Test GET /users."""
    response = await client.get("/users")

    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert "total" in data
```

### POST Test with Unique Data
```python
async def test_post_users(client: AsyncClient) -> None:
    """Test POST /users."""
    payload = {
        "email": unique_email("post"),
        "name": "Test User",
    }
    response = await client.post("/users", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "email" in data
```

### DELETE Test with Setup
```python
async def test_delete_users_user_id(client: AsyncClient) -> None:
    """Test DELETE /users/{user_id}."""
    # First create a user to delete
    create_payload = {
        "email": unique_email("delete"),
        "name": "Delete Test User",
    }
    create_response = await client.post("/users", json=create_payload)
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]

    # Now delete the user
    response = await client.delete(f"/users/{user_id}")

    assert response.status_code == 204
```

## Test Categories

Generated tests cover:
1. **Happy path** - Successful requests with valid data
2. **Status codes** - Correct HTTP status for each operation
3. **Schema validation** - Required fields present in response

## Running Tests

```bash
# Run all generated tests
pytest tests/generated/ -v

# Run with coverage
pytest tests/generated/ --cov=services --cov-report=term-missing

# Run specific test
pytest tests/generated/test_api_endpoints.py::test_get_users -v
```

## Integration

This agent is typically invoked by:
- `/gen-tests` command
- CI/CD pipelines for test regeneration
