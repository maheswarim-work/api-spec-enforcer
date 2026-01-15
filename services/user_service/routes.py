"""API routes for the User Service.

NOTE: This file is INTENTIONALLY INCOMPLETE for demonstration purposes.
The following endpoints are implemented:
- GET /users (list users)
- GET /users/{user_id} (get user by ID)

The following endpoints are MISSING and should be detected by the compliance checker:
- POST /users (create user)
- PUT /users/{user_id} (update user)
- DELETE /users/{user_id} (delete user)
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from services.user_service.database import (
    get_all_users,
    get_user_by_id,
    create_user as db_create_user,
    update_user as db_update_user,
    delete_user as db_delete_user,
)
from services.user_service.schemas import HTTPError, User, UserList
from services.user_service.schemas import UserCreate, UserUpdate
from fastapi import Response

router = APIRouter(tags=["users"])


@router.get("/users", response_model=UserList)
async def list_users(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of records to return"),
) -> UserList:
    """List all users.

    Retrieve a paginated list of all users in the system.
    """
    users, total = await get_all_users(skip=skip, limit=limit)
    return UserList(
        users=[User(**u) for u in users],
        total=total,
    )


@router.get("/users/{user_id}", response_model=User, responses={404: {"model": HTTPError}})
async def get_user(user_id: int) -> User:
    """Get user by ID.

    Retrieve a specific user by their unique identifier.
    """
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)


# =============================================================================
# MISSING ENDPOINTS (for compliance checker demonstration)
# =============================================================================
# The following endpoints are defined in spec/openapi.yaml but NOT implemented:
#
# POST /users - Create a new user
# PUT /users/{user_id} - Update user by ID
# DELETE /users/{user_id} - Delete user by ID
#
# These will be detected as compliance gaps and can be auto-generated.
# =============================================================================


@router.post("/users", status_code=201)
async def create_user(data: UserCreate) -> User:
    """Create a new user

    Create a new user with the provided information
    """
    user_data = await db_create_user(
        email=data.email,
        name=data.name,
        is_active=data.is_active if data.is_active is not None else True,
    )
    return User(**user_data)


@router.put("/users/{user_id}")
async def update_user(user_id: int, data: UserUpdate) -> User:
    """Update user by ID

    Update an existing user's information
    """
    user_data = await db_update_user(
        user_id=user_id,
        email=data.email,
        name=data.name,
        is_active=data.is_active,
    )
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user_data)


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: int) -> None:
    """Delete user by ID

    Permanently delete a user from the system
    """
    deleted = await db_delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
