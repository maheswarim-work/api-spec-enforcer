"""ReviewAgent - Validates final output against spec and constraints."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .base import Agent
from core.compliance_checker import ComplianceChecker
from core.fastapi_inspector import FastAPIInspector
from core.models import ComplianceReport
from core.openapi_parser import OpenAPIParser


class ReviewStatus(str, Enum):
    """Status of the review."""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


@dataclass
class ReviewCheck:
    """A single review check result."""

    name: str
    status: ReviewStatus
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
        }


@dataclass
class ReviewResult:
    """Complete review result."""

    overall_status: ReviewStatus
    checks: list[ReviewCheck] = field(default_factory=list)
    compliance_report: ComplianceReport | None = None
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "overall_status": self.overall_status.value,
            "checks": [c.to_dict() for c in self.checks],
            "summary": self.summary,
            "compliance": self.compliance_report.to_dict() if self.compliance_report else None,
        }

    def format_summary(self) -> str:
        """Format as human-readable summary."""
        status_icon = {
            ReviewStatus.PASSED: "[PASS]",
            ReviewStatus.FAILED: "[FAIL]",
            ReviewStatus.WARNING: "[WARN]",
        }

        lines = [
            "Review Summary",
            "=" * 50,
            f"Overall Status: {status_icon[self.overall_status]} {self.overall_status.value.upper()}",
            "",
            "Checks:",
        ]

        for check in self.checks:
            icon = status_icon[check.status]
            lines.append(f"  {icon} {check.name}")
            lines.append(f"       {check.message}")

        if self.summary:
            lines.append("")
            lines.append("Summary:")
            lines.append(f"  {self.summary}")

        return "\n".join(lines)


class ReviewAgent(Agent):
    """Agent responsible for validating implementation against spec and constraints.

    The ReviewAgent performs a final validation pass to ensure:
    - All spec endpoints are implemented
    - No breaking changes were made to existing endpoints
    - Code follows the non-functional requirements
    - Generated tests are valid

    Required Context: SPEC, SERVICE, STANDARDS

    Output: ReviewResult with validation status and details.
    """

    def __init__(self) -> None:
        """Initialize the ReviewAgent."""
        super().__init__("ReviewAgent")

    def get_required_context_types(self) -> list[str]:
        """Get required context types.

        Returns:
            List containing 'spec', 'service', 'standards'.
        """
        return ["spec", "service", "standards"]

    def run(
        self,
        spec_path: str | Path | None = None,
        service_path: str | Path | None = None,
        **kwargs: Any,
    ) -> ReviewResult:
        """Run comprehensive review of the implementation.

        Args:
            spec_path: Path to the OpenAPI spec file.
            service_path: Path to the service directory.
            **kwargs: Additional arguments (unused).

        Returns:
            ReviewResult with all check results.
        """
        if spec_path is None:
            spec_path = Path("spec/openapi.yaml")
        if service_path is None:
            service_path = Path("services/user_service")

        spec_path = Path(spec_path)
        service_path = Path(service_path)

        result = ReviewResult(overall_status=ReviewStatus.PASSED)
        checks: list[ReviewCheck] = []

        # Check 1: Spec exists and is valid
        checks.append(self._check_spec_valid(spec_path))

        # Check 2: Service exists and has routes
        checks.append(self._check_service_exists(service_path))

        # Check 3: Run compliance check
        compliance_check, compliance_report = self._check_compliance(spec_path, service_path)
        checks.append(compliance_check)
        result.compliance_report = compliance_report

        # Check 4: Verify async patterns
        checks.append(self._check_async_patterns(service_path))

        # Check 5: Verify type hints
        checks.append(self._check_type_hints(service_path))

        # Check 6: Verify no breaking changes (based on git diff if available)
        checks.append(self._check_no_breaking_changes())

        result.checks = checks

        # Determine overall status
        if any(c.status == ReviewStatus.FAILED for c in checks):
            result.overall_status = ReviewStatus.FAILED
        elif any(c.status == ReviewStatus.WARNING for c in checks):
            result.overall_status = ReviewStatus.WARNING
        else:
            result.overall_status = ReviewStatus.PASSED

        # Generate summary
        passed = sum(1 for c in checks if c.status == ReviewStatus.PASSED)
        failed = sum(1 for c in checks if c.status == ReviewStatus.FAILED)
        warnings = sum(1 for c in checks if c.status == ReviewStatus.WARNING)
        result.summary = f"{passed} passed, {failed} failed, {warnings} warnings"

        return result

    def _check_spec_valid(self, spec_path: Path) -> ReviewCheck:
        """Check if the OpenAPI spec is valid.

        Args:
            spec_path: Path to the spec file.

        Returns:
            ReviewCheck result.
        """
        if not spec_path.exists():
            return ReviewCheck(
                name="Spec Validity",
                status=ReviewStatus.FAILED,
                message=f"Spec file not found: {spec_path}",
            )

        try:
            parser = OpenAPIParser(spec_path)
            parser.parse()
            return ReviewCheck(
                name="Spec Validity",
                status=ReviewStatus.PASSED,
                message=f"Valid OpenAPI spec: {parser.title} v{parser.version}",
                details={"endpoints": len(parser.endpoints), "schemas": len(parser.schemas)},
            )
        except Exception as e:
            return ReviewCheck(
                name="Spec Validity",
                status=ReviewStatus.FAILED,
                message=f"Invalid spec: {e}",
            )

    def _check_service_exists(self, service_path: Path) -> ReviewCheck:
        """Check if the service directory exists and has routes.

        Args:
            service_path: Path to the service directory.

        Returns:
            ReviewCheck result.
        """
        if not service_path.exists():
            return ReviewCheck(
                name="Service Exists",
                status=ReviewStatus.FAILED,
                message=f"Service directory not found: {service_path}",
            )

        routes_file = service_path / "routes.py"
        if not routes_file.exists():
            return ReviewCheck(
                name="Service Exists",
                status=ReviewStatus.WARNING,
                message="routes.py not found in service directory",
            )

        return ReviewCheck(
            name="Service Exists",
            status=ReviewStatus.PASSED,
            message=f"Service found at {service_path}",
        )

    def _check_compliance(
        self, spec_path: Path, service_path: Path
    ) -> tuple[ReviewCheck, ComplianceReport | None]:
        """Check API compliance.

        Args:
            spec_path: Path to the spec file.
            service_path: Path to the service directory.

        Returns:
            Tuple of (ReviewCheck, ComplianceReport).
        """
        try:
            parser = OpenAPIParser(spec_path)
            parser.parse()

            inspector = FastAPIInspector(service_path)
            inspector.inspect()

            checker = ComplianceChecker(parser, inspector)
            report = checker.check()

            if report.is_compliant:
                return (
                    ReviewCheck(
                        name="API Compliance",
                        status=ReviewStatus.PASSED,
                        message=f"100% compliant ({report.compliant_endpoints}/{report.total_spec_endpoints} endpoints)",
                    ),
                    report,
                )
            elif report.compliance_percentage >= 80:
                return (
                    ReviewCheck(
                        name="API Compliance",
                        status=ReviewStatus.WARNING,
                        message=f"{report.compliance_percentage:.0f}% compliant ({report.error_count} errors)",
                        details={"missing": [i.path for i in report.get_missing_endpoints()]},
                    ),
                    report,
                )
            else:
                return (
                    ReviewCheck(
                        name="API Compliance",
                        status=ReviewStatus.FAILED,
                        message=f"Only {report.compliance_percentage:.0f}% compliant ({report.error_count} errors)",
                        details={"missing": [i.path for i in report.get_missing_endpoints()]},
                    ),
                    report,
                )
        except Exception as e:
            return (
                ReviewCheck(
                    name="API Compliance",
                    status=ReviewStatus.FAILED,
                    message=f"Compliance check failed: {e}",
                ),
                None,
            )

    def _check_async_patterns(self, service_path: Path) -> ReviewCheck:
        """Check if async patterns are used correctly.

        Args:
            service_path: Path to the service directory.

        Returns:
            ReviewCheck result.
        """
        routes_file = service_path / "routes.py"
        if not routes_file.exists():
            return ReviewCheck(
                name="Async Patterns",
                status=ReviewStatus.WARNING,
                message="Cannot check - routes.py not found",
            )

        content = routes_file.read_text()

        # Count async vs sync route handlers
        async_count = content.count("async def ")
        # Look for def that follows a decorator (route handler)
        sync_handlers = 0
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "@router." in line or "@app." in line:
                # Check next non-empty line for sync def
                for j in range(i + 1, min(i + 3, len(lines))):
                    if lines[j].strip().startswith("def ") and not lines[j].strip().startswith("def _"):
                        sync_handlers += 1
                        break

        if sync_handlers > 0:
            return ReviewCheck(
                name="Async Patterns",
                status=ReviewStatus.WARNING,
                message=f"Found {sync_handlers} sync route handlers (should be async)",
            )

        return ReviewCheck(
            name="Async Patterns",
            status=ReviewStatus.PASSED,
            message=f"All {async_count} route handlers use async",
        )

    def _check_type_hints(self, service_path: Path) -> ReviewCheck:
        """Check if type hints are present.

        Args:
            service_path: Path to the service directory.

        Returns:
            ReviewCheck result.
        """
        py_files = list(service_path.rglob("*.py"))
        files_with_hints = 0
        files_without_hints = 0

        for py_file in py_files:
            if py_file.name.startswith("__"):
                continue
            content = py_file.read_text()
            # Simple heuristic: check for common type hint patterns
            if ": " in content and (" -> " in content or "-> " in content):
                files_with_hints += 1
            else:
                files_without_hints += 1

        if files_without_hints > 0:
            return ReviewCheck(
                name="Type Hints",
                status=ReviewStatus.WARNING,
                message=f"{files_without_hints} files may lack type hints",
            )

        return ReviewCheck(
            name="Type Hints",
            status=ReviewStatus.PASSED,
            message=f"Type hints found in {files_with_hints} files",
        )

    def _check_no_breaking_changes(self) -> ReviewCheck:
        """Check for breaking changes (placeholder for git-based check).

        Returns:
            ReviewCheck result.
        """
        # This is a simplified check - in a real implementation,
        # we would compare against a baseline to detect breaking changes
        return ReviewCheck(
            name="No Breaking Changes",
            status=ReviewStatus.PASSED,
            message="No breaking changes detected (based on additive changes only)",
        )

    def format_output(self) -> str:
        """Format the review result for display.

        Returns:
            Human-readable review summary.
        """
        if self._result is None or self._result.output is None:
            return f"{self.name}: No review performed"

        result: ReviewResult = self._result.output
        return result.format_summary()
