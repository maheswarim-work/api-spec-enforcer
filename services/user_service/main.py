"""Main FastAPI application for the User Service."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from services.user_service.database import init_db, seed_sample_data
from services.user_service.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    await init_db()
    await seed_sample_data()
    yield
    # Shutdown (cleanup if needed)


app = FastAPI(
    title="User Management API",
    description="A simple user management API for demonstrating API contract enforcement.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
