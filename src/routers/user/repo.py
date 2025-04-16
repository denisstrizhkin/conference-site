from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from sqlmodel import select, update

from .models import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_one(
        self, id: Optional[int] = None, email: Optional[str] = None
    ) -> User:
        stmt = select(User)
        if id:
            stmt = stmt.where(id == User.id)
        if email:
            stmt = stmt.where(email == User.email)
        result = await self._session.execute(stmt)
        user = result.scalar_one()
        return User.model_validate(user)

    async def get_one_or_none(
        self, id: Optional[int] = None, email: Optional[str] = None
    ) -> Optional[User]:
        try:
            return await self.get_one(id, email)
        except NoResultFound:
            return None

    async def get(self) -> list[User]:
        stmt = select(User)
        result = await self._session.execute(stmt)
        return [User.model_validate(user) for user in result.scalars().all()]

    async def create(self, email: str, hashed_password: str) -> User:
        user = User(email=email, password=hashed_password)
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return User.model_validate(user)

    async def update(self, user: User) -> User:
        stmt = (
            update(User).where(user.id == User.id).values(**user.model_dump())
        )
        await self._session.execute(stmt)
        return await self.get_one(id=user.id)
