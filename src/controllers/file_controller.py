from typing import Optional, Annotated

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from fastapi import HTTPException, status, Depends
from sqlmodel import select, delete

from src.db import Session
from src.routers.files.models import File


class FileRepo:
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
        file = result.scalar_one()
        return File.model_validate(file)

    async def get(self) -> list[File]:
        stmt = select(File)
        result = await self._session.execute(stmt)
        files = result.scalars().all()
        return [File.model_validate(file) for file in files]

    async def delete(self, id: int):
        stmt = delete(File).where(File.id == id)
        await self._session.execute(stmt)


class FileController:
    def __init__(self, session: AsyncSession):
        self._repo = FileRepo(session)

    async def create(self, file: File) -> File:
        return await self._repo.create(file)

    async def get_one_or_none(self, id: int) -> Optional[File]:
        try:
            return await self._repo.get_one(id)
        except NoResultFound:
            return None

    async def get_one(self, id: int) -> File:
        file = await self.get_one_or_none(id)
        if file is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return file

    async def get(self) -> list[File]:
        return await self._repo.get()

    async def delete(self, id: int):
        await self._repo.delete(id)


def get_file_controller(session: Session) -> FileController:
    return FileController(session)


FileControllerDep = Annotated[FileController, Depends(get_file_controller)]
