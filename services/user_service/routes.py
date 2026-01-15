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

from fastapi import APIRouter, HTTPException, Query

from services.user_service.database import get_all_users, get_user_by_id
from services.user_service.schemas import HTTPError, User, UserList

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
