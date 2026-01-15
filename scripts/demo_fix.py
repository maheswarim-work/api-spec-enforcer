#!/usr/bin/env python3
"""Demo script: Fix missing endpoints.

This script demonstrates the endpoint fix workflow:
1. Run compliance check to find missing endpoints
2. Generate code fixes using FixAgent
3. Apply fixes to the service (with confirmation)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.openapi_parser import OpenAPIParser
from core.fastapi_inspector import FastAPIInspector
from core.compliance_checker import ComplianceChecker
from agents.fix_agent import FixAgent


def main() -> None:
    """Run fix generation demonstration."""
    print("=" * 60)
    print("API Contract Enforcer - Fix Missing Endpoints Demo")
    print("=" * 60)
    print()

    # Run compliance check
    print("1. Running compliance check...")
    spec_path = project_root / "spec" / "openapi.yaml"
    service_path = project_root / "services" / "user_service"

    parser = OpenAPIParser(spec_path)
    parser.parse()

    inspector = FastAPIInspector(service_path)
    inspector.inspect()

    checker = ComplianceChecker(parser, inspector)
    report = checker.check()

    print(f"   Compliance: {report.compliance_percentage:.0f}%")
    print(f"   Missing endpoints: {report.error_count}")
    print()

    # Get missing endpoints
    missing = checker.get_missing_endpoints()

    if not missing:
        print("No missing endpoints - implementation is fully compliant!")
        sys.exit(0)

    print("2. Missing endpoints detected:")
    for endpoint in missing:
        print(f"   - {endpoint.method} {endpoint.path}")
    print()

    # Generate fixes
    print("3. Generating fixes...")
    fix_agent = FixAgent()
    result = fix_agent.execute(
        compliance_report=report,
        missing_endpoints=missing,
        service_path=service_path,
    )

    fix_result = result.output
    print(f"   Generated {fix_result.endpoints_fixed} endpoint fixes")
    print()

    # Show generated code
    print("4. Generated code preview:")
    print("-" * 60)
    for fix in fix_result.fixes:
        if fix.fix_type == "endpoint":
            print(f"\n# {fix.description}")
            print(fix.code)
    print("-" * 60)
    print()

    # Dry run - show what would change
    print("5. Files that would be modified:")
    changes = fix_agent.apply_fixes(fix_result, dry_run=True)
    for file_path in changes:
        print(f"   - {file_path}")
    print()

    # Ask for confirmation
    print("6. Apply fixes?")
    print("   Run with --apply flag to write changes to disk")
    print()

    if len(sys.argv) > 1 and sys.argv[1] == "--apply":
        print("   Applying fixes...")
        fix_agent.apply_fixes(fix_result, dry_run=False)
        print("   Done! Fixes applied.")
        print()
        print("   Run compliance check again to verify:")
        print("   python scripts/demo_compliance.py")
    else:
        print("   Dry run complete. No files were modified.")


if __name__ == "__main__":
    main()
