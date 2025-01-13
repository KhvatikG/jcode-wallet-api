import os
import logging
from typing import AsyncGenerator, AsyncIterator
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from app.db.models import Base
from app.main import app
from app.db.database import get_async_session

# Настраиваем логирование
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv('../test.env')

# Выводим параметры подключения (без пароля)
db_params = {
    'user': os.getenv('DB_USER'),
    'database': os.getenv('DB_NAME'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}
logger.debug(f"Параметры подключения: {db_params}")

TEST_DATABASE_URL = f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

engine = create_async_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
    echo=True  # включаем echo для отладки SQL
)

test_async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)


@asynccontextmanager
async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
    try:
        async with test_async_session_maker() as session:
            logger.debug("Сессия базы данных создана успешно")
            yield session
    except Exception as e:
        logger.error(f"Ошибка создания сессии базы данных: {e}")
        raise


@pytest_asyncio.fixture(autouse=True)
async def setup_database() -> AsyncGenerator[None, None]:
    """Создание базы данных для каждого теста"""
    try:
        async with engine.begin() as conn:
            logger.debug("Удаление всех таблиц...")
            await conn.run_sync(Base.metadata.drop_all)
            logger.debug("Создание всех таблиц...")
            await conn.run_sync(Base.metadata.create_all)
        yield
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    except Exception as e:
        logger.error(f"Ошибка при создании базы данных: {e}")
        raise


@pytest_asyncio.fixture
async def test_session() -> AsyncGenerator[AsyncSession, None]:
    """Получение сессии"""
    async with test_async_session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def test_client() -> AsyncIterator[AsyncClient]:
    """Создание клиента для тестов"""
    app.dependency_overrides[get_async_session] = override_get_async_session

    async with AsyncClient(
            base_url="http://test",
            follow_redirects=True
    ) as client:
        yield client

    app.dependency_overrides.clear()
