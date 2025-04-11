from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from .models import User, ReportForm

from sqlmodel import select, update


class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_one(
        self, id: Optional[int] = None, email: Optional[str] = None
    ) -> Optional[User]:
        stmt = select(User)
        if id:
            stmt = stmt.where(User.id == id)
        if email:
            stmt = stmt.where(User.email == email)
        result = await self._session.execute(stmt)
        user: User | None = result.scalar_one_or_none()
        if user and user.form:
            return user.model_copy(update={"form": ReportForm(**user.form)})
        return user

    async def get(self) -> list[User]:
        stmt = select(User)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def create(self, email: str, hashed_password: str) -> User:
        user = User(email=email, password=hashed_password)
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def update(self, user: User) -> User:
        stmt = (
            update(User).where(User.id == user.id).values(**user.model_dump())
        )
        await self._session.execute(stmt)
        return await self.get_one(user.id)
