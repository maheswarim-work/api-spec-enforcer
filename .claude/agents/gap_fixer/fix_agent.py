"""FixAgent - Generates code fixes for missing endpoints."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agents.base import Agent
from core.code_generator import CodeGenerator
from core.models import ComplianceReport, EndpointInfo


@dataclass
class CodeFix:
    """A single code fix to apply."""

    file_path: str
    code: str
    description: str
    endpoint: EndpointInfo
    fix_type: str  # 'endpoint', 'schema', 'import'

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "file_path": self.file_path,
            "code": self.code,
            "description": self.description,
            "fix_type": self.fix_type,
            "endpoint": self.endpoint.to_dict(),
        }


@dataclass
class FixResult:
    """Result of fix generation."""

    fixes: list[CodeFix] = field(default_factory=list)
    endpoints_fixed: int = 0
    schemas_added: int = 0
    files_modified: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "endpoints_fixed": self.endpoints_fixed,
            "schemas_added": self.schemas_added,
            "files_modified": self.files_modified,
            "fixes": [f.to_dict() for f in self.fixes],
        }

    def format_summary(self) -> str:
        """Format as human-readable summary."""
        lines = [
            "Fix Generation Summary",
            "-" * 50,
            f"Endpoints to add: {self.endpoints_fixed}",
            f"Schemas to add: {self.schemas_added}",
            f"Files to modify: {len(self.files_modified)}",
            "",
        ]

        if self.fixes:
            lines.append("Generated Fixes:")
            for fix in self.fixes:
                lines.append(f"  [{fix.fix_type.upper()}] {fix.description}")
                lines.append(f"           File: {fix.file_path}")
        else:
            lines.append("No fixes needed - implementation is compliant!")

        return "\n".join(lines)

    def get_code_for_file(self, file_path: str) -> str:
        """Get all code fixes for a specific file.

        Args:
            file_path: Path to the file.

        Returns:
            Combined code for all fixes targeting this file.
        """
        file_fixes = [f for f in self.fixes if f.file_path == file_path]
        return "\n\n".join(f.code for f in file_fixes)


class FixAgent(Agent):
    """Agent responsible for generating code fixes for missing endpoints.

    The FixAgent takes a compliance report and generates the necessary code
    to implement missing endpoints. It follows the non-breaking changes
    principle by only adding new code without modifying existing endpoints.

    Required Context: SPEC, SERVICE, COMPLIANCE

    Output: FixResult with generated code fixes.
    """

    def __init__(self) -> None:
        """Initialize the FixAgent."""
        super().__init__("FixAgent")
        self._generator = CodeGenerator()

    def get_required_context_types(self) -> list[str]:
        """Get required context types.

        Returns:
            List containing 'spec', 'service', 'compliance'.
        """
        return ["spec", "service", "compliance"]

    def run(
        self,
        compliance_report: ComplianceReport,
        missing_endpoints: list[EndpointInfo],
        service_path: str | Path | None = None,
        **kwargs: Any,
    ) -> FixResult:
        """Generate code fixes for missing endpoints.

        Args:
            compliance_report: The compliance check report.
            missing_endpoints: List of endpoints to implement.
            service_path: Path to the service directory.
            **kwargs: Additional arguments (unused).

        Returns:
            FixResult with generated code fixes.
        """
        if service_path is None:
            service_path = Path("services/user_service")

        service_path = Path(service_path)
        routes_file = service_path / "routes.py"

        result = FixResult()
        imports_needed: set[str] = set()

        for endpoint in missing_endpoints:
            # Generate endpoint code
            endpoint_code = self._generator.generate_endpoint(endpoint)

            fix = CodeFix(
                file_path=str(routes_file),
                code=endpoint_code,
                description=f"Add {endpoint.method} {endpoint.path} endpoint",
                endpoint=endpoint,
                fix_type="endpoint",
            )
            result.fixes.append(fix)
            result.endpoints_fixed += 1

            # Track required imports
            if endpoint.request_schema:
                imports_needed.add(endpoint.request_schema.name)
            if endpoint.response_schema:
                imports_needed.add(endpoint.response_schema.name)

            # Check if response includes 201/204 status codes
            if 201 in endpoint.response_status_codes or 204 in endpoint.response_status_codes:
                imports_needed.add("Response")

        # Generate import fix if needed
        if imports_needed:
            existing_imports = self._get_existing_imports(routes_file)
            new_imports = imports_needed - existing_imports

            if new_imports:
                import_code = self._generate_import_fix(new_imports)
                import_fix = CodeFix(
                    file_path=str(routes_file),
                    code=import_code,
                    description=f"Add imports: {', '.join(new_imports)}",
                    endpoint=missing_endpoints[0] if missing_endpoints else EndpointInfo(path="", method=""),
                    fix_type="import",
                )
                result.fixes.insert(0, import_fix)

        result.files_modified = list(set(f.file_path for f in result.fixes))

        return result

    def _get_existing_imports(self, routes_file: Path) -> set[str]:
        """Get existing imports from the routes file.

        Args:
            routes_file: Path to the routes file.

        Returns:
            Set of imported names.
        """
        imports: set[str] = set()
        if not routes_file.exists():
            return imports

        content = routes_file.read_text()
        for line in content.split("\n"):
            if "from" in line and "import" in line:
                # Extract imported names
                parts = line.split("import")
                if len(parts) > 1:
                    names = parts[1].strip()
                    for name in names.split(","):
                        clean_name = name.strip().split(" ")[0]
                        imports.add(clean_name)

        return imports

    def _generate_import_fix(self, imports: set[str]) -> str:
        """Generate import statement for new imports.

        Args:
            imports: Set of names to import.

        Returns:
            Import statement code.
        """
        schema_imports = [i for i in imports if i not in ("Response",)]
        other_imports = [i for i in imports if i in ("Response",)]

        lines = []

        if schema_imports:
            lines.append(
                f"from services.user_service.schemas import {', '.join(sorted(schema_imports))}"
            )

        if other_imports:
            lines.append(f"from fastapi import {', '.join(sorted(other_imports))}")

        return "\n".join(lines)

    def apply_fixes(self, result: FixResult, dry_run: bool = True) -> dict[str, str]:
        """Apply generated fixes to the codebase.

        Args:
            result: FixResult with fixes to apply.
            dry_run: If True, return what would be changed without writing.

        Returns:
            Dictionary mapping file paths to their new content.
        """
        changes: dict[str, str] = {}

        for file_path in result.files_modified:
            path = Path(file_path)
            if path.exists():
                content = path.read_text()
            else:
                content = ""

            # Get all fixes for this file
            file_fixes = [f for f in result.fixes if f.file_path == file_path]

            # Apply import fixes first
            import_fixes = [f for f in file_fixes if f.fix_type == "import"]
            endpoint_fixes = [f for f in file_fixes if f.fix_type == "endpoint"]

            # Add imports at the top (after existing imports)
            for fix in import_fixes:
                # Find last import line
                lines = content.split("\n")
                last_import_idx = 0
                for i, line in enumerate(lines):
                    if line.startswith("from ") or line.startswith("import "):
                        last_import_idx = i

                lines.insert(last_import_idx + 1, fix.code)
                content = "\n".join(lines)

            # Add endpoints at the end
            for fix in endpoint_fixes:
                content = content.rstrip() + "\n\n\n" + fix.code + "\n"

            changes[file_path] = content

            if not dry_run:
                path.write_text(content)

        return changes

    def format_output(self) -> str:
        """Format the fix result for display.

        Returns:
            Human-readable fix summary.
        """
        if self._result is None or self._result.output is None:
            return f"{self.name}: No fixes generated"

        result: FixResult = self._result.output
        return result.format_summary()
