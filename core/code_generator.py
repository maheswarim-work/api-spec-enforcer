"""Code generator for missing API endpoints."""

from pathlib import Path
from typing import Any

from core.models import EndpointInfo, FieldInfo, SchemaInfo


class CodeGenerator:
    """Generate Python code for missing API endpoints and schemas."""

    def __init__(self) -> None:
        """Initialize code generator."""
        self._indent = "    "

    def generate_endpoint(self, endpoint: EndpointInfo) -> str:
        """Generate FastAPI endpoint handler code.

        Args:
            endpoint: Endpoint information from spec.

        Returns:
            Python code string for the endpoint handler.
        """
        lines: list[str] = []

        # Build decorator
        decorator = self._build_decorator(endpoint)
        lines.append(decorator)

        # Build function signature
        signature = self._build_signature(endpoint)
        lines.append(signature)

        # Build docstring
        docstring = self._build_docstring(endpoint)
        lines.extend(docstring)

        # Build function body
        body = self._build_body(endpoint)
        lines.extend(body)

        return "\n".join(lines)

    def generate_schema(self, schema: SchemaInfo) -> str:
        """Generate Pydantic model code for a schema.

        Args:
            schema: Schema information from spec.

        Returns:
            Python code string for the Pydantic model.
        """
        lines: list[str] = []

        # Class definition
        lines.append(f"class {schema.name}(BaseModel):")

        # Docstring
        if schema.description:
            lines.append(f'{self._indent}"""{schema.description}"""')
            lines.append("")

        # Fields
        for field in schema.fields:
            field_line = self._generate_field(field)
            lines.append(f"{self._indent}{field_line}")

        if not schema.fields:
            lines.append(f"{self._indent}pass")

        return "\n".join(lines)

    def generate_test(self, endpoint: EndpointInfo) -> str:
        """Generate pytest test code for an endpoint.

        Args:
            endpoint: Endpoint information.

        Returns:
            Python code string for the test.
        """
        lines: list[str] = []

        # Test function name
        test_name = self._generate_test_name(endpoint)
        lines.append(f"async def {test_name}(client: AsyncClient) -> None:")

        # Docstring
        lines.append(f'{self._indent}"""Test {endpoint.method} {endpoint.path}."""')

        # Build test body
        body = self._build_test_body(endpoint)
        lines.extend(body)

        return "\n".join(lines)

    def _build_decorator(self, endpoint: EndpointInfo) -> str:
        """Build route decorator string.

        Args:
            endpoint: Endpoint information.

        Returns:
            Decorator string.
        """
        method = endpoint.method.lower()
        path = endpoint.path

        # Determine status code
        success_codes = [c for c in endpoint.response_status_codes if 200 <= c < 300]
        status_code = success_codes[0] if success_codes else 200

        parts = [f'@router.{method}("{path}"']

        if status_code != 200:
            parts.append(f", status_code={status_code}")

        parts.append(")")

        return "".join(parts)

    def _build_signature(self, endpoint: EndpointInfo) -> str:
        """Build function signature string.

        Args:
            endpoint: Endpoint information.

        Returns:
            Function signature string.
        """
        func_name = endpoint.operation_id or self._generate_func_name(endpoint)
        params: list[str] = []

        # Add path parameters
        for param in endpoint.parameters:
            if param.location == "path":
                params.append(f"{param.name}: {self._map_type(param.param_type)}")

        # Add query parameters
        for param in endpoint.parameters:
            if param.location == "query":
                default = f" = {param.default}" if param.default is not None else " = None"
                param_type = self._map_type(param.param_type)
                if not param.required and "| None" not in param_type:
                    param_type = f"{param_type} | None"
                params.append(f"{param.name}: {param_type}{default}")

        # Add request body parameter
        if endpoint.request_schema:
            params.append(f"data: {endpoint.request_schema.name}")

        # Add return type
        return_type = "None"
        if endpoint.response_schema:
            return_type = endpoint.response_schema.name

        # Handle 204 No Content
        if 204 in endpoint.response_status_codes:
            return_type = "None"

        params_str = ", ".join(params)
        return f"async def {func_name}({params_str}) -> {return_type}:"

    def _build_docstring(self, endpoint: EndpointInfo) -> list[str]:
        """Build docstring lines.

        Args:
            endpoint: Endpoint information.

        Returns:
            List of docstring lines.
        """
        lines: list[str] = []
        summary = endpoint.summary or f"{endpoint.method} {endpoint.path}"

        lines.append(f'{self._indent}"""{summary}')

        if endpoint.description and endpoint.description != endpoint.summary:
            lines.append("")
            lines.append(f"{self._indent}{endpoint.description}")

        lines.append(f'{self._indent}"""')
        return lines

    def _build_body(self, endpoint: EndpointInfo) -> list[str]:
        """Build function body lines.

        Args:
            endpoint: Endpoint information.

        Returns:
            List of body lines.
        """
        lines: list[str] = []
        method = endpoint.method.upper()

        # Handle DELETE (204 No Content)
        if method == "DELETE":
            lines.append(f"{self._indent}# TODO: Implement deletion logic")
            lines.append(f"{self._indent}raise HTTPException(status_code=404, detail=\"Not found\")")
            return lines

        # Handle POST (201 Created)
        if method == "POST" and endpoint.request_schema:
            lines.append(f"{self._indent}# TODO: Implement creation logic")
            if endpoint.response_schema:
                lines.append(f"{self._indent}# Placeholder: return created resource")
                lines.append(f"{self._indent}return {endpoint.response_schema.name}(")
                lines.append(f"{self._indent}{self._indent}id=1,")
                lines.append(f"{self._indent}{self._indent}**data.model_dump(),")
                lines.append(f'{self._indent}{self._indent}created_at=datetime.now(timezone.utc).isoformat() + "Z",')
                lines.append(f"{self._indent})")
            else:
                lines.append(f"{self._indent}pass")
            return lines

        # Handle PUT (200 OK)
        if method == "PUT" and endpoint.request_schema:
            lines.append(f"{self._indent}# TODO: Implement update logic")
            if endpoint.response_schema:
                lines.append(f"{self._indent}# Placeholder: return updated resource")
                lines.append(f"{self._indent}raise HTTPException(status_code=404, detail=\"User not found\")")
            else:
                lines.append(f"{self._indent}pass")
            return lines

        # Default placeholder
        lines.append(f"{self._indent}# TODO: Implement endpoint logic")
        if endpoint.response_schema:
            lines.append(f"{self._indent}raise HTTPException(status_code=404, detail=\"Not found\")")
        else:
            lines.append(f"{self._indent}pass")

        return lines

    def _build_test_body(self, endpoint: EndpointInfo) -> list[str]:
        """Build test function body.

        Args:
            endpoint: Endpoint information.

        Returns:
            List of test body lines.
        """
        lines: list[str] = []
        method = endpoint.method.lower()
        path = self._replace_path_params(endpoint.path)

        # Build request
        if endpoint.request_schema:
            lines.append(f"{self._indent}payload = {{")
            if endpoint.request_schema:
                for field in endpoint.request_schema.fields:
                    if field.required:
                        example = self._get_example_value(field)
                        lines.append(f'{self._indent}{self._indent}"{field.name}": {example},')
            lines.append(f"{self._indent}}}")
            lines.append(f"{self._indent}response = await client.{method}(\"{path}\", json=payload)")
        else:
            lines.append(f"{self._indent}response = await client.{method}(\"{path}\")")

        lines.append("")

        # Assert status code
        expected_codes = [c for c in endpoint.response_status_codes if 200 <= c < 300]
        expected = expected_codes[0] if expected_codes else 200
        lines.append(f"{self._indent}assert response.status_code == {expected}")

        # Assert response schema if not 204
        if expected != 204 and endpoint.response_schema:
            lines.append(f"{self._indent}data = response.json()")
            for field in endpoint.response_schema.fields:
                if field.required:
                    lines.append(f'{self._indent}assert "{field.name}" in data')

        return lines

    def _generate_func_name(self, endpoint: EndpointInfo) -> str:
        """Generate function name from endpoint.

        Args:
            endpoint: Endpoint information.

        Returns:
            Function name string.
        """
        method = endpoint.method.lower()
        path_parts = endpoint.path.strip("/").replace("{", "").replace("}", "").split("/")
        name_parts = [method] + path_parts
        return "_".join(name_parts)

    def _generate_test_name(self, endpoint: EndpointInfo) -> str:
        """Generate test function name.

        Args:
            endpoint: Endpoint information.

        Returns:
            Test function name.
        """
        base = self._generate_func_name(endpoint)
        return f"test_{base}"

    def _generate_field(self, field: FieldInfo) -> str:
        """Generate field definition string.

        Args:
            field: Field information.

        Returns:
            Field definition string.
        """
        python_type = self._map_type(field.field_type)

        if not field.required:
            if field.default is not None:
                return f"{field.name}: {python_type} = {repr(field.default)}"
            else:
                return f"{field.name}: {python_type} | None = None"

        return f"{field.name}: {python_type}"

    def _map_type(self, openapi_type: str) -> str:
        """Map OpenAPI type to Python type.

        Args:
            openapi_type: OpenAPI type string.

        Returns:
            Python type string.
        """
        type_mapping = {
            "string": "str",
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "array": "list",
            "object": "dict",
        }

        # Handle array types
        if openapi_type.startswith("array["):
            inner = openapi_type[6:-1]
            inner_python = self._map_type(inner)
            return f"list[{inner_python}]"

        return type_mapping.get(openapi_type, openapi_type)

    def _replace_path_params(self, path: str) -> str:
        """Replace path parameters with example values.

        Args:
            path: URL path with parameters.

        Returns:
            Path with example values.
        """
        import re
        return re.sub(r"\{[^}]+\}", "1", path)

    def _get_example_value(self, field: FieldInfo) -> str:
        """Get example value for a field.

        Args:
            field: Field information.

        Returns:
            Example value as string.
        """
        if field.format == "email":
            return '"test@example.com"'
        if field.field_type == "string":
            return f'"{field.name}_value"'
        if field.field_type == "integer":
            return "1"
        if field.field_type == "boolean":
            return "True"
        return '""'
