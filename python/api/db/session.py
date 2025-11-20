"""Database session utilities and lifecycle management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from python.api.db.sql import async_session_maker, init_db
from python.api.db.vector import close_vector_dbs, init_vector_dbs


async def startup_db() -> None:
    """Initialize all databases on application startup."""
    await init_db()
    await init_vector_dbs()


async def shutdown_db() -> None:
    """Clean up database connections on application shutdown."""
    await close_vector_dbs()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database sessions outside of FastAPI dependency injection.

    Useful for background tasks, CLI scripts, or testing.
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
