# Gap Fixer Agent

A sub-agent that generates code fixes for missing API endpoints identified by compliance checks.

## Purpose

Automatically generate Python code to implement missing endpoints, following the non-breaking changes principle (only adds new code, never modifies existing endpoints).

## Capabilities

- Generate async FastAPI endpoint handlers
- Create proper type hints and docstrings
- Match response schemas to OpenAPI spec
- Handle imports and dependencies automatically

## Required Context

- `spec/openapi.yaml` - Endpoint definitions and schemas
- `spec/non_functional_spec.md` - Code style requirements
- `services/*/routes.py` - Existing route implementations
- `services/*/schemas.py` - Pydantic models

## Usage

```python
from pathlib import Path
from agents import FixAgent
from core.compliance_checker import ComplianceChecker

# After running compliance check
missing = checker.get_missing_endpoints()

# Generate fixes
fix_agent = FixAgent()
result = fix_agent.execute(
    compliance_report=report,
    missing_endpoints=missing,
    service_path=Path("services/user_service")
)

# Preview changes
print(fix_agent.format_output())

# Apply fixes (dry_run=False to write)
changes = fix_agent.apply_fixes(result.output, dry_run=True)
```

## Output

Generates a `FixResult` containing:
- List of `CodeFix` objects with generated code
- Count of endpoints and schemas to add
- List of files to be modified

## Code Generation Rules

Based on `spec/non_functional_spec.md`:
1. All handlers use `async def`
2. Include proper type hints
3. Add docstrings from spec descriptions
4. Use correct status codes (201 for POST, 204 for DELETE)
5. Never modify existing endpoints

## Endpoint Template

```python
@router.{{method}}("{{path}}"{{status_code}})
async def {{function_name}}({{parameters}}) -> {{return_type}}:
    """{{summary}}

    {{description}}
    """
    {{body}}
```

### Template Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `method` | HTTP method (lowercase) | `post`, `get`, `put`, `delete` |
| `path` | URL path | `/users`, `/users/{user_id}` |
| `status_code` | Optional status code | `, status_code=201` |
| `function_name` | Python function name | `create_user` |
| `parameters` | Function parameters | `data: UserCreate` |
| `return_type` | Return type hint | `User`, `None` |

## Examples

### POST Endpoint
```python
@router.post("/users", status_code=201)
async def create_user(data: UserCreate) -> User:
    """Create a new user

    Create a new user with the provided information
    """
    user_data = await db_create_user(
        email=data.email,
        name=data.name,
    )
    return User(**user_data)
```

### DELETE Endpoint
```python
@router.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: int) -> None:
    """Delete user by ID

    Permanently delete a user from the system
    """
    deleted = await db_delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
```

## Integration

This agent is typically invoked by:
- `/fix-gaps` command
- Pipeline orchestration after compliance check fails
