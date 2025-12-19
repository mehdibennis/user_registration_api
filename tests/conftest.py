import pytest
from pathlib import Path
from httpx import ASGITransport, AsyncClient

from src.infrastructure.database import db
from src.main import app


@pytest.fixture
async def database():
    await db.connect()

    # Initialize schema
    schema_path = Path(__file__).parent.parent / "scripts" / "init.sql"
    if schema_path.exists():
        with open(schema_path, "r") as f:
            schema_sql = f.read()
            async with db.pool.acquire() as conn:
                await conn.execute(schema_sql)

    async with db.pool.acquire() as conn:
        await conn.execute("TRUNCATE TABLE users")
    yield db
    await db.disconnect()


@pytest.fixture
async def client(database):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
