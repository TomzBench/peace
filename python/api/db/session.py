"""Database session utilities and lifecycle management."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from python.api.db.sql import get_session_maker, init_db
from python.api.db.vector import close_vector_db, init_vector_db

logger = logging.getLogger(__name__)


async def startup_db() -> None:
    """Initialize all databases on application startup."""
    logger.info("Starting database initialization")
    await init_db()
    await init_vector_db()
    logger.info("Database initialization complete")


async def shutdown_db() -> None:
    """Clean up database connections on application shutdown."""
    logger.info("Starting database shutdown")
    await close_vector_db()
    logger.info("Database shutdown complete")


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database sessions outside of FastAPI dependency injection.

    Useful for background tasks, CLI scripts, or testing.
    Settings are retrieved from context automatically.
    """
    logger.debug("Creating database context session")
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            logger.debug("Committing database context session")
            await session.commit()
        except Exception as e:
            logger.error(f"Error in database context session, rolling back: {e}")
            await session.rollback()
            raise
        finally:
            logger.debug("Closing database context session")
            await session.close()
