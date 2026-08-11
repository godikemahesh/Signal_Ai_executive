"""
Signal — Database Connection
Async SQLAlchemy engine connected to Supabase PostgreSQL.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.is_development,
    poolclass=NullPool,
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
    },
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncSession:
    """Dependency that yields a database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database connection and create tables if they do not exist."""
    # Import all models to ensure they are registered on Base.metadata
    import app.models.user
    import app.models.gmail
    import app.models.signal
    import app.models.entity
    import app.models.ai_decision
    import app.models.behavior
    import app.models.category

    async with engine.begin() as conn:
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        except Exception:
            pass
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections (called on app shutdown)."""
    await engine.dispose()


