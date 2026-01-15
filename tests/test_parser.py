"""Tests for OpenAPI parser."""

from pathlib import Path

import pytest

from core.openapi_parser import OpenAPIParser


class TestOpenAPIParser:
    """Tests for OpenAPIParser class."""

    def test_parse_spec_file(self, spec_path: Path) -> None:
        """Test parsing the actual OpenAPI spec file."""
        parser = OpenAPIParser(spec_path)
        parser.parse()

        assert parser.title == "User Management API"
        assert parser.version == "1.0.0"
        assert len(parser.endpoints) == 5

    def test_parse_endpoints(self, spec_path: Path) -> None:
        """Test that all endpoints are parsed correctly."""
        parser = OpenAPIParser(spec_path)
        parser.parse()

        # Check we have the expected endpoints
        endpoint_keys = {e.endpoint_key for e in parser.endpoints}

        assert "GET /users" in endpoint_keys
        assert "POST /users" in endpoint_keys
        assert "GET /users/{user_id}" in endpoint_keys
        assert "PUT /users/{user_id}" in endpoint_keys
        assert "DELETE /users/{user_id}" in endpoint_keys

    def test_parse_schemas(self, spec_path: Path) -> None:
        """Test that schemas are parsed correctly."""
        parser = OpenAPIParser(spec_path)
        parser.parse()

        assert "User" in parser.schemas
        assert "UserCreate" in parser.schemas
        assert "UserUpdate" in parser.schemas
        assert "UserList" in parser.schemas

        # Check User schema fields
        user_schema = parser.schemas["User"]
        field_names = {f.name for f in user_schema.fields}

        assert "id" in field_names
        assert "email" in field_names
        assert "name" in field_names
        assert "is_active" in field_names
        assert "created_at" in field_names

    def test_get_endpoint(self, spec_path: Path) -> None:
        """Test getting a specific endpoint."""
        parser = OpenAPIParser(spec_path)
        parser.parse()

        endpoint = parser.get_endpoint("GET", "/users")
        assert endpoint is not None
        assert endpoint.operation_id == "list_users"
        assert endpoint.summary == "List all users"

    def test_get_nonexistent_endpoint(self, spec_path: Path) -> None:
        """Test getting an endpoint that doesn't exist."""
        parser = OpenAPIParser(spec_path)
        parser.parse()

        endpoint = parser.get_endpoint("GET", "/nonexistent")
        assert endpoint is None

    def test_endpoint_parameters(self, spec_path: Path) -> None:
        """Test that endpoint parameters are parsed."""
        parser = OpenAPIParser(spec_path)
        parser.parse()

        endpoint = parser.get_endpoint("GET", "/users")
        assert endpoint is not None

        param_names = {p.name for p in endpoint.parameters}
        assert "skip" in param_names
        assert "limit" in param_names

    def test_endpoint_response_codes(self, spec_path: Path) -> None:
        """Test that response status codes are parsed."""
        parser = OpenAPIParser(spec_path)
        parser.parse()

        # GET should have 200
        get_endpoint = parser.get_endpoint("GET", "/users")
        assert 200 in get_endpoint.response_status_codes

        # POST should have 201 and 422
        post_endpoint = parser.get_endpoint("POST", "/users")
        assert 201 in post_endpoint.response_status_codes
        assert 422 in post_endpoint.response_status_codes

        # DELETE should have 204 and 404
        delete_endpoint = parser.get_endpoint("DELETE", "/users/{user_id}")
        assert 204 in delete_endpoint.response_status_codes
        assert 404 in delete_endpoint.response_status_codes

    def test_to_dict(self, spec_path: Path) -> None:
        """Test conversion to dictionary."""
        parser = OpenAPIParser(spec_path)
        parser.parse()

        data = parser.to_dict()

        assert data["title"] == "User Management API"
        assert data["version"] == "1.0.0"
        assert len(data["endpoints"]) == 5
        assert "User" in data["schemas"]

    def test_file_not_found(self, tmp_path: Path) -> None:
        """Test handling of missing file."""
        parser = OpenAPIParser(tmp_path / "nonexistent.yaml")

        with pytest.raises(FileNotFoundError):
            parser.parse()

    def test_parse_from_string(self, tmp_path: Path, sample_spec_content: str) -> None:
        """Test parsing spec from string content."""
        spec_file = tmp_path / "test_spec.yaml"
        spec_file.write_text(sample_spec_content)

        parser = OpenAPIParser(spec_file)
        parser.parse()

        assert parser.title == "Test API"
        assert len(parser.endpoints) == 1
        assert "Item" in parser.schemas
