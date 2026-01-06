"""
Application startup helpers: initialize external clients and bootstrap admin user.
"""
import logging
from typing import Optional
from contextlib import asynccontextmanager

import redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from backend.core.config import get_settings
from backend.core.security import get_password_hash
from backend import models

logger = logging.getLogger(__name__)
settings = get_settings()

# Async engine/session for startup tasks
def _build_async_db_url(url: str) -> str:
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://"):]
    return url


try:
    async_engine = create_async_engine(
        _build_async_db_url(settings.database_url),
        pool_pre_ping=True,
    )
    AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)
except Exception:
    async_engine = None
    AsyncSessionLocal = None


async def create_default_admin_async() -> None:
    """
    Create default admin user if not exists using async session.
    Password must be set via INITIAL_ADMIN_PASSWORD in settings/environment.
    """
    if AsyncSessionLocal is not None:
        try:
            async with AsyncSessionLocal() as session:
                try:
                    result = await session.execute(
                        select(models.User).where(models.User.username == "admin")
                    )
                    user = result.scalar_one_or_none()
                    if user:
                        return

                    initial_password = settings.initial_admin_password
                    if not initial_password:
                        logger.error(
                            "INITIAL_ADMIN_PASSWORD environment variable not set! "
                            "Default admin account will NOT be created. "
                            "Set INITIAL_ADMIN_PASSWORD to create the initial admin user."
                        )
                        return

                    logger.info("Creating default superadmin user...")
                    hashed_pwd = get_password_hash(initial_password)
                    admin = models.User(
                        username="admin",
                        hashed_password=hashed_pwd,
                        role="superadmin"
                    )
                    session.add(admin)
                    await session.commit()
                    logger.info("Default superadmin 'admin' created successfully.")
                    logger.warning("IMPORTANT: Change the admin password immediately after first login!")
                except Exception as e:
                    logger.error(f"Error creating default admin: {e}")
                    await session.rollback()
                    return
        except Exception:
            # fall through to sync
            pass

    # Sync fallback
    create_default_admin_sync()


def create_default_admin_sync() -> None:
    """
    Synchronous version for entrypoint script.
    Create default admin user if not exists.
    """
    from backend.core.database import SessionLocal  # type: ignore
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.username == "admin").first()
        if user:
            logger.info("Default admin user already exists.")
            return
        initial_password = settings.initial_admin_password
        if not initial_password:
            logger.error(
                "INITIAL_ADMIN_PASSWORD environment variable not set! "
                "Default admin account will NOT be created."
            )
            return
        logger.info("Creating default superadmin user...")
        hashed_pwd = get_password_hash(initial_password)
        admin = models.User(username="admin", hashed_password=hashed_pwd, role="superadmin")
        db.add(admin)
        db.commit()
        logger.info("Default superadmin 'admin' created successfully.")
        logger.warning("IMPORTANT: Change the admin password immediately after first login!")
    except Exception as e:
        logger.error(f"Sync error creating admin: {e}")
        db.rollback()
    finally:
        db.close()


def init_redis_client() -> Optional[redis.Redis]:
    """Create a Redis client for health checks."""
    try:
        client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )
        client.ping()
        logger.info("Redis connection established for health checks")
        return client
    except Exception as e:
        logger.warning(f"Redis not available at startup: {e}")
        return None


def get_celery_app():
    """Import and return Celery app reference (lazy import to avoid cycles)."""
    try:
        from worker.tasks import celery_app  # type: ignore
        logger.info("Celery app reference stored")
        return celery_app
    except Exception as e:
        logger.warning(f"Celery app not available: {e}")
        return None
