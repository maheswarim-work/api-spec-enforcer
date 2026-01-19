# Run Agent

Run a specific agent from the multi-agent system.

## Usage

```
/run-agent <agent-name>
```

Where `<agent-name>` is one of:
- `spec-validator` - Validate implementation against OpenAPI spec
- `gap-fixer` - Generate code for missing endpoints
- `test-generator` - Generate pytest tests from spec

## Instructions

When the user runs this command, use the Task tool to spawn a sub-agent:

```
Task(
  subagent_type="general-purpose",
  prompt="Read the agent instructions from .claude/agents/<agent-name>/AGENT.md and execute the agent's task. Use the core/ modules as described in the instructions."
)
```

## Example

User: `/run-agent spec-validator`

Claude should:
1. Read `.claude/agents/spec_validator/AGENT.md`
2. Use Task tool with `general-purpose` subagent
3. Execute the compliance check as described
4. Return the results
