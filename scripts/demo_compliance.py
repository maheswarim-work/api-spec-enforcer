#!/usr/bin/env python3
"""Demo script: Check API compliance.

This script demonstrates the compliance checking workflow:
1. Parse the OpenAPI specification
2. Inspect the FastAPI service implementation
3. Compare and generate a compliance report
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.openapi_parser import OpenAPIParser
from core.fastapi_inspector import FastAPIInspector
from core.compliance_checker import ComplianceChecker
from mcp.context_provider import ContextProvider, ContextType


def main() -> None:
    """Run compliance check demonstration."""
    print("=" * 60)
    print("API Contract Enforcer - Compliance Check Demo")
    print("=" * 60)
    print()

    # Show MCP context usage
    print("1. Loading context via MCP...")
    provider = ContextProvider(project_root)
    context = provider.get_compliance_context()
    summary = provider.get_context_summary(context)
    print(f"   Loaded {summary['total_items']} context items")
    print(f"   Estimated tokens: {summary['estimated_tokens']}")
    print()

    # Parse spec
    print("2. Parsing OpenAPI specification...")
    spec_path = project_root / "spec" / "openapi.yaml"
    parser = OpenAPIParser(spec_path)
    parser.parse()
    print(f"   API: {parser.title} v{parser.version}")
    print(f"   Endpoints defined: {len(parser.endpoints)}")
    print()

    # Inspect service
    print("3. Inspecting FastAPI service...")
    service_path = project_root / "services" / "user_service"
    inspector = FastAPIInspector(service_path)
    inspector.inspect()
    print(f"   Endpoints found: {len(inspector.endpoints)}")
    print(f"   Schemas found: {len(inspector.schemas)}")
    print()

    # Run compliance check
    print("4. Running compliance check...")
    checker = ComplianceChecker(parser, inspector)
    report = checker.check()
    print()

    # Display report
    print(report.format_report())

    # Return exit code based on compliance
    if report.is_compliant:
        print("\nResult: COMPLIANT")
        sys.exit(0)
    else:
        print(f"\nResult: NON-COMPLIANT ({report.error_count} errors)")
        sys.exit(1)


if __name__ == "__main__":
    main()
