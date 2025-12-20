from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from src.domain.ports import EmailService, UserRepository
from src.infrastructure.email import ConsoleEmailService
from src.infrastructure.repositories import PostgresUserRepository
from src.service.security import SecurityService
from src.service.user_service import UserService

security = HTTPBasic()


def get_user_repository() -> UserRepository:
    return PostgresUserRepository()


def get_email_service() -> EmailService:
    return ConsoleEmailService()


def get_user_service(
    repo: UserRepository = Depends(get_user_repository),
    email_service: EmailService = Depends(get_email_service),
) -> UserService:
    return UserService(repo, email_service)


async def get_current_user_email(
    credentials: HTTPBasicCredentials = Depends(security),
    repo: UserRepository = Depends(get_user_repository),
) -> str:
    user = await repo.get_by_email(credentials.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    is_valid = await SecurityService.verify_password(
        credentials.password, user.password_hash
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return user.email
