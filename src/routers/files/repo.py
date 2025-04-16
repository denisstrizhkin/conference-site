from sqlalchemy.ext.asyncio import AsyncSession
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

    async def get(self, id: int) -> File | None:
        stmt = select(File).where(File.id == id)
        result = await self._session.execute(stmt)
        file: File | None = result.scalar_one_or_none()
        if file is None:
            return None
        return File.model_validate(file)

    async def delete(self, id: int):
        stmt = delete(File).where(File.id == id)
        await self._session.execute(stmt)
