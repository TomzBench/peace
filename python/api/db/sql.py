"""SQLModel database setup and session management."""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel

from python.api.config import get_settings

# Import models so SQLModel can create tables
from python.api.models.user import User  # noqa: F401

logger = logging.getLogger(__name__)

# Module-level cache
_engine: AsyncEngine | None = None
_session_maker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Get or create the async engine.

    Uses settings from context (set by app factory).
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        logger.info(f"Creating async engine with URL: {settings.database_url}")
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.echo_sql,
            future=True,
        )
        logger.debug(f"Engine created with echo_sql={settings.echo_sql}")
    return _engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """Get or create the session maker."""
    global _session_maker
    if _session_maker is None:
        _session_maker = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
        logger.debug("Session factory created with expire_on_commit=False")
    return _session_maker


async def init_db() -> None:
    """Initialize database tables.

    Settings are retrieved from context automatically.
    """
    logger.info("Initializing database tables")
    engine = get_engine()
    async with engine.begin() as conn:
        logger.debug("Running SQLModel.metadata.create_all")
        await conn.run_sync(SQLModel.metadata.create_all)
    logger.info("Database tables initialized successfully")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions.

    No need to inject settings - retrieved from context.
    """
    logger.debug("Creating new database session")
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            logger.debug("Database session completed successfully")
        except Exception as e:
            logger.error(f"Error in database session: {e}")
            raise
        finally:
            logger.debug("Closing database session")


def reset_db() -> None:
    """Reset database connection (useful for testing with different settings)."""
    global _engine, _session_maker
    _engine = None
    _session_maker = None
