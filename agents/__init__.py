"""Multi-agent system for API contract enforcement.

This is a compatibility wrapper that re-exports from .claude/agents/.
"""

import importlib.util
import sys
from pathlib import Path

# Path to the actual implementation
_impl_path = Path(__file__).parent.parent / ".claude" / "agents"


def _load_module(name: str, file_path: Path):
    """Load a module from a file path."""
    spec = importlib.util.spec_from_file_location(name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Load base module first (needed by other modules)
_base = _load_module("_claude_agents_base", _impl_path / "base.py")
Agent = _base.Agent
AgentResult = _base.AgentResult
AgentStatus = _base.AgentStatus

# Patch the module lookup so relative imports work
sys.modules["agents.base"] = _base

# Load agent modules
_spec_agent = _load_module(
    "_claude_agents_spec_agent", _impl_path / "spec_validator" / "spec_agent.py"
)
SpecAgent = _spec_agent.SpecAgent

_code_agent = _load_module(
    "_claude_agents_code_agent", _impl_path / "spec_validator" / "code_agent.py"
)
CodeAgent = _code_agent.CodeAgent

_fix_agent = _load_module(
    "_claude_agents_fix_agent", _impl_path / "gap_fixer" / "fix_agent.py"
)
FixAgent = _fix_agent.FixAgent

_test_agent = _load_module(
    "_claude_agents_test_agent", _impl_path / "test_generator" / "test_agent.py"
)
TestAgent = _test_agent.TestAgent

_review_agent = _load_module(
    "_claude_agents_review_agent", _impl_path / "review_agent.py"
)
ReviewAgent = _review_agent.ReviewAgent

__all__ = [
    "Agent",
    "AgentResult",
    "AgentStatus",
    "CodeAgent",
    "FixAgent",
    "ReviewAgent",
    "SpecAgent",
    "TestAgent",
]
