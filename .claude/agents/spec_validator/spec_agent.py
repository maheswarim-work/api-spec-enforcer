"""SpecAgent - Parses and summarizes specification requirements."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..base import Agent
from core.openapi_parser import OpenAPIParser
from core.models import EndpointInfo, SchemaInfo


@dataclass
class SpecSummary:
    """Summary of parsed specification."""

    title: str
    version: str
    description: str
    endpoints: list[EndpointInfo]
    schemas: dict[str, SchemaInfo]
    endpoint_count: int
    schema_count: int
    methods_used: list[str]
    paths: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "title": self.title,
            "version": self.version,
            "description": self.description,
            "endpoint_count": self.endpoint_count,
            "schema_count": self.schema_count,
            "methods_used": self.methods_used,
            "paths": self.paths,
            "endpoints": [e.to_dict() for e in self.endpoints],
            "schemas": {k: v.to_dict() for k, v in self.schemas.items()},
        }

    def format_summary(self) -> str:
        """Format as human-readable summary."""
        lines = [
            f"API Specification: {self.title} v{self.version}",
            "-" * 50,
            f"Description: {self.description[:100]}..." if len(self.description) > 100 else f"Description: {self.description}",
            "",
            f"Endpoints: {self.endpoint_count}",
            f"Schemas: {self.schema_count}",
            f"HTTP Methods: {', '.join(self.methods_used)}",
            "",
            "Endpoint Summary:",
        ]

        for endpoint in self.endpoints:
            lines.append(f"  {endpoint.method:6} {endpoint.path}")
            if endpoint.summary:
                lines.append(f"         └─ {endpoint.summary}")

        return "\n".join(lines)


class SpecAgent(Agent):
    """Agent responsible for parsing and summarizing API specifications.

    The SpecAgent reads the OpenAPI specification and non-functional requirements,
    extracts the key information, and provides a structured summary that other
    agents can use for their tasks.

    Required Context: SPEC (OpenAPI spec and NFR documents)

    Output: SpecSummary with parsed endpoints, schemas, and metadata.
    """

    def __init__(self) -> None:
        """Initialize the SpecAgent."""
        super().__init__("SpecAgent")
        self._parser: OpenAPIParser | None = None

    def get_required_context_types(self) -> list[str]:
        """Get required context types.

        Returns:
            List containing 'spec'.
        """
        return ["spec"]

    def run(self, spec_path: str | Path | None = None, **kwargs: Any) -> SpecSummary:
        """Parse the OpenAPI spec and generate a summary.

        Args:
            spec_path: Path to the OpenAPI spec file. If not provided,
                      uses default path.
            **kwargs: Additional arguments (unused).

        Returns:
            SpecSummary with parsed specification data.

        Raises:
            FileNotFoundError: If spec file doesn't exist.
            ValueError: If spec file is invalid.
        """
        if spec_path is None:
            spec_path = Path("spec/openapi.yaml")

        spec_path = Path(spec_path)
        if not spec_path.exists():
            raise FileNotFoundError(f"Specification file not found: {spec_path}")

        self._parser = OpenAPIParser(spec_path)
        self._parser.parse()

        # Extract unique methods and paths
        methods = sorted(set(e.method for e in self._parser.endpoints))
        paths = sorted(set(e.path for e in self._parser.endpoints))

        return SpecSummary(
            title=self._parser.title,
            version=self._parser.version,
            description=self._parser.description,
            endpoints=self._parser.endpoints,
            schemas=self._parser.schemas,
            endpoint_count=len(self._parser.endpoints),
            schema_count=len(self._parser.schemas),
            methods_used=methods,
            paths=paths,
        )

    @property
    def parser(self) -> OpenAPIParser | None:
        """Get the underlying parser instance."""
        return self._parser

    def format_output(self) -> str:
        """Format the spec summary for display.

        Returns:
            Human-readable specification summary.
        """
        if self._result is None or self._result.output is None:
            return f"{self.name}: No specification parsed"

        summary: SpecSummary = self._result.output
        return summary.format_summary()
