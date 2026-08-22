"""
Database connection module for Polymarket Analytics Platform.

Provides async connection management and connection pooling for PostgreSQL.
"""

import os
import asyncpg
from contextlib import asynccontextmanager
from typing import Optional, AsyncIterator
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    host: str = "localhost"
    port: int = 5432
    user: str = "polymarket"
    password: str = ""
    database: str = "polymarket"
    min_size: int = 5
    max_size: int = 20

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create config from environment variables"""
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            user=os.getenv("DB_USER", "polymarket"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "polymarket"),
            min_size=int(os.getenv("DB_POOL_MIN", "5")),
            max_size=int(os.getenv("DB_POOL_MAX", "20"))
        )


class DatabaseConnection:
    """Async database connection manager with pooling"""

    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig.from_env()
        self._pool: Optional[asyncpg.pool.Pool] = None

    async def create_pool(self) -> asyncpg.pool.Pool:
        """Create connection pool"""
        if self._pool is not None:
            return self._pool

        logger.info(
            f"Creating database pool: {self.config.user}@{self.config.host}:"
            f"{self.config.port}/{self.config.database}"
        )

        self._pool = await asyncpg.create_pool(
            host=self.config.host,
            port=self.config.port,
            user=self.config.user,
            password=self.config.password,
            database=self.config.database,
            min_size=self.config.min_size,
            max_size=self.config.max_size,
            command_timeout=60
        )

        logger.info("Database pool created successfully")
        return self._pool

    async def close_pool(self):
        """Close connection pool"""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Database pool closed")

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[asyncpg.Connection]:
        """Acquire connection from pool"""
        if self._pool is None:
            await self.create_pool()

        async with self._pool.acquire() as connection:
            yield connection

    async def execute(self, query: str, *args, timeout: float = None) -> str:
        """Execute a query and return the status"""
        async with self.acquire() as conn:
            return await conn.execute(query, *args, timeout=timeout)

    async def fetch(
        self,
        query: str,
        *args,
        timeout: float = None
    ) -> list[asyncpg.Record]:
        """Execute query and return results"""
        async with self.acquire() as conn:
            return await conn.fetch(query, *args, timeout=timeout)

    async def fetchrow(
        self,
        query: str,
        *args,
        timeout: float = None
    ) -> Optional[asyncpg.Record]:
        """Execute query and return first row"""
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args, timeout=timeout)

    async def fetchval(
        self,
        query: str,
        *args,
        column: int = 0,
        timeout: float = None
    ):
        """Execute query and return single value"""
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args, column=column, timeout=timeout)

    async def execute_many(
        self,
        command: str,
        args: list[tuple],
        timeout: float = None
    ):
        """Execute command multiple times with different parameters"""
        async with self.acquire() as conn:
            async with conn.transaction():
                await conn.executemany(command, args, timeout=timeout)

    async def health_check(self) -> bool:
        """Check if database connection is healthy"""
        try:
            result = await self.fetchval("SELECT 1")
            return result == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database connection instance
db: Optional[DatabaseConnection] = None


async def get_db() -> DatabaseConnection:
    """Get or create global database connection"""
    global db
    if db is None:
        db = DatabaseConnection()
        await db.create_pool()
    return db


async def close_db():
    """Close global database connection"""
    global db
    if db:
        await db.close_pool()
        db = None
