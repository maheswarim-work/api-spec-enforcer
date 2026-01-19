# Enforce API Compliance

Check the FastAPI service implementation against the OpenAPI specification.

## Usage

Run this command to generate a compliance report showing:
- Missing endpoints (in spec but not implemented)
- Extra endpoints (implemented but not in spec)
- Schema mismatches
- Status code discrepancies

## Instructions

1. Parse the OpenAPI spec at `spec/openapi.yaml` using the SpecAgent
2. Inspect the service at `services/user_service` using the CodeAgent
3. Run the ComplianceChecker to compare spec vs implementation
4. Generate and display a formatted compliance report

## Quick Run

```bash
python scripts/demo_compliance.py
```

## Programmatic Usage

```python
from pathlib import Path
from core.openapi_parser import OpenAPIParser
from core.fastapi_inspector import FastAPIInspector
from core.compliance_checker import ComplianceChecker

def run_compliance_check(
    spec_path: str = "spec/openapi.yaml",
    service_path: str = "services/user_service"
) -> tuple:
    """Run a compliance check and return results."""
    parser = OpenAPIParser(Path(spec_path))
    parser.parse()

    inspector = FastAPIInspector(Path(service_path))
    inspector.inspect()

    checker = ComplianceChecker(parser, inspector)
    report = checker.check()

    return parser, inspector, checker, report

# Run check
parser, inspector, checker, report = run_compliance_check()
print(report.format_report())

# Get missing endpoints for follow-up
missing = checker.get_missing_endpoints()
```

## Expected Output

A compliance report showing:
- API title and version
- Number of endpoints in spec vs implemented
- Compliance percentage
- List of issues with severity levels
- Suggestions for fixing each issue

## Context Provided (MCP)

This command uses selective context loading:
- `spec/openapi.yaml` - The source of truth
- `spec/non_functional_spec.md` - Coding standards
- `services/user_service/*.py` - Implementation files
