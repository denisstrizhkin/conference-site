from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.settings import settings

engine = create_async_engine(
    settings.db_uri,
    echo=settings.echo_sql,
)
session_factory = async_sessionmaker(
    bind=engine,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with session_factory.begin() as session:
        yield session


Session = Annotated[AsyncSession, Depends(get_session)]
