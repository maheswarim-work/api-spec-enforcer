"""Database setup and utilities for User Service."""

from datetime import datetime, timezone
from typing import Any

import aiosqlite

DATABASE_PATH = "users.db"


async def init_db() -> None:
    """Initialize the SQLite database with required tables."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TEXT NOT NULL
            )
        """)
        await db.commit()


async def get_db() -> aiosqlite.Connection:
    """Get a database connection.

    Returns:
        Database connection instance.
    """
    return await aiosqlite.connect(DATABASE_PATH)


async def get_all_users(skip: int = 0, limit: int = 10) -> tuple[list[dict[str, Any]], int]:
    """Get all users with pagination.

    Args:
        skip: Number of records to skip.
        limit: Maximum number of records to return.

    Returns:
        Tuple of (users list, total count).
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Get total count
        async with db.execute("SELECT COUNT(*) as count FROM users") as cursor:
            row = await cursor.fetchone()
            total = row["count"] if row else 0

        # Get paginated users
        async with db.execute(
            "SELECT * FROM users LIMIT ? OFFSET ?", (limit, skip)
        ) as cursor:
            rows = await cursor.fetchall()
            users = [dict(row) for row in rows]

    return users, total


async def get_user_by_id(user_id: int) -> dict[str, Any] | None:
    """Get a user by ID.

    Args:
        user_id: The user's unique identifier.

    Returns:
        User dict if found, None otherwise.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def create_user(email: str, name: str, is_active: bool = True) -> dict[str, Any]:
    """Create a new user.

    Args:
        email: User's email address.
        name: User's full name.
        is_active: Whether the account is active.

    Returns:
        Created user dict.
    """
    created_at = datetime.now(timezone.utc).isoformat()

    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO users (email, name, is_active, created_at) VALUES (?, ?, ?, ?)",
            (email, name, is_active, created_at),
        )
        await db.commit()
        user_id = cursor.lastrowid

    return {
        "id": user_id,
        "email": email,
        "name": name,
        "is_active": is_active,
        "created_at": created_at,
    }


async def update_user(
    user_id: int, email: str | None = None, name: str | None = None, is_active: bool | None = None
) -> dict[str, Any] | None:
    """Update an existing user.

    Args:
        user_id: The user's unique identifier.
        email: New email address (optional).
        name: New name (optional).
        is_active: New active status (optional).

    Returns:
        Updated user dict if found, None otherwise.
    """
    user = await get_user_by_id(user_id)
    if not user:
        return None

    updates = []
    values = []

    if email is not None:
        updates.append("email = ?")
        values.append(email)
    if name is not None:
        updates.append("name = ?")
        values.append(name)
    if is_active is not None:
        updates.append("is_active = ?")
        values.append(is_active)

    if not updates:
        return user

    values.append(user_id)

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
            tuple(values),
        )
        await db.commit()

    return await get_user_by_id(user_id)


async def delete_user(user_id: int) -> bool:
    """Delete a user by ID.

    Args:
        user_id: The user's unique identifier.

    Returns:
        True if user was deleted, False if not found.
    """
    user = await get_user_by_id(user_id)
    if not user:
        return False

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        await db.commit()

    return True


async def seed_sample_data() -> None:
    """Seed the database with sample users for testing."""
    sample_users = [
        ("alice@example.com", "Alice Johnson", True),
        ("bob@example.com", "Bob Smith", True),
        ("charlie@example.com", "Charlie Brown", False),
    ]

    for email, name, is_active in sample_users:
        try:
            await create_user(email, name, is_active)
        except Exception:
            # User might already exist
            pass
