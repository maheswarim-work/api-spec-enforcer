# Check API Compliance

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

Execute the following Python code to run the compliance check:

```python
from pathlib import Path
from core.openapi_parser import OpenAPIParser
from core.fastapi_inspector import FastAPIInspector
from core.compliance_checker import ComplianceChecker

# Parse the spec
parser = OpenAPIParser(Path("spec/openapi.yaml"))
parser.parse()

# Inspect the service
inspector = FastAPIInspector(Path("services/user_service"))
inspector.inspect()

# Run compliance check
checker = ComplianceChecker(parser, inspector)
report = checker.check()

# Display report
print(report.format_report())
```

Alternatively, run the demo script:
```bash
python scripts/demo_compliance.py
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
