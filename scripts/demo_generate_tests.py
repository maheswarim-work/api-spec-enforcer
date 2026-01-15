#!/usr/bin/env python3
"""Demo script: Generate API tests.

This script demonstrates the test generation workflow:
1. Parse endpoints from OpenAPI spec
2. Generate pytest tests using TestAgent
3. Write tests to tests/generated/
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.openapi_parser import OpenAPIParser
from agents.test_agent import TestAgent


def main() -> None:
    """Run test generation demonstration."""
    print("=" * 60)
    print("API Contract Enforcer - Test Generation Demo")
    print("=" * 60)
    print()

    # Parse spec
    print("1. Parsing OpenAPI specification...")
    spec_path = project_root / "spec" / "openapi.yaml"
    parser = OpenAPIParser(spec_path)
    parser.parse()

    print(f"   API: {parser.title} v{parser.version}")
    print(f"   Endpoints to test: {len(parser.endpoints)}")
    print()

    # Show endpoints
    print("2. Endpoints found:")
    for endpoint in parser.endpoints:
        print(f"   - {endpoint.method:6} {endpoint.path}")
    print()

    # Generate tests
    print("3. Generating tests...")
    test_agent = TestAgent()
    result = test_agent.execute(
        endpoints=parser.endpoints,
        output_dir=project_root / "tests" / "generated",
    )

    test_result = result.output
    print(f"   Generated {test_result.test_count} test functions")
    print()

    # Show generated tests
    print("4. Generated test functions:")
    for test in test_result.tests:
        print(f"   - {test.function_name}")
    print()

    # Write to file
    print("5. Writing tests to file...")
    content = test_agent.write_tests(test_result, dry_run=False)
    print(f"   Output: {test_result.output_file}")
    print()

    # Show preview
    print("6. Test file preview (first 50 lines):")
    print("-" * 60)
    lines = content.split("\n")[:50]
    for line in lines:
        print(line)
    if len(content.split("\n")) > 50:
        print("... (truncated)")
    print("-" * 60)
    print()

    # Instructions
    print("7. Run the generated tests:")
    print("   pytest tests/generated/ -v")
    print()
    print("   With coverage:")
    print("   pytest tests/generated/ --cov=services --cov-report=term-missing")


if __name__ == "__main__":
    main()
