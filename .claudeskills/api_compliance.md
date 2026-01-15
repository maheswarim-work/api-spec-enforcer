# API Compliance Analysis Skill

A reusable skill for analyzing API implementation compliance against OpenAPI specifications.

## Skill Description

This skill enables analysis of FastAPI applications against their OpenAPI specifications. It can:
- Parse OpenAPI 3.0 YAML specifications
- Inspect FastAPI route definitions via AST analysis
- Compare implemented endpoints against spec requirements
- Generate detailed compliance reports

## When to Use

Use this skill when you need to:
- Audit an API implementation for spec compliance
- Identify missing or mismatched endpoints
- Validate response schemas match the spec
- Check for undocumented endpoints

## Input Requirements

1. **OpenAPI Spec** - Path to a valid OpenAPI 3.0 YAML file
2. **Service Path** - Path to a FastAPI service directory containing:
   - `main.py` or `app.py` with FastAPI application
   - `routes.py` with route definitions
   - `schemas.py` with Pydantic models

## Analysis Process

### Step 1: Parse OpenAPI Specification
```python
from core.openapi_parser import OpenAPIParser

parser = OpenAPIParser("spec/openapi.yaml")
parser.parse()

# Access parsed data
print(f"API: {parser.title} v{parser.version}")
print(f"Endpoints: {len(parser.endpoints)}")
print(f"Schemas: {len(parser.schemas)}")
```

### Step 2: Inspect Implementation
```python
from core.fastapi_inspector import FastAPIInspector

inspector = FastAPIInspector("services/user_service")
inspector.inspect()

# Access discovered routes
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

## Output Format

The compliance report includes:
- **Summary**: Endpoint counts, compliance percentage
- **Issues**: Categorized by type and severity
  - `MISSING_ENDPOINT` (ERROR): Spec endpoint not implemented
  - `EXTRA_ENDPOINT` (WARNING): Implemented but not in spec
  - `SCHEMA_MISMATCH` (WARNING): Response schema differences
  - `MISSING_FIELD` (ERROR): Required field not in schema

## Example Report

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
           Endpoint: POST /users
           Suggestion: Implement POST handler for /users
  [ERROR] Missing endpoint: PUT /users/{user_id}
           Endpoint: PUT /users/{user_id}
           Suggestion: Implement PUT handler for /users/{user_id}
  [ERROR] Missing endpoint: DELETE /users/{user_id}
           Endpoint: DELETE /users/{user_id}
           Suggestion: Implement DELETE handler for /users/{user_id}
============================================================
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
