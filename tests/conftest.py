import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from src.config import settings
from src.infrastructure.database import db
from src.main import app


@pytest.fixture
async def database():
    await db.connect()
    async with db.pool.acquire() as conn:
        await conn.execute("TRUNCATE TABLE users")
    yield db
    await db.disconnect()


@pytest.fixture
async def client(database):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
