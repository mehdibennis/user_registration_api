from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from src.domain.exceptions import (
    ActivationCodeExpiredError,
    InvalidActivationCodeError,
    UserAlreadyActivatedError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from src.infrastructure.database import db
from src.main import app, lifespan


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_lifespan_coverage():
    # This test ensures the lifespan context manager is covered
    async with lifespan(app):
        pass


@pytest.mark.asyncio
async def test_full_user_flow(client: AsyncClient):
    email = "flow@example.com"
    password = "password123"

    # 1. Register
    response = await client.post(
        "/api/v1/users", json={"email": email, "password": password}
    )
    assert response.status_code == 201

    # 2. Get activation code from DB
    async with db.pool.acquire() as conn:
        code = await conn.fetchval(
            "SELECT activation_code FROM users WHERE email = $1", email
        )

    # 3. Activate
    response = await client.post(
        "/api/v1/users/activate", json={"code": code}, auth=(email, password)
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is True

    # 4. Try to activate again (Already Activated)
    response = await client.post(
        "/api/v1/users/activate", json={"code": code}, auth=(email, password)
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_duplicate_user(client: AsyncClient):
    email = "duplicate@example.com"
    password = "password123"

    await client.post("/api/v1/users", json={"email": email, "password": password})
    response = await client.post(
        "/api/v1/users", json={"email": email, "password": password}
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_auth_failure_wrong_password(client: AsyncClient):
    email = "auth@example.com"
    password = "password123"
    await client.post("/api/v1/users", json={"email": email, "password": password})

    response = await client.post(
        "/api/v1/users/activate", json={"code": "1234"}, auth=(email, "wrongpassword")
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_failure_user_not_found(client: AsyncClient):
    response = await client.post(
        "/api/v1/users/activate",
        json={"code": "1234"},
        auth=("unknown@example.com", "password"),
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_activation_code_expired(client: AsyncClient):
    email = "expired@example.com"
    password = "password123"
    await client.post("/api/v1/users", json={"email": email, "password": password})

    # Manually expire the code in DB
    async with db.pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET activation_code_expires_at = $1 WHERE email = $2",
            datetime.now(timezone.utc) - timedelta(minutes=10),
            email,
        )
        code = await conn.fetchval(
            "SELECT activation_code FROM users WHERE email = $1", email
        )

    response = await client.post(
        "/api/v1/users/activate", json={"code": code}, auth=(email, password)
    )
    assert response.status_code == 400
    assert "expired" in response.json()["detail"]


@pytest.mark.asyncio
async def test_regenerate_code(client: AsyncClient):
    email = "regen@example.com"
    password = "password123"
    await client.post("/api/v1/users", json={"email": email, "password": password})

    # Get old code
    async with db.pool.acquire() as conn:
        old_code = await conn.fetchval(
            "SELECT activation_code FROM users WHERE email = $1", email
        )

    # Regenerate
    response = await client.post(
        "/api/v1/users/regenerate-code", auth=(email, password)
    )
    assert response.status_code == 200

    # Check new code
    async with db.pool.acquire() as conn:
        new_code = await conn.fetchval(
            "SELECT activation_code FROM users WHERE email = $1", email
        )

    assert old_code != new_code

    # Activate with new code
    response = await client.post(
        "/api/v1/users/activate", json={"code": new_code}, auth=(email, password)
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_regenerate_code_already_active(client: AsyncClient):
    email = "regen_active@example.com"
    password = "password123"
    await client.post("/api/v1/users", json={"email": email, "password": password})

    # Activate manually
    async with db.pool.acquire() as conn:
        await conn.execute("UPDATE users SET is_active = true WHERE email = $1", email)

    response = await client.post(
        "/api/v1/users/regenerate-code", auth=(email, password)
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_exceptions_instantiation():
    e1 = UserAlreadyExistsError("test")
    assert str(e1) == "User with email test already exists"

    e2 = UserNotFoundError("test")
    assert str(e2) == "User with email test not found"

    e3 = InvalidActivationCodeError()
    assert str(e3) == "Invalid activation code"

    e4 = ActivationCodeExpiredError()
    assert str(e4) == "Activation code has expired"

    e5 = UserAlreadyActivatedError("test")
    assert str(e5) == "User test is already active"
