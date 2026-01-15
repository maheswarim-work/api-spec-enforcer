"""Tests for compliance checker."""

from pathlib import Path

import pytest

from core.compliance_checker import ComplianceChecker
from core.fastapi_inspector import FastAPIInspector
from core.models import IssueType, IssueSeverity
from core.openapi_parser import OpenAPIParser


class TestComplianceChecker:
    """Tests for ComplianceChecker class."""

    @pytest.fixture
    def parser(self, spec_path: Path) -> OpenAPIParser:
        """Create a parser instance."""
        parser = OpenAPIParser(spec_path)
        parser.parse()
        return parser

    @pytest.fixture
    def inspector(self, service_path: Path) -> FastAPIInspector:
        """Create an inspector instance."""
        inspector = FastAPIInspector(service_path)
        inspector.inspect()
        return inspector

    @pytest.fixture
    def checker(
        self, parser: OpenAPIParser, inspector: FastAPIInspector
    ) -> ComplianceChecker:
        """Create a compliance checker instance."""
        return ComplianceChecker(parser, inspector)

    def test_check_generates_report(self, checker: ComplianceChecker) -> None:
        """Test that check() generates a compliance report."""
        report = checker.check()

        assert report is not None
        assert report.spec_title == "User Management API"
        assert report.spec_version == "1.0.0"
        assert report.total_spec_endpoints == 5

    def test_detects_missing_endpoints(self, checker: ComplianceChecker) -> None:
        """Test that missing endpoints are detected."""
        report = checker.check()

        missing = report.get_missing_endpoints()
        assert len(missing) > 0

        # The intentionally missing endpoints
        missing_methods = {f"{i.method} {i.path}" for i in missing}
        assert "POST /users" in missing_methods or any("POST" in m for m in missing_methods)

    def test_compliance_percentage(self, checker: ComplianceChecker) -> None:
        """Test compliance percentage calculation."""
        report = checker.check()

        # With 2/5 endpoints implemented, should be 40%
        assert report.compliance_percentage == pytest.approx(40.0, rel=0.1)

    def test_error_count(self, checker: ComplianceChecker) -> None:
        """Test error counting."""
        report = checker.check()

        # Should have 3 errors (3 missing endpoints)
        assert report.error_count == 3

    def test_is_not_compliant(self, checker: ComplianceChecker) -> None:
        """Test that incomplete implementation is not compliant."""
        report = checker.check()

        assert report.is_compliant is False

    def test_issue_types(self, checker: ComplianceChecker) -> None:
        """Test that issues have correct types."""
        report = checker.check()

        issue_types = {i.issue_type for i in report.issues}
        assert IssueType.MISSING_ENDPOINT in issue_types

    def test_issue_severities(self, checker: ComplianceChecker) -> None:
        """Test that missing endpoints are errors."""
        report = checker.check()

        for issue in report.issues:
            if issue.issue_type == IssueType.MISSING_ENDPOINT:
                assert issue.severity == IssueSeverity.ERROR

    def test_format_report(self, checker: ComplianceChecker) -> None:
        """Test report formatting."""
        report = checker.check()
        formatted = report.format_report()

        assert "API COMPLIANCE REPORT" in formatted
        assert "User Management API" in formatted
        assert "Compliance:" in formatted
        assert "[ERROR]" in formatted

    def test_get_missing_endpoints(self, checker: ComplianceChecker) -> None:
        """Test getting list of missing endpoints."""
        checker.check()
        missing = checker.get_missing_endpoints()

        assert len(missing) == 3
        methods = {e.method for e in missing}
        assert "POST" in methods
        assert "PUT" in methods
        assert "DELETE" in methods

    def test_report_to_dict(self, checker: ComplianceChecker) -> None:
        """Test report conversion to dictionary."""
        report = checker.check()
        data = report.to_dict()

        assert "spec_title" in data
        assert "compliance_percentage" in data
        assert "issues" in data
        assert isinstance(data["issues"], list)

    def test_suggestions_provided(self, checker: ComplianceChecker) -> None:
        """Test that issues include suggestions."""
        report = checker.check()

        for issue in report.issues:
            if issue.issue_type == IssueType.MISSING_ENDPOINT:
                assert issue.suggestion != ""
                assert "Implement" in issue.suggestion
