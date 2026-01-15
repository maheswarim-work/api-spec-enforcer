"""Pytest configuration and fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def spec_path(project_root: Path) -> Path:
    """Get the path to the OpenAPI spec."""
    return project_root / "spec" / "openapi.yaml"


@pytest.fixture
def service_path(project_root: Path) -> Path:
    """Get the path to the user service."""
    return project_root / "services" / "user_service"


@pytest.fixture
def sample_spec_content() -> str:
    """Sample OpenAPI spec content for testing."""
    return """
openapi: 3.0.3
info:
  title: Test API
  version: 1.0.0
paths:
  /items:
    get:
      operationId: list_items
      summary: List items
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ItemList'
components:
  schemas:
    Item:
      type: object
      required:
        - id
        - name
      properties:
        id:
          type: integer
        name:
          type: string
    ItemList:
      type: object
      required:
        - items
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/Item'
"""
