"""Pytest fixtures for generated API tests."""

import os
import pytest
from httpx import AsyncClient, ASGITransport

# Change to project root directory to ensure database is created in correct location
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.user_service.main import app
from services.user_service.database import init_db, seed_sample_data


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Initialize database before running tests."""
    import asyncio

    async def init():
        await init_db()
        await seed_sample_data()

    asyncio.get_event_loop().run_until_complete(init())


@pytest.fixture
async def client():
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
