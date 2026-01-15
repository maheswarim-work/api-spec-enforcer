"""FastAPI application route inspector."""

import ast
import re
from pathlib import Path
from typing import Any

from core.models import EndpointInfo, FieldInfo, ParameterInfo, SchemaInfo


class FastAPIInspector:
    """Inspector for FastAPI application routes and schemas."""

    def __init__(self, service_path: str | Path) -> None:
        """Initialize inspector with path to service directory.

        Args:
            service_path: Path to the FastAPI service directory.
        """
        self.service_path = Path(service_path)
        self._endpoints: list[EndpointInfo] = []
        self._schemas: dict[str, SchemaInfo] = {}
        self._route_files: list[Path] = []

    def inspect(self) -> None:
        """Inspect the FastAPI application for routes and schemas."""
        self._find_route_files()
        self._parse_schemas()
        self._parse_routes()

    @property
    def endpoints(self) -> list[EndpointInfo]:
        """Get all discovered endpoints."""
        return self._endpoints

    @property
    def schemas(self) -> dict[str, SchemaInfo]:
        """Get all discovered schemas."""
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
        # Normalize path for comparison (handle path parameters)
        normalized_path = self._normalize_path(path)
        for endpoint in self._endpoints:
            if endpoint.method.upper() == method:
                if self._normalize_path(endpoint.path) == normalized_path:
                    return endpoint
        return None

    def _normalize_path(self, path: str) -> str:
        """Normalize path for comparison by replacing param names.

        Args:
            path: URL path

        Returns:
            Normalized path with generic param placeholders.
        """
        # Replace {param_name} and <param_name> with generic placeholder
        return re.sub(r"[{<][^}>]+[}>]", "{param}", path)

    def _find_route_files(self) -> None:
        """Find all Python files that might contain routes."""
        for py_file in self.service_path.rglob("*.py"):
            if py_file.name.startswith("_"):
                continue
            # Look for files likely to contain routes
            if py_file.name in ("main.py", "routes.py", "app.py", "api.py"):
                self._route_files.append(py_file)
            else:
                # Check file content for route decorators
                try:
                    content = py_file.read_text()
                    if "@app." in content or "@router." in content:
                        self._route_files.append(py_file)
                except Exception:
                    continue

    def _parse_schemas(self) -> None:
        """Parse Pydantic schemas from the service."""
        schema_files = list(self.service_path.rglob("schemas.py"))
        schema_files.extend(self.service_path.rglob("models.py"))

        for schema_file in schema_files:
            try:
                content = schema_file.read_text()
                tree = ast.parse(content)
                self._extract_pydantic_models(tree)
            except Exception:
                continue

    def _extract_pydantic_models(self, tree: ast.AST) -> None:
        """Extract Pydantic model definitions from AST.

        Args:
            tree: Parsed AST of a Python file.
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if it inherits from BaseModel
                base_names = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        base_names.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        base_names.append(base.attr)

                if "BaseModel" in base_names:
                    schema = self._parse_pydantic_class(node)
                    self._schemas[schema.name] = schema

    def _parse_pydantic_class(self, node: ast.ClassDef) -> SchemaInfo:
        """Parse a Pydantic class definition.

        Args:
            node: AST ClassDef node.

        Returns:
            Parsed SchemaInfo object.
        """
        fields: list[FieldInfo] = []
        required_fields: list[str] = []

        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                field_name = item.target.id
                field_type = self._get_annotation_type(item.annotation)

                # Check if field has a default value
                has_default = item.value is not None
                is_required = not has_default

                if is_required:
                    required_fields.append(field_name)

                fields.append(
                    FieldInfo(
                        name=field_name,
                        field_type=field_type,
                        required=is_required,
                    )
                )

        # Get docstring if present
        docstring = ""
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
        ):
            docstring = str(node.body[0].value.value)

        return SchemaInfo(
            name=node.name,
            fields=fields,
            description=docstring,
            required_fields=required_fields,
        )

    def _get_annotation_type(self, annotation: ast.expr | None) -> str:
        """Get string representation of a type annotation.

        Args:
            annotation: AST annotation node.

        Returns:
            String representation of the type.
        """
        if annotation is None:
            return "any"

        if isinstance(annotation, ast.Name):
            return annotation.id

        if isinstance(annotation, ast.Constant):
            return str(annotation.value)

        if isinstance(annotation, ast.Subscript):
            # Handle generic types like list[User], Optional[str]
            if isinstance(annotation.value, ast.Name):
                base = annotation.value.id
                if isinstance(annotation.slice, ast.Name):
                    return f"{base}[{annotation.slice.id}]"
                elif isinstance(annotation.slice, ast.Constant):
                    return f"{base}[{annotation.slice.value}]"
                else:
                    return base
            return "complex"

        if isinstance(annotation, ast.BinOp):
            # Handle union types (X | Y)
            return "union"

        return "unknown"

    def _parse_routes(self) -> None:
        """Parse route definitions from all route files."""
        for route_file in self._route_files:
            try:
                content = route_file.read_text()
                tree = ast.parse(content)
                self._extract_routes_from_ast(tree, content)
            except Exception:
                continue

    def _extract_routes_from_ast(self, tree: ast.AST, content: str) -> None:
        """Extract route definitions from AST.

        Args:
            tree: Parsed AST of a Python file.
            content: Raw file content for decorator parsing.
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) or isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    endpoint = self._parse_route_decorator(decorator, node, content)
                    if endpoint:
                        self._endpoints.append(endpoint)

    def _parse_route_decorator(
        self,
        decorator: ast.expr,
        func: ast.FunctionDef | ast.AsyncFunctionDef,
        content: str,
    ) -> EndpointInfo | None:
        """Parse a route decorator to extract endpoint info.

        Args:
            decorator: AST decorator node.
            func: AST function node.
            content: Raw file content.

        Returns:
            EndpointInfo if this is a route decorator, None otherwise.
        """
        # Handle @app.get("/path") or @router.get("/path") style
        if not isinstance(decorator, ast.Call):
            return None

        if not isinstance(decorator.func, ast.Attribute):
            return None

        attr = decorator.func
        if not isinstance(attr.value, ast.Name):
            return None

        # Check if it's a route decorator
        router_names = ("app", "router")
        method_names = ("get", "post", "put", "patch", "delete", "head", "options")

        if attr.value.id not in router_names:
            return None

        if attr.attr not in method_names:
            return None

        method = attr.attr.upper()

        # Get the path from first argument
        path = ""
        if decorator.args:
            first_arg = decorator.args[0]
            if isinstance(first_arg, ast.Constant):
                path = str(first_arg.value)

        if not path:
            return None

        # Parse function parameters
        parameters = self._parse_function_params(func)

        # Get function docstring
        summary = ""
        if (
            func.body
            and isinstance(func.body[0], ast.Expr)
            and isinstance(func.body[0].value, ast.Constant)
        ):
            summary = str(func.body[0].value.value).split("\n")[0]

        # Try to determine response status code from decorator
        status_codes = self._extract_status_codes(decorator)

        return EndpointInfo(
            path=path,
            method=method,
            operation_id=func.name,
            summary=summary,
            parameters=parameters,
            response_status_codes=status_codes,
        )

    def _parse_function_params(
        self, func: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> list[ParameterInfo]:
        """Parse function parameters to extract API parameters.

        Args:
            func: AST function node.

        Returns:
            List of ParameterInfo objects.
        """
        parameters: list[ParameterInfo] = []

        for arg in func.args.args:
            if arg.arg in ("self", "request", "db", "session"):
                continue

            param_type = self._get_annotation_type(arg.annotation)

            # Determine parameter location based on naming conventions
            location = "query"
            if "_id" in arg.arg or arg.arg == "id":
                location = "path"

            parameters.append(
                ParameterInfo(
                    name=arg.arg,
                    location=location,
                    param_type=param_type,
                )
            )

        return parameters

    def _extract_status_codes(self, decorator: ast.Call) -> list[int]:
        """Extract status codes from route decorator.

        Args:
            decorator: AST Call node for the decorator.

        Returns:
            List of status codes.
        """
        status_codes: list[int] = []

        for keyword in decorator.keywords:
            if keyword.arg == "status_code":
                if isinstance(keyword.value, ast.Constant):
                    status_codes.append(int(keyword.value.value))

        # Default to 200 if no explicit status code
        if not status_codes:
            status_codes = [200]

        return status_codes

    def to_dict(self) -> dict[str, Any]:
        """Convert inspector results to dictionary.

        Returns:
            Dictionary containing all discovered information.
        """
        return {
            "service_path": str(self.service_path),
            "endpoints": [e.to_dict() for e in self._endpoints],
            "schemas": {name: s.to_dict() for name, s in self._schemas.items()},
        }
