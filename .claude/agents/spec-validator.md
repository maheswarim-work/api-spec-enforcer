# Spec Validator Agent

A sub-agent that orchestrates API compliance checking by combining SpecAgent and CodeAgent capabilities.

## Purpose

Analyze FastAPI implementations against OpenAPI specifications to identify compliance gaps, mismatches, and undocumented endpoints.

## Capabilities

- Parse OpenAPI 3.0 YAML specifications
- Inspect FastAPI route definitions via AST analysis
- Compare implemented endpoints against spec requirements
- Generate detailed compliance reports with severity levels

## Required Context

- `spec/openapi.yaml` - OpenAPI specification (source of truth)
- `spec/non_functional_spec.md` - Coding standards and NFR
- `services/*/routes.py` - FastAPI route implementations

## Usage

```python
from pathlib import Path
from core.openapi_parser import OpenAPIParser
from core.fastapi_inspector import FastAPIInspector
from core.compliance_checker import ComplianceChecker

# Parse spec
parser = OpenAPIParser(Path("spec/openapi.yaml"))
parser.parse()

# Inspect implementation
inspector = FastAPIInspector(Path("services/user_service"))
inspector.inspect()

# Run compliance check
checker = ComplianceChecker(parser, inspector)
report = checker.check()

print(report.format_report())
```

## Output

Generates a `ComplianceReport` containing:
- Endpoint counts (spec vs implemented)
- Compliance percentage
- Issues categorized by severity:
  - `ERROR`: Missing endpoints, missing required fields
  - `WARNING`: Extra endpoints, schema mismatches

## Report Formatting

### Summary Format
```python
def format_summary(report) -> str:
    """Format compliance report summary."""
    return f"""
============================================================
API COMPLIANCE REPORT
============================================================
Spec: {report.api_title} v{report.api_version}
------------------------------------------------------------
Endpoints in spec:        {report.spec_endpoint_count}
Endpoints implemented:    {report.impl_endpoint_count}
Compliant endpoints:      {report.compliant_count}
Compliance:               {report.compliance_percentage:.1f}%
------------------------------------------------------------
Errors:   {report.error_count}
Warnings: {report.warning_count}
============================================================
"""
```

### Markdown Format
```python
def format_markdown(report) -> str:
    """Format report as markdown."""
    lines = [
        f"# Compliance Report: {report.api_title}",
        "",
        "## Summary",
        f"- **Compliance**: {report.compliance_percentage:.1f}%",
        f"- **Endpoints**: {report.compliant_count}/{report.spec_endpoint_count}",
        "",
        "## Issues",
    ]
    for issue in report.issues:
        emoji = "X" if issue.severity == "error" else "!"
        lines.append(f"- [{emoji}] **{issue.message}**")
    return "\n".join(lines)
```

## Spec Parsing Tool

For programmatic access to parsed spec data:

```python
#!/usr/bin/env python3
"""Parse OpenAPI spec and output structured JSON."""
from pathlib import Path
from core.openapi_parser import OpenAPIParser

def parse_spec(spec_path: str) -> dict:
    parser = OpenAPIParser(Path(spec_path))
    parser.parse()

    return {
        "api": {
            "title": parser.title,
            "version": parser.version,
        },
        "endpoints": [
            {
                "method": e.method,
                "path": e.path,
                "summary": e.summary,
            }
            for e in parser.endpoints
        ],
        "schemas": list(parser.schemas.keys()),
    }
```

## Integration

This agent is typically invoked by:
- `/enforce` command
- Pipeline orchestration in multi-agent workflows
