from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from sqlmodel import select, delete

from .models import File


class FileRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, file: File) -> File:
        self._session.add(file)
        await self._session.flush()
        await self._session.refresh(file)
        return File.model_validate(file)

    async def get_one(self, id: int) -> File:
        stmt = select(File).where(File.id == id)
        result = await self._session.execute(stmt)
        file = result.scalar_one_or_none()
        return File.model_validate(file)

    async def get_one_or_none(self, id: int) -> Optional[File]:
        try:
            return await self.get_one(id)
        except NoResultFound:
            return None

    async def delete(self, id: int):
        stmt = delete(File).where(File.id == id)
        await self._session.execute(stmt)
