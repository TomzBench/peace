"""SQLModel database setup and session management."""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from python.api.config import settings

# Import models so SQLModel can create tables
from python.api.models.user import User  # noqa: F401

logger = logging.getLogger(__name__)

# Create async engine
logger.info(f"Creating async engine with URL: {settings.database_url}")
engine = create_async_engine(
    settings.database_url,
    echo=settings.echo_sql,
    future=True,
)
logger.debug(f"Engine created with echo_sql={settings.echo_sql}")

# Create session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
logger.debug("Session factory created with expire_on_commit=False")


async def init_db() -> None:
    """Initialize database tables."""
    logger.info("Initializing database tables")
    async with engine.begin() as conn:
        logger.debug("Running SQLModel.metadata.create_all")
        await conn.run_sync(SQLModel.metadata.create_all)
    logger.info("Database tables initialized successfully")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions."""
    logger.debug("Creating new database session")
    async with async_session_maker() as session:
        try:
            yield session
            logger.debug("Database session completed successfully")
        except Exception as e:
            logger.error(f"Error in database session: {e}")
            raise
        finally:
            logger.debug("Closing database session")
