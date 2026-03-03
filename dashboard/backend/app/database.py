"""Database connection and session management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from app.config import get_settings
from app.models import Base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

settings = get_settings()

# Database engine configuration
db_url = settings.database_url

# For SQLite, ensure data directory exists
if "sqlite" in db_url:
    db_path = db_url.split("///")[-1]
    if db_path.startswith("./"):
        db_path = db_path[2:]
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)

# PostgreSQL connection pool settings
engine_kwargs = {
    "echo": settings.debug,
    "future": True,
}

if "postgresql" in db_url:
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,
        "pool_recycle": 300,
    })

engine = create_async_engine(settings.database_url, **engine_kwargs)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db() -> None:
    """Initialize database tables and seed default admin user."""
    import logging

    logger = logging.getLogger(__name__)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed default admin user if no users exist
    async with async_session_maker() as session:
        from app.models import User
        from sqlalchemy import func, select

        count = (await session.execute(select(func.count(User.id)))).scalar() or 0
        if count == 0:
            import bcrypt
            import secrets

            raw_password = settings.admin_default_password or secrets.token_urlsafe(16)
            hashed = bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            admin = User(
                username="admin",
                email="admin@example.com",
                hashed_password=hashed,
                full_name="Administrator",
                role="admin",
                is_superuser=True,
                must_change_password=True,
            )
            session.add(admin)
            await session.commit()
            if settings.admin_default_password:
                logger.info("Created default admin user (admin / <from ADMIN_DEFAULT_PASSWORD>)")
            else:
                logger.warning("Created default admin user — username: admin, password: %s", raw_password)
                logger.warning("This password is shown ONCE. Change it immediately or set ADMIN_DEFAULT_PASSWORD.")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for dependency injection."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_session_context() -> AsyncGenerator[AsyncSession, None]:
    """Get database session as context manager."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
