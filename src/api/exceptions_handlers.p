from fastapi import Request, status
from fastapi.responses import JSONResponse

from src.domain.exceptions import DomainError


async def domain_exception_handler(request: Request, exc: DomainError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )
