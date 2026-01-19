"""CodeAgent - Inspects current codebase for endpoints and schemas."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..base import Agent
from core.fastapi_inspector import FastAPIInspector
from core.models import EndpointInfo, SchemaInfo


@dataclass
class CodeSummary:
    """Summary of inspected codebase."""

    service_path: str
    endpoints: list[EndpointInfo]
    schemas: dict[str, SchemaInfo]
    endpoint_count: int
    schema_count: int
    methods_used: list[str]
    paths: list[str]
    source_files: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "service_path": self.service_path,
            "endpoint_count": self.endpoint_count,
            "schema_count": self.schema_count,
            "methods_used": self.methods_used,
            "paths": self.paths,
            "source_files": self.source_files,
            "endpoints": [e.to_dict() for e in self.endpoints],
            "schemas": {k: v.to_dict() for k, v in self.schemas.items()},
        }

    def format_summary(self) -> str:
        """Format as human-readable summary."""
        lines = [
            f"Service: {self.service_path}",
            "-" * 50,
            f"Endpoints Found: {self.endpoint_count}",
            f"Schemas Found: {self.schema_count}",
            f"HTTP Methods: {', '.join(self.methods_used) if self.methods_used else 'None'}",
            "",
            "Implemented Endpoints:",
        ]

        if self.endpoints:
            for endpoint in self.endpoints:
                lines.append(f"  {endpoint.method:6} {endpoint.path}")
                if endpoint.summary:
                    lines.append(f"         └─ {endpoint.summary}")
        else:
            lines.append("  (none found)")

        lines.append("")
        lines.append("Source Files:")
        for src in self.source_files:
            lines.append(f"  - {src}")

        return "\n".join(lines)


class CodeAgent(Agent):
    """Agent responsible for inspecting FastAPI application code.

    The CodeAgent analyzes the target service's source code to discover
    implemented endpoints, Pydantic schemas, and route handlers. It uses
    AST parsing to extract this information without executing the code.

    Required Context: SERVICE (target service source files)

    Output: CodeSummary with discovered endpoints and schemas.
    """

    def __init__(self) -> None:
        """Initialize the CodeAgent."""
        super().__init__("CodeAgent")
        self._inspector: FastAPIInspector | None = None

    def get_required_context_types(self) -> list[str]:
        """Get required context types.

        Returns:
            List containing 'service'.
        """
        return ["service"]

    def run(self, service_path: str | Path | None = None, **kwargs: Any) -> CodeSummary:
        """Inspect the service codebase and generate a summary.

        Args:
            service_path: Path to the service directory. If not provided,
                         uses default path.
            **kwargs: Additional arguments (unused).

        Returns:
            CodeSummary with discovered endpoints and schemas.

        Raises:
            FileNotFoundError: If service directory doesn't exist.
        """
        if service_path is None:
            service_path = Path("services/user_service")

        service_path = Path(service_path)
        if not service_path.exists():
            raise FileNotFoundError(f"Service directory not found: {service_path}")

        self._inspector = FastAPIInspector(service_path)
        self._inspector.inspect()

        # Extract unique methods and paths
        methods = sorted(set(e.method for e in self._inspector.endpoints))
        paths = sorted(set(e.path for e in self._inspector.endpoints))

        # Get list of source files
        source_files = []
        for py_file in service_path.rglob("*.py"):
            if not py_file.name.startswith("__"):
                source_files.append(str(py_file))

        return CodeSummary(
            service_path=str(service_path),
            endpoints=self._inspector.endpoints,
            schemas=self._inspector.schemas,
            endpoint_count=len(self._inspector.endpoints),
            schema_count=len(self._inspector.schemas),
            methods_used=methods,
            paths=paths,
            source_files=sorted(source_files),
        )

    @property
    def inspector(self) -> FastAPIInspector | None:
        """Get the underlying inspector instance."""
        return self._inspector

    def format_output(self) -> str:
        """Format the code summary for display.

        Returns:
            Human-readable code inspection summary.
        """
        if self._result is None or self._result.output is None:
            return f"{self.name}: No codebase inspected"

        summary: CodeSummary = self._result.output
        return summary.format_summary()
