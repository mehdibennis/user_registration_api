import secrets
import uuid
from datetime import datetime, timedelta, timezone

from src.core.logging import get_logger
from src.domain.exceptions import (
    ActivationCodeExpiredError,
    InvalidActivationCodeError,
    UserAlreadyActivatedError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from src.domain.models import User
from src.domain.ports import EmailService, UserRepository
from src.service.security import SecurityService

logger = get_logger(__name__)


class UserService:
    """
    Service layer implementing user registration and activation use cases.
    """

    def __init__(self, user_repo: UserRepository, email_service: EmailService):
        self.user_repo = user_repo
        self.email_service = email_service

    async def register_user(self, email: str, password: str) -> User:
        """
        Register a new user and send activation email.

        Args:
            email: User's email address.
            password: User's plain text password.

        Returns:
            The newly created User object.

        Raises:
            UserAlreadyExistsError: If a user with this email already exists.
        """
        logger.info("Attempting to register user", email=email)

        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            logger.warning("Registration failed: user already exists", email=email)
            raise UserAlreadyExistsError(email)

        password_hash = SecurityService.get_password_hash(password)
        activation_code = f"{secrets.randbelow(10000):04d}"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=1)

        new_user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=password_hash,
            is_active=False,
            activation_code=activation_code,
            activation_code_expires_at=expires_at,
        )

        await self.user_repo.save(new_user)
        await self.email_service.send_activation_code(email, activation_code)

        logger.info(
            "User registered successfully", email=email, user_id=str(new_user.id)
        )
        return new_user

    async def activate_user(self, email: str, code: str) -> User:
        """
        Activate a user account with the provided activation code.

        Args:
            email: User's email address.
            code: 4-digit activation code.

        Returns:
            The activated User object.

        Raises:
            UserNotFoundError: If no user with this email exists.
            UserAlreadyActivatedError: If the user is already active.
            InvalidActivationCodeError: If the code doesn't match.
            ActivationCodeExpiredError: If the code has expired.
        """
        logger.info("Attempting to activate user", email=email)

        user = await self.user_repo.get_by_email(email)
        if not user:
            logger.warning("Activation failed: user not found", email=email)
            raise UserNotFoundError(email)

        if user.is_active:
            logger.warning("Activation failed: user already active", email=email)
            raise UserAlreadyActivatedError(email)

        if user.activation_code != code:
            logger.warning("Activation failed: invalid code", email=email)
            raise InvalidActivationCodeError()

        if user.activation_code_expires_at and datetime.now(
            timezone.utc
        ) > user.activation_code_expires_at.replace(tzinfo=timezone.utc):
            logger.warning("Activation failed: code expired", email=email)
            raise ActivationCodeExpiredError()

        user.is_active = True
        user.activation_code = None
        user.activation_code_expires_at = None

        await self.user_repo.update(user)

        logger.info("User activated successfully", email=email, user_id=str(user.id))
        return user

    async def regenerate_activation_code(self, email: str) -> User:
        """
        Generate a new activation code for a user.

        Args:
            email: User's email address.

        Returns:
            The User object with updated activation code.

        Raises:
            UserNotFoundError: If no user with this email exists.
            UserAlreadyActivatedError: If the user is already active.
        """
        logger.info("Attempting to regenerate activation code", email=email)

        user = await self.user_repo.get_by_email(email)
        if not user:
            logger.warning("Regeneration failed: user not found", email=email)
            raise UserNotFoundError(email)

        if user.is_active:
            logger.warning("Regeneration failed: user already active", email=email)
            raise UserAlreadyActivatedError(email)

        activation_code = f"{secrets.randbelow(10000):04d}"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=1)

        user.activation_code = activation_code
        user.activation_code_expires_at = expires_at

        await self.user_repo.update(user)
        await self.email_service.send_activation_code(email, activation_code)

        logger.info("Activation code regenerated", email=email, user_id=str(user.id))
        return user
