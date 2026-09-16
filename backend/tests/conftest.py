"""
Pytest configuration for async tests with proper DB isolation.
Uses a session-scoped AsyncClient to prevent asyncpg event loop issues.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from sqlalchemy import text

from app.core.database import async_session_factory, engine
from app.main import app


@pytest.fixture(scope="session")
async def client():
    """Session-scoped async HTTP client that reuses the same event loop."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


@pytest.fixture(autouse=True, scope="session")
async def setup_and_teardown_db():
    """Clean test data before session and dispose engine after."""
    async with async_session_factory() as session:
        await session.execute(text("DELETE FROM tutor_messages"))
        await session.execute(text("DELETE FROM tutor_sessions"))
        await session.execute(text("DELETE FROM math_expressions"))
        await session.execute(text("DELETE FROM learning_modules"))
        await session.execute(text("DELETE FROM documents"))
        await session.execute(text("DELETE FROM users"))
        await session.commit()
    yield
    await engine.dispose()
