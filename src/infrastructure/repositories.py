from typing import Optional

from src.domain.models import User
from src.domain.ports import UserRepository
from src.infrastructure.database import db


class PostgresUserRepository(UserRepository):
    async def save(self, user: User) -> None:
        query = """
            INSERT INTO users (id, email, password_hash, is_active, activation_code, activation_code_expires_at)
            VALUES ($1, $2, $3, $4, $5, $6)
        """
        async with db.pool.acquire() as conn:
            await conn.execute(
                query,
                user.id,
                user.email,
                user.password_hash,
                user.is_active,
                user.activation_code,
                user.activation_code_expires_at,
            )

    async def get_by_email(self, email: str) -> Optional[User]:
        query = "SELECT * FROM users WHERE email = $1"
        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(query, email)
            if row:
                return User(
                    id=row["id"],
                    email=row["email"],
                    password_hash=row["password_hash"],
                    is_active=row["is_active"],
                    activation_code=row["activation_code"],
                    activation_code_expires_at=row["activation_code_expires_at"],
                )
        return None

    async def update(self, user: User) -> None:
        query = """
            UPDATE users 
            SET is_active = $1, activation_code = $2, activation_code_expires_at = $3
            WHERE id = $4
        """
        async with db.pool.acquire() as conn:
            await conn.execute(
                query,
                user.is_active,
                user.activation_code,
                user.activation_code_expires_at,
                user.id,
            )
