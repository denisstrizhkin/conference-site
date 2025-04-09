from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from .models import File


class FileRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        content: bytes,
        name: str,
        type: str,
    ) -> File:
        file = File(content=content, name=name, type=type)
        self._session.add(file)
        await self._session.flush()
        await self._session.refresh(file)
        return file

    async def get(self, id: int) -> File | None:
        stmt = select(File).where(File.id == id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
