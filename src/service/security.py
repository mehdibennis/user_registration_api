import asyncio
from concurrent.futures import ThreadPoolExecutor

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Create a dedicated thread pool for CPU-bound password operations
# This prevents blocking the main asyncio event loop
_executor: ThreadPoolExecutor | None = None


def _get_executor() -> ThreadPoolExecutor:
    """Get or create the thread pool executor."""
    global _executor
    if _executor is None or _executor._shutdown:
        _executor = ThreadPoolExecutor(max_workers=4)
    return _executor


def shutdown_executor() -> None:
    """Gracefully shutdown the thread pool executor."""
    global _executor
    if _executor is not None:
        _executor.shutdown(wait=False)
        _executor = None


class SecurityService:
    @staticmethod
    async def verify_password(plain_password: str, hashed_password: str) -> bool:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            _get_executor(), pwd_context.verify, plain_password, hashed_password
        )

    @staticmethod
    async def get_password_hash(password: str) -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(_get_executor(), pwd_context.hash, password)
