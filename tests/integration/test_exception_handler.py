import pytest
from httpx import AsyncClient

from src.api.dependencies import get_user_service
from src.domain.exceptions import DomainError
from src.main import app


@pytest.mark.asyncio
async def test_domain_exception_handler(client: AsyncClient):
    # Mock service to raise DomainError
    class MockService:
        async def register_user(self, email, password):
            raise DomainError("A generic domain error")

    # Override the dependency
    app.dependency_overrides[get_user_service] = lambda: MockService()

    try:
        response = await client.post(
            "/api/v1/users", json={"email": "error@example.com", "password": "password"}
        )

        # The global handler should catch the error and return 400
        assert response.status_code == 400
        assert response.json() == {"detail": "A generic domain error"}
    finally:
        # Cleanup the override
        app.dependency_overrides = {}
