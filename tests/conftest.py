import os
import logging
from typing import AsyncGenerator, AsyncIterator
import pytest
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


@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """Create engine instance for the session."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        pool_size=5,  # Уменьшаем размер пула
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
        echo=True
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Create session for each test."""
    async_session = async_sessionmaker(
        db_engine,
        expire_on_commit=False,
        class_=AsyncSession
    )
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def setup_database(db_engine):
    """Create test database for each test."""
    try:
        async with db_engine.begin() as conn:
            logger.debug("Удаление всех таблиц...")
            await conn.run_sync(Base.metadata.drop_all)
            logger.debug("Создание всех таблиц...")
            await conn.run_sync(Base.metadata.create_all)
        yield
    except Exception as e:
        logger.error(f"Ошибка при создании базы данных: {e}")
        raise
    finally:
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@asynccontextmanager
async def override_get_db():
    """Переопределение зависимости для тестов."""
    try:
        async_session = async_sessionmaker(
            db_engine,
            expire_on_commit=False,
            class_=AsyncSession
        )
        async with async_session() as session:
            yield session
    finally:
        await session.close()


@pytest_asyncio.fixture
async def test_client() -> AsyncIterator[AsyncClient]:
    """Create test client."""
    app.dependency_overrides[get_async_session] = override_get_db

    # Используем async with для создания клиента
    async with AsyncClient(
            base_url="http://tests",
            follow_redirects=True
    ) as client:
        yield client

    app.dependency_overrides.clear()
