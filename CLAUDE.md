# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**API Contract Enforcer** - A spec-driven compliance checker that compares FastAPI implementations against OpenAPI specifications. Demonstrates Claude Code Skills, Commands, Multi-Agent workflows, and MCP context management.

## Commands

```bash
# Install dependencies
pip install -e ".[dev]"

# Run the FastAPI service
uvicorn services.user_service.main:app --reload

# Run compliance check
python scripts/demo_compliance.py

# Fix missing endpoints (dry run)
python scripts/demo_fix.py

# Apply fixes
python scripts/demo_fix.py --apply

# Generate tests
python scripts/demo_generate_tests.py

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=core --cov=services --cov-report=term-missing

# Lint
ruff check .

# Type check
mypy core mcp
```

## Architecture

### Core Components (`core/`)
- `openapi_parser.py` - Parses OpenAPI 3.0 YAML specs into structured EndpointInfo/SchemaInfo
- `fastapi_inspector.py` - AST-based inspection of FastAPI routes without execution
- `compliance_checker.py` - Compares spec vs implementation, generates ComplianceReport
- `code_generator.py` - Generates Python code for missing endpoints and tests
- `models.py` - Shared dataclasses: EndpointInfo, SchemaInfo, ComplianceIssue, etc.

### Multi-Agent System (`.claude/agents/`)
Pipeline: SpecAgent → CodeAgent → Checker → FixAgent/TestAgent → ReviewAgent

| Agent | Purpose |
|-------|---------|
| SpecAgent | Parse OpenAPI spec |
| CodeAgent | Inspect FastAPI routes |
| FixAgent | Generate missing endpoint code |
| TestAgent | Generate pytest tests |
| ReviewAgent | Validate final output |

### MCP Context Provider (`mcp/`)
Provides selective context to agents. Use `ContextProvider.get_context([ContextType.SPEC, ContextType.SERVICE])` instead of loading entire repo.

### Custom Commands (`.claude/commands/`)
- `/enforce` - Run API compliance check
- `/fix-gaps` - Generate code for missing endpoints
- `/gen-tests` - Generate pytest tests from spec
- `/run-agent` - Run a specific agent as a sub-agent

### Skills (`.claude/skills/`)
- `openapi-compliance/SKILL.md` - Comprehensive compliance and test generation skill

### Agents (`.claude/agents/`)
- `spec_validator/AGENT.md` - Validates implementation against OpenAPI spec (+ Python code)
- `gap_fixer/AGENT.md` - Generates code for missing endpoints (+ Python code)
- `test_generator/AGENT.md` - Generates pytest tests from spec (+ Python code)

## Using Sub-Agents with Task Tool

To run agents as Claude Code sub-agents, use the Task tool with `general-purpose` type:

```python
# Example: Run spec-validator as a sub-agent
Task(
  subagent_type="general-purpose",
  prompt="""
    Read .claude/agents/spec_validator/AGENT.md for instructions.
    Then run compliance check using:
    - core/openapi_parser.py to parse spec/openapi.yaml
    - core/fastapi_inspector.py to inspect services/user_service
    - core/compliance_checker.py to compare and generate report
    Return the compliance report.
  """
)
```

Available agents to spawn:
- `spec_validator` - Parse spec + inspect code + check compliance
- `gap_fixer` - Generate code for missing endpoints
- `test_generator` - Generate pytest tests from spec

## Key Files

- `spec/openapi.yaml` - Source of truth for API contract (5 endpoints)
- `spec/non_functional_spec.md` - Coding standards (async-only, type hints, 80% coverage)
- `services/user_service/routes.py` - FastAPI route implementations (all 5 endpoints + health check)

## Spec-Driven Approach

The OpenAPI spec is the single source of truth. All compliance checks, code generation, and tests derive from `spec/openapi.yaml`.

## Non-Breaking Changes Policy

FixAgent only adds new code - never modifies existing endpoints. Generated handlers use `async def`, include type hints, and follow patterns from non_functional_spec.md.
