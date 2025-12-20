from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.exception_handlers import domain_exception_handler
from src.api.routes import router
from src.core.logging import get_logger
from src.domain.exceptions import DomainError
from src.infrastructure.database import db
from src.service.security import shutdown_executor

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle: startup and shutdown events."""
    logger.info("Starting application")
    await db.connect()
    logger.info("Database connection established")
    yield
    logger.info("Shutting down application")
    await db.disconnect()
    logger.info("Database connection closed")
    shutdown_executor()
    logger.info("Thread pool executor shutdown")


API_DESCRIPTION = """
## User Registration API

This API allows you to:

* **Register** a new user with email and password
* **Activate** the account using a 4-digit code sent by email
* **Regenerate** the activation code if it has expired

### Authentication

The activation and code regeneration endpoints require **Basic Authentication**
using the user's email and password.

### Activation Code

- The activation code is a **4-digit number**
- It expires after **1 minute**
- Check your email (or console logs in development) to get the code
"""

app = FastAPI(
    title="User Registration API",
    description=API_DESCRIPTION,
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Users",
            "description": "User registration and account management operations",
        }
    ],
)

app.add_exception_handler(DomainError, domain_exception_handler)  # type: ignore[arg-type]

app.include_router(router, prefix="/api/v1")


@app.get("/health", tags=["Health"], summary="Health check endpoint")
async def health_check():
    """Check if the API is running and healthy."""
    return {"status": "ok"}
