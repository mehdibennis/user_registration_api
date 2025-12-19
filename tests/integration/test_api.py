import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    response = await client.post(
        "/api/v1/users",
        json={"email": "test@example.com", "password": "strongpassword"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_activate_user_invalid_code(client: AsyncClient):
    # First register
    await client.post(
        "/api/v1/users",
        json={"email": "test2@example.com", "password": "strongpassword"},
    )

    # Try to activate with wrong code
    response = await client.post(
        "/api/v1/users/activate",
        json={"code": "0000"},
        auth=("test2@example.com", "strongpassword"),
    )
    assert response.status_code == 400
