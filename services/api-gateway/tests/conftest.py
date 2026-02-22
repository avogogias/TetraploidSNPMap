"""Shared test fixtures for API Gateway tests.

Uses an in-memory SQLite database with a single shared connection
so all requests within a test see the same data.
"""

import asyncio
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Override settings before importing app modules
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["COMPUTATION_SERVICE_URL"] = "http://localhost:8001"
os.environ["PROJECT_STORAGE_PATH"] = "/tmp/tpmap_test_projects"

from app.models.db import Base, get_db
from app.routers import projects, datasets, analyses

# Use a shared in-memory engine with a single connection for test isolation
_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
)
_session_factory = async_sessionmaker(
    bind=_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def _build_app() -> FastAPI:
    """Build a minimal FastAPI app with all routers for testing."""
    app = FastAPI()
    app.include_router(projects.router)
    app.include_router(datasets.router)
    app.include_router(analyses.router)
    return app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create tables before each test, drop after."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with _session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTP test client with DB dependency overridden."""
    app = _build_app()

    async def _override_get_db():
        async with _session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
