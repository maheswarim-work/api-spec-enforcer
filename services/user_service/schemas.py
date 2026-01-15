"""Pydantic schemas for the User Service API."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    email: EmailStr = Field(..., description="User's email address")
    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    is_active: bool = Field(default=True, description="Whether the user account is active")


class UserUpdate(BaseModel):
    """Schema for updating an existing user (all fields optional)."""

    email: EmailStr | None = Field(default=None, description="User's email address")
    name: str | None = Field(default=None, min_length=1, max_length=100, description="User's full name")
    is_active: bool | None = Field(default=None, description="Whether the user account is active")


class User(BaseModel):
    """Complete user object with all fields."""

    id: int = Field(..., description="Unique identifier for the user")
    email: EmailStr = Field(..., description="User's email address")
    name: str = Field(..., description="User's full name")
    is_active: bool = Field(default=True, description="Whether the user account is active")
    created_at: datetime = Field(..., description="Timestamp when the user was created")


class UserList(BaseModel):
    """Paginated list of users."""

    users: list[User] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users in the system")


class HTTPError(BaseModel):
    """Standard HTTP error response."""

    detail: str = Field(..., description="Error message")
