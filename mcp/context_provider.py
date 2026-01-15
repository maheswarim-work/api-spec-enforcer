"""MCP Context Provider for selective context loading.

This module demonstrates the Model Context Protocol (MCP) principle of providing
ONLY relevant context to agents, rather than dumping the entire repository.

The context provider supports different context types:
- SPEC: OpenAPI specification and non-functional requirements
- SERVICE: Target service source files
- DIFF: Changed files and git diffs
- STANDARDS: Coding standards and conventions

Each agent receives only the context it needs for its specific task.
"""

import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ContextType(str, Enum):
    """Types of context that can be provided to agents."""

    SPEC = "spec"  # OpenAPI spec and NFR documents
    SERVICE = "service"  # Target service source files
    DIFF = "diff"  # Git diffs and changed files
    STANDARDS = "standards"  # Coding standards summary
    COMPLIANCE = "compliance"  # Compliance report
    ALL = "all"  # All available context (use sparingly)


@dataclass
class ContextItem:
    """A single item of context."""

    path: str
    content: str
    context_type: ContextType
    description: str = ""


@dataclass
class Context:
    """Container for context items provided to an agent."""

    items: list[ContextItem] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_item(self, item: ContextItem) -> None:
        """Add a context item."""
        self.items.append(item)

    def get_by_type(self, context_type: ContextType) -> list[ContextItem]:
        """Get all items of a specific type."""
        return [item for item in self.items if item.context_type == context_type]

    def to_prompt(self) -> str:
        """Convert context to a formatted prompt string."""
        sections: list[str] = []

        for ctx_type in ContextType:
            items = self.get_by_type(ctx_type)
            if items and ctx_type != ContextType.ALL:
                section_name = ctx_type.value.upper()
                sections.append(f"=== {section_name} CONTEXT ===\n")

                for item in items:
                    if item.description:
                        sections.append(f"# {item.description}")
                    sections.append(f"# File: {item.path}\n")
                    sections.append(item.content)
                    sections.append("\n")

        return "\n".join(sections)

    @property
    def total_tokens_estimate(self) -> int:
        """Estimate total token count (rough approximation)."""
        total_chars = sum(len(item.content) for item in self.items)
        # Rough estimate: 1 token ≈ 4 characters
        return total_chars // 4


class ContextProvider:
    """Provides selective context to agents based on their needs.

    This class implements the MCP principle of minimal, relevant context.
    Instead of providing the entire repository, it supplies only the files
    and information each agent needs for its specific task.
    """

    def __init__(self, project_root: str | Path) -> None:
        """Initialize context provider.

        Args:
            project_root: Root directory of the project.
        """
        self.project_root = Path(project_root)
        self._spec_dir = self.project_root / "spec"
        self._services_dir = self.project_root / "services"

    def get_context(
        self,
        context_types: list[ContextType],
        service_path: str | None = None,
    ) -> Context:
        """Get context for specified types.

        Args:
            context_types: List of context types to include.
            service_path: Optional specific service path to include.

        Returns:
            Context object with requested items.
        """
        context = Context()

        for ctx_type in context_types:
            if ctx_type == ContextType.SPEC:
                self._add_spec_context(context)
            elif ctx_type == ContextType.SERVICE:
                self._add_service_context(context, service_path)
            elif ctx_type == ContextType.DIFF:
                self._add_diff_context(context)
            elif ctx_type == ContextType.STANDARDS:
                self._add_standards_context(context)
            elif ctx_type == ContextType.ALL:
                self._add_spec_context(context)
                self._add_service_context(context, service_path)
                self._add_diff_context(context)
                self._add_standards_context(context)

        return context

    def get_spec_context(self) -> Context:
        """Get only specification context.

        Returns:
            Context with spec files only.
        """
        return self.get_context([ContextType.SPEC])

    def get_service_context(self, service_path: str | None = None) -> Context:
        """Get only service source context.

        Args:
            service_path: Optional specific service path.

        Returns:
            Context with service files only.
        """
        return self.get_context([ContextType.SERVICE], service_path)

    def get_compliance_context(self, service_path: str | None = None) -> Context:
        """Get context needed for compliance checking.

        This provides both spec and service context for comparison.

        Args:
            service_path: Optional specific service path.

        Returns:
            Context with spec and service files.
        """
        return self.get_context([ContextType.SPEC, ContextType.SERVICE], service_path)

    def _add_spec_context(self, context: Context) -> None:
        """Add specification files to context."""
        # Add OpenAPI spec
        openapi_path = self._spec_dir / "openapi.yaml"
        if openapi_path.exists():
            context.add_item(
                ContextItem(
                    path=str(openapi_path.relative_to(self.project_root)),
                    content=openapi_path.read_text(),
                    context_type=ContextType.SPEC,
                    description="OpenAPI 3.0 specification (source of truth)",
                )
            )

        # Add non-functional requirements
        nfr_path = self._spec_dir / "non_functional_spec.md"
        if nfr_path.exists():
            context.add_item(
                ContextItem(
                    path=str(nfr_path.relative_to(self.project_root)),
                    content=nfr_path.read_text(),
                    context_type=ContextType.SPEC,
                    description="Non-functional requirements and coding standards",
                )
            )

    def _add_service_context(self, context: Context, service_path: str | None) -> None:
        """Add service source files to context."""
        if service_path:
            service_dir = self.project_root / service_path
        else:
            # Default to user_service
            service_dir = self._services_dir / "user_service"

        if not service_dir.exists():
            return

        # Add Python files from the service
        for py_file in service_dir.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue

            context.add_item(
                ContextItem(
                    path=str(py_file.relative_to(self.project_root)),
                    content=py_file.read_text(),
                    context_type=ContextType.SERVICE,
                    description=f"Service source file: {py_file.name}",
                )
            )

    def _add_diff_context(self, context: Context) -> None:
        """Add git diff information to context."""
        try:
            # Get unstaged changes
            result = subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )
            changed_files = result.stdout.strip().split("\n") if result.stdout.strip() else []

            # Get staged changes
            result = subprocess.run(
                ["git", "diff", "--staged", "--name-only"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )
            staged_files = result.stdout.strip().split("\n") if result.stdout.strip() else []

            all_changed = set(changed_files + staged_files)

            if all_changed and all_changed != {""}:
                # Get the actual diff content
                result = subprocess.run(
                    ["git", "diff", "HEAD"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                )

                if result.stdout.strip():
                    context.add_item(
                        ContextItem(
                            path="[git diff]",
                            content=result.stdout,
                            context_type=ContextType.DIFF,
                            description=f"Git diff for changed files: {', '.join(all_changed)}",
                        )
                    )
        except Exception:
            # Git not available or not a git repo
            pass

    def _add_standards_context(self, context: Context) -> None:
        """Add coding standards summary to context."""
        standards = """
# Coding Standards Summary

## Python Style
- Use async/await for all I/O operations
- Type hints required on all functions
- Google-style docstrings
- snake_case for functions, PascalCase for classes

## API Design
- RESTful conventions
- Consistent error responses with 'detail' field
- Pagination for list endpoints

## Testing
- pytest with async support
- One test per endpoint minimum
- 80% code coverage target
"""
        context.add_item(
            ContextItem(
                path="[standards]",
                content=standards,
                context_type=ContextType.STANDARDS,
                description="Coding standards and conventions",
            )
        )

    def list_available_services(self) -> list[str]:
        """List all available services.

        Returns:
            List of service directory names.
        """
        services = []
        if self._services_dir.exists():
            for item in self._services_dir.iterdir():
                if item.is_dir() and not item.name.startswith("_"):
                    services.append(item.name)
        return services

    def get_context_summary(self, context: Context) -> dict[str, Any]:
        """Get a summary of provided context.

        Args:
            context: Context object to summarize.

        Returns:
            Summary dictionary with counts and estimates.
        """
        type_counts: dict[str, int] = {}
        for item in context.items:
            key = item.context_type.value
            type_counts[key] = type_counts.get(key, 0) + 1

        return {
            "total_items": len(context.items),
            "items_by_type": type_counts,
            "estimated_tokens": context.total_tokens_estimate,
            "files": [item.path for item in context.items],
        }
