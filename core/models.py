"""Shared data models for API Contract Enforcer."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IssueType(str, Enum):
    """Types of compliance issues."""

    MISSING_ENDPOINT = "missing_endpoint"
    EXTRA_ENDPOINT = "extra_endpoint"
    METHOD_MISMATCH = "method_mismatch"
    SCHEMA_MISMATCH = "schema_mismatch"
    STATUS_CODE_MISMATCH = "status_code_mismatch"
    MISSING_FIELD = "missing_field"
    FIELD_TYPE_MISMATCH = "field_type_mismatch"
    MISSING_PARAMETER = "missing_parameter"


class IssueSeverity(str, Enum):
    """Severity levels for compliance issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class FieldInfo:
    """Information about a schema field."""

    name: str
    field_type: str
    required: bool = False
    description: str = ""
    format: str | None = None
    default: Any = None
    min_length: int | None = None
    max_length: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "type": self.field_type,
            "required": self.required,
            "description": self.description,
            "format": self.format,
            "default": self.default,
            "min_length": self.min_length,
            "max_length": self.max_length,
        }


@dataclass
class SchemaInfo:
    """Information about a request/response schema."""

    name: str
    fields: list[FieldInfo] = field(default_factory=list)
    description: str = ""
    required_fields: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "fields": [f.to_dict() for f in self.fields],
            "required_fields": self.required_fields,
        }

    def get_field(self, name: str) -> FieldInfo | None:
        """Get a field by name."""
        for f in self.fields:
            if f.name == name:
                return f
        return None


@dataclass
class ParameterInfo:
    """Information about an endpoint parameter."""

    name: str
    location: str  # path, query, header
    param_type: str
    required: bool = False
    description: str = ""
    default: Any = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "location": self.location,
            "type": self.param_type,
            "required": self.required,
            "description": self.description,
            "default": self.default,
        }


@dataclass
class EndpointInfo:
    """Information about an API endpoint."""

    path: str
    method: str
    operation_id: str = ""
    summary: str = ""
    description: str = ""
    parameters: list[ParameterInfo] = field(default_factory=list)
    request_schema: SchemaInfo | None = None
    response_schema: SchemaInfo | None = None
    response_status_codes: list[int] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    @property
    def endpoint_key(self) -> str:
        """Generate a unique key for this endpoint."""
        return f"{self.method.upper()} {self.path}"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "path": self.path,
            "method": self.method,
            "operation_id": self.operation_id,
            "summary": self.summary,
            "description": self.description,
            "parameters": [p.to_dict() for p in self.parameters],
            "request_schema": self.request_schema.to_dict() if self.request_schema else None,
            "response_schema": self.response_schema.to_dict() if self.response_schema else None,
            "response_status_codes": self.response_status_codes,
            "tags": self.tags,
        }


@dataclass
class ComplianceIssue:
    """A single compliance issue found during checking."""

    issue_type: IssueType
    severity: IssueSeverity
    message: str
    path: str = ""
    method: str = ""
    expected: Any = None
    actual: Any = None
    suggestion: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "type": self.issue_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "path": self.path,
            "method": self.method,
            "expected": self.expected,
            "actual": self.actual,
            "suggestion": self.suggestion,
        }


@dataclass
class ComplianceReport:
    """Complete compliance report."""

    spec_title: str
    spec_version: str
    total_spec_endpoints: int
    total_impl_endpoints: int
    compliant_endpoints: int
    issues: list[ComplianceIssue] = field(default_factory=list)

    @property
    def is_compliant(self) -> bool:
        """Check if implementation is fully compliant."""
        return len([i for i in self.issues if i.severity == IssueSeverity.ERROR]) == 0

    @property
    def compliance_percentage(self) -> float:
        """Calculate compliance percentage."""
        if self.total_spec_endpoints == 0:
            return 100.0
        return (self.compliant_endpoints / self.total_spec_endpoints) * 100

    @property
    def error_count(self) -> int:
        """Count of error-level issues."""
        return len([i for i in self.issues if i.severity == IssueSeverity.ERROR])

    @property
    def warning_count(self) -> int:
        """Count of warning-level issues."""
        return len([i for i in self.issues if i.severity == IssueSeverity.WARNING])

    def get_missing_endpoints(self) -> list[ComplianceIssue]:
        """Get all missing endpoint issues."""
        return [i for i in self.issues if i.issue_type == IssueType.MISSING_ENDPOINT]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "spec_title": self.spec_title,
            "spec_version": self.spec_version,
            "total_spec_endpoints": self.total_spec_endpoints,
            "total_impl_endpoints": self.total_impl_endpoints,
            "compliant_endpoints": self.compliant_endpoints,
            "compliance_percentage": self.compliance_percentage,
            "is_compliant": self.is_compliant,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "issues": [i.to_dict() for i in self.issues],
        }

    def format_report(self) -> str:
        """Format the report as a human-readable string."""
        lines = [
            "=" * 60,
            "API COMPLIANCE REPORT",
            "=" * 60,
            f"Spec: {self.spec_title} v{self.spec_version}",
            "-" * 60,
            f"Endpoints in spec:        {self.total_spec_endpoints}",
            f"Endpoints implemented:    {self.total_impl_endpoints}",
            f"Compliant endpoints:      {self.compliant_endpoints}",
            f"Compliance:               {self.compliance_percentage:.1f}%",
            "-" * 60,
            f"Errors:   {self.error_count}",
            f"Warnings: {self.warning_count}",
            "-" * 60,
        ]

        if self.issues:
            lines.append("ISSUES:")
            for issue in self.issues:
                severity_icon = {
                    IssueSeverity.ERROR: "[ERROR]",
                    IssueSeverity.WARNING: "[WARN] ",
                    IssueSeverity.INFO: "[INFO] ",
                }[issue.severity]
                lines.append(f"  {severity_icon} {issue.message}")
                if issue.path:
                    lines.append(f"           Endpoint: {issue.method.upper()} {issue.path}")
                if issue.suggestion:
                    lines.append(f"           Suggestion: {issue.suggestion}")
        else:
            lines.append("No issues found. Implementation is fully compliant!")

        lines.append("=" * 60)
        return "\n".join(lines)
