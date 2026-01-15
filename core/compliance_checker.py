"""Compliance checker comparing OpenAPI spec to FastAPI implementation."""

import re
from typing import Any

from core.models import (
    ComplianceIssue,
    ComplianceReport,
    EndpointInfo,
    IssueSeverity,
    IssueType,
    SchemaInfo,
)
from core.openapi_parser import OpenAPIParser
from core.fastapi_inspector import FastAPIInspector


class ComplianceChecker:
    """Check FastAPI implementation compliance against OpenAPI spec."""

    def __init__(self, parser: OpenAPIParser, inspector: FastAPIInspector) -> None:
        """Initialize compliance checker.

        Args:
            parser: Parsed OpenAPI specification.
            inspector: Inspected FastAPI application.
        """
        self.parser = parser
        self.inspector = inspector
        self._issues: list[ComplianceIssue] = []

    def check(self) -> ComplianceReport:
        """Run compliance check and generate report.

        Returns:
            ComplianceReport with all findings.
        """
        self._issues = []

        # Check for missing endpoints
        self._check_missing_endpoints()

        # Check for extra endpoints (not in spec)
        self._check_extra_endpoints()

        # Check schema compliance for implemented endpoints
        self._check_schema_compliance()

        # Calculate compliant endpoints
        spec_endpoints = set(e.endpoint_key for e in self.parser.endpoints)
        impl_endpoints = set(
            self._normalize_endpoint_key(e.endpoint_key) for e in self.inspector.endpoints
        )
        missing = self._get_missing_endpoint_keys()
        compliant = len(spec_endpoints) - len(missing)

        return ComplianceReport(
            spec_title=self.parser.title,
            spec_version=self.parser.version,
            total_spec_endpoints=len(self.parser.endpoints),
            total_impl_endpoints=len(self.inspector.endpoints),
            compliant_endpoints=compliant,
            issues=self._issues,
        )

    def _normalize_endpoint_key(self, key: str) -> str:
        """Normalize endpoint key for comparison.

        Args:
            key: Endpoint key in format "METHOD /path"

        Returns:
            Normalized key with generic path parameters.
        """
        # Replace {param_name} variations with standard format
        return re.sub(r"\{[^}]+\}", "{id}", key)

    def _get_missing_endpoint_keys(self) -> set[str]:
        """Get set of missing endpoint keys.

        Returns:
            Set of endpoint keys that are in spec but not implemented.
        """
        missing = set()
        for spec_endpoint in self.parser.endpoints:
            impl_endpoint = self._find_matching_endpoint(spec_endpoint)
            if impl_endpoint is None:
                missing.add(spec_endpoint.endpoint_key)
        return missing

    def _find_matching_endpoint(self, spec_endpoint: EndpointInfo) -> EndpointInfo | None:
        """Find matching implementation endpoint for a spec endpoint.

        Args:
            spec_endpoint: Endpoint from the spec.

        Returns:
            Matching implementation endpoint or None.
        """
        for impl_endpoint in self.inspector.endpoints:
            if self._endpoints_match(spec_endpoint, impl_endpoint):
                return impl_endpoint
        return None

    def _endpoints_match(self, spec: EndpointInfo, impl: EndpointInfo) -> bool:
        """Check if two endpoints match.

        Args:
            spec: Endpoint from spec.
            impl: Endpoint from implementation.

        Returns:
            True if endpoints match, False otherwise.
        """
        if spec.method.upper() != impl.method.upper():
            return False

        # Normalize paths for comparison
        spec_path = self._normalize_path(spec.path)
        impl_path = self._normalize_path(impl.path)

        return spec_path == impl_path

    def _normalize_path(self, path: str) -> str:
        """Normalize path by replacing parameter names with placeholders.

        Args:
            path: URL path.

        Returns:
            Normalized path.
        """
        return re.sub(r"\{[^}]+\}", "{param}", path)

    def _check_missing_endpoints(self) -> None:
        """Check for endpoints in spec that are not implemented."""
        for spec_endpoint in self.parser.endpoints:
            impl_endpoint = self._find_matching_endpoint(spec_endpoint)

            if impl_endpoint is None:
                self._issues.append(
                    ComplianceIssue(
                        issue_type=IssueType.MISSING_ENDPOINT,
                        severity=IssueSeverity.ERROR,
                        message=f"Missing endpoint: {spec_endpoint.endpoint_key}",
                        path=spec_endpoint.path,
                        method=spec_endpoint.method,
                        expected=spec_endpoint.to_dict(),
                        suggestion=f"Implement {spec_endpoint.method} handler for {spec_endpoint.path}",
                    )
                )

    def _check_extra_endpoints(self) -> None:
        """Check for endpoints in implementation not in spec."""
        for impl_endpoint in self.inspector.endpoints:
            found = False
            for spec_endpoint in self.parser.endpoints:
                if self._endpoints_match(spec_endpoint, impl_endpoint):
                    found = True
                    break

            if not found:
                self._issues.append(
                    ComplianceIssue(
                        issue_type=IssueType.EXTRA_ENDPOINT,
                        severity=IssueSeverity.WARNING,
                        message=f"Extra endpoint not in spec: {impl_endpoint.endpoint_key}",
                        path=impl_endpoint.path,
                        method=impl_endpoint.method,
                        actual=impl_endpoint.to_dict(),
                        suggestion="Add endpoint to OpenAPI spec or remove from implementation",
                    )
                )

    def _check_schema_compliance(self) -> None:
        """Check schema compliance for implemented endpoints."""
        for spec_endpoint in self.parser.endpoints:
            impl_endpoint = self._find_matching_endpoint(spec_endpoint)
            if impl_endpoint is None:
                continue

            # Check response schema
            if spec_endpoint.response_schema:
                self._check_response_schema(spec_endpoint, impl_endpoint)

            # Check request schema
            if spec_endpoint.request_schema:
                self._check_request_schema(spec_endpoint, impl_endpoint)

    def _check_response_schema(
        self, spec_endpoint: EndpointInfo, impl_endpoint: EndpointInfo
    ) -> None:
        """Check response schema compliance.

        Args:
            spec_endpoint: Endpoint from spec.
            impl_endpoint: Endpoint from implementation.
        """
        spec_schema = spec_endpoint.response_schema
        if spec_schema is None:
            return

        # Try to find matching schema in implementation
        impl_schema = self.inspector.schemas.get(spec_schema.name)

        if impl_schema is None:
            # Look for similar schema names
            for name in self.inspector.schemas:
                if name.lower() == spec_schema.name.lower():
                    impl_schema = self.inspector.schemas[name]
                    break

        if impl_schema is None:
            self._issues.append(
                ComplianceIssue(
                    issue_type=IssueType.SCHEMA_MISMATCH,
                    severity=IssueSeverity.WARNING,
                    message=f"Response schema '{spec_schema.name}' not found in implementation",
                    path=spec_endpoint.path,
                    method=spec_endpoint.method,
                    expected=spec_schema.name,
                    suggestion=f"Define Pydantic model '{spec_schema.name}' matching the spec",
                )
            )
            return

        # Check required fields
        self._check_schema_fields(spec_schema, impl_schema, spec_endpoint)

    def _check_request_schema(
        self, spec_endpoint: EndpointInfo, impl_endpoint: EndpointInfo
    ) -> None:
        """Check request schema compliance.

        Args:
            spec_endpoint: Endpoint from spec.
            impl_endpoint: Endpoint from implementation.
        """
        spec_schema = spec_endpoint.request_schema
        if spec_schema is None:
            return

        impl_schema = self.inspector.schemas.get(spec_schema.name)

        if impl_schema is None:
            self._issues.append(
                ComplianceIssue(
                    issue_type=IssueType.SCHEMA_MISMATCH,
                    severity=IssueSeverity.WARNING,
                    message=f"Request schema '{spec_schema.name}' not found in implementation",
                    path=spec_endpoint.path,
                    method=spec_endpoint.method,
                    expected=spec_schema.name,
                    suggestion=f"Define Pydantic model '{spec_schema.name}' matching the spec",
                )
            )

    def _check_schema_fields(
        self, spec_schema: SchemaInfo, impl_schema: SchemaInfo, endpoint: EndpointInfo
    ) -> None:
        """Check schema field compliance.

        Args:
            spec_schema: Schema from spec.
            impl_schema: Schema from implementation.
            endpoint: Related endpoint for context.
        """
        impl_field_names = {f.name for f in impl_schema.fields}

        for spec_field in spec_schema.fields:
            if spec_field.required and spec_field.name not in impl_field_names:
                self._issues.append(
                    ComplianceIssue(
                        issue_type=IssueType.MISSING_FIELD,
                        severity=IssueSeverity.ERROR,
                        message=f"Required field '{spec_field.name}' missing from schema '{impl_schema.name}'",
                        path=endpoint.path,
                        method=endpoint.method,
                        expected=spec_field.to_dict(),
                        suggestion=f"Add field '{spec_field.name}: {spec_field.field_type}' to {impl_schema.name}",
                    )
                )

    def get_missing_endpoints(self) -> list[EndpointInfo]:
        """Get list of endpoints that are missing from implementation.

        Returns:
            List of EndpointInfo objects for missing endpoints.
        """
        missing = []
        for spec_endpoint in self.parser.endpoints:
            impl_endpoint = self._find_matching_endpoint(spec_endpoint)
            if impl_endpoint is None:
                missing.append(spec_endpoint)
        return missing

    def to_dict(self) -> dict[str, Any]:
        """Convert checker state to dictionary.

        Returns:
            Dictionary with all compliance information.
        """
        return {
            "spec": self.parser.to_dict(),
            "implementation": self.inspector.to_dict(),
            "issues": [i.to_dict() for i in self._issues],
        }
