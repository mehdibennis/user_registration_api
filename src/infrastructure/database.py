import asyncpg

from src.config import settings


class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                dsn=settings.database_url, min_size=1, max_size=10
            )

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def get_connection(self):
        if not self.pool:
            await self.connect()
        return self.pool.acquire()


db = Database()
