from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from loguru import logger

from app.config.config import settings

DATABASE_URL = settings.get_db_url

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)


async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False,
    class_=AsyncSession
)


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Асинхронный контекстный менеджер для работы с базой данных.
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as err:
            logger.exception(f"Error in async session {err}")
            await session.rollback()
            raise
        finally:
            await session.close()
