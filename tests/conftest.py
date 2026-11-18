"""Подключение к тестовой PostgreSQL и изоляция данных каждого теста."""

from collections.abc import AsyncIterator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from app.core.config import settings


@pytest_asyncio.fixture(loop_scope="function")
async def db_engine() -> AsyncIterator[AsyncEngine]:
    """Создаёт engine исключительно из настроек TEST_DB_*."""
    engine = create_async_engine(settings.test_sqlalchemy_database_uri)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture(loop_scope="function")
async def db_session(db_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Откатывает данные теста, включая commit внутри репозитория."""
    async with db_engine.connect() as connection:
        transaction = await connection.begin()
        try:
            async with AsyncSession(
                bind=connection,
                join_transaction_mode="create_savepoint",
                expire_on_commit=False,
            ) as session:
                yield session
        finally:
            await transaction.rollback()
