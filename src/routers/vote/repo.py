from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from sqlmodel import select, update

from .models import Vote, Reports


class VoteRepository:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._dto = Vote

    async def get_one(self, code: Optional[str] = None) -> Vote:
        stmt = select(self._dto)
        if id:
            stmt = stmt.where(code == self._dto.code)
        result = await self._session.execute(stmt)
        user = result.scalar_one()
        return self._dto.model_validate(user)

    async def get_one_or_none(
        self, id: Optional[int] = None, email: Optional[str] = None
    ) -> Optional[Vote]:
        try:
            return await self.get_one(id, email)
        except NoResultFound:
            return None

    async def get(self) -> list[Vote]:
        stmt = select(self._dto)
        result = await self._session.execute(stmt)
        return [
            self._dto.model_validate(user) for user in result.scalars().all()
        ]

    async def create(
        self, code: str, report: Optional[Reports] = None
    ) -> Vote:
        user = self._dto(code=code, report=report)
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return self._dto.model_validate(user)

    async def update(self, code: str, report: Reports) -> Vote:
        stmt = (
            update(self._dto)
            .where(code == self._dto.code)
            .values(
                Vote(code=code, report=report).model_dump(exclude_none=True)
            )
        )
        await self._session.execute(stmt)
        return await self.get_one(code)
