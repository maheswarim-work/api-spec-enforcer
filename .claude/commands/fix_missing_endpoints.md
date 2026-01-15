# Fix Missing Endpoints

Generate and apply code fixes for endpoints defined in the spec but missing from the implementation.

## Usage

Run this command after `/check_api_compliance` reveals missing endpoints. This command will:
- Generate placeholder implementations for missing endpoints
- Ensure correct function signatures and response schemas
- Apply non-breaking changes only (no modifications to existing code)

## Instructions

1. Run compliance check to identify missing endpoints
2. Use FixAgent to generate code for each missing endpoint
3. Show the generated code for review
4. Apply fixes to `services/user_service/routes.py`

Execute the following Python code:

```python
from pathlib import Path
from core.openapi_parser import OpenAPIParser
from core.fastapi_inspector import FastAPIInspector
from core.compliance_checker import ComplianceChecker
from agents.fix_agent import FixAgent

# Run compliance check first
parser = OpenAPIParser(Path("spec/openapi.yaml"))
parser.parse()

inspector = FastAPIInspector(Path("services/user_service"))
inspector.inspect()

checker = ComplianceChecker(parser, inspector)
report = checker.check()

# Get missing endpoints
missing = checker.get_missing_endpoints()

if missing:
    print(f"Found {len(missing)} missing endpoints. Generating fixes...")

    # Generate fixes
    fix_agent = FixAgent()
    result = fix_agent.execute(
        compliance_report=report,
        missing_endpoints=missing,
        service_path=Path("services/user_service")
    )

    # Show what will be added
    print(fix_agent.format_output())

    # Apply fixes (set dry_run=False to actually write)
    changes = fix_agent.apply_fixes(result.output, dry_run=True)
    for file_path, content in changes.items():
        print(f"\n=== Changes for {file_path} ===")
        print(content[-500:])  # Show last 500 chars
else:
    print("No missing endpoints - implementation is compliant!")
```

Alternatively, run:
```bash
python scripts/demo_fix.py
```

## Non-Breaking Changes Policy

Generated fixes follow these rules from `spec/non_functional_spec.md`:
- Only ADD new endpoints, never modify existing ones
- Use correct status codes (201 for POST, 204 for DELETE)
- All handlers use `async def`
- Include proper type hints and docstrings
- Response schemas match the spec exactly

## Generated Code Structure

Each generated endpoint includes:
1. Route decorator with correct path and status code
2. Async function with typed parameters
3. Docstring from spec description
4. Placeholder implementation (TODO comments)
5. Proper error handling with HTTPException

## Context Provided (MCP)

This command uses:
- `spec/openapi.yaml` - Endpoint definitions
- `spec/non_functional_spec.md` - Code style requirements
- `services/user_service/routes.py` - File to modify
- `services/user_service/schemas.py` - Existing Pydantic models
