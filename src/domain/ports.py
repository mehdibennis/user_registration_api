from abc import ABC, abstractmethod
from typing import Optional

from src.domain.models import User


class UserRepository(ABC):
    @abstractmethod
    async def save(self, user: User) -> None:
        """Save a new user or update an existing one"""
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by email"""
        pass

    @abstractmethod
    async def update(self, user: User) -> None:
        """Update user details"""
        pass


class EmailService(ABC):
    @abstractmethod
    async def send_activation_code(self, email: str, code: str) -> None:
        """Send the activation code to the user's email"""
        pass
