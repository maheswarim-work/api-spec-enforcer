"""OpenAPI specification parser."""

from pathlib import Path
from typing import Any

import yaml

from core.models import EndpointInfo, FieldInfo, ParameterInfo, SchemaInfo


class OpenAPIParser:
    """Parser for OpenAPI 3.0 specifications."""

    def __init__(self, spec_path: str | Path) -> None:
        """Initialize parser with path to OpenAPI spec.

        Args:
            spec_path: Path to the OpenAPI YAML file.
        """
        self.spec_path = Path(spec_path)
        self._spec: dict[str, Any] = {}
        self._schemas: dict[str, SchemaInfo] = {}
        self._endpoints: list[EndpointInfo] = []

    def parse(self) -> None:
        """Parse the OpenAPI specification file."""
        with open(self.spec_path) as f:
            self._spec = yaml.safe_load(f)

        self._parse_schemas()
        self._parse_endpoints()

    @property
    def title(self) -> str:
        """Get the API title from spec."""
        return self._spec.get("info", {}).get("title", "Unknown API")

    @property
    def version(self) -> str:
        """Get the API version from spec."""
        return self._spec.get("info", {}).get("version", "0.0.0")

    @property
    def description(self) -> str:
        """Get the API description from spec."""
        return self._spec.get("info", {}).get("description", "")

    @property
    def endpoints(self) -> list[EndpointInfo]:
        """Get all parsed endpoints."""
        return self._endpoints

    @property
    def schemas(self) -> dict[str, SchemaInfo]:
        """Get all parsed schemas."""
        return self._schemas

    def get_endpoint(self, method: str, path: str) -> EndpointInfo | None:
        """Get a specific endpoint by method and path.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: URL path

        Returns:
            EndpointInfo if found, None otherwise.
        """
        method = method.upper()
        for endpoint in self._endpoints:
            if endpoint.method.upper() == method and endpoint.path == path:
                return endpoint
        return None

    def _parse_schemas(self) -> None:
        """Parse component schemas from the spec."""
        components = self._spec.get("components", {})
        schemas = components.get("schemas", {})

        for schema_name, schema_def in schemas.items():
            schema_info = self._parse_schema_definition(schema_name, schema_def)
            self._schemas[schema_name] = schema_info

    def _parse_schema_definition(
        self, name: str, schema_def: dict[str, Any]
    ) -> SchemaInfo:
        """Parse a single schema definition.

        Args:
            name: Schema name
            schema_def: Schema definition dict

        Returns:
            Parsed SchemaInfo object.
        """
        fields: list[FieldInfo] = []
        required_fields = schema_def.get("required", [])

        properties = schema_def.get("properties", {})
        for field_name, field_def in properties.items():
            field_info = self._parse_field(field_name, field_def, field_name in required_fields)
            fields.append(field_info)

        return SchemaInfo(
            name=name,
            description=schema_def.get("description", ""),
            fields=fields,
            required_fields=required_fields,
        )

    def _parse_field(
        self, name: str, field_def: dict[str, Any], required: bool
    ) -> FieldInfo:
        """Parse a single field definition.

        Args:
            name: Field name
            field_def: Field definition dict
            required: Whether the field is required

        Returns:
            Parsed FieldInfo object.
        """
        # Handle $ref
        if "$ref" in field_def:
            ref_name = field_def["$ref"].split("/")[-1]
            return FieldInfo(
                name=name,
                field_type=ref_name,
                required=required,
                description=f"Reference to {ref_name}",
            )

        # Handle array types
        if field_def.get("type") == "array":
            items = field_def.get("items", {})
            if "$ref" in items:
                item_type = items["$ref"].split("/")[-1]
            else:
                item_type = items.get("type", "any")
            field_type = f"array[{item_type}]"
        else:
            field_type = field_def.get("type", "any")

        return FieldInfo(
            name=name,
            field_type=field_type,
            required=required,
            description=field_def.get("description", ""),
            format=field_def.get("format"),
            default=field_def.get("default"),
            min_length=field_def.get("minLength"),
            max_length=field_def.get("maxLength"),
        )

    def _parse_endpoints(self) -> None:
        """Parse all endpoint paths from the spec."""
        paths = self._spec.get("paths", {})

        for path, path_item in paths.items():
            for method in ["get", "post", "put", "patch", "delete", "head", "options"]:
                if method in path_item:
                    operation = path_item[method]
                    endpoint = self._parse_operation(path, method, operation)
                    self._endpoints.append(endpoint)

    def _parse_operation(
        self, path: str, method: str, operation: dict[str, Any]
    ) -> EndpointInfo:
        """Parse a single operation definition.

        Args:
            path: URL path
            method: HTTP method
            operation: Operation definition dict

        Returns:
            Parsed EndpointInfo object.
        """
        # Parse parameters
        parameters: list[ParameterInfo] = []
        for param in operation.get("parameters", []):
            param_info = ParameterInfo(
                name=param.get("name", ""),
                location=param.get("in", "query"),
                param_type=param.get("schema", {}).get("type", "string"),
                required=param.get("required", False),
                description=param.get("description", ""),
                default=param.get("schema", {}).get("default"),
            )
            parameters.append(param_info)

        # Parse request body schema
        request_schema = None
        request_body = operation.get("requestBody", {})
        if request_body:
            content = request_body.get("content", {})
            json_content = content.get("application/json", {})
            schema_ref = json_content.get("schema", {})
            if "$ref" in schema_ref:
                schema_name = schema_ref["$ref"].split("/")[-1]
                request_schema = self._schemas.get(schema_name)

        # Parse response schema (use success response)
        response_schema = None
        response_status_codes: list[int] = []
        responses = operation.get("responses", {})
        for status_code, response in responses.items():
            try:
                response_status_codes.append(int(status_code))
            except ValueError:
                continue

            # Get schema from first success response
            if status_code.startswith("2") and response_schema is None:
                content = response.get("content", {})
                json_content = content.get("application/json", {})
                schema_ref = json_content.get("schema", {})
                if "$ref" in schema_ref:
                    schema_name = schema_ref["$ref"].split("/")[-1]
                    response_schema = self._schemas.get(schema_name)

        return EndpointInfo(
            path=path,
            method=method.upper(),
            operation_id=operation.get("operationId", ""),
            summary=operation.get("summary", ""),
            description=operation.get("description", ""),
            parameters=parameters,
            request_schema=request_schema,
            response_schema=response_schema,
            response_status_codes=sorted(response_status_codes),
            tags=operation.get("tags", []),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert parsed spec to dictionary representation.

        Returns:
            Dictionary containing all parsed information.
        """
        return {
            "title": self.title,
            "version": self.version,
            "description": self.description,
            "endpoints": [e.to_dict() for e in self._endpoints],
            "schemas": {name: s.to_dict() for name, s in self._schemas.items()},
        }
