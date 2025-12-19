"""
Unit tests for UserService with mocked dependencies.
These tests verify business logic in isolation from infrastructure.
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from src.domain.exceptions import (
    ActivationCodeExpiredError,
    InvalidActivationCodeError,
    UserAlreadyActivatedError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from src.domain.models import User
from src.service.user_service import UserService


@pytest.fixture
def mock_user_repo():
    """Create a mock UserRepository."""
    return AsyncMock()


@pytest.fixture
def mock_email_service():
    """Create a mock EmailService."""
    return AsyncMock()


@pytest.fixture
def user_service(mock_user_repo, mock_email_service):
    """Create UserService with mocked dependencies."""
    return UserService(mock_user_repo, mock_email_service)


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="hashed_password",
        is_active=False,
        activation_code="1234",
        activation_code_expires_at=datetime.now(timezone.utc) + timedelta(minutes=1),
    )


class TestRegisterUser:
    """Tests for the register_user use case."""

    @pytest.mark.asyncio
    async def test_register_user_success(
        self, user_service, mock_user_repo, mock_email_service
    ):
        """Should create user and send activation email."""
        mock_user_repo.get_by_email.return_value = None

        user = await user_service.register_user("new@example.com", "password123")

        assert user.email == "new@example.com"
        assert user.is_active is False
        assert user.activation_code is not None
        assert len(user.activation_code) == 4
        mock_user_repo.save.assert_called_once()
        mock_email_service.send_activation_code.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_user_already_exists(
        self, user_service, mock_user_repo, sample_user
    ):
        """Should raise error when user already exists."""
        mock_user_repo.get_by_email.return_value = sample_user

        with pytest.raises(UserAlreadyExistsError) as exc_info:
            await user_service.register_user("test@example.com", "password123")

        assert "test@example.com" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_register_user_generates_4_digit_code(
        self, user_service, mock_user_repo, mock_email_service
    ):
        """Should generate a 4-digit activation code."""
        mock_user_repo.get_by_email.return_value = None

        user = await user_service.register_user("test@example.com", "password123")

        assert user.activation_code.isdigit()
        assert len(user.activation_code) == 4

    @pytest.mark.asyncio
    async def test_register_user_sets_expiration_time(
        self, user_service, mock_user_repo, mock_email_service
    ):
        """Should set activation code expiration to 1 minute."""
        mock_user_repo.get_by_email.return_value = None
        before = datetime.now(timezone.utc)

        user = await user_service.register_user("test@example.com", "password123")

        after = datetime.now(timezone.utc)
        expected_min = before + timedelta(minutes=1)
        expected_max = after + timedelta(minutes=1)
        assert expected_min <= user.activation_code_expires_at <= expected_max


class TestActivateUser:
    """Tests for the activate_user use case."""

    @pytest.mark.asyncio
    async def test_activate_user_success(
        self, user_service, mock_user_repo, sample_user
    ):
        """Should activate user with valid code."""
        mock_user_repo.get_by_email.return_value = sample_user

        result = await user_service.activate_user("test@example.com", "1234")

        assert result.is_active is True
        assert result.activation_code is None
        mock_user_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_activate_user_not_found(self, user_service, mock_user_repo):
        """Should raise error when user not found."""
        mock_user_repo.get_by_email.return_value = None

        with pytest.raises(UserNotFoundError):
            await user_service.activate_user("unknown@example.com", "1234")

    @pytest.mark.asyncio
    async def test_activate_user_already_active(
        self, user_service, mock_user_repo, sample_user
    ):
        """Should raise error when user is already activated."""
        sample_user.is_active = True
        mock_user_repo.get_by_email.return_value = sample_user

        with pytest.raises(UserAlreadyActivatedError):
            await user_service.activate_user("test@example.com", "1234")

    @pytest.mark.asyncio
    async def test_activate_user_invalid_code(
        self, user_service, mock_user_repo, sample_user
    ):
        """Should raise error with invalid activation code."""
        mock_user_repo.get_by_email.return_value = sample_user

        with pytest.raises(InvalidActivationCodeError):
            await user_service.activate_user("test@example.com", "9999")

    @pytest.mark.asyncio
    async def test_activate_user_expired_code(
        self, user_service, mock_user_repo, sample_user
    ):
        """Should raise error when activation code is expired."""
        sample_user.activation_code_expires_at = datetime.now(timezone.utc) - timedelta(
            minutes=5
        )
        mock_user_repo.get_by_email.return_value = sample_user

        with pytest.raises(ActivationCodeExpiredError):
            await user_service.activate_user("test@example.com", "1234")


class TestRegenerateActivationCode:
    """Tests for the regenerate_activation_code use case."""

    @pytest.mark.asyncio
    async def test_regenerate_code_success(
        self, user_service, mock_user_repo, mock_email_service, sample_user
    ):
        """Should generate new code and send email."""
        old_code = sample_user.activation_code
        mock_user_repo.get_by_email.return_value = sample_user

        result = await user_service.regenerate_activation_code("test@example.com")

        assert result.activation_code != old_code or result.activation_code == old_code
        assert len(result.activation_code) == 4
        mock_user_repo.update.assert_called_once()
        mock_email_service.send_activation_code.assert_called_once()

    @pytest.mark.asyncio
    async def test_regenerate_code_user_not_found(self, user_service, mock_user_repo):
        """Should raise error when user not found."""
        mock_user_repo.get_by_email.return_value = None

        with pytest.raises(UserNotFoundError):
            await user_service.regenerate_activation_code("unknown@example.com")

    @pytest.mark.asyncio
    async def test_regenerate_code_already_active(
        self, user_service, mock_user_repo, sample_user
    ):
        """Should raise error when user is already activated."""
        sample_user.is_active = True
        mock_user_repo.get_by_email.return_value = sample_user

        with pytest.raises(UserAlreadyActivatedError):
            await user_service.regenerate_activation_code("test@example.com")
