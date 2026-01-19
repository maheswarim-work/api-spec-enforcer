# Generate API Tests

Generate pytest tests for all API endpoints defined in the OpenAPI specification.

## Usage

Run this command to automatically generate test cases for your API endpoints. Tests will:
- Cover all endpoints in the spec
- Validate response status codes
- Check required fields in responses
- Use async test client (httpx)

## Instructions

1. Parse the OpenAPI spec to get all endpoint definitions
2. Use TestAgent to generate pytest test functions
3. Write tests to `tests/generated/test_api_endpoints.py`
4. Run the tests to verify they pass

## Quick Run

```bash
# Generate tests
python scripts/demo_generate_tests.py

# Run generated tests
pytest tests/generated/ -v
```

## Programmatic Usage

```python
from pathlib import Path
from core.openapi_parser import OpenAPIParser
from agents import TestAgent

# Parse the spec
parser = OpenAPIParser(Path("spec/openapi.yaml"))
parser.parse()

# Generate tests for all endpoints
test_agent = TestAgent()
result = test_agent.execute(endpoints=parser.endpoints)

# Show summary
print(test_agent.format_output())

# Write test file
test_content = test_agent.write_tests(result.output, dry_run=False)
print(f"\nTests written to: {result.output.output_file}")
print(f"\nGenerated {result.output.test_count} tests")
```

## Generated Test Structure

Each test function:
```python
async def test_get_users(client: AsyncClient) -> None:
    """Test GET /users."""
    response = await client.get("/users")

    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert "total" in data
```

## Test Categories

Generated tests cover:
1. **Happy path** - Successful requests with valid data
2. **Status codes** - Correct HTTP status for each operation
3. **Schema validation** - Required fields present in response
4. **Basic assertions** - Response structure matches spec

## Running Tests

```bash
# Run all generated tests
pytest tests/generated/ -v

# Run with coverage
pytest tests/generated/ --cov=services --cov-report=term-missing

# Run specific test
pytest tests/generated/test_api_endpoints.py::test_get_users -v
```

## Context Provided (MCP)

This command uses:
- `spec/openapi.yaml` - Endpoint and schema definitions
- `services/user_service/main.py` - FastAPI app for test client
